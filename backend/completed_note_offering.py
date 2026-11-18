"""Narrow original-8-K completed-note grammar; not financing/trade qualification."""
import argparse, hashlib, io, json, re, zipfile
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from financial_admission_rehearsal import plain
from filing_feature_rows import header_features
ARCHIVE_SHA='0f92e2c02a597b14f08c29395ae2fc9b87f2db580016e632c8d76c3059e449c0'
MANIFEST_SHA='ac6316ad597b9a931613c71e4f1442425f5f83c873d47ba17192f0c1b6a2274a'
PATTERN=re.compile(r'On ([A-Z][a-z]+ [0-9]{1,2}, 20[0-9]{2}), ([A-Za-z0-9 .,]+) \(the “Company”\) completed its previously announced public offering of €([0-9]{1,3}(?:,[0-9]{3})+) aggregate principal amount of the Company’s ([0-9]+\.[0-9]+)% Notes due (20[0-9]{2}) \(the “Notes”\)\. The pricing of the Notes was previously announced in a Current Report on Form 8-K filed on ([A-Z][a-z]+ [0-9]{1,2}, 20[0-9]{2})\.')
def sha(b):return hashlib.sha256(b).hexdigest()
def extract(raw,cik,accession):
    headers,_=header_features(raw,cik,accession)
    if headers['header_is_8k_amendment']:return {'status':'AMENDMENT_REQUIRES_REVIEW','facts':[]}
    candidates=[]
    for d in re.finditer(rb'<DOCUMENT>.*?</DOCUMENT>',raw,re.S):
        if not re.search(rb'<TYPE>8-K\s*\n',d[0]):continue
        blocked=[(m.start(),m.end()) for m in re.finditer(rb'<!--.*?(?:-->|$)|<(script|style)\b[^>]*>.*?(?:</\1\s*>|$)',d[0],re.S|re.I)]
        for p in re.finditer(rb'<(div|p)\b[^>]*>.*?</\1>',d[0],re.S|re.I):
            if any(p.start()<b and p.end()>a for a,b in blocked):continue
            # Only a whole paragraph match; no hidden-prefix/negation trimming.
            m=PATTERN.fullmatch(plain(p[0]))
            if not m:continue
            date,name,principal,coupon,year,prior=m.groups()
            complete=datetime.strptime(date,'%B %d, %Y').date();pricing=datetime.strptime(prior,'%B %d, %Y').date()
            if pricing>complete or int(year)<complete.year or Decimal(coupon)<=0 or Decimal(coupon)>100:continue
            candidates.append({'issuer_name_as_reported':name,'reported_completion_date':complete.isoformat(),
                'reported_prior_pricing_filing_date':pricing.isoformat(),'principal_as_reported':principal,
                'principal_unscaled':principal.replace(',',''),'currency':'EUR','currency_basis':'explicit euro symbol',
                'coupon_percent_as_reported':coupon,'maturity_year_as_reported':year,
                'maturity_date':None,'instrument':'NOTES_DEBT','completion_basis':'ISSUER_REPORTED_NOT_INDEPENDENT_SETTLEMENT',
                'previously_announced':True,'net_proceeds':None,'equity_dilution':None,
                'first_public_utc':None,'historical_security_mapping_verified':False,
                'evidence_span':{'byte_start':d.start()+p.start(),'byte_end':d.start()+p.end(),'sha256':sha(p[0])}})
    return {'status':'SOURCE_REPORTED_DEBT_COMPLETION' if len(candidates)==1 else ('AMBIGUOUS_MULTIPLE_MATCHES' if candidates else 'NO_SUPPORTED_PARAGRAPH'),
            'facts':candidates if len(candidates)==1 else [],'candidate_count':len(candidates)}
def build(archive):
    with Path(archive).open('rb') as f:raw=f.read(20_000_001)
    if len(raw)>20_000_000 or sha(raw)!=ARCHIVE_SHA:raise ValueError('package bound or pin')
    rows=[]
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        infos=z.infolist()
        if len(infos)>20 or len({i.filename for i in infos})!=len(infos):raise ValueError('archive inventory')
        if z.getinfo('manifest.jsonl').file_size>100_000:raise ValueError('manifest bound')
        manifest=z.read('manifest.jsonl')
        if sha(manifest)!=MANIFEST_SHA:raise ValueError('manifest pin')
        entries=sorted(map(json.loads,manifest.splitlines()),key=lambda r:r['accession'])
        if len(entries)!=10 or len({r['accession'] for r in entries})!=10:raise ValueError('cohort bounds')
        for r in entries:
            info=z.getinfo(r['archive_file'])
            if info.file_size>15_000_000 or info.file_size!=r['byte_count']:raise ValueError('original byte bound')
            body=z.read(info)
            if sha(body)!=r['sha256']:raise ValueError('original hash')
            result=extract(body,r['issuer_cik'],r['accession'])
            rows.append({'accession':r['accession'],'issuer_cik':str(r['issuer_cik']).zfill(10),
                'source_url':r['url'],'source_sha256':r['sha256'],'observed_utc':r['retrieved_utc'],**result})
    return {'version':1,'selection':'All ten pinned retained originals, accession order; no replacement or outcome selection.',
        'archive_sha256':sha(raw),'manifest_sha256':MANIFEST_SHA,'rows':rows,
        'reported_completion_count':sum(r['status']=='SOURCE_REPORTED_DEBT_COMPLETION' for r in rows),
        'qualified_outcomes':0,'training_ready':False,'execution_ready':False,
        'limitations':['Exact euro-denominated completed-note narrative grammar only; absence is not absence of financing.',
          'Issuer-reported completion is not independent settlement, proceeds, current debt balance, equity dilution or new announcement.',
          'Dates are narrative declarations, not authenticated publication/decision times. Coupon is not yield.',
          'No licensed prices, returns, predictions, paper orders or collectors changed.']}
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('archive');p.add_argument('output');a=p.parse_args()
    result=build(a.archive)
    with Path(a.output).open('x') as f:json.dump(result,f,indent=2);f.write('\n')
