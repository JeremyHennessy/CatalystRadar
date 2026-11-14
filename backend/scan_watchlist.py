"""Bounded public SEC metadata poll. No prices, scoring, orders or broker calls."""
from pathlib import Path
from datetime import datetime,timedelta,timezone
import json,argparse,os,hashlib,re
from discover_sec import Archive,rows,parse,stamp
ROOT=Path(__file__).resolve().parent.parent

def public_error(message):
 match=re.search(r'HTTP (?:Error )?(\d{3})',str(message))
 return 'HTTP '+match.group(1)+' from public source' if match else 'Source fetch or verification failed; local diagnostics retained privately'

def scan(root=ROOT):
 now=datetime.now(timezone.utc);start=now-timedelta(hours=96);config=json.loads((root/'data/watchlist.json').read_text())
 if not config or len(config)>20:raise ValueError('watchlist must contain1..20 issuers')
 run_id=now.strftime('%Y%m%dT%H%M%S%fZ');archive_root=root/'.data/scans'/run_id;archive_root.mkdir(parents=True,exist_ok=False)
 arc=Archive(archive_root,'CatalystRadar/0.1 public SEC read-only research https://github.com/JeremyHennessy/CatalystRadar')
 events=[];sources=[];errors=[];halt=False
 for issuer in config:
  cik=str(issuer['cik']).zfill(10);ticker=issuer['ticker']
  if halt:errors.append({'ticker':ticker,'error':'not attempted after access/rate denial'});continue
  url=f'https://data.sec.gov/submissions/CIK{cik}.json';raw,meta=arc.get(url,cik+'.json')
  public={k:v for k,v in meta.items() if k in ('url','request_utc','retrieved_utc','status','sha256','byte_count','error')};public['ticker']=ticker
  if public.get('error'):public['error']=public_error(public['error'])
  if raw is not None:
   publicdir=root/'data/sec-snapshots';publicdir.mkdir(exist_ok=True);target=publicdir/(meta['sha256']+'.json')
   if target.exists() and hashlib.sha256(target.read_bytes()).hexdigest()!=meta['sha256']:raise ValueError('content-addressed evidence conflict')
   if not target.exists():
    with target.open('xb') as f:f.write(raw)
   public['archive_path']='data/sec-snapshots/'+target.name
  sources.append(public)
  if raw is None:
   errors.append({'ticker':ticker,'error':public_error(meta.get('error'))});halt=any(x in meta.get('error','') for x in ('403','429'));continue
  try:
   j=json.loads(raw)
   if ticker not in j.get('tickers',[]):raise ValueError('ticker/CIK mismatch')
   rr=rows(j['filings']['recent']);times=[parse(x['acceptanceDateTime']) for x in rr if x.get('acceptanceDateTime')]
   if not times or min(times)>start:raise ValueError('recent API window may be truncated; backfill required')
   for r in rr:
    if r['form'] not in ('8-K','8-K/A') or not start<=parse(r['acceptanceDateTime'])<=now:continue
    acc=r['accessionNumber'];events.append({'ticker':ticker,'issuer':j['name'],'issuer_cik':cik,'accession':acc,'form':r['form'],'items_raw':r.get('items'),'sec_accepted_utc':r['acceptanceDateTime'],'observed_utc':meta['retrieved_utc'],'first_public_utc':None,'source_url':f'https://www.sec.gov/Archives/edgar/data/{int(cik)}/{acc.replace("-","")}/{acc}.txt','source_metadata_sha256':meta['sha256'],'status':'METADATA_DISCOVERY_NOT_ELIGIBLE','reason':'Full source and earlier public release, catalyst facts, prices and halts require validation','eligible':False})
  except Exception as err:errors.append({'ticker':ticker,'error':public_error(err)})
 report={'run_id':run_id,'started_at':now.isoformat(),'finished_at':stamp(),'window_start':start.isoformat(),'mode':'OBSERVATION_ONLY','scope':'10 configured issuer metadata feeds; NOT whole market','configured_issuers':len(config),'successful_issuers':len(config)-len(errors),'metadata_window_complete':not errors,'errors':errors,'sources':sources,'events':sorted(events,key=lambda e:(e['sec_accepted_utc'],e['accession'])),'eligible_count':0,'orders_created':0,'schedule_status':'GITHUB_RUN' if os.environ.get('GITHUB_ACTIONS')=='true' else 'MANUAL_RUN','github_event_name':os.environ.get('GITHUB_EVENT_NAME'),'github_run_url':('https://github.com/'+os.environ.get('GITHUB_REPOSITORY','')+'/actions/runs/'+os.environ.get('GITHUB_RUN_ID','')) if os.environ.get('GITHUB_ACTIONS')=='true' else None}
 (archive_root/'report.json').write_text(json.dumps(report,indent=2));tmp=root/'data/latest_scan.json.tmp';tmp.write_text(json.dumps(report,indent=2));tmp.replace(root/'data/latest_scan.json');return report
if __name__=='__main__':
 r=scan();print(json.dumps({k:r[k] for k in ('run_id','successful_issuers','configured_issuers','metadata_window_complete','eligible_count','orders_created')},indent=2))
