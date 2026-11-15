"""Offline all-observed SEC metadata normalization, no date-window filtering.

Consumes retained reports and hash-bound public snapshots. No provider calls,
classification or activation. First retained observation is NOT first-public.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path
from discover_sec import parse, rows
from fact_admission import unknown_families

MAX_REPORTS=400
MAX_ROWS_PER_SOURCE=20000

def normalize(reports, root):
    root=Path(root).resolve()
    if not isinstance(reports,list) or len(reports)>MAX_REPORTS:raise ValueError('bounded report list required')
    candidates={};source_results=[];report_ids=set()
    for report in sorted(reports,key=lambda x:x['run_id']):
        rid=report['run_id']
        if rid in report_ids:raise ValueError('duplicate run id')
        report_ids.add(rid)
        if not isinstance(report['sources'],list) or len(report['sources'])>20:raise ValueError('bounded source list required')
        for source in report['sources']:
            sr={'run_id':rid,'source_sha256':source.get('sha256'),'ticker_context':source.get('ticker'),
                'status':'UNAVAILABLE','candidate_rows':0,'error':None}
            source_results.append(sr)
            if 'archive_path' not in source:
                sr['error']='SOURCE_NOT_RETAINED';continue
            try:
                digest=source['sha256']
                if not re.fullmatch(r'[a-f0-9]{64}',digest):raise ValueError('bad snapshot hash')
                if source['archive_path']!='data/sec-snapshots/'+digest+'.json':raise ValueError('unexpected snapshot path')
                path=(root/source['archive_path']).resolve()
                if root not in path.parents:raise ValueError('snapshot outside root')
                if path.stat().st_size>4*1024*1024:raise ValueError('snapshot size cap')
                raw=path.read_bytes()
                if hashlib.sha256(raw).hexdigest()!=digest:raise ValueError('snapshot hash mismatch')
                if 'byte_count' in source and source['byte_count']!=len(raw):raise ValueError('snapshot length mismatch')
                observed=parse(source['retrieved_utc']);start=parse(report['started_at']);finish=parse(report['finished_at'])
                if not start<=observed<=finish:raise ValueError('observation outside report')
                j=json.loads(raw)
                if not re.fullmatch(r'[0-9]{1,10}',str(j['cik'])) or int(j['cik'])==0:raise ValueError('invalid CIK')
                cik=str(int(j['cik'])).zfill(10)
                if source['url']!=f'https://data.sec.gov/submissions/CIK{cik}.json':raise ValueError('source CIK mismatch')
                recent=j['filings']['recent']
                required=('accessionNumber','filingDate','acceptanceDateTime','form','primaryDocument')
                if not isinstance(recent,dict) or any(not isinstance(recent.get(k),list) for k in required):
                    raise ValueError('required submission columns must be lists')
                rr=rows(recent)
                if len(rr)>MAX_ROWS_PER_SOURCE:raise ValueError('source row cap')
                sr['status']='HASH_AND_METADATA_VALIDATED'
            except (ValueError,KeyError,TypeError,AttributeError,OSError,OverflowError):
                sr['status']='INVALID';sr['error']='SNAPSHOT_OR_METADATA_VALIDATION_FAILED';continue
            for index,row in enumerate(rr):
                if row['form'] not in ('8-K','8-K/A'):continue
                sr['candidate_rows']+=1
                accession=row.get('accessionNumber');issues=[]
                if not isinstance(accession,str) or not re.fullmatch(r'\d{10}-\d{2}-\d{6}',accession):issues.append('INVALID_ACCESSION')
                accepted=row.get('acceptanceDateTime')
                try:
                    accepted_time=parse(accepted)
                    if accepted_time>observed:issues.append('ACCEPTANCE_AFTER_OBSERVATION')
                except (ValueError,TypeError,AttributeError):issues.append('INVALID_ACCEPTANCE_CLOCK');accepted_time=None
                # Invalid accessions remain visible without merging unrelated rows.
                key=f'{cik}:{accession}' if 'INVALID_ACCESSION' not in issues else f'{cik}:invalid:{rid}:{digest}:{index}'
                c=candidates.setdefault(key,{'candidate_id':key,'issuer_cik':cik,'accession':accession,
                    'first_retained_observation_utc':observed.isoformat(),'first_public_utc':None,
                    'event_group':None,'status':'METADATA_ONLY_UNQUALIFIED','observations':[],
                    'family_admission':unknown_families(),'qualified':False,'outcome':None})
                c['first_retained_observation_utc']=min(c['first_retained_observation_utc'],observed.isoformat())
                c['observations'].append({'run_id':rid,'row_index':index,'source_sha256':digest,
                    'observed_utc':observed.isoformat(),'ticker_context':source.get('ticker'),
                    'historical_security_mapping_verified':False,'form':row['form'],
                    'sec_accepted_utc':accepted,'filing_date':row.get('filingDate'),
                    'primary_document':row.get('primaryDocument'),'issues':issues,
                    'older_than_96h_at_observation':None if accepted_time is None else (observed-accepted_time).total_seconds()>96*3600})
    for c in candidates.values():
        signatures={json.dumps([o['form'],o['sec_accepted_utc'],o['filing_date'],o['primary_document']],sort_keys=True) for o in c['observations']}
        c['metadata_revision_conflict']=len(signatures)>1
        if c['metadata_revision_conflict'] or any(o['issues'] for o in c['observations']):c['status']='HELD_METADATA_CONFLICT_OR_INVALID'
    return {'mode':'RETROSPECTIVE_CAPTURE_REHEARSAL_NOT_ACTIVATED','report_ids':sorted(report_ids),
            'candidate_count':len(candidates),'candidate_observation_count':sum(len(c['observations']) for c in candidates.values()),
            'source_results':source_results,'report_errors':[{'run_id':r['run_id'],'errors':r.get('errors',[])} for r in sorted(reports,key=lambda x:x['run_id'])],
            'candidates':sorted(candidates.values(),key=lambda c:c['candidate_id']),
            'complete_history':False,'first_public_verified':False,'qualified_count':0,'orders_created':0}

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,required=True);ap.add_argument('--report',type=Path,action='append',required=True);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
    result=normalize([json.loads(p.read_text()) for p in a.report],a.root)
    with a.output.open('x') as f:json.dump(result,f,indent=2,allow_nan=False)
