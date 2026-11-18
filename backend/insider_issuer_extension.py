"""Q2 insider issuer-source extension; no security identity or transaction signals."""
import argparse,datetime as dt,hashlib,json,re,sqlite3
from pathlib import Path
from issuer_coverage import text
from sec_prepared_data import SCHEMAS
from sec_insider_history import ARCHIVE,URL,invalid_constant,save as save_json
from financial_pair_candidates import sha
from private_prices import unique_object
BASELINE_SHA='d2f865683fca6681b54295b144efc1e62d9950ae5ec0ac2d2290ffd08a01ef58'
BATCH='insider_2026q2'
def build(rows):
 items={};seen=set()
 for n,row in enumerate(rows,1):
  if n>100000 or len(row)!=5:raise ValueError('row bound/schema')
  acc,cik,name,ticker,filed=row
  if not isinstance(acc,str) or not re.fullmatch('[0-9]{10}-[0-9]{2}-[0-9]{6}',acc) or acc in seen:raise ValueError('accession')
  if not isinstance(cik,str) or not re.fullmatch('[0-9]{1,10}',cik) or not int(cik):raise ValueError('CIK')
  seen.add(acc);cik=str(int(cik)).zfill(10);name=text(name,500);ticker=text(ticker,80)
  day=dt.datetime.strptime(filed,'%d-%b-%Y').date().isoformat()
  if not '2026-04-01'<=day<='2026-06-30':raise ValueError('filing quarter')
  s=items.setdefault(cik,dict(batch_id=BATCH,submissions=0,names=set(),reported_tickers=set(),filing_date_min=day,filing_date_max=day))
  s['submissions']+=1;s['names'].add(name)
  if ticker:s['reported_tickers'].add(ticker)
  s['filing_date_min']=min(s['filing_date_min'],day);s['filing_date_max']=max(s['filing_date_max'],day)
 if not seen:raise ValueError('empty source')
 return [{'cik':c,'sources':[dict(v,names=sorted(v['names']),reported_tickers=sorted(v['reported_tickers']))]} for c,v in sorted(items.items())]
def read_json(path,limit):
 with Path(path).open('rb') as f:raw=f.read(limit+1)
 if len(raw)>limit:raise ValueError('JSON bound')
 return raw,json.loads(raw,object_pairs_hook=unique_object,parse_constant=invalid_constant)
def baseline(path):
 raw,rows=read_json(path,10_000_000)
 if hashlib.sha256(raw).hexdigest()!=BASELINE_SHA:raise ValueError('baseline hash')
 if not isinstance(rows,list) or len(rows)!=7912:raise ValueError('baseline count')
 keys=[]
 for row in rows:
  if not isinstance(row,dict) or set(row)!={'cik','sources'} or not re.fullmatch('[0-9]{10}',row['cik']) or not int(row['cik']):raise ValueError('baseline identity')
  keys.append(row['cik'])
 if len(set(keys))!=len(keys):raise ValueError('baseline duplicates')
 return set(keys)
def audit(config):
 expected={'database','database_sha256','archive','archive_sha256','baseline','completed_ingest'}
 if set(config)!=expected:raise ValueError('configuration schema')
 for k in ['database','archive']:
  if not re.fullmatch('[a-f0-9]{64}',config[k+'_sha256']) or sha(config[k])!=config[k+'_sha256']:raise ValueError('input hash')
 complete=Path(config['completed_ingest'])
 if (complete/'INCOMPLETE').exists():raise ValueError('incomplete ingest')
 marker_raw,marker=read_json(complete/'COMPLETE.json',10000);summary_raw,s=read_json(complete/'summary.json',100000)
 if marker!={'database_sha256':config['database_sha256'],'summary_sha256':hashlib.sha256(summary_raw).hexdigest()} or s['database_sha256']!=config['database_sha256'] or s['source']['sha256']!=config['archive_sha256'] or s['source']['url']!=URL or s['source']['path']!=ARCHIVE or not s['full_field_persistence_verified']:raise ValueError('completed ingestion lineage')
 old=baseline(config['baseline']);db=sqlite3.connect(Path(config['database']).resolve().as_uri()+'?mode=ro',uri=True)
 try:
  if db.execute('PRAGMA quick_check').fetchone()!=('ok',):raise ValueError('database integrity')
  schema=[r[1] for r in db.execute('PRAGMA table_info(insider_submission)')]
  if schema!=SCHEMAS['SUBMISSION.tsv']:raise ValueError('source schema')
  rows=build(db.execute('SELECT ACCESSION_NUMBER,ISSUERCIK,ISSUERNAME,ISSUERTRADINGSYMBOL,FILING_DATE FROM insider_submission ORDER BY rowid'))
 finally:db.close()
 total=sum(r['sources'][0]['submissions'] for r in rows)
 if total!=s['submissions'] or len(rows)!=s['issuer_ciks']:raise ValueError('source counts')
 for k in ['database','archive']:
  if sha(config[k])!=config[k+'_sha256']:raise ValueError('input changed')
 if (complete/'INCOMPLETE').exists() or read_json(complete/'COMPLETE.json',10000)[0]!=marker_raw or read_json(complete/'summary.json',100000)[0]!=summary_raw:raise ValueError('ingestion changed')
 if baseline(config['baseline'])!=old:raise ValueError('baseline changed')
 current={r['cik'] for r in rows};raw=(json.dumps(rows,separators=(',',':'))+'\n').encode()
 if len(raw)>10_000_000:raise ValueError('output bound')
 summary={'version':1,'status':'HISTORICAL_INSIDER_ISSUER_EXTENSION_NOT_SECURITY_MASTER','generated_at':dt.datetime.now(dt.timezone.utc).isoformat(),'batch_id':BATCH,'issuer_ciks':len(rows),'submissions':total,'baseline':{'sha256':BASELINE_SHA,'issuer_ciks':len(old)},'combined_issuer_ciks':len(old|current),'added_issuer_coverage':len(current-old),'source':{'archive_sha256':config['archive_sha256'],'database_sha256':config['database_sha256'],'ingest_summary_sha256':hashlib.sha256(summary_raw).hexdigest(),'source_url':URL,'source_table':'insider_submission','filing_batch_start':'2026-04-01','filing_batch_end':'2026-06-30'},'issuer_metadata':{'sha256':hashlib.sha256(raw).hexdigest(),'byte_count':len(raw)},'simulation_enabled':False,'training_ready':False,'orders_created':0,'limitations':['Extension only: original six-batch issuer snapshot remains unchanged. Combined count deduplicates issuer CIK, not securities or current listings.','Source-associated names and reported tickers include placeholders and conflicting/as-filed names. No preferred/current name, valid ticker or historical security mapping is inferred.','Filing quarter is not transaction quarter; amendments remain separate source submissions. Names must render as inert text, never HTML.','No owner information, signatures, addresses, narrative or transaction values are included. No signals, economic totals or qualified outcomes.','Generation is local audit time; no download or first-public time is inferred. Database-to-archive derivation relies on the completed ingestion and independent field audit.']}
 return raw,summary
def run(config,out):
 out=Path(out)
 if out.exists() or out.resolve().is_relative_to(Path(__file__).resolve().parents[1]):raise ValueError('new private output required')
 out.mkdir(parents=True,mode=0o700);p=out/'INCOMPLETE';p.write_text('Do not use\n');p.chmod(0o600)
 raw,s=audit(config);f=out/'issuers.json';f.write_bytes(raw);f.chmod(0o600);save_json(out/'summary.json',s);save_json(out/'COMPLETE.json',{n:sha(out/n) for n in ['issuers.json','summary.json']});p.unlink();return s
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--config',type=Path,required=True);a.add_argument('--out',type=Path,required=True);v=a.parse_args();_,c=read_json(v.config,20000);print(json.dumps(run(c,v.out),indent=2))
