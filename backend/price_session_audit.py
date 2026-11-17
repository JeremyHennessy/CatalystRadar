"""Offline scheduled-date coverage diagnostic. Does not qualify prices for use."""
import argparse,base64,hashlib,json,re
from datetime import date,datetime,timedelta,timezone
from pathlib import Path
from financial_pair_candidates import publish,write_private
from openfigi_evidence import read_pinned,stamp
from private_prices import unique_object,metadata
CLOSED={'2026-01-01','2026-01-19','2026-02-16','2026-04-03','2026-05-25','2026-06-19','2026-07-03','2026-09-07','2026-11-26','2026-12-25'}
EARLY={'2026-11-27','2026-12-24'}
SOURCES=['https://www.nasdaq.com/holiday-trading-hours','https://www.nyse.com/trade/hours-calendars']

def day(value):
    if not isinstance(value,str):raise ValueError('date must be text')
    d=date.fromisoformat(value)
    if value!=d.isoformat() or d.year!=2026:raise ValueError('unsupported date/calendar year')
    return d

def scheduled(start,end):
    a,b=day(start),day(end)
    if a>b:raise ValueError('inverted window')
    result=[]
    while a<=b:
        if a.weekday()<5 and a.isoformat() not in CLOSED:result.append(a.isoformat())
        a+=timedelta(days=1)
    return result

def compare(dates,start,end):
    if not isinstance(dates,list) or len(dates)>1000:raise ValueError('date count')
    for d in dates:day(d)
    if len(set(dates))!=len(dates):raise ValueError('duplicate date')
    expected=set(scheduled(start,end));actual=set(dates)
    return {'expected_scheduled_sessions':len(expected),'observed_dates':len(actual),'missing_scheduled_dates':sorted(expected-actual),'unexpected_dates':sorted(actual-expected),'matches_scheduled_date_set':expected==actual}

def audit(directory,manifest_path,manifest_sha,start,end):
    scheduled(start,end) # The requested window is independent of available data bounds.
    manifest,_=read_pinned(manifest_path,manifest_sha,100000)
    if not isinstance(manifest,dict) or not isinstance(manifest.get('snapshots'),list) or not 1<=len(manifest['snapshots'])<=11:raise ValueError('manifest bounds')
    files=list(Path(directory).glob('2026*.json'))
    if len(files)!=len(manifest['snapshots']):raise ValueError('snapshot file count')
    by_hash={}
    for p in files:
        with p.open('rb') as f:b=f.read(3000001)
        if len(b)>3000000:raise ValueError('snapshot bound')
        h=hashlib.sha256(b).hexdigest()
        if h in by_hash:raise ValueError('duplicate snapshot')
        by_hash[h]=p
    reports=[];seen=set();evidence=[]
    for ref in manifest['snapshots']:
        if not isinstance(ref,dict) or not isinstance(ref.get('symbol'),str) or not re.fullmatch('[A-Z]{1,5}',ref['symbol']) or ref['symbol'] in seen:raise ValueError('manifest symbol')
        seen.add(ref['symbol']);p=by_hash.get(ref['snapshot_sha256'])
        if p is None:raise ValueError('snapshot pin missing')
        snap,_=read_pinned(p,ref['snapshot_sha256'],3000000)
        if snap['symbol']!=ref['symbol'] or snap['observed_utc']!=ref['observed_utc'] or snap['source_function']!='TIME_SERIES_DAILY' or snap['source_outputsize']!='compact' or snap['source_endpoint']!='https://www.alphavantage.co/query':raise ValueError('snapshot source identity')
        observed=stamp(snap['observed_utc']);raw=base64.b64decode(snap['response_base64'],validate=True)
        if len(raw)>2000000 or hashlib.sha256(raw).hexdigest()!=snap['response_sha256'] or snap['response_sha256']!=ref['response_sha256']:raise ValueError('response pin')
        def bad(v):raise ValueError('nonstandard JSON constant')
        body=json.loads(raw,object_pairs_hook=unique_object,parse_constant=bad)
        quality=metadata(raw,ref['symbol'],observed)
        if quality!=snap['quality'] or quality['returned_rows']!=ref['rows'] or quality['first_session']!=ref['first_session'] or quality['last_session']!=ref['last_session']:raise ValueError('prior quality mismatch')
        dates=sorted(body['Time Series (Daily)'])
        result=compare(dates,start,end)
        reports.append({'symbol':ref['symbol'],'observed_utc':snap['observed_utc'],'snapshot_sha256':ref['snapshot_sha256'],'response_sha256':ref['response_sha256'],**result})
        evidence.append({'symbol':ref['symbol'],'dates':dates,'prior_quality':quality})
    summary={'schema_version':1,'status':'SCHEDULED_SESSION_DATE_COMPARISON_ONLY','audit_completed_at':datetime.now(timezone.utc).isoformat(),'input_manifest_sha256':manifest_sha,
      'window_start':start,'window_end':end,'calendar_year':2026,'calendar_sources':SOURCES,'calendar_checked_on':'2026-11-17','scheduled_full_closures_in_window':sorted(d for d in CLOSED if start<=d<=end),'scheduled_early_close_sessions_in_window':sorted(d for d in EARLY if start<=d<=end),
      'symbols_checked':len(reports),'total_retained_dates':sum(r['observed_dates'] for r in reports),'symbols_matching_date_set':sum(r['matches_scheduled_date_set'] for r in reports),'results':reports,
      'collector_calendar_complete_flag_changed':False,'security_identity_verified':False,'corporate_actions_verified':False,'training_ready':False,'execution_ready':False,
      'limitations':['Comparison is against published scheduled 2026 US equity sessions, not proof of actual exchange operations or absence of unplanned closures.',
       'Historical listing continuity, individual security halts, identity and corporate actions are not established by matching dates.',
       'One daily row does not prove full intraday coverage, consolidated volume, auction price, executable liquidity or correct returns.',
       'Existing snapshot raw-schema validation is rechecked but its calendar_complete/eligible flags remain false; no collector/workflow or gate is changed.',
       'Fixed requested window is not derived from available rows. No completeness outside that window or historical point-in-time availability claimed.',
       'No new provider calls or price redistribution; account-specific training/redistribution rights remain unverified.']}
    return summary,evidence

if __name__=='__main__':
    p=argparse.ArgumentParser()
    for n in ('directory','manifest-path','manifest-sha','start','end','output-directory'):p.add_argument('--'+n,required=True)
    a=p.parse_args();out=Path(a.output_directory).resolve()
    if out.is_relative_to(Path(__file__).resolve().parents[1]) or not out.parent.is_dir():raise ValueError('trusted private parent outside checkout required')
    out.mkdir(mode=0o700,exist_ok=False);write_private(out/'INCOMPLETE',{'status':'INCOMPLETE_NOT_USABLE'})
    args=vars(a);args.pop('output_directory');summary,evidence=audit(**args);publish(out,summary,evidence);print(json.dumps(summary))
