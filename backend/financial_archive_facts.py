"""Reusable raw-archive correspondence for reported values, never comparable growth."""
import argparse,hashlib,json,sqlite3,zipfile
from pathlib import Path
from decimal import Decimal
from financial_review_names import enrich
from financial_review_catalog import date
from financial_pair_candidates import sha,finite
from sec_prepared_data import inventory,tab_rows,SCHEMAS
METRICS={'Revenues','RevenueFromContractWithCustomerExcludingAssessedTax','NetIncomeLoss'}

def qualify(record,observation,num,sub,tag):
 """Narrow extraction qualification, not accounting truth or comparability."""
 if record['metric'] not in METRICS:raise ValueError('unsupported metric or EPS unit')
 if num['adsh']!=observation['accession'] or num['tag']!=record['metric'] or num['version']!=record['taxonomy'] or date(num['ddate'])!=record['reported_end_date']:raise ValueError('numeric context mismatch')
 if num['qtrs']!='1' or num['uom']!='USD' or num['segments']!='' or num['coreg']!='' or num['footnote']!='':raise ValueError('unsupported or qualified numeric context')
 if not finite(num['value']):raise ValueError('missing/nonfinite number')
 if str(sub['cik']).zfill(10)!=record['issuer_cik'] or sub['adsh']!=num['adsh'] or sub['name']!=observation['issuer_name_as_filed'] or date(sub['filed'])!=observation['filing_date_as_filed'] or sub['form'] not in {'10-Q','10-Q/A','10-K','10-K/A'}:raise ValueError('submission mismatch')
 if tag['tag']!=num['tag'] or tag['version']!=num['version'] or tag['datatype']!='monetary' or tag['custom']!='0' or tag['abstract']!='0' or tag['iord']!='D':raise ValueError('unsupported taxonomy')
 return {'accession':num['adsh'],'issuer_name_as_filed':sub['name'],'value_as_reported':num['value'],'unit_as_reported':num['uom'],'metric':num['tag'],'taxonomy_as_reported':num['version'],'period_start':None,'period_end':date(num['ddate']),'quarters_as_reported':num['qtrs'],'segments_as_reported':num['segments'],'co_registrant_as_reported':num['coreg'],'consolidated_scope_verified':False,'form_as_filed':sub['form'],'amendment_as_filed':sub['form'].endswith('/A'),'filing_date_as_filed':date(sub['filed']),'source_url':observation['source_url'],'first_public_utc':None,'first_observed_utc':None,'original_filing_text_checked':False,'source_archive_sha256':observation['source_archive_sha256'],'database_sha256':observation['database_sha256'],'source_num_data_row':observation['source_rowid'],'source_sub_data_row':observation['prepared_sub_rowid']}

def read_source_rows(z,member,wanted):
 it=tab_rows(z,member);header=next(it);found={}
 for number,values in enumerate(it,1):
  if number in wanted:found[number]=dict(zip(header,values))
 if set(found)!=set(wanted):raise ValueError('source row absent')
 return found

def audit(candidate,databases,archives):
 catalog=enrich(candidate,databases)
 if set(archives)!=set(databases):raise ValueError('exact archive scope required')
 chosen=[r for r in catalog['records'] if r['metric'] in METRICS];bindings={};verified={}
 for r in chosen:
  for o in r['observations']:
   b=o['filing_batch'];entry=bindings.setdefault(b,{'archive':o['source_archive_sha256'],'db':o['database_sha256'],'pairs':[]})
   if (entry['archive'],entry['db'])!=(o['source_archive_sha256'],o['database_sha256']):raise ValueError('conflicting source binding')
   entry['pairs'].append((r,o))
 receipts={}
 for b,entry in bindings.items():
  if sha(archives[b])!=entry['archive'] or sha(databases[b])!=entry['db']:raise ValueError('source hash mismatch')
  conn=sqlite3.connect(Path(databases[b]).resolve().as_uri()+'?mode=ro',uri=True);conn.row_factory=sqlite3.Row
  try:
   with zipfile.ZipFile(archives[b]) as z:
    inventory(z,'financial');wanted_num={o['source_rowid'] for r,o in entry['pairs']};wanted_sub={o['prepared_sub_rowid'] for r,o in entry['pairs']}
    raw_num=read_source_rows(z,'num.txt',wanted_num);raw_sub=read_source_rows(z,'sub.txt',wanted_sub)
    selected_tags={};wanted_tags=set()
    for r,o in entry['pairs']:
     key=(r['metric'],r['taxonomy'])
     if key not in selected_tags:
      tags=list(conn.execute('SELECT rowid,* FROM financial_tag WHERE tag=? AND version=?',key))
      if len(tags)!=1:raise ValueError('taxonomy ambiguity')
      selected_tags[key]=dict(tags[0]);wanted_tags.add(tags[0]['rowid'])
    raw_tags=read_source_rows(z,'tag.txt',wanted_tags)
    member_hashes={}
    for member in ('num.txt','sub.txt','tag.txt'):
     h=hashlib.sha256()
     with z.open(member) as f:
      for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
     member_hashes[member]=h.hexdigest()
    for r,o in entry['pairs']:
     rows=list(conn.execute('SELECT rowid,* FROM financial_num WHERE rowid=?',(o['source_rowid'],)))
     subs=list(conn.execute('SELECT rowid,* FROM financial_sub WHERE rowid=?',(o['prepared_sub_rowid'],)))
     if len(rows)!=1 or len(subs)!=1:raise ValueError('database row missing')
     num=dict(rows[0]);sub=dict(subs[0]);tag=selected_tags[(r['metric'],r['taxonomy'])]
     for member,dbrow,raw in [('num.txt',num,raw_num[num['rowid']]),('sub.txt',sub,raw_sub[sub['rowid']]),('tag.txt',tag,raw_tags[tag['rowid']])]:
      if {k:dbrow[k] for k in SCHEMAS[member]}!=raw:raise ValueError('raw archive/database disagreement')
     fact=qualify(r,o,num,sub,tag);fact['source_tag_data_row']=tag['rowid'];fact['source_member_sha256']=member_hashes
     key=(r['id'],b,o['source_rowid'])
     if key in verified:raise ValueError('duplicate observation')
     verified[key]=fact
    receipts[b]={'source_archive_url':'https://www.sec.gov/files/dera/data/financial-statement-data-sets/'+b.split('_')[1]+b.split('_')[0]+'.zip','archive_sha256':entry['archive'],'database_sha256':entry['db'],'members_sha256':member_hashes,'num_rows_checked':len(wanted_num),'sub_rows_checked':len(wanted_sub),'tag_rows_checked':len(wanted_tags)}
  finally:conn.close()
  if sha(archives[b])!=entry['archive'] or sha(databases[b])!=entry['db']:raise ValueError('source changed during verification')
 contexts=[]
 for r in chosen:
  facts=[verified[(r['id'],o['filing_batch'],o['source_rowid'])] for o in r['observations']]
  relation='numerically_equal' if len({Decimal(f['value_as_reported']) for f in facts})==1 else 'different_reported_numbers'
  if relation!=r['numeric_relation']:raise ValueError('archive relation disagrees with review context')
  contexts.append({'id':r['id'],'issuer_cik':r['issuer_cik'],'metric':r['metric'],'status':'ARCHIVE_CORRESPONDENCE_VERIFIED_NOT_COMPARABLE','facts':facts,'comparability_verified':False,'percentage_change':None,'absolute_change':None,'outcome_status':'INSUFFICIENT_EVIDENCE'})
 return {'version':1,'scope':'SEC_PREPARED_ARCHIVE_REPORTED_VALUES_NOT_GROWTH','contexts':contexts,'source_receipts':receipts,'excluded_eps_contexts':len(catalog['records'])-len(chosen),'training_ready':False,'execution_ready':False,'limitations':['Values correspond exactly to retained SEC prepared num.txt rows, associated submission and monetary taxonomy records; original filing text has not been checked.', 'Period start is unknown. qtrs=1 and equal end dates do not prove exact durations, accounting comparability or consolidated scope.', 'Amendments remain separate observations; different numbers are not confirmed restatements or economic changes.', 'No financial-change arithmetic, prices, predictions, decisions or outcomes are generated. EPS contexts remain excluded because source per-share unit is unverified.']}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('candidate');p.add_argument('databases');p.add_argument('archives');p.add_argument('output');a=p.parse_args()
 result=audit(a.candidate,json.loads(Path(a.databases).read_text()),json.loads(Path(a.archives).read_text()))
 with Path(a.output).open('x') as f:json.dump(result,f,separators=(',',':'));f.write('\n')
