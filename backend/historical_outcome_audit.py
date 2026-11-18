"""Fixed-policy historical research exclusion audit; never constructs returns."""
import argparse
import hashlib
import json
from pathlib import Path

FEATURE_SHA='db3af91a42cb7d9bc948af75ec47f8900855afb997549c4c1d4955cf701f2453'
READINESS_SHA='0a0cc2fea2e9baffeeedfb3d303b53df28373e9ad4e6e2c420a8922c55f758da'
POLICY={
 'id':'results-header-next-session-close-v1',
 'question':'What descriptive close-to-close changes follow retained results-of-operations headers?',
 'selection':'All retained rows with results-of-operations header=1 and amendment=0, ordered by accession; no replacements or price-coverage selection.',
 'entry_convention':'First regular-session close strictly after independently verified event first-public time; next actual trading-session close is endpoint.',
 'status':'RETROSPECTIVE_RESEARCH_SPECIFICATION_NOT_FROZEN_HISTORICAL_DECISION',
 'causal_or_predictive_claim':False,
 'no_intraday_interpolation':True,
 'no_execution_fill_claim':True}

def read_pinned(path, expected):
    with Path(path).open('rb') as f: raw=f.read(2_000_001)
    if len(raw)>2_000_000 or hashlib.sha256(raw).hexdigest()!=expected:
        raise ValueError('input bound or reviewed snapshot hash mismatch')
    return json.loads(raw)

def audit_rows(rows, readiness):
    """Internal deterministic diagnostics, not an admission API or fresh source audit."""
    if not isinstance(rows,list) or len(rows)>100:raise ValueError('row bounds')
    selected=[];excluded=[];seen=set()
    for row in sorted(rows,key=lambda r:r['event_id']):
        event=row['event_id']
        if event in seen:raise ValueError('duplicate event')
        seen.add(event);features={}
        for f in row['features']:
            if f['name'] in features:raise ValueError('duplicate feature')
            features[f['name']]=f['value']
        results=features.get('header_reports_results_of_operations');amendment=features.get('header_is_8k_amendment')
        if type(results) is not int or results not in (0,1) or type(amendment) is not int or amendment not in (0,1):
            raise ValueError('missing or invalid selection feature')
        if results!=1 or amendment!=0:
            excluded.append({'event_id':event,'reason':'AMENDMENT_EXCLUDED_BY_POLICY' if amendment else 'NO_RESULTS_HEADER'})
            continue
        # These historical source bounds remain unqualified even if someone adds
        # a timestamp/eligible flag to an input. Presence is not authentication.
        missing=['VERIFIED_EVENT_FIRST_PUBLIC_TIME','SOURCE_BOUND_ENTRY_CONVENTION_AND_DECISION',
                 'HISTORICAL_SECURITY_CLASS_MAPPING','INTENDED_USE_PRICE_RIGHTS',
                 'EFFECTIVE_CORPORATE_ACTION_COVERAGE','QUALIFIED_ENTRY_AND_NEXT_SESSION_ENDPOINTS']
        selected.append({'event_id':event,'issuer_cik':str(row['issuer_id']).zfill(10),
            'classification':'REPORTED_RESULTS_HEADER_NOT_VERIFIED_EARNINGS_EVENT',
            'declared_first_public_present':row.get('first_public_utc') is not None,
            'declared_decision_present':row.get('decision_utc') is not None,
            'status':'EXCLUDED_INSUFFICIENT_EVIDENCE','first_missing_dependency':missing[0],
            'missing_dependencies':missing,'entry_session':None,'endpoint_session':None,
            'return_value':None,'qualified':False})
    p=readiness['retained_price_evidence']
    return {'version':1,'policy':POLICY,'selection_count':len(selected),'universe_count':len(rows),
        'selected':selected,'excluded_by_selection':excluded,'qualified_outcomes':0,
        'price_evidence_reference':{k:p[k] for k in ('symbols','sessions_per_symbol','first_session','last_session',
            'intraday_coverage_verified','corporate_actions_verified','historical_security_identity_verified','training_rights_verified')},
        'price_reference_scope':'Prior reviewed metadata checkpoint, not a fresh raw-price or rights audit; no ticker join attempted.',
        'execution_ready':False,'training_ready':False,
        'limitations':['Header disclosure classification is not proof of earnings content, novelty or independent economic event.',
          'Retrospective specification is not a backdated decision or point-in-time availability receipt.',
          'No comparison group or causal test, no returns computed, and no licensed price values exposed.',
          'This fixed audit abstains even if declared fields are filled; changing qualifications requires new reviewed source evidence.']}

def build(root):
    root=Path(root)
    f=read_pinned(root/'data/filing_feature_rows.json',FEATURE_SHA)
    r=read_pinned(root/'docs/research/horizon-readiness-2026-11-17.json',READINESS_SHA)
    result=audit_rows(f['rows'],r)
    result['input_sha256']={'feature_rows':FEATURE_SHA,'horizon_readiness':READINESS_SHA}
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('root');p.add_argument('output');a=p.parse_args()
    with Path(a.output).open('x') as f:json.dump(build(a.root),f,indent=2);f.write('\n')
