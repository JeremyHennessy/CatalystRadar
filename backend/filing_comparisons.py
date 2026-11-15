"""Bounded retrospective issuer-reported comparison, not a signal engine.

Only the explicitly reviewed IEH revenue paragraph is supported. No API facts,
current ticker mapping, amended replacement, historical decision or trade.
"""
import argparse
from decimal import Decimal, ROUND_HALF_EVEN
import json
from pathlib import Path
import re
from filing_feature_rows import build as build_headers, sha, header_features

ACCESSION='0001174947-26-000991'
CIK='50292'
MODE='RETROSPECTIVE_REPORTED_PAIR_NOT_QUALIFIED'
PATTERN=(rb'For the quarter ended September 30, 2026, IEH had revenues of '
         rb'\$([0-9,]+)\s+as compared to \$([0-9,]+) for the quarter ended '
         rb'September 30, 2025, reflecting a 51% increase;')

def supplemental_pairs(paragraph):
    # Same-release values only. Never call a negative-baseline ratio growth.
    specifications=[
        ('operating_profit_loss','reported dollar units',
         rb'an operating profit of \$([0-9,]+) for 2nd\s+quarter fiscal year 2027 as compared to an operating loss of \$([0-9,]+) for 2nd quarter fiscal year 2026'),
        ('net_income_loss','reported dollar units',
         rb'net income of \$([0-9,]+) for 2nd\s+quarter fiscal year 2027 as compared to a net loss of \$([0-9,]+) for 2nd quarter fiscal year 2026'),
        ('basic_earnings_loss_per_share','reported dollar units per basic share',
         rb'a basic gain per share of \$(\.[0-9]+) for\s+2nd quarter fiscal year 2027 as compared to a basic loss per share of \$(\.[0-9]+) for 2nd quarter fiscal year 2026')]
    pairs=[]
    for name,unit,pattern in specifications:
        row={'metric':name,'unit':unit,'currency_iso':None,'scale':1,
             'current_value':None,'prior_value':None,'difference_reported_units':None,
             'current_fiscal_period':'second quarter fiscal year 2027',
             'prior_fiscal_period':'second quarter fiscal year 2026',
             'calculated_percent_change':None,'status':'MISSING_OR_AMBIGUOUS_LITERAL_PAIR',
             'basis':'same-release narrative; basic EPS is not diluted EPS',
             'cross_filing_comparability_verified':False}
        matches=list(re.finditer(pattern,paragraph))
        if len(matches)==1:
            m=matches[0];current=Decimal(m[1].decode().replace(',',''));prior=-Decimal(m[2].decode().replace(',',''))
            if current>=0 and prior<0:
                row.update(current_value=str(current),prior_value=str(prior),
                    difference_reported_units=str(current-prior),status='REPORTED_POSITIVE_VS_LOSS_PAIR',
                    percentage_blocker='NEGATIVE_BASELINE_NOT_MEANINGFUL_GROWTH_PERCENT')
        pairs.append(row)
    return pairs

def extract(raw,cik,accession):
    values,_=header_features(raw,cik,accession)
    if values['header_is_8k_amendment']:raise ValueError('amendment requires separate review')
    if cik!=CIK or accession!=ACCESSION:raise ValueError('unsupported issuer/accession')
    candidates=[]
    for d in re.finditer(rb'<DOCUMENT>.*?</DOCUMENT>',raw,re.S):
        doc=d.group()
        if not re.search(rb'<TYPE>EX-99\.1\s*\n',doc):continue
        for p in re.finditer(rb'<P\b[^>]*>.*?</P>',doc,re.S|re.I):
            matches=list(re.finditer(PATTERN,p.group()))
            for m in matches:candidates.append((d.start()+p.start(),d.start()+p.end(),m))
    if len(candidates)!=1:raise ValueError('one unambiguous literal exhibit paragraph required')
    start,end,m=candidates[0]
    current=Decimal(m[1].decode().replace(',',''));prior=Decimal(m[2].decode().replace(',',''))
    if current<0 or prior<=0:raise ValueError('positive comparator required')
    # Fail closed if the purported rounded issuer percentage contradicts values.
    pct=(current/prior-1)*100
    if pct.quantize(Decimal('1'),rounding=ROUND_HALF_EVEN)!=Decimal(51):raise ValueError('reported rounding inconsistency')
    return {'metric':'issuer_reported_revenue','basis':'same-release revenue narrative; not independently audited',
        'current':{'value':str(current),'period_end':'2026-09-30','period_start':None,'period_label':'quarter ended September 30, 2026'},
        'prior':{'value':str(prior),'period_end':'2025-09-30','period_start':None,'period_label':'quarter ended September 30, 2025'},
        'unit':'reported dollar units','currency_iso':None,'scale':1,
        'difference_reported_units':str(current-prior),
        'calculated_percent_change':str(pct.quantize(Decimal('0.000001'))),
        'issuer_reported_rounded_percent_change':'51',
        'cross_filing_comparability_verified':False,'corporate_action_adjustment_verified':False,
        'additional_reported_pairs':supplemental_pairs(raw[start:end]),
        'evidence_span':{'byte_start':start,'byte_end':end,'sha256':sha(raw[start:end])}}

def build(reviews_path,archive_dir,computed_at=None):
    headers=build_headers(reviews_path,archive_dir,computed_at)
    rows=[]
    for h in headers['rows']:
        r={'accession':h['event_id'],'issuer_cik':h['issuer_id'],'review_status':h['review_status'],
           'review_reason':h['review_reason'],'analysis_utc':headers['computed_at'],
           'first_public_utc':None,'historical_ticker':None,'decision_utc':None,'outcome':None,
           'eligible':False,'comparison':None,'status':'NOT_SUPPORTED_BY_BOUNDED_EXTRACTOR',
           'blockers':['RETROSPECTIVE_SELECTION','HISTORICAL_AVAILABILITY_UNKNOWN','HISTORICAL_SECURITY_IDENTITY_UNVERIFIED',
                       'NO_FROZEN_DECISION','PRICE_ACTION_HALT_OUTCOMES_UNQUALIFIED']}
        if not h['features']:
            r['status']='SOURCE_MISSING_CHANGED_OR_INVALID'
        elif h['event_id']==ACCESSION:
            try:
                s=h['features'][0]['sources'][0]
                raw=(Path(archive_dir)/(s['sha256']+'.txt')).read_bytes()
                if sha(raw)!=s['sha256']:raise ValueError('source changed')
                comparison=extract(raw,h['issuer_id'],h['event_id'])
                comparison['source']={'accession':h['event_id'],'issuer_cik':h['issuer_id'],
                    'source_url':s['source_ref'],'sha256':s['sha256'],'retrieved_utc':s['observed_utc']}
                r['comparison']=comparison;r['status']='REPORTED_PAIR_COMPUTED_NOW_NOT_QUALIFIED'
                r['blockers']+=['OUTSIDE_APPROVED_UNIVERSE','CURRENCY_ISO_NOT_EXPLICIT','PRIOR_ORIGINAL_NOT_CHECKED']
            except (ValueError,KeyError,OSError):r['status']='COMPARISON_AMBIGUOUS_OR_UNSUPPORTED'
        rows.append(r)
    return {'mode':MODE,'analysis_utc':headers['computed_at'],'reviews_sha256':headers['reviews_sha256'],
            'manifest_sha256':headers['manifest_sha256'],'rows':rows,
            'reported_comparisons':sum(r['comparison']is not None for r in rows),
            'reported_metric_pairs':sum(1+sum(p['current_value']is not None for p in r['comparison']['additional_reported_pairs']) for r in rows if r['comparison']),
            'qualified_comparisons':0,'financial_signals':0,'orders':0,
            'historical_availability_verified':False,
            'limitations':['One manually selected accession-specific narrative parser, not broad financial extraction.',
                'Prior value is as reported in this later release, not verified against its original filing or amendment history.',
                'Dollar sign does not independently establish ISO currency; do not combine with other currency series.',
                'Analysis timestamp is invocation/reproduction time, not authenticated completion or historical availability.',
                'No SEC Frames/company-facts/current ticker API inputs; no investment or forecast conclusion.']}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--reviews',required=True);p.add_argument('--archive-dir',required=True);p.add_argument('--output',required=True);a=p.parse_args()
    result=build(a.reviews,a.archive_dir)
    with Path(a.output).open('x')as f:f.write(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'reported_comparisons':result['reported_comparisons'],'qualified_comparisons':0}))
