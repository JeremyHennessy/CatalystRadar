"""Current-analysis structural SEC-header rows; never financial signal extraction.

No prices, first-public inference, historical decision reconstruction or trading.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
from archive_reviewed_filings import identity, validate, MAX_BYTES
from study_split_audit import instant

MODE='CURRENT_HEADER_FEATURES_NOT_FINANCIAL_SIGNALS'
FEATURES=('header_item_count','header_reports_results_of_operations','header_reports_regulation_fd',
          'header_reports_material_agreement','header_is_8k_amendment')

def sha(raw):return hashlib.sha256(raw).hexdigest()

def header_features(raw,cik,accession):
    validate(raw,cik,accession)
    start=raw.index(b'<SEC-HEADER>');end=raw.index(b'</SEC-HEADER>')+len(b'</SEC-HEADER>')
    header=raw[start:end]
    forms=re.findall(rb'CONFORMED SUBMISSION TYPE:\s*([^\r\n]+)',header)
    if len(forms)!=1 or forms[0].strip()not in (b'8-K',b'8-K/A'):
        raise ValueError('unambiguous 8-K header required')
    items=[x.strip()for x in re.findall(rb'ITEM INFORMATION:\s*([^\r\n]+)',header)]
    values=(len(items),int(b'Results of Operations and Financial Condition'in items),
        int(b'Regulation FD Disclosure'in items),int(b'Entry into a Material Definitive Agreement'in items),
        int(forms[0].strip()==b'8-K/A'))
    return dict(zip(FEATURES,values)),{'byte_start':start,'byte_end':end,'sha256':sha(header)}

def build(reviews_path,archive_dir,computed_at=None):
    reviews_raw=Path(reviews_path).read_bytes();reviews=json.loads(reviews_raw)['records']
    if not isinstance(reviews,list)or not 1<=len(reviews)<=10:raise ValueError('bounded review sample required')
    if len({r['accession']for r in reviews})!=len(reviews):raise ValueError('duplicate review')
    computed_at=computed_at or datetime.now(timezone.utc).isoformat();now=instant(computed_at)
    archive_dir=Path(archive_dir).resolve();mp=archive_dir/'manifest.jsonl'
    manifest=mp.read_bytes()if mp.exists()else b''
    receipts=[json.loads(x)for x in manifest.splitlines()]
    by_id={r['accession']:r for r in receipts}
    if len(by_id)!=len(receipts):raise ValueError('conflicting receipt identity')
    rows=[]
    for review in reviews:
        cik,acc,url=identity(review)
        row={'event_id':acc,'issuer_id':cik,'review_status':review['status'],
             'review_reason':review['reason'],'computed_utc':computed_at,
             'first_public_utc':None,'decision_utc':None,'outcome':None,
             'financial_comparators':None,'financial_extraction_verified':False,
             'eligible':False,'features':[],'status':'MISSING_OR_INVALID_SOURCE',
             'blockers':['FIRST_PUBLIC_UNVERIFIED','FINANCIAL_COMPARATORS_UNRESOLVED',
                         'NO_FROZEN_DECISION_WINDOW','PRICE_ACTION_HALT_OUTCOMES_UNQUALIFIED']}
        try:
            r=by_id[acc]
            if r['status']!='ARCHIVED_IDENTITY_VERIFIED' or r['issuer_cik']!=cik or r['url']!=url:raise ValueError('identity')
            if r['sha256']!=review['source_sha256'] or r['prior_recorded_sha256']!=review['source_sha256']:raise ValueError('review source differs')
            if not instant(r['request_utc'])<=instant(r['retrieved_utc'])<=now:raise ValueError('clock')
            if r['archive_file']!=r['sha256']+'.txt':raise ValueError('filename')
            path=(archive_dir/r['archive_file']).resolve()
            if path.parent!=archive_dir:raise ValueError('escape')
            raw=path.read_bytes()
            if len(raw)>MAX_BYTES or sha(raw)!=r['sha256'] or len(raw)!=r['byte_count']:raise ValueError('bytes')
            values,span=header_features(raw,cik,acc)
            source={'source_ref':url,'sha256':r['sha256'],'observed_utc':r['retrieved_utc'],'header_span':span}
            row['features']=[{'name':name,'value':values[name],'computed_utc':computed_at,'sources':[source]}for name in FEATURES]
            row['status']='STRUCTURAL_HEADER_FEATURES_COMPUTED_NOW'
        except (KeyError,ValueError,TypeError,OSError):
            row['blockers'].append('SOURCE_MISSING_CHANGED_OR_INVALID')
        rows.append(row)
    return {'mode':MODE,'computed_at':computed_at,'reviews_sha256':sha(reviews_raw),
            'manifest_sha256':sha(manifest),'feature_names':list(FEATURES),'rows':rows,
            'structural_feature_rows':sum(bool(r['features'])for r in rows),
            'source_authenticity_verified':False,'historical_availability_verified':False,
            'financial_signals':0,'orders':0,'forecast_probability':None,
            'limitations':['Retrospective manual sample, not prospective selection or a training dataset.',
                'Header item categories do not establish earnings growth, a guidance raise or a customer contract.',
                'Zero means an explicit marker absent from the complete header, not absence of a business event.',
                'All values computed now; no pre-event knowledge or historic decisions claimed.']}



def read_recorded_features(report,reviews_raw,checkpoint_records,as_of):
    """Validate recorded bindings only; public builds cannot recompute private bytes."""
    if report.get('mode')!=MODE or report.get('reviews_sha256')!=sha(reviews_raw):raise ValueError('feature input mismatch')
    if report.get('feature_names')!=list(FEATURES) or report.get('financial_signals')!=0 or report.get('orders')!=0:raise ValueError('unexpected feature/signal schema')
    if report.get('source_authenticity_verified')is not False or report.get('historical_availability_verified')is not False or report.get('forecast_probability')is not None:raise ValueError('unsupported qualification')
    computed=instant(report['computed_at'])
    if computed>instant(as_of):raise ValueError('future extraction')
    expected={r['accession']:r for r in json.loads(reviews_raw)['records']}
    rows=report['rows']
    if not isinstance(rows,list)or len(rows)!=len(expected):raise ValueError('incomplete rows')
    seen=set();ready={}
    for row in rows:
        acc=row['event_id']
        if acc in seen or acc not in expected:raise ValueError('duplicate/unknown feature row')
        seen.add(acc);review=expected[acc]
        if row['issuer_id']!=str(int(review['issuer_cik'])) or row['computed_utc']!=report['computed_at']:raise ValueError('identity/clock mismatch')
        if any(row[k]is not None for k in ('first_public_utc','decision_utc','outcome','financial_comparators'))or row['financial_extraction_verified']is not False or row['eligible']is not False:raise ValueError('unexpected qualification')
        features=row['features']
        if not features:continue
        if row['status']!='STRUCTURAL_HEADER_FEATURES_COMPUTED_NOW' or [f['name']for f in features]!=list(FEATURES):raise ValueError('partial feature row')
        checkpoint=checkpoint_records.get(acc)
        if not checkpoint or checkpoint['prior_hash_matches']is not True:raise ValueError('no bound original checkpoint')
        for f in features:
            value=f['value']
            if type(value)is not int or value<0 or (f['name']!='header_item_count'and value not in (0,1)):raise ValueError('invalid structural count')
            if f['computed_utc']!=report['computed_at']or len(f['sources'])!=1:raise ValueError('feature evidence schema')
            s=f['sources'][0];span=s['header_span']
            if s['sha256']!=review['source_sha256']or s['sha256']!=checkpoint['sha256']or s['source_ref']!=identity(review)[2]or s['observed_utc']!=checkpoint['retrieved_utc']:raise ValueError('source binding mismatch')
            if instant(s['observed_utc'])>computed:raise ValueError('future source')
            if (type(span['byte_start'])is not int or type(span['byte_end'])is not int or
                not 0<=span['byte_start']<span['byte_end']<=100_000 or not re.fullmatch('[a-f0-9]{64}',span['sha256'])):raise ValueError('invalid header span')
        ready[acc]=row
    if report['structural_feature_rows']!=len(ready):raise ValueError('count mismatch')
    return ready


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--reviews',required=True);p.add_argument('--archive-dir',required=True);p.add_argument('--output',required=True);a=p.parse_args()
    result=build(a.reviews,a.archive_dir)
    with Path(a.output).open('x')as f:f.write(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'rows':len(result['rows']),'structural_feature_rows':result['structural_feature_rows'],'financial_signals':0}))

