"""Exact-CIK navigation across fixed public sources; no security or event joining."""
import argparse,datetime as dt,hashlib,json,re,unicodedata
from collections import Counter,defaultdict
from pathlib import Path
from openfigi_evidence import read_pinned
from insider_full_review import package as rebuild_insider
from research_scanner import build_package as rebuild_scanner
PINS={'prepared': {'path': 'web/issuer-coverage/issuers.json', 'bytes': 5607678, 'sha256': 'd2f865683fca6681b54295b144efc1e62d9950ae5ec0ac2d2290ffd08a01ef58'}, 'prepared_summary': {'path': 'web/issuer-coverage/summary.json', 'bytes': 4695, 'sha256': '38efc2c9f5ae3151d53b55dc6827a6e68aa0f06745dea800f87db202362d3fab'}, 'prepared_q2': {'path': 'web/issuer-coverage-q2-insider/issuers.json', 'bytes': 1033537, 'sha256': 'f578d45f320c79a30e0a4201091a68fbbc86993345b3b4d87d2d5891c6a921b0'}, 'prepared_q2_summary': {'path': 'web/issuer-coverage-q2-insider/summary.json', 'bytes': 2008, 'sha256': '347507aae987de18e179fc3b93762e168507af079ad86cb7be318b084db2b14b'}, 'insider': {'path': 'web/insider-full/v1/index.json', 'bytes': 1520624, 'sha256': 'ba097a652e868b5d6679471c4624480b6ad698eeaed968772b2373fef88f8662'}, 'disclosure': {'path': 'web/disclosure-catalog/filings.json', 'bytes': 215476, 'sha256': 'e9ff960153c9ea13c4afd3ba049a46e61d30699989c126303ca093c81451c036'}, 'disclosure_summary': {'path': 'web/disclosure-catalog/summary.json', 'bytes': 2512, 'sha256': 'd4b42d28e603da94ed5d7fe230d404884191af692213078c834e152a470cf003'}, 'scanner': {'path': 'web/research-scanner/v1/index.json', 'bytes': 1451309, 'sha256': '6c11b89a1c133c0d2a8f6da7ca3726ff9ef4da14dbe6564c16015c090e1e7182'}}
BASE='web/company-investigation/v1/'
LIMITS={'index_bytes':2400000,'shard_bytes':500000,'package_bytes':24000000}
BATCH_FIELDS={'batch_id','submissions','names','reported_tickers','filing_date_min','filing_date_max'}
def encoded(x):return (json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False)+'\n').encode()
def digest(x):return hashlib.sha256(encoded(x)).hexdigest()
def bucket(c):return f'{hashlib.sha256(c.encode()).digest()[0]%128:02x}'
def cik(c):
 if not isinstance(c,str) or not re.fullmatch('[0-9]{10}',c) or not int(c):raise ValueError('invalid CIK; no identity repair or silent omission')
 return c
def labels(xs,empty=False):
 if not isinstance(xs,list) or (not empty and not xs) or len(xs)!=len(set(xs)):raise ValueError('source label list')
 for x in xs:
  if not isinstance(x,str) or len(x)>500 or any(unicodedata.category(c).startswith('C') for c in x):raise ValueError('source label')
 return xs
def source_ref(key,pointer,obj):return {'key':key,'json_pointer':pointer,'object_sha256':digest(obj)}
def number(n):
 if type(n)is not int or n<0:raise ValueError('nonnegative integer required')
 return n

def prepared(data):
 out=defaultdict(list);census=defaultdict(Counter)
 for key,summarykey in [('prepared','prepared_summary'),('prepared_q2','prepared_q2_summary')]:
  rows=data[key];summary=data[summarykey];meta=summary['issuer_metadata']
  if meta['sha256']!=PINS[key]['sha256'] or meta['byte_count']!=PINS[key]['bytes'] or len(rows)!=summary['issuer_ciks']:raise ValueError('prepared metadata pin/count')
  seen=set()
  for i,r in enumerate(rows):
   if set(r)!={'cik','sources'} or cik(r['cik']) in seen:raise ValueError('duplicate/invalid prepared issuer')
   ci=r['cik'];seen.add(ci);batches=set()
   for s in r['sources']:
    if set(s)!=BATCH_FIELDS or s['batch_id'] in batches or not number(s['submissions']):raise ValueError('batch fields/count')
    batches.add(s['batch_id']);labels(s['names']);labels(s['reported_tickers'],True)
    provenance=summary['sources'][s['batch_id']] if key=='prepared' else summary['source']
    if key=='prepared_q2' and s['batch_id']!='insider_2026q2':raise ValueError('extension batch')
    a,b=(dt.date.fromisoformat(s[k]) for k in ('filing_date_min','filing_date_max'))
    if not dt.date.fromisoformat(provenance['filing_batch_start'])<=a<=b<=dt.date.fromisoformat(provenance['filing_batch_end']):raise ValueError('batch filing dates')
    census[s['batch_id']]['issuer_ciks']+=1;census[s['batch_id']]['submissions']+=s['submissions']
   out[ci].append({'source_record':r,'source_ref':source_ref(key,f'/{i}',r)})
  expected=summary['batch_counts'] if key=='prepared' else {summary['batch_id']:{'issuer_ciks':summary['issuer_ciks'],'submissions':summary['submissions']}}
  if any(dict(census[k])!=v for k,v in expected.items()):raise ValueError('per-batch conservation')
 if len(out)!=8034 or data['prepared_q2_summary']['combined_issuer_ciks']!=len(out) or data['prepared_q2_summary']['baseline']['sha256']!=PINS['prepared']['sha256']:raise ValueError('prepared union')
 return out,dict(census)

def project(data):
 prep,batches=prepared(data);ins={};disc=defaultdict(list);scan=defaultdict(list)
 upstream=data['insider'];shards={}
 if upstream['quarantine'] or upstream['counts']['quarantined_rows'] or upstream['counts']['quarantined_filings']:raise ValueError('new quarantine requires explicit review; never silently omit')
 all_shard_ciks=[]
 for s in upstream['detail_shards']:
  b=s['bucket']
  if not re.fullmatch('[0-9a-f]{2}',b) or b in shards or s['path']!='web/insider-full/v1/details/'+b+'.json':raise ValueError('insider shard path/bucket')
  shards[b]=s;all_shard_ciks+=s['issuer_ciks']
 if len(shards)!=256 or len(all_shard_ciks)!=len(set(all_shard_ciks)):raise ValueError('insider shard membership')
 for i,r in enumerate(upstream['issuers']):
  ci=cik(r['issuer_cik'])
  if ci in ins or ci not in prep or ci not in shards[r['shard']]['issuer_ciks']:raise ValueError('insider identity/membership')
  labels(r['issuer_names_as_filed']);labels(r['issuer_tickers_as_filed'],True)
  ins[ci]={'source_record':r,'source_ref':source_ref('insider',f'/issuers/{i}',r),'filing_detail_shard':{k:shards[r['shard']][k] for k in ('bucket','path','byte_count','sha256')}}
 if set(all_shard_ciks)!=set(ins) or len(ins)!=3809 or sum(r['source_record']['filings'] for r in ins.values())!=26827 or sum(r['source_record']['selected_transaction_rows'] for r in ins.values())!=63552:raise ValueError('insider conservation')
 summary=data['disclosure_summary'];meta=summary['metadata'];seen=set()
 if meta['sha256']!=PINS['disclosure']['sha256'] or meta['byte_count']!=PINS['disclosure']['bytes']:raise ValueError('disclosure pin')
 for i,r in enumerate(data['disclosure']):
  ci=cik(r['issuer_cik']);a=r['accession']
  if ci not in prep or a in seen or not re.fullmatch('[0-9]{10}-[0-9]{2}-[0-9]{6}',a):raise ValueError('disclosure identity')
  seen.add(a);labels([r['issuer_name_as_filed']]);disc[ci].append({'source_record':r,'source_ref':source_ref('disclosure',f'/{i}',r)})
 if (len(seen),len(disc),sum(r['disclosure_records'] for r in data['disclosure']),sum(r['records_with_dimensions'] for r in data['disclosure']))!=(summary['filings'],summary['issuer_ciks'],summary['disclosure_records'],summary['records_with_dimensions']):raise ValueError('disclosure conservation')
 seen=set()
 for i,r in enumerate(data['scanner']['records']):
  if r['id'] in seen:raise ValueError('duplicate scanner ID')
  seen.add(r['id']);members=set()
  for association in r['issuer_associations']:
   ci=cik(association['issuer_cik']);labels(association['names_as_reported'])
   if ci in members:raise ValueError('duplicate scanner CIK association')
   members.add(ci);scan[ci].append({'source_record':r,'source_ref':source_ref('scanner',f'/records/{i}',r)})
 if len(seen)!=905 or len(scan)!=117 or set(scan)-set(prep)!={'0000108772'}:raise ValueError('unexpected scanner source-only union')
 union=sorted(set(prep)|set(ins)|set(disc)|set(scan))
 if len(union)!=8035:raise ValueError('union changed; review required')
 details={};directory=[]
 for ci in union:
  names=set()
  for r in prep.get(ci,[]):
   for s in r['source_record']['sources']:names.update(s['names'])
  if ci in ins:names.update(ins[ci]['source_record']['issuer_names_as_filed'])
  for r in disc.get(ci,[]):names.add(r['source_record']['issuer_name_as_filed'])
  for r in scan.get(ci,[]):
   for a in r['source_record']['issuer_associations']:
    if a['issuer_cik']==ci:names.update(a['names_as_reported'])
  b=bucket(ci);counts={'prepared_batches':sum(len(x['source_record']['sources']) for x in prep.get(ci,[])),'insider_filings':ins[ci]['source_record']['filings'] if ci in ins else 0,'disclosure_filings':len(disc.get(ci,[])),'scanner_records':len(scan.get(ci,[]))}
  directory.append({'issuer_cik':ci,'names_as_reported':sorted(names),'detail_bucket':b,'source_counts':counts})
  details[ci]={'issuer_cik':ci,'prepared':{'status':'SOURCE_ASSOCIATED_PREPARED_BATCHES' if ci in prep else 'NO_ENTRY_IN_FIXED_PREPARED_INDEX','records':prep.get(ci,[])},'insider':{'status':'SELECTED_P_S_FILINGS_IN_RETAINED_Q2_Q3' if ci in ins else 'NO_SELECTED_P_S_FILINGS_IN_FIXED_RETAINED_BATCH_INDEX','record':ins.get(ci)},'disclosure':{'status':'SELECTED_DISCLOSURE_FILINGS_IN_FIXED_OCTOBER_CATALOG' if ci in disc else 'NO_SELECTED_DISCLOSURE_IN_FIXED_OCTOBER_CATALOG','records':disc.get(ci,[])},'scanner':{'status':'SELECTED_RECORDS_IN_FIXED_SCANNER' if ci in scan else 'NO_RECORD_IN_FIXED_SCANNER','records':scan.get(ci,[])},'existing_dossier_available':ci in data['scanner']['coverage']['existing_dossier_ciks'],'historical_security_identity_verified':False,'first_public_utc':None,'training_ready':False,'execution_ready':False}
 groups={f'{i:02x}':[] for i in range(128)}
 for ci,r in details.items():groups[bucket(ci)].append(r)
 payloads={};manifest=[]
 for b,rs in groups.items():
  raw=encoded({'schema_version':1,'bucket':b,'companies':rs});path=BASE+'details/'+b+'.json'
  if len(raw)>LIMITS['shard_bytes']:raise ValueError('company shard bound')
  payloads[path]=raw;manifest.append({'bucket':b,'path':path,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'issuer_ciks':[r['issuer_cik'] for r in rs]})
 result={'schema_version':1,'status':'EXACT_CIK_PUBLIC_SOURCE_INVESTIGATION_NOT_SECURITY_MASTER','sources':PINS,'counts':{'company_ciks':8035,'prepared_ciks':8034,'scanner_only_ciks':1,'insider_ciks':3809,'insider_filings':26827,'selected_insider_rows':63552,'disclosure_ciks':454,'disclosure_filings':466,'scanner_ciks':117,'scanner_evidence_records':905,'scanner_company_associations':sum(len(x) for x in scan.values())},'prepared_batch_counts':batches,'directory':directory,'detail_shards':manifest,'source_context':{'prepared':data['prepared_summary'],'prepared_q2':data['prepared_q2_summary'],'insider':{k:upstream[k] for k in ('status','selection','sources','limitations','quarantine')},'disclosure':data['disclosure_summary'],'scanner':{k:data['scanner'][k] for k in ('status','coverage','limitations')}},'limitations':['Exact CIK is a source association, not security identity, a merged company, economic event or causal/timing join. Names are source-reported search labels, not preferred/current names.','8034 issuers have prepared batch associations; Xerox Corporation CIK0000108772 is present only through separately reviewed scanner evidence. No prepared batch is fabricated for it, and Xerox Holdings remains a separate CIK.','Prepared submission counts and filing-date bounds retain each batch and source. Do not sum them into unique histories or comparable fiscal results.','No selected insider/disclosure/scanner record means only none in that fixed selected projection, not no activity. Prepared index absence is not missing all SEC filings. Outside-directory CIK coverage is unassessed.','P/S filings are open-market OR private reported rows; amendments are unreconciled. Plan flags are submission-level; unchecked/missing does not establish an unplanned transaction. No intent, compliance, prices, quantities or owner identities are inferred.','Disclosure concepts are not confirmed deals; scanner source-reviewed status is narrow documentary review, not independent accounting truth or training/price qualification.','Source-specific filing/report/transaction/observation clocks remain distinct. No first-public, present availability or historical security mapping is established.','Existing source objects, source-specific unknowns and separate registrant roles are preserved unchanged. No provider call, model, new collection or trading occurs.'],'limits':LIMITS,'provider_requests_made':False,'training_ready':False,'execution_ready':False}
 payloads[BASE+'index.json']=encoded(result)
 if len(payloads[BASE+'index.json'])>LIMITS['index_bytes'] or sum(map(len,payloads.values()))>LIMITS['package_bytes']:raise ValueError('package bound')
 return result,payloads

def build(root):
 data={}
 for key,m in PINS.items():
  data[key],n=read_pinned(Path(root)/m['path'],m['sha256'],m['bytes'])
  if n!=m['bytes']:raise ValueError('source bytes')
 # Verify the complete public insider index against all original pinned filing shards.
 cards=[]
 for s in data['insider']['detail_shards']:
  if s['path']!='web/insider-full/v1/details/'+s['bucket']+'.json' or s['byte_count']>1000000:raise ValueError('upstream path/bound')
  obj,n=read_pinned(Path(root)/s['path'],s['sha256'],s['byte_count'])
  if n!=s['byte_count'] or obj['bucket']!=s['bucket']:raise ValueError('upstream shard identity')
  for issuer in obj['issuers']:
   for f in issuer['filings']:
    if f['issuer_cik']!=issuer['issuer_cik']:raise ValueError('cross-CIK filing')
    cards.append(f)
 rebuilt,_=rebuild_insider(cards,data['insider']['quarantine'],data['insider']['sources'])
 if rebuilt!=data['insider']:raise ValueError('upstream insider rebuild')
 scanner,_=rebuild_scanner(root)
 if scanner!=data['scanner']:raise ValueError('upstream scanner rebuild')
 return project(data)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--root',default=str(Path(__file__).resolve().parents[1]));a=p.parse_args();print(encoded(build(a.root)[0]).decode(),end='')
