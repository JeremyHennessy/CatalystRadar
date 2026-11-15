"""Two explicitly reviewed original filings; retrospective guidance-basis check."""
import argparse
from datetime import datetime,timezone
from decimal import Decimal
from html import unescape
import json
from pathlib import Path
import re
from filing_feature_rows import sha,header_features
from study_split_audit import instant

SOURCES=(
 ('0000031791-26-000031','455263eda95726fe8ac4c39128c763b4fed901d991c7876f157e5298d9144038','EX-99.1'),
 ('0001628280-26-073578','01690a89df5c831901cc0c495e772925e1c9eafcc9876e48afd676656e3f31d9','EX-99.2'))

def exhibit(raw,acc,typ):
    values,_=header_features(raw,'31791',acc)
    if values['header_is_8k_amendment']:raise ValueError('amendment requires independent review')
    docs=[d for d in re.finditer(rb'<DOCUMENT>.*?</DOCUMENT>',raw,re.S)
          if re.search(rb'<TYPE>'+re.escape(typ.encode())+rb'\s*\n',d.group().split(b'<TEXT>',1)[0])]
    if len(docs)!=1:raise ValueError('one exact exhibit required')
    d=docs[0];text=re.sub(r'\s+',' ',unescape(re.sub('<[^>]+>',' ',d.group().decode('utf-8'))))
    return text,{'byte_start':d.start(),'byte_end':d.end(),'sha256':sha(d.group())}

def compare_text(prior,later):
    required_prior=('For the full year 2026, on a pro forma basis, the Company forecasts total revenue of approximately $2.86 billion, pro forma organic revenue growth of approximately 5%, and pro forma adjusted earnings per share of $5.40-$5.45.',
                    'forward-looking guidance is provided on a pro forma basis only and excludes China IDX.')
    required_later=('2026E Revenue: ~$2.9B','based on 2026 pro forma guidance as provided on November 3, 2026',
                   'Immunodiagnostics business in China','~6% organic growth','2027 considerations',
                   'Formal 2027 guidance to be provided on our Q4 earnings call')
    if not all(x in prior for x in required_prior)or not all(x in later for x in required_later):raise ValueError('reviewed basis text not present')
    return {'fy2026_prior':{'revenue_billion_reported_dollars':'2.86','organic_growth_percent':'5','adjusted_eps_low':'5.40','adjusted_eps_high':'5.45',
                'basis':'pro forma; excludes China IDX','currency_iso':None,'approximate_revenue_and_growth':True},
            'fy2026_later':{'revenue_billion_reported_dollars':'2.9','approximate':True,'cites_prior_guidance_date':'2026-11-03'},
            'revenue_comparison':'COMPATIBLE_ROUNDING_NOT_VERIFIED_RAISE',
            'rounded_prior_one_decimal':str(Decimal('2.86').quantize(Decimal('0.1'))),
            'later_organic_considerations':{'year':2027,'percent':'6','approximate':True,'formal_guidance':False},
            'organic_growth_comparison':'DIFFERENT_FISCAL_YEAR_NO_SAME_PERIOD_DELTA',
            'eps_raise_comparison':None,'guidance_raise_verified':False}

def build(prior_dir,later_dir,analysis_utc=None):
    analysis_utc=analysis_utc or datetime.now(timezone.utc).isoformat();now=instant(analysis_utc)
    receipts=[json.loads((Path(prior_dir)/'receipt.json').read_text()),
              next(r for r in map(json.loads,(Path(later_dir)/'manifest.jsonl').read_text().splitlines())if r['accession']==SOURCES[1][0])]
    evidence=[];texts=[]
    for folder,(acc,digest,typ),receipt in zip((prior_dir,later_dir),SOURCES,receipts):
        raw=(Path(folder)/(digest+'.txt')).read_bytes()
        url=f'https://www.sec.gov/Archives/edgar/data/31791/{acc.replace("-", "")}/{acc}.txt'
        if sha(raw)!=digest or receipt['sha256']!=digest or receipt['issuer_cik']!='31791' or receipt['accession']!=acc or receipt['url']!=url or receipt['byte_count']!=len(raw):raise ValueError('source binding mismatch')
        if not instant(receipt['request_utc'])<=instant(receipt['retrieved_utc'])<=now:raise ValueError('source clock mismatch')
        text,span=exhibit(raw,acc,typ);texts.append(text)
        evidence.append({'accession':acc,'issuer_cik':'31791','source_url':url,'sha256':digest,'retrieved_utc':receipt['retrieved_utc'],'exhibit_type':typ,'exhibit_span':span})
    return {'mode':'RETROSPECTIVE_BASIS_RECONCILIATION_NOT_SIGNAL','analysis_utc':analysis_utc,
            'sources':evidence,'comparison':compare_text(*texts),'first_public_utc':None,'decision_utc':None,'outcome':None,
            'historical_ticker':None,'qualified':False,'financial_signals':0,'orders':0,
            'limitations':['Exact accession-specific text checks, not a general presentation extractor.',
                'Presentation text is not independently matched to rendered slides; graphics review remains incomplete.',
                'Compatible rounding does not prove unchanged guidance; no verified same-period raise is established.',
                'No historical availability, authenticated completion clock, complete amendment history or trading eligibility claimed.']}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--prior-dir',required=True);p.add_argument('--later-dir',required=True);p.add_argument('--output',required=True);a=p.parse_args()
    with Path(a.output).open('x')as f:f.write(json.dumps(build(a.prior_dir,a.later_dir),indent=2)+'\n')
