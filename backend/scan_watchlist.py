"""Bounded public SEC metadata poll. No prices, scoring, orders or broker calls."""
from pathlib import Path
from datetime import datetime,timedelta,timezone
import json,argparse,os,hashlib,re,tempfile
from html import unescape
from urllib.parse import unquote
from discover_sec import Archive,rows,parse,stamp
from sec_identity import contact_email,user_agent
ROOT=Path(__file__).resolve().parent.parent

def public_error(message):
 match=re.search(r'HTTP (?:Error )?(\d{3})',str(message))
 return 'HTTP '+match.group(1)+' from public source' if match else 'Source fetch or verification failed; local diagnostics retained privately'

def persist_observation(report, root=ROOT):
 """Append one complete public scan report; never overwrite an earlier run.

 Local clocks/bytes are observations, not authenticated first-public evidence.
 A hard failure before this function leaves no complete receipt; git publication
 is a separate step. Atomic hard-link creation avoids partial final files.
 """
 run_id=report.get('run_id')
 if not isinstance(run_id,str) or not re.fullmatch(r'[0-9]{8}T[0-9]{12}Z',run_id):
  raise ValueError('invalid observation run id')
 payload=(json.dumps(report,sort_keys=True,indent=2,allow_nan=False)+'\n').encode('utf-8')
 if len(payload)>4*1024*1024:raise ValueError('observation report exceeds 4 MiB limit')
 directory=root/'data/sec-observations';directory.mkdir(parents=True,exist_ok=True)
 target=directory/(run_id+'.json')
 # Pending files never have a .json suffix and are not staged by the workflow.
 pending=None
 try:
  with tempfile.NamedTemporaryFile(dir=directory,prefix='.pending-',delete=False) as f:
   pending=Path(f.name);f.write(payload);f.flush();os.fsync(f.fileno())
  try:os.link(pending,target)
  except FileExistsError:
   if target.is_symlink() or target.read_bytes()!=payload:
    raise ValueError('conflicting immutable observation run')
 finally:
  if pending is not None:pending.unlink(missing_ok=True)
 return target

def scan(root=ROOT):
 contact=contact_email() # Fail before requests or output when private contact is absent.
 now=datetime.now(timezone.utc);start=now-timedelta(hours=96);config=json.loads((root/'data/watchlist.json').read_text())
 if not isinstance(config,list) or not config or len(config)>20:raise ValueError('watchlist must contain1..20 issuers')
 identities=[]
 for issuer in config:
  if not isinstance(issuer,dict) or not re.fullmatch(r'[0-9]{1,10}',str(issuer.get('cik',''))) or int(issuer['cik'])<=0:raise ValueError('invalid configured CIK')
  if not isinstance(issuer.get('ticker'),str) or not re.fullmatch(r'[A-Z0-9.-]{1,20}',issuer['ticker']):raise ValueError('invalid configured ticker')
  identities.append((str(int(issuer['cik'])).zfill(10),issuer['ticker']))
 if len(set(c for c,t in identities))!=len(identities) or len(set(t for c,t in identities))!=len(identities):raise ValueError('duplicate configured issuer')
 run_id=now.strftime('%Y%m%dT%H%M%S%fZ');archive_root=root/'.data/scans'/run_id;archive_root.mkdir(parents=True,exist_ok=False)
 arc=Archive(archive_root,user_agent(contact))
 events=[];sources=[];errors=[];halt=False
 for issuer in config:
  cik=str(issuer['cik']).zfill(10);ticker=issuer['ticker']
  if halt:
   sources.append({'ticker':ticker,'url':f'https://data.sec.gov/submissions/CIK{cik}.json','validation_status':'NOT_ATTEMPTED_AFTER_DENIAL'})
   errors.append({'ticker':ticker,'error':'not attempted after access/rate denial'});continue
  url=f'https://data.sec.gov/submissions/CIK{cik}.json';raw,meta=arc.get(url,cik+'.json')
  if raw is not None:
   text=raw.decode('utf-8',errors='replace')
   try:text+=' '+json.dumps(json.loads(raw),ensure_ascii=False)
   except (ValueError,UnicodeError):pass
   if contact.casefold() in unescape(unquote(text)).casefold():
    raw=None;meta={k:v for k,v in meta.items() if k in ('url','request_utc','retrieved_utc','status')}
    meta['error']='Private contact reflected in source response; response withheld';halt=True
  public={k:v for k,v in meta.items() if k in ('url','request_utc','retrieved_utc','status','sha256','byte_count','error','http_diagnostic')};public['ticker']=ticker;public['validation_status']='FETCH_FAILED' if raw is None else 'UNVALIDATED'
  if public.get('error'):public['error']=public_error(public['error'])
  if raw is not None:
   publicdir=root/'data/sec-snapshots';publicdir.mkdir(exist_ok=True);target=publicdir/(meta['sha256']+'.json')
   if target.exists() and hashlib.sha256(target.read_bytes()).hexdigest()!=meta['sha256']:raise ValueError('content-addressed evidence conflict')
   if not target.exists():
    with target.open('xb') as f:f.write(raw)
   public['archive_path']='data/sec-snapshots/'+target.name
  sources.append(public)
  if raw is None:
   errors.append({'ticker':ticker,'error':public_error(meta.get('error'))});halt=halt or any(x in meta.get('error','') for x in ('403','429'));continue
  try:
   j=json.loads(raw)
   if not re.fullmatch(r'[0-9]{1,10}',str(j.get('cik',''))) or int(j['cik'])!=int(cik) or not isinstance(j.get('tickers'),list) or not all(isinstance(t,str) for t in j['tickers']) or ticker not in j['tickers']:raise ValueError('ticker/CIK mismatch')
   recent=j['filings']['recent']
   required=('accessionNumber','filingDate','acceptanceDateTime','form','primaryDocument')
   if not isinstance(recent,dict) or any(not isinstance(recent.get(k),list) for k in required):raise ValueError('invalid submission columns')
   rr=rows(j['filings']['recent']);times=[parse(x['acceptanceDateTime']) for x in rr if x.get('acceptanceDateTime')]
   if not times or min(times)>start:raise ValueError('recent API window may be truncated; backfill required')
   issuer_events=[];seen={}
   for r in rr:
    if r['form'] not in ('8-K','8-K/A') or not start<=parse(r['acceptanceDateTime'])<=now:continue
    acc=r['accessionNumber']
    if not isinstance(acc,str) or not re.fullmatch(r'[0-9]{10}-[0-9]{2}-[0-9]{6}',acc):raise ValueError('invalid accession')
    if acc in seen:
     if seen[acc]!=r:raise ValueError('conflicting duplicate accession')
     continue
    seen[acc]=r
    issuer_events.append({'ticker':ticker,'issuer':j['name'],'issuer_cik':cik,'accession':acc,'form':r['form'],'items_raw':r.get('items'),'sec_accepted_utc':r['acceptanceDateTime'],'observed_utc':meta['retrieved_utc'],'first_public_utc':None,'source_url':f'https://www.sec.gov/Archives/edgar/data/{int(cik)}/{acc.replace("-","")}/{acc}.txt','source_metadata_sha256':meta['sha256'],'status':'METADATA_DISCOVERY_NOT_ELIGIBLE','reason':'Full source and earlier public release, catalyst facts, prices and halts require validation','eligible':False})
   events.extend(issuer_events)
   public['validation_status']='METADATA_WINDOW_VALIDATED'
  except Exception as err:
   public['validation_status']='METADATA_VALIDATION_FAILED'
   errors.append({'ticker':ticker,'error':public_error(err)})
 report={'run_id':run_id,'started_at':now.isoformat(),'finished_at':stamp(),'window_start':start.isoformat(),'mode':'OBSERVATION_ONLY','scope':f'{len(config)} configured issuer metadata feeds; NOT whole market','configured_issuers':len(config),'successful_issuers':len(config)-len(errors),'metadata_window_complete':not errors,'errors':errors,'sources':sources,'events':sorted(events,key=lambda e:(e['sec_accepted_utc'],e['accession'])),'eligible_count':0,'orders_created':0,'schedule_status':'GITHUB_RUN' if os.environ.get('GITHUB_ACTIONS')=='true' else 'MANUAL_RUN','github_event_name':os.environ.get('GITHUB_EVENT_NAME'),'github_run_url':('https://github.com/'+os.environ.get('GITHUB_REPOSITORY','')+'/actions/runs/'+os.environ.get('GITHUB_RUN_ID','')) if os.environ.get('GITHUB_ACTIONS')=='true' else None}
 persist_observation(report,root)
 (archive_root/'report.json').write_text(json.dumps(report,indent=2));tmp=root/'data/latest_scan.json.tmp';tmp.write_text(json.dumps(report,indent=2));tmp.replace(root/'data/latest_scan.json');return report
if __name__=='__main__':
 r=scan();print(json.dumps({k:r[k] for k in ('run_id','successful_issuers','configured_issuers','metadata_window_complete','eligible_count','orders_created')},indent=2))
