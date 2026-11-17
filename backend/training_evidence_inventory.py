"""Read-only inventory of retained research evidence, not admission or model training.

No provider calls, report regeneration, private-byte access, execution imports or
changes to inputs. Missing evidence never becomes a zero or an affirmative gate.
"""
import argparse,collections,hashlib,json,re,subprocess
from pathlib import Path
from normalize_candidates import normalize,MAX_REPORTS
from private_prices import unique_object

FEATURES='data/filing_feature_rows.json'
FROZEN='data/research_report.json'
LEDGER='data/paper_ledger.json'
LATEST='data/latest_scan.json'
MANIFESTS=['web/prepared/summary.json','web/notes/summary.json','web/holdings/summary.json','web/formd/summary.json','web/smalloffers/summary.json','web/financial-history/summary.json']
MAX_INPUT_BYTES=8*1024*1024

def _invalid_constant(value):
    raise ValueError('nonstandard JSON numeric constant')

def _list(value,name):
    if not isinstance(value,list) or len(value)>10000:raise ValueError('bounded '+name+' list required')
    return value

def assess_features(document):
    if not isinstance(document,dict):raise ValueError('feature document required')
    rows=_list(document.get('rows'),'feature rows');seen=set()
    counts=collections.Counter(feature_rows=len(rows),feature_values=0,declared_eligible_rows=0,rows_with_decision=0,rows_with_outcome=0,rows_with_decision_and_outcome=0,rows_with_first_public_time=0,financial_extraction_declared_verified=0)
    for row in rows:
        if not isinstance(row,dict):raise ValueError('feature row object required')
        event=row.get('event_id')
        if not isinstance(event,str) or not event or event in seen:raise ValueError('unique feature event required')
        seen.add(event)
        for key in ['eligible','financial_extraction_verified']:
            if type(row.get(key)) is not bool:raise ValueError('explicit feature verification flags required')
        if any(key not in row for key in ['decision_utc','outcome','first_public_utc']):raise ValueError('explicit missing feature context required')
        features=_list(row.get('features'),'feature values');counts['feature_values']+=len(features)
        # Presence is not validity, authenticity, comparability or admission.
        decision=row['decision_utc'] is not None;outcome=row['outcome'] is not None
        counts['declared_eligible_rows']+=row['eligible'];counts['financial_extraction_declared_verified']+=row['financial_extraction_verified']
        counts['rows_with_decision']+=decision;counts['rows_with_outcome']+=outcome;counts['rows_with_decision_and_outcome']+=decision and outcome
        counts['rows_with_first_public_time']+=row['first_public_utc'] is not None
    impossible=counts['rows_with_decision_and_outcome']==0
    return {'scope':'RETAINED_FEATURE_ROWS_ONLY_NOT_ALL_PRIVATE_DATA','counts':dict(counts),'qualified_example_count':0 if impossible else None,'readiness':'BLOCKED_NO_DECISION_OUTCOME_PAIRS' if impossible else 'UNASSESSED_REQUIRES_INDEPENDENT_ADMISSION','qualification_verified':False,'presence_is_not_validation':True,'source_clock_authentication':'NOT_ASSESSED','security_identity':'NOT_ASSESSED','training_rights':'NOT_ASSESSED','corporate_action_and_outcome_validation':'NOT_ASSESSED','model_training_performed':False,'predictive_metrics':None}

def build_inventory(root):
    root=Path(root).resolve();hashes={}
    def read(rel,cap=MAX_INPUT_BYTES):
        path=(root/rel).resolve()
        if not path.is_relative_to(root) or path.stat().st_size>cap:raise ValueError('input path or byte bound')
        raw=path.read_bytes();hashes[rel]=hashlib.sha256(raw).hexdigest()
        return json.loads(raw,object_pairs_hook=unique_object,parse_constant=_invalid_constant)
    feature=assess_features(read(FEATURES));frozen=read(FROZEN);ledger=read(LEDGER);latest=read(LATEST)
    if frozen.get('mode')!='REAL_ARCHIVE_READINESS_NOT_FORECAST' or not isinstance(frozen.get('counts'),dict):raise ValueError('frozen report schema')
    frozen_counts={k:frozen['counts'].get(k) for k in ['reviewed_records','qualified_observations','outcomes_available']}
    if any(type(v) is not int or v<0 for v in frozen_counts.values()):raise ValueError('frozen report counts')
    candidate_count=frozen.get('candidate_rehearsal',{}).get('counts',{}).get('metadata_candidates')
    if candidate_count is not None and (type(candidate_count) is not int or candidate_count<0):raise ValueError('frozen candidate count')
    for k in ['orders','fills','positions']:_list(ledger.get(k),'ledger '+k)
    if type(ledger.get('simulation_enabled')) is not bool:raise ValueError('ledger state missing')
    files=sorted((root/'data/sec-observations').glob('*.json'))
    if not files or len(files)>MAX_REPORTS:raise ValueError('bounded retained receipt inventory required')
    reports=[read(p.relative_to(root).as_posix()) for p in files]
    if not any(r==latest for r in reports):raise ValueError('latest scan has no identical retained receipt')
    # Strictly decode all referenced snapshots before calling the existing normalizer.
    # It verifies hash, byte count, CIK, metadata clocks and preserves failed sources.
    for report in reports:
        for source in report.get('sources',[]):
            path=source.get('archive_path')
            if path is None:continue
            sha=source.get('sha256')
            if not isinstance(sha,str) or not re.fullmatch('[a-f0-9]{64}',sha) or path!='data/sec-snapshots/'+sha+'.json':raise ValueError('snapshot identity')
            if path not in hashes:read(path,4*1024*1024)
    normalized=normalize(reports,root)
    manifests=[]
    for path in MANIFESTS:
        if not (root/path).exists():manifests.append({'path':path,'status':'MISSING','table_rows':None});continue
        m=read(path);counts=m.get('table_rows')
        if not isinstance(counts,dict) or any(type(n) is not int or n<0 for n in counts.values()):raise ValueError('prepared manifest counts')
        manifests.append({'path':path,'status':'RECORDED_SUMMARY_NOT_PRIVATE_DB_REVERIFICATION','table_rows':counts,'training_examples_inferred':False})
    try:
        head=subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'],text=True,stderr=subprocess.DEVNULL).strip()
        if not re.fullmatch('[a-f0-9]{40}',head):head=None
    except (OSError,subprocess.CalledProcessError):head=None
    for rel,sha in hashes.items():
        if hashlib.sha256((root/rel).read_bytes()).hexdigest()!=sha:raise ValueError('input changed during inventory')
    metadata={'retained_scan_receipts':len(reports),'unique_metadata_candidates':normalized['candidate_count'],'metadata_observations':normalized['candidate_observation_count'],'source_observation_status_counts':dict(sorted(collections.Counter(r['status'] for r in normalized['source_results']).items())),'latest_run_id':latest['run_id'],'latest_finished_at':latest['finished_at'],'first_public_verified':False,'training_examples_inferred':False}
    return {'version':1,'meaning':'RESEARCH_EVIDENCE_INVENTORY_NOT_TRAINING_ADMISSION','basis_git_head':head,'basis':'HASHED_WORKING_TREE_INPUTS_NOT_COMMIT_ATTESTATION','input_sha256':dict(sorted(hashes.items())),'metadata':metadata,'frozen_report':{'generated_at':frozen.get('generated_at'),'declared_counts':frozen_counts,'declared_metadata_candidate_count':candidate_count,'not_regenerated':True},'feature_evidence':feature,'prepared_sources':manifests,'paper_state':{'simulation_enabled':ledger['simulation_enabled'],'order_count':len(ledger['orders']),'fill_count':len(ledger['fills']),'position_count':len(ledger['positions']),'not_modified':True},'limitations':['Scope is retained repository evidence. Private source databases/receipts and all possible cohorts are not reverified by this inventory.','Metadata observations, prepared numeric rows, declared eligibility and source-byte integrity are not qualified training examples.','Zero decision/outcome pairs proves zero usable examples only within these retained feature rows; otherwise qualification count stays unknown.','A source rights registry, point-in-time security identity, authenticated availability, feature recomputation, qualified outcome labels and chronological evaluation remain prerequisites.','Frozen report and current metadata are different dated views; neither is silently replaced. No model, prediction, order, fill or return is produced.']}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    # Never overwrite existing evidence; caller selects a separate research artifact.
    result=build_inventory(a.root)
    with a.output.open('x') as f:json.dump(result,f,indent=2,allow_nan=False);f.write('\n')
