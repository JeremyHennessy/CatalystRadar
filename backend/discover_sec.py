"""Public SEC read-only archive prototype. No orders, scores or predictions.
Coverage is a declared fixed issuer universe, NEVER the whole market.
"""
import argparse,datetime as dt,hashlib,json,time,urllib.request,urllib.error,re
from pathlib import Path
UTC=dt.timezone.utc
class NoRedirect(urllib.request.HTTPRedirectHandler):
 def redirect_request(self,req,fp,code,msg,headers,newurl):return None
HTTP=urllib.request.build_opener(NoRedirect())

def stamp():return dt.datetime.now(UTC).isoformat()
def parse(x):
 value=dt.datetime.fromisoformat(x.replace('Z','+00:00'))
 if value.tzinfo is None:raise ValueError('explicit timezone required')
 return value.astimezone(UTC)
def rows(data):
 required=['accessionNumber','filingDate','acceptanceDateTime','form','primaryDocument']
 if any(k not in data for k in required):raise ValueError('missing submission columns')
 n=len(data['accessionNumber'])
 if any(len(data[k])!=n for k in required):raise ValueError('unequal submission columns')
 return [{k:v[i] for k,v in data.items() if isinstance(v,list) and len(v)==n} for i in range(n)]
def http_error_diagnostic(error):
 """Read at most 4 KiB of a denial; publish only fixed labels, never body text.

 A response phrase is diagnostic evidence, not proof of the root cause.
 No retries, alternate routes, contact identities or request headers are changed.
 """
 result={'category':'HTTP_ERROR_UNCLASSIFIED','body_bytes_examined':0,'body_truncated':False}
 try:
  raw=error.read(4097)
  result.update(body_bytes_examined=min(len(raw),4096),body_truncated=len(raw)>4096)
  text=raw[:4096].decode('utf-8',errors='replace').lower()
  if 'undeclared automated tool' in text:result['category']='UNDECLARED_AUTOMATED_TOOL_RESPONSE'
  elif 'request rate threshold exceeded' in text:result['category']='RATE_THRESHOLD_RESPONSE'
  elif 'access denied' in text:result['category']='ACCESS_DENIED_RESPONSE'
 except Exception:
  result['category']='HTTP_ERROR_BODY_UNAVAILABLE'
 finally:
  error.close()
 return result

class Archive:
 def __init__(self,root,agent):self.root=root;self.agent=agent;self.last=0;self.manifest=[]
 def get(self,url,label):
  if not (url.startswith(('https://data.sec.gov/','https://www.sec.gov/Archives/')) or url=='https://www.sec.gov/submit-filings/filer-support-resources/edgar-calendar'):raise ValueError('unapproved host')
  wait=2-(time.monotonic()-self.last)
  if wait>0:time.sleep(wait)
  self.last=time.monotonic();record={'url':url,'request_utc':stamp(),'label':label}
  try:
   req=urllib.request.Request(url,headers={'User-Agent':self.agent,'Accept-Encoding':'identity'})
   with HTTP.open(req,timeout=30) as response:
    raw=response.read(25_000_001)
    if len(raw)>25_000_000:raise ValueError('response exceeds archive limit; not truncated into evidence')
    record.update(status=response.status,content_type=response.headers.get('Content-Type'),server_date_raw=response.headers.get('Date'),etag=response.headers.get('ETag'),last_modified_raw=response.headers.get('Last-Modified'))
   record.update(retrieved_utc=stamp(),byte_count=len(raw),sha256=hashlib.sha256(raw).hexdigest(),path=label)
   with (self.root/label).open('xb') as f:f.write(raw)
   self.manifest.append(record);self.flush()
   return raw,record
  except urllib.error.HTTPError as err:
   record.update(retrieved_utc=stamp(),status=err.code,error='HTTP Error '+str(err.code),http_diagnostic=http_error_diagnostic(err))
   self.manifest.append(record);self.flush();return None,record
  except Exception as err:
   record.update(retrieved_utc=stamp(),error=type(err).__name__+': source request failed; details withheld');self.manifest.append(record);self.flush();return None,record
 def flush(self):
  # Manifest journal append-only, one unique entry per request; atomic final snapshot separately.
  with (self.root/'manifest.jsonl').open('a') as f:f.write(json.dumps(self.manifest[-1])+'\n')

def run(root,universe,start,cutoff,agent):
 root.mkdir(parents=True,exist_ok=False)
 (root/'universe.json').write_text(json.dumps(universe,indent=2));archive=Archive(root,agent)
 report={'started_utc':stamp(),'requested_window_start':start,'cutoff':cutoff,'cutoff_semantics':'ACCEPTANCE_WINDOW_END_NOT_DECISION_FREEZE','universe_scope':'FIXED_ISSUERS_ONLY_NOT_MARKET_WIDE','filing_forms':['8-K','8-K/A'],'issuers':[],'events':[],'real_transactions':0}
 for issuer in universe:
  cik=str(issuer['cik']).zfill(10)
  if not re.fullmatch(r'\d{10}',cik):raise ValueError('invalid CIK')
  summary={'cik':cik,'expected_ticker':issuer['ticker'],'status':'INCOMPLETE','errors':[]};report['issuers'].append(summary)
  raw,meta=archive.get(f'https://data.sec.gov/submissions/CIK{cik}.json',f'{cik}-submissions.json')
  if raw is None:summary['errors'].append('submissions unavailable');continue
  try:
   j=json.loads(raw);summary['name']=j['name'];summary['tickers']=j.get('tickers',[])
   if issuer['ticker'] not in summary['tickers']:raise ValueError('ticker/CIK mismatch')
   allrows=[(r,meta) for r in rows(j['filings']['recent'])];history=j['filings']['files']
   summary['history_files_considered']=len(history)
   for h in history:
    if h['filingTo']>=start[:10] and h['filingFrom']<=cutoff[:10]:
     hraw,hm=archive.get('https://data.sec.gov/submissions/'+h['name'],h['name'])
     if hraw is None:raise ValueError('required history missing')
     allrows += [(r,hm) for r in rows(json.loads(hraw))]
   unique={};observations={}
   for r,source in allrows:
    key=r['accessionNumber']
    if key in unique and unique[key]!=r:raise ValueError('conflicting duplicate accession')
    unique[key]=r
    observations.setdefault(key,[]).append({k:source[k] for k in ('url','retrieved_utc','sha256','path')})
   selected=[r for r in unique.values() if r['form'] in ('8-K','8-K/A') and parse(start)<=parse(r['acceptanceDateTime'])<=parse(cutoff)]
   selected.sort(key=lambda r:(parse(r['acceptanceDateTime']),r['accessionNumber']))
   summary.update(api_rows_examined=len(unique),selected_count=len(selected),archived_count=0,coverage_basis='all returned recent records plus all declared overlapping historical files; not independently reconciled to daily master index')
   for r in selected:
    acc=r['accessionNumber'];digits=acc.replace('-','')
    if not re.fullmatch(r'\d{18}',digits):raise ValueError('invalid accession')
    url=f'https://www.sec.gov/Archives/edgar/data/{int(cik)}/{digits}/{acc}.txt'
    text,tm=archive.get(url,f'{digits}-complete.txt')
    event={'issuer_cik':cik,'ticker':issuer['ticker'],'accession':acc,'form':r['form'],'items_raw':r.get('items'),'event_date_raw':r.get('reportDate'),'sec_accepted_utc':r['acceptanceDateTime'],'filing_date_raw':r['filingDate'],'primary_document':r['primaryDocument'],'discovered_utc':min((o['retrieved_utc'] for o in observations[acc]),key=parse),'metadata_observations':observations[acc],'document_observed_utc':None,'observation_semantics':'THIS_RUN_RETRIEVAL_NOT_FIRST_PUBLIC_OR_HISTORICAL_AVAILABILITY','original_submission_url':url,'first_public_utc':None,'status':'DISCOVERED_NOT_ELIGIBLE','reason':'first issuer public disclosure timestamp and extraction unverified','raw_archive':tm}
    if text is not None:
     # Verify accession in full submission, not merely HTTP200 (which could be a block page).
     if acc.encode() not in text or b'<SEC-DOCUMENT>' not in text:
      event['status']='INVALID_DOCUMENT_RESPONSE';summary['errors'].append(acc+': invalid full text')
     else:
      summary['archived_count']+=1
      event['document_observed_utc']=tm['retrieved_utc']
    else:summary['errors'].append(acc+': full text unavailable')
    report['events'].append(event)
   summary['status']='API_SCOPE_ARCHIVED_NOT_INDEX_RECONCILED' if not summary['errors'] else 'INCOMPLETE'
  except Exception as err:summary['errors'].append(type(err).__name__+': '+str(err))
 report['finished_utc']=stamp();report['coverage_complete_for_orders']=False
 report['historical_availability_verified']=False
 report['absence_semantics']='NOT_RETURNED_DOES_NOT_PROVE_DELETION_OR_HISTORICAL_ABSENCE'
 report['blocking_gates']=['No independent daily-index reconciliation','First-public timestamps and factual extraction unverified','Price/volume/halts feed not connected','No execution engine authorized or enabled']
 (root/'report.json').write_text(json.dumps(report,indent=2))
 return report
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--root',required=True);a.add_argument('--universe',required=True);a.add_argument('--start',required=True);a.add_argument('--cutoff',required=True);a.add_argument('--user-agent',required=True);args=a.parse_args()
 result=run(Path(args.root),json.loads(Path(args.universe).read_text()),args.start,args.cutoff,args.user_agent)
 print(json.dumps({'issuers':result['issuers'],'events':len(result['events']),'root':args.root},indent=2))
