"""Allowlisted, amount-free projection of retained repeated-context evidence."""
import argparse, datetime as dt, hashlib, json, re
from pathlib import Path
from decimal import Decimal

TAGS={'Revenues','RevenueFromContractWithCustomerExcludingAssessedTax','NetIncomeLoss','EarningsPerShareDiluted'}
PIN='19327178d9dbe5e8a2d5956bd51a717d4f7ce458ae7e7ee89b8fa77b52915ba1'
BLOCKERS=['Prepared end date and qtrs do not establish exact reporting duration or full accounting comparability.', 'Repeated values are not independent evidence; different numbers do not prove a restatement or economic change.', 'First-public time, historical security mapping and eligible price outcomes are unverified.']
def match(pattern,value):
 if not isinstance(value,str) or not re.fullmatch(pattern,value):raise ValueError('invalid identifier')
 return value
def date(value):
 match(r'\d{8}',value);return dt.datetime.strptime(value,'%Y%m%d').date().isoformat()
def project(rows):
 if not isinstance(rows,list) or not 1<=len(rows)<=1000:raise ValueError('catalog bound')
 output=[];seen=set()
 for r in rows:
  ident=match(r'[a-f0-9]{64}',r['context_id'])
  if ident in seen:raise ValueError('duplicate context')
  seen.add(ident);c=r['context'];cik=match(r'[1-9]\d{0,9}',c['issuer_cik'])
  if c['tag'] not in TAGS or c['qtrs']!='1' or c['segments']!='' or c['coreg']!='' or c['uom']!='USD':raise ValueError('unsupported context')
  match(r'us-gaap/\d{4}',c['version'])
  if any(r.get(k) is not False for k in ('restatement_verified','comparability_verified','event_group_verified','training_ready')):raise ValueError('unreviewed qualification')
  if r['category']!='multiple_accession_context' or type(r['cross_batch']) is not bool:raise ValueError('category')
  obs=[];values=[]
  if not 2<=len(r['observations'])<=30:raise ValueError('observation bound')
  for o in r['observations']:
   if o['issuer_cik_as_filed']!=cik:raise ValueError('identity conflict')
   acc=match(r'\d{10}-\d{2}-\d{6}',o['accession']);batch=match(r'q[1-4]_20\d{2}_filing_batch',o['batch'])
   value=Decimal(o['value_as_filed'])
   if not value.is_finite():raise ValueError('nonfinite')
   values.append(value)
   obs.append({'accession':acc,'filing_batch':batch,'filing_date_as_filed':date(o['filed_as_filed']),'source_rowid':o['source_rowid'],'database_sha256':match(r'[a-f0-9]{64}',o['database_sha256']),'source_archive_sha256':match(r'[a-f0-9]{64}',o['source_archive_sha256']),'source_url':f'https://www.sec.gov/Archives/edgar/data/{cik}/{acc.replace("-","")}/{acc}-index.html'})
  relation='numerically_equal' if len(set(values))==1 else 'different_reported_numbers'
  if relation!=r['numeric_relation'] or len({o['accession'] for o in obs})<2 or r['cross_batch']!=(len({o['filing_batch'] for o in obs})>1):raise ValueError('relation mismatch')
  output.append({'id':ident,'issuer_cik':cik.zfill(10),'metric':c['tag'],'taxonomy':c['version'],'reported_unit':c['uom'],'unit_status':('EPS_UNIT_REQUIRES_REVIEW' if c['tag']=='EarningsPerShareDiluted' else 'SOURCE_REPORTED_NOT_COMPARABILITY_VERIFIED'),'reported_end_date':date(c['ddate']),'numeric_relation':relation,'cross_batch':r['cross_batch'],'status':'EVIDENCE_REVIEW_REQUIRED','observations':obs,'first_observed_utc':None,'comparability_verified':False,'outcome_status':'INSUFFICIENT_EVIDENCE'})
 return {'version':1,'scope':'HISTORICAL_REPEATED_FINANCIAL_CONTEXT_REVIEW','source_candidate_sha256':PIN,'records':output,'blockers':BLOCKERS,'training_ready':False,'execution_ready':False}
def build(path):
 raw=Path(path).read_bytes()
 if len(raw)>10000000 or hashlib.sha256(raw).hexdigest()!=PIN:raise ValueError('source pin mismatch')
 return project(json.loads(raw))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('input');p.add_argument('output');a=p.parse_args();out=Path(a.output)
 with out.open('x') as f:json.dump(build(a.input),f,separators=(',',':'));f.write('\n')
