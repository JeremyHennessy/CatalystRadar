"""Offline validation of a bounded keyless OpenFIGI mapping observation."""
import argparse
from collections import Counter
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import re
from private_prices import unique_object
from financial_pair_candidates import publish,write_private
URL='https://api.openfigi.com/v3/mapping'
TRUSTED_FIELDS={'figi','name','ticker','exchCode','compositeFIGI','securityType','marketSector','shareClassFIGI','securityType2','securityDescription'}

def digest(b):return hashlib.sha256(b).hexdigest()
def read_pinned(path,expected,limit):
    if not re.fullmatch('[a-f0-9]{64}',expected):raise ValueError('invalid hash')
    with Path(path).open('rb') as f:raw=f.read(limit+1)
    if len(raw)>limit or digest(raw)!=expected:raise ValueError('input bounds/hash mismatch')
    def bad(v):raise ValueError('nonstandard JSON constant')
    return json.loads(raw.decode('utf-8'),object_pairs_hook=unique_object,parse_constant=bad),len(raw)
def figi_valid(value):
    if not isinstance(value,str) or not re.fullmatch(r'[BCDFGHJKLMNPQRSTVWXYZ]{2}G[BCDFGHJKLMNPQRSTVWXYZ0-9]{8}[0-9]',value):return False
    digits=[]
    for i,c in enumerate(value[:11]):
        n=(int(c) if c.isdigit() else ord(c)-55)*(1 if i%2==0 else 2)
        digits.extend(int(d) for d in str(n))
    return (10-sum(digits)%10)%10==int(value[-1])
def stamp(value):
    if not isinstance(value,str):raise ValueError('timestamp required')
    d=datetime.fromisoformat(value)
    if d.tzinfo is None or d.utcoffset().total_seconds()!=0 or d>datetime.now(timezone.utc):raise ValueError('invalid observation clock')
    return d

def validate(request,response,receipt,request_sha,response_sha):
    expected={'source_url','method','authentication','request_sha256','requested_at','http_status','response_sha256','response_bytes','status','headers','finished_at'}
    if not isinstance(receipt,dict) or set(receipt)!=expected:raise ValueError('unsupported receipt schema')
    if receipt['source_url']!=URL or receipt['method']!='POST' or receipt['authentication']!='NONE' or receipt['http_status']!=200 or receipt['status']!='RETAINED_NOT_YET_VALIDATED':raise ValueError('unsuccessful or unsupported collection')
    headers=receipt['headers']
    if not isinstance(headers,dict) or set(headers)!={'Content-Type','Date','ratelimit-limit','ratelimit-remaining','ratelimit-reset'} or any(v is not None and (not isinstance(v,str) or len(v)>200) for v in headers.values()):raise ValueError('unsupported response headers')
    if not isinstance(headers['Content-Type'],str) or headers['Content-Type'].split(';')[0]!='application/json':raise ValueError('unexpected content type')
    if receipt['request_sha256']!=request_sha or receipt['response_sha256']!=response_sha:raise ValueError('receipt hash mismatch')
    if stamp(receipt['requested_at'])>stamp(receipt['finished_at']):raise ValueError('inverted observation clocks')
    if not isinstance(request,list) or not 1<=len(request)<=10 or not isinstance(response,list) or len(request)!=len(response):raise ValueError('job count mismatch')
    seen=set();records=[];counts=Counter();figi_jobs=Counter()
    for position,(job,result) in enumerate(zip(request,response)):
        if not isinstance(job,dict) or set(job)!={'idType','idValue','exchCode','marketSecDes','includeUnlistedEquities'} or job['idType']!='TICKER' or job['exchCode']!='US' or job['marketSecDes']!='Equity' or job['includeUnlistedEquities'] is not True:raise ValueError('unsupported query scope')
        ticker=job['idValue']
        if not isinstance(ticker,str) or not re.fullmatch('[A-Z][A-Z0-9. -]{0,15}',ticker) or ticker in seen:raise ValueError('ambiguous query identity')
        seen.add(ticker)
        if not isinstance(result,dict):raise ValueError('invalid job response')
        if set(result) in ({'error'},{'warning'}):
            if not isinstance(next(iter(result.values())),str):raise ValueError('invalid refusal')
            disposition='PROVIDER_ERROR' if 'error' in result else 'NO_MAPPING_WARNING';candidates=[]
        elif set(result)=={'data'}:
            data=result['data']
            if not isinstance(data,list) or len(data)>1000:raise ValueError('result count bounds')
            candidates=[];ids=set()
            for row in data:
                if not isinstance(row,dict) or set(row)!=TRUSTED_FIELDS or any(not isinstance(v,str) or len(v)>1000 for v in row.values()):raise ValueError('unsupported result schema')
                if row['ticker']!=ticker or row['exchCode']!='US' or row['marketSector']!='Equity':raise ValueError('response/query mismatch')
                for field in ['figi','compositeFIGI','shareClassFIGI']:
                    if not figi_valid(row[field]):raise ValueError('invalid FIGI checksum or structure')
                if row['figi'] in ids:raise ValueError('duplicate candidate FIGI')
                ids.add(row['figi']);figi_jobs[row['figi']]+=1
                candidates.append({k:row[k] for k in ['figi','compositeFIGI','shareClassFIGI']})
            disposition='NO_MAPPING_RETURNED' if not candidates else ('SINGLE_CURRENT_CANDIDATE' if len(candidates)==1 else 'AMBIGUOUS_CURRENT_CANDIDATES')
        else:raise ValueError('ambiguous response status')
        counts[disposition]+=1
        records.append({'request_position':position,'query_ticker':ticker,'query_exchange':'US','query_market_sector':'Equity','include_unlisted_equities':True,'disposition':disposition,'candidates':candidates,'issuer_cik_link_verified':False,'historical_ticker_ownership_verified':False,'active_listing_verified':False,'training_ready':False})
    return records,dict(sorted(counts.items())),sum(v>1 for v in figi_jobs.values())

def audit(request_path,request_sha,response_path,response_sha,receipt_path,receipt_sha):
    request,_=read_pinned(request_path,request_sha,20000);response,response_length=read_pinned(response_path,response_sha,2000000);receipt,_=read_pinned(receipt_path,receipt_sha,20000)
    if type(receipt.get('response_bytes')) is not int or receipt['response_bytes']!=response_length:raise ValueError('receipt byte count mismatch')
    records,counts,shared=validate(request,response,receipt,request_sha,response_sha)
    summary={'schema_version':1,'status':'OBSERVED_IDENTIFIER_CANDIDATES_NOT_HISTORICAL_SECURITY_LINKS','source_url':URL,'requested_at':receipt['requested_at'],'observed_at':receipt['finished_at'],'request_sha256':request_sha,'response_sha256':response_sha,'receipt_sha256':receipt_sha,'response_bytes':receipt['response_bytes'],'job_count':len(request),'candidate_count':sum(len(r['candidates']) for r in records),'dispositions':counts,'figis_shared_across_queries':shared,'mappings':records,'training_ready':False,'execution_ready':False,
      'limitations':['Only the submitted US/equity ticker jobs are covered; includeUnlistedEquities means a match is not proof of active trading.',
      'FIGI/composite/share-class identifiers retain distinct scopes. A single result is not an independently verified issuer-CIK or historical ticker link.',
      'Response order aligns with request order per provider documentation; unexpected or conflicting responses fail closed.',
      'Local request/response receipt clocks are current collection evidence, not historical effective dates or authenticated public-release times.',
      'No prices, returns, execution, historical universe completeness or model-training admission.']}
    return summary,{'request':request,'response':response,'receipt':receipt}

if __name__=='__main__':
    p=argparse.ArgumentParser()
    for name in ['request','request-sha256','response','response-sha256','receipt','receipt-sha256','output-directory']:p.add_argument('--'+name,required=True)
    a=p.parse_args();out=Path(a.output_directory).resolve()
    if out.is_relative_to(Path(__file__).resolve().parents[1]) or not out.parent.is_dir():raise ValueError('trusted private parent outside checkout required')
    out.mkdir(mode=0o700,exist_ok=False);write_private(out/'INCOMPLETE',{'status':'INCOMPLETE_NOT_USABLE'})
    summary,evidence=audit(a.request,a.request_sha256,a.response,a.response_sha256,a.receipt,a.receipt_sha256);publish(out,summary,evidence);print(json.dumps(summary))
