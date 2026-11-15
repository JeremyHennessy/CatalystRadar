"""Connect the latest retained actual scan to an offline research summary.

Latest-run scope only. Full historical receipts remain retained independently;
this bounded dashboard build does not load every run into memory.
"""
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
from discover_sec import parse
from normalize_candidates import normalize

MODE='LATEST_RETAINED_RUN_REHEARSAL_NOT_ACTIVATED'

def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()

def summarize_latest(root,latest,as_of):
    root=Path(root).resolve()
    out={'mode':MODE,'status':'UNAVAILABLE','scope':'latest retained run only, not all history or a prospective cohort',
         'run_id':latest.get('run_id'),'counts':None,'source_observations':[],
         'family_fact_unknowns':None,'input_sha256':{},'normalizer_output_sha256':None,
         'failure_reason':None,'qualified_count':0,'outcomes_available':0,
         'protocol_activated':False,'first_public_verified':False,'orders_created':0}
    rid=latest.get('run_id')
    if not isinstance(rid,str) or not re.fullmatch(r'[0-9]{8}T[0-9]{12}Z',rid):
        out['failure_reason']='NO_RETAINED_RUN_ID';return out
    relative=f'data/sec-observations/{rid}.json';path=(root/relative).resolve()
    try:
        if root not in path.parents:raise ValueError('report outside root')
        if path.stat().st_size>4*1024*1024:raise ValueError('report size cap')
        raw=path.read_bytes();out['input_sha256'][relative]=hashlib.sha256(raw).hexdigest()
        report=json.loads(raw)
        if canonical(report)!=canonical(latest):raise ValueError('latest and retained reports differ')
        if parse(report['finished_at'])>parse(as_of):raise ValueError('observation report after summary')
        result=normalize([report],root)
    except (ValueError,KeyError,TypeError,AttributeError,OSError,OverflowError):
        out['failure_reason']='RETAINED_REPORT_MISSING_INVALID_OR_MISMATCHED';return out
    candidates=result['candidates'];source_counts=Counter(s['status'] for s in result['source_results'])
    held=sum(c['status']=='HELD_METADATA_CONFLICT_OR_INVALID' for c in candidates)
    out['status']='REHEARSAL_AVAILABLE' if source_counts.get('HASH_AND_METADATA_VALIDATED',0)>0 and not report.get('errors') and source_counts.get('INVALID',0)==0 and source_counts.get('UNAVAILABLE',0)==0 else 'PARTIAL_REHEARSAL'
    out['started_at']=report['started_at'];out['finished_at']=report['finished_at']
    out['normalizer_output_sha256']=hashlib.sha256(canonical(result)).hexdigest()
    out['counts']={'metadata_candidates':len(candidates),'candidate_observations':result['candidate_observation_count'],
        'older_than_96h_candidates':sum(any(o['older_than_96h_at_observation'] is True for o in c['observations']) for c in candidates),
        'metadata_conflict_or_invalid_candidates':held,'metadata_only_unqualified_candidates':len(candidates)-held,
        'source_status_counts':dict(sorted(source_counts.items())),
        'unknown_underlying_event_groups':sum(c['event_group'] is None for c in candidates),
        'unknown_outcomes':sum(c['outcome'] is None for c in candidates)}
    families={}
    for c in candidates:
        for family,admission in c['family_admission'].items():
            counter=families.setdefault(family,{'candidate_status_counts':Counter(),'missing_field_counts':Counter(),'invalid_field_counts':Counter()})
            counter['candidate_status_counts'][admission['status']]+=1
            counter['missing_field_counts'].update(admission['missing_fields'])
            counter['invalid_field_counts'].update(admission['invalid_fields'])
    out['family_fact_unknowns']={family:{kind:dict(sorted(counts.items())) for kind,counts in counters.items()} for family,counters in sorted(families.items())}
    for src,checked in zip(report['sources'],result['source_results']):
        out['source_observations'].append({'source_url':src.get('url'),'ticker_context':src.get('ticker'),
            'request_utc':src.get('request_utc'),'retrieved_utc':src.get('retrieved_utc'),
            'declared_sha256':src.get('sha256'),'validation_status':checked['status'],
            'candidate_rows':checked['candidate_rows'],'failure_reason':checked['error']})
        if checked['status']=='HASH_AND_METADATA_VALIDATED':out['input_sha256'][src['archive_path']]=src['sha256']
    out['scan_errors']=report.get('errors',[])
    out['limitations']=['Metadata candidates are not financial samples or new announcements.',
        'All family facts and underlying event groups remain unknown; no classifications executed.',
        'No complete filing history, authenticated observation time, or first-public availability established.',
        'Detailed candidate exclusions and observations reproduce through normalize_candidates using this retained run.']
    return out
