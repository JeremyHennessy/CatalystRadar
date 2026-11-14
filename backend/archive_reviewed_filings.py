"""Bounded SEC original-document archive. Local inert bytes, no scores or trading.

Run deliberately; not added to any scheduler. Never treats a new retrieval as
historical availability. Archive directories are immutable and must be retained
by the caller; workspace storage alone is not a durable remote archive.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import time
import urllib.error
import urllib.request

MAX_BYTES = 25_000_000
MAX_RUN_BYTES = 75_000_000
MAX_REQUESTS = 10
USER_AGENT = 'CatalystRadar/0.1 public SEC read-only research https://github.com/JeremyHennessy/CatalystRadar'

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

HTTP = urllib.request.build_opener(NoRedirect())

class ResponseTooLarge(ValueError):
    pass

def stamp():
    return datetime.now(timezone.utc).isoformat()

def identity(review):
    cik, acc = str(review['issuer_cik']), review['accession']
    if not re.fullmatch(r'\d{1,10}', cik) or not re.fullmatch(r'\d{10}-\d{2}-\d{6}', acc):
        raise ValueError('valid reviewed CIK/accession required')
    cik = str(int(cik))
    return cik, acc, f'https://www.sec.gov/Archives/edgar/data/{cik}/{acc.replace("-", "")}/{acc}.txt'

def validate(raw, cik, accession):
    # SEC header only; do not accept identity strings merely found in an exhibit.
    prefix = raw[:100_000]
    start, end = prefix.find(b'<SEC-HEADER>'), prefix.find(b'</SEC-HEADER>')
    first_document = prefix.find(b'<DOCUMENT>')
    if (not raw.startswith(b'<SEC-DOCUMENT>') or start < 0 or end < start or
            (first_document >= 0 and first_document < end)):
        raise ValueError('complete original SEC header required')
    head = prefix[start:end]
    if not re.search(rb'ACCESSION NUMBER:\s*' + re.escape(accession.encode()) + rb'\s', head):
        raise ValueError('submission accession mismatch')
    ciks = re.findall(rb'CENTRAL INDEX KEY:\s*(\d+)', head)
    if int(cik) not in [int(x) for x in ciks]:
        raise ValueError('submission issuer CIK mismatch')

def fetch(url):
    req=urllib.request.Request(url,headers={'User-Agent':USER_AGENT,'Accept-Encoding':'identity'})
    with HTTP.open(req,timeout=30) as response:
        if response.geturl() != url or response.status != 200:
            raise ValueError('unexpected URL/status')
        raw=response.read(MAX_BYTES+1)
        if len(raw)>MAX_BYTES:raise ResponseTooLarge('oversized response')
        return raw

def run(reviews, destination, *, get=fetch, clock=stamp, sleep=time.sleep):
    if not isinstance(reviews,list) or not 1<=len(reviews)<=MAX_REQUESTS:
        raise ValueError('1..10 reviewed records required')
    identities=[identity(r) for r in reviews]
    if len({a for _,a,_ in identities})!=len(identities):
        raise ValueError('duplicate accession')
    for r in reviews:
        if not re.fullmatch('[a-f0-9]{64}',r['source_sha256']):raise ValueError('prior hash required')
    destination=Path(destination)
    destination.mkdir(parents=True,exist_ok=False)
    records=[];total=0;halt=False
    for index,(review,(cik,acc,url)) in enumerate(zip(reviews,identities)):
        record={'issuer_cik':cik,'accession':acc,'url':url,
                'prior_recorded_sha256':review['source_sha256'],
                'first_public_utc':None,'historical_availability_verified':False}
        if halt:
            record['status']='NOT_ATTEMPTED_AFTER_STOP';records.append(record)
            with (destination/'manifest.jsonl').open('a') as f:f.write(json.dumps(record,sort_keys=True)+'\n')
            continue
        if index:sleep(2)
        record['request_utc']=clock()
        try:
            raw=get(url)
            record['retrieved_utc']=clock()
            if type(raw) is not bytes:raise ValueError('exact bytes required')
            if len(raw)>MAX_BYTES:raise ResponseTooLarge('oversized response')
            total+=len(raw)
            if total>MAX_RUN_BYTES:
                halt=True;raise ValueError('run byte budget exceeded')
            validate(raw,cik,acc)
            sha=hashlib.sha256(raw).hexdigest()
            name=sha+'.txt'
            with (destination/name).open('xb') as f:f.write(raw)
            record.update(status='ARCHIVED_IDENTITY_VERIFIED',sha256=sha,byte_count=len(raw),
                          archive_file=name,prior_hash_matches=sha==review['source_sha256'])
        except ResponseTooLarge:
            record.update(status='RESPONSE_SIZE_LIMIT_STOP', failed_utc=clock())
            halt=True
        except urllib.error.HTTPError as error:
            record.update(status='HTTP_FAILURE',http_status=error.code,failed_utc=clock())
            halt=error.code in (403,429)
        except Exception as error:
            record.update(status='VALIDATION_OR_FETCH_FAILURE',error_type=type(error).__name__,failed_utc=clock())
        records.append(record)
        # Persist each result, including failures, without rewriting prior receipts.
        with (destination/'manifest.jsonl').open('a') as f:f.write(json.dumps(record,sort_keys=True)+'\n')
    report={'mode':'CURRENT_RETRIEVAL_NOT_HISTORICAL_AVAILABILITY','records':records,
            'archived_count':sum(x['status']=='ARCHIVED_IDENTITY_VERIFIED' for x in records),
            'accounted_response_bytes_lower_bound':total,'raw_documents_publicly_published':False,
            'durable_remote_storage_verified':False,'first_public_times_verified':False,
            'trade_eligible':False}
    (destination/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    return report

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--reviews',required=True);p.add_argument('--destination',required=True)
    a=p.parse_args();report=run(json.loads(Path(a.reviews).read_text())['records'],a.destination)
    print(json.dumps({'archived_count':report['archived_count'],'records':len(report['records']),
                      'accounted_response_bytes_lower_bound':report['accounted_response_bytes_lower_bound'],'durable_remote_storage_verified':False}))
