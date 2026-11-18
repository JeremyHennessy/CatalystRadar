"""Conservative observation-clock coverage bound, never an outcome calculator."""
import argparse,hashlib,json,zipfile
from datetime import datetime,time,timedelta
from pathlib import Path
from zoneinfo import ZoneInfo
from price_session_audit import audit,scheduled,EARLY
from completed_note_offering import ARCHIVE_SHA as ZIP_SHA

# Frozen receipt set: no selective substitution or automatic admission of new runs.
RECEIPTS = {'20261115T021704113580Z.json': '495adca83e0ba8105e728418afb8d91cc320bce76486f4defd958a7744af493c', '20261116T181527938922Z.json': '151b16c795c00cf1a57f7b1a165e98027b8ea5a3a1810046670604dc9569be98', '20261116T210556263571Z.json': '2893f3b65634d04ba52b042737561c148dc041a6ac7ff9f6157b76263cb62333', '20261117T142027564955Z.json': '47596af22a63358a80380bf5cb83d01e8f2ac0622c6cc19151b663780fbc950c', '20261117T162921498482Z.json': 'c5831af0db3ac4ade2c2b167a79c1257f33387d6b73171acbe6c7e6e5d29735b', '20261117T174017624874Z.json': '040af576a3f1050db1a59e11b877420df7f5431859fa7da1f01ecdcec8862b22', '20261117T195421146121Z.json': 'fbc6dc9b0287a113ab2f2ecdd61f4a7810fad525040c0afdbb37e1ea056f8db9'}
PRICE_MANIFEST_SHA='d03acb2c6e4162d32b11d193dc71778a116a2438cebf455ae5d5a8e59ddf4747'

def stamp(value):
    d=datetime.fromisoformat(value.replace('Z','+00:00'))
    if d.tzinfo is None:raise ValueError('observation timezone required')
    return d

def candidate_dates(observed):
    clock=stamp(observed);day=clock.astimezone(ZoneInfo('America/New_York')).date()
    sessions=scheduled(day.isoformat(),(day+timedelta(days=10)).isoformat())
    future=[d for d in sessions if datetime.combine(datetime.fromisoformat(d).date(),time(13 if d in EARLY else 16),ZoneInfo('America/New_York'))>clock]
    if len(future)<2:raise ValueError('calendar coverage')
    return future[:2]

def read(path,pin,limit):
    with Path(path).open('rb') as f:b=f.read(limit+1)
    if len(b)>limit or hashlib.sha256(b).hexdigest()!=pin:raise ValueError('input pin/bound')
    return b

def summarize(records,dates):
    groups={}
    for r in records:
        key=(r['issuer_cik'],r['accession']);stamp(r['observed_utc'])
        groups.setdefault(key,[]).append(r)
    identities={}
    for cik,acc in groups:identities.setdefault(acc,set()).add(cik)
    out=[]
    for (cik,acc),history in sorted(groups.items()):
        earliest=min(history,key=lambda r:stamp(r['observed_utc']));start,end=candidate_dates(earliest['observed_utc'])
        # No ticker join. Even the union of every retained provider date must
        # cover both dates before any identity-specific study could proceed.
        missing=[d for d in (start,end) if d not in dates]
        out.append({'issuer_cik':cik,'accession':acc,'earliest_retained_observation_utc':earliest['observed_utc'],
          'clock_kind':earliest['kind'],'accession_issuer_conflict':len(identities[acc])>1,'receipt_count':len(history),'candidate_scheduled_start':start,
          'candidate_scheduled_endpoint':end,'missing_from_all_retained_series':missing,
          'coverage_bound_passed':not missing,'security_join_attempted':False,
          'qualified':False,'return_value':None,'first_public_utc':None,
          'missing_dependencies':(['POST_OBSERVATION_ENDPOINT_COVERAGE'] if missing else [])+['HISTORICAL_SECURITY_CLASS_ASSOCIATION','CORPORATE_ACTION_AND_ACTUAL_SESSION_QUALIFICATION','SOURCE_SPECIFIC_EVENT_INTERPRETATION','PUBLIC_DERIVED_DATA_RIGHTS_IF_PUBLISHED']})
    return {'version':1,'policy':'ALL_RETAINED_8K_OBSERVATIONS_FIRST_SCHEDULED_CLOSE_STRICTLY_AFTER_OBSERVATION_THEN_NEXT_SESSION_V1',
      'policy_timing':'RETROSPECTIVE_SPECIFICATION_NOT_HISTORICAL_DECISION','events':out,'issuer_accession_pairs':len(out),'unique_accessions':len(identities),
      'qualified_outcomes':0,'coverage_bound_passes':sum(r['coverage_bound_passed'] for r in out),
      'no_fill_claim':True,'execution_ready':False,'training_ready':False,
      'limitations':['Earliest retained observation is not first public availability, event occurrence or proof of novel content.',
       'Scheduled calendar dates are candidates, not verified actual sessions, security trading or official closing-auction prices.',
       'Union-of-series date test is a necessary coverage bound only, never issuer/ticker/security matching.',
       'Private individual research permission is distinct from public redistribution/derived-data rights; no quotes or return values are published.']}

def build(root,archive,prices):
    root=Path(root);records=[];runs=[]
    actual={p.name for p in (root/'data/sec-observations').glob('*.json')}
    if actual!=set(RECEIPTS):raise ValueError('receipt inventory changed')
    for name,pin in sorted(RECEIPTS.items()):
        run=json.loads(read(root/'data/sec-observations'/name,pin,100000))
        runs.append({'receipt':name,'sha256':pin,'events':len(run['events']),'errors':len(run['errors'])})
        for e in run['events']:
            if e['form'] not in ('8-K','8-K/A'):raise ValueError('unsupported form')
            records.append({'issuer_cik':e['issuer_cik'].zfill(10),'accession':e['accession'],'observed_utc':e['observed_utc'],'kind':'METADATA_OBSERVED'})
    raw=read(archive,ZIP_SHA,20_000_000)
    import io
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        if z.getinfo('manifest.jsonl').file_size>100000:raise ValueError('manifest bound')
        manifest=z.read('manifest.jsonl')
        for line in manifest.splitlines():
            r=json.loads(line)
            if r['status']!='ARCHIVED_IDENTITY_VERIFIED':raise ValueError('original status')
            records.append({'issuer_cik':r['issuer_cik'].zfill(10),'accession':r['accession'],'observed_utc':r['retrieved_utc'],'kind':'ORIGINAL_RETRIEVED'})
    price_summary,evidence=audit(prices,Path(prices)/'audit-summary.json',PRICE_MANIFEST_SHA,'2026-06-26','2026-11-16')
    dates=set(d for series in evidence for d in series['dates'])
    result=summarize(records,dates);result['runs']=runs;result['original_archive_sha256']=ZIP_SHA
    result['price_manifest_sha256']=PRICE_MANIFEST_SHA;result['price_snapshots_revalidated']=len(evidence)
    result['retained_date_bounds']=[min(dates),max(dates)];return result

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('root');p.add_argument('archive');p.add_argument('prices');p.add_argument('output');a=p.parse_args()
    result=build(a.root,a.archive,a.prices)
    with Path(a.output).open('x') as f:json.dump(result,f,indent=2);f.write('\n')
