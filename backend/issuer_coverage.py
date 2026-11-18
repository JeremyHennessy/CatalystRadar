"""Offline issuer-level source coverage, not a security master or current directory."""
import argparse, collections, datetime as dt, hashlib, json, re, sqlite3
from pathlib import Path
from financial_pair_candidates import sha
from private_prices import unique_object

BATCHES={
 'financial_2025q4':('financial_sub','2025-10-01','2025-12-31'),
 'financial_2026q1':('financial_sub','2026-01-01','2026-03-31'),
 'financial_2026q2':('financial_sub','2026-04-01','2026-06-30'),
 'financial_2026q3':('financial_sub','2026-07-01','2026-09-30'),
 'insider_2026q3':('insider_submission','2026-07-01','2026-09-30'),
 'notes_2026_10':('notes_sub','2026-10-01','2026-10-31')}
OLD={'financial_2026q3','insider_2026q3','notes_2026_10'}

def text(v,limit):
 if not isinstance(v,str) or len(v)>limit or any(ord(c)<32 for c in v):raise ValueError('invalid source text')
 return v

def build_rows(batch,rows):
 if batch not in BATCHES:raise ValueError('unknown batch')
 items={};seen=set();start,end=BATCHES[batch][1:]
 for count,row in enumerate(rows,1):
  if count>100000 or len(row)!=5:raise ValueError('row bound/schema')
  acc,cik,name,ticker,filed=row
  if not isinstance(acc,str) or not re.fullmatch(r'\d{10}-\d{2}-\d{6}',acc) or acc in seen:raise ValueError('duplicate/invalid accession')
  seen.add(acc)
  if not isinstance(cik,str) or not re.fullmatch(r'\d{1,10}',cik) or int(cik)==0:raise ValueError('CIK')
  cik=str(int(cik)).zfill(10);name=text(name,500);ticker=text(ticker,80)
  if batch.startswith('insider_'):
   day=dt.datetime.strptime(filed,'%d-%b-%Y').date().isoformat()
  else:day=dt.datetime.strptime(filed,'%Y%m%d').date().isoformat()
  if not start<=day<=end:raise ValueError('filing batch boundary')
  r=items.setdefault(cik,{'batch_id':batch,'submissions':0,'names':set(),'reported_tickers':set(),'filing_date_min':day,'filing_date_max':day})
  r['submissions']+=1;r['names'].add(name)
  if ticker:r['reported_tickers'].add(ticker)
  r['filing_date_min']=min(r['filing_date_min'],day);r['filing_date_max']=max(r['filing_date_max'],day)
 if not seen:raise ValueError('empty batch')
 return {k:dict(v,names=sorted(v['names']),reported_tickers=sorted(v['reported_tickers'])) for k,v in sorted(items.items())}

def combine(batches):
 if set(batches)!=set(BATCHES):raise ValueError('exact six batches required')
 combined={};old=set();counts={}
 for batch,items in sorted(batches.items()):
  counts[batch]={'issuer_ciks':len(items),'submissions':sum(x['submissions'] for x in items.values())}
  for cik,r in items.items():
   combined.setdefault(cik,[]).append(r)
   if batch in OLD:old.add(cik)
 result=[{'cik':cik,'sources':v} for cik,v in sorted(combined.items())]
 return result,{'issuer_ciks':len(result),'previous_three_batch_issuer_ciks':len(old),'added_issuer_coverage':len(set(combined)-old),'batch_counts':counts,'issuers_with_multiple_reported_names':sum(len({n for s in v for n in s['names']})>1 for v in combined.values())}

def audit(config):
 if set(config)!=set(BATCHES):raise ValueError('input batches')
 batches={};pins={}
 for batch,p in sorted(config.items()):
  if set(p)!={'database','database_sha256','archive','archive_sha256','source_url'}:raise ValueError('input schema')
  for key in ['database','archive']:
   if not re.fullmatch('[a-f0-9]{64}',p[key+'_sha256']) or sha(p[key])!=p[key+'_sha256']:raise ValueError('input hash')
  if not re.fullmatch(r'https://www\.sec\.gov/files/[A-Za-z0-9_./-]+\.zip',p['source_url']):raise ValueError('source URL')
  path=Path(p['database']);db=sqlite3.connect(path.resolve().as_uri()+'?mode=ro',uri=True)
  try:
   if db.execute('PRAGMA quick_check').fetchone()!=('ok',):raise ValueError('database integrity')
   table=BATCHES[batch][0]
   query=('SELECT ACCESSION_NUMBER,ISSUERCIK,ISSUERNAME,ISSUERTRADINGSYMBOL,FILING_DATE FROM insider_submission' if batch.startswith('insider_') else f"SELECT adsh,cik,name,'',filed FROM {table}")
   batches[batch]=build_rows(batch,db.execute(query))
  finally:db.close()
  for key in ['database','archive']:
   if sha(p[key])!=p[key+'_sha256']:raise ValueError('input changed')
  pins[batch]={'database_sha256':p['database_sha256'],'archive_sha256':p['archive_sha256'],'source_url':p['source_url'],'source_table':table,'filing_batch_start':BATCHES[batch][1],'filing_batch_end':BATCHES[batch][2]}
 rows,counts=combine(batches)
 raw=(json.dumps(rows,separators=(',',':'))+'\n').encode()
 if len(raw)>10000000:raise ValueError('public metadata size bound')
 summary={'version':1,'status':'HISTORICAL_ISSUER_COVERAGE_NOT_SECURITY_MASTER','generated_at':dt.datetime.now(dt.timezone.utc).isoformat(),**counts,'sources':pins,'issuer_metadata':{'sha256':hashlib.sha256(raw).hexdigest(),'byte_count':len(raw)},'simulation_enabled':False,'training_ready':False,'orders_created':0,'limitations':['CIK joins issuer source coverage only, not securities, active listings, ticker history or stock returns.','Names and insider-reported tickers (including placeholders such as NONE) are retained by filing batch, not preferred, validated or current identifiers. Name variation is not proof of a corporate event.','Financial filing quarters contain mixed fiscal periods; counts retain amendments and repeated reporting. The same accession can occur in distinct dataset families.','No owner names, addresses, raw disclosures or financial values included. Text must be rendered inertly, not as HTML.','Generated time is local audit time, not download or first-public timing. Input hashes pin retained evidence; earlier ingestion audits establish database-to-archive derivation.','Prior public snapshots remain unchanged. Added coverage means newly searchable retained evidence, not newly listed companies or training examples.']}
 return raw,summary

def save(config,out):
 if out.exists() or out.resolve().is_relative_to(Path(__file__).resolve().parents[1]):raise ValueError('new private output required')
 out.mkdir(mode=0o700,parents=True);marker=out/'INCOMPLETE';marker.write_text('Not completed\n');marker.chmod(0o600)
 raw,summary=audit(config)
 for name,data in [('issuers.json',raw),('summary.json',(json.dumps(summary,indent=2)+'\n').encode())]:
  p=out/name;p.write_bytes(data);p.chmod(0o600)
 complete={n:sha(out/n) for n in ['issuers.json','summary.json']};p=out/'COMPLETE.json';p.write_text(json.dumps(complete,indent=2)+'\n');p.chmod(0o600);marker.unlink()
 return summary

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--config',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
 raw=a.config.read_bytes()
 if len(raw)>20000:raise ValueError('config bound')
 c=json.loads(raw,object_pairs_hook=unique_object,parse_constant=lambda _:(_ for _ in ()).throw(ValueError('nonfinite JSON')))
 print(json.dumps(save(c,a.out),indent=2))
