"""Attach as-filed issuer labels through exact SEC submission joins, never name identity."""
import argparse,copy,json,sqlite3
from pathlib import Path
from financial_review_catalog import build,date
from financial_pair_candidates import sha

def attach(record,lookup):
 r=copy.deepcopy(record);names=set()
 for o in r['observations']:
  rows=lookup(o['filing_batch'],o['accession'])
  if len(rows)!=1:raise ValueError('missing or ambiguous submission')
  sub=rows[0]
  if str(sub['cik']).zfill(10)!=r['issuer_cik'] or sub['adsh']!=o['accession'] or date(sub['filed'])!=o['filing_date_as_filed']:raise ValueError('submission identity/date conflict')
  name=sub['name']
  if not isinstance(name,str) or not name.strip() or len(name)>400 or any(ord(x)<32 for x in name):raise ValueError('invalid as-filed name')
  o['issuer_name_as_filed']=name;o['prepared_sub_rowid']=sub['rowid'];names.add(name)
 r['issuer_names_as_filed']=sorted(names);return r

def enrich(candidate,databases):
 d=build(candidate);expected={}
 for r in d['records']:
  for o in r['observations']:
   batch=o['filing_batch'];digest=o['database_sha256']
   if batch in expected and expected[batch]!=digest:raise ValueError('conflicting database identity')
   expected[batch]=digest
 if set(databases)!=set(expected):raise ValueError('exact source database scope required')
 conns={}
 try:
  for batch,path in databases.items():
   if sha(path)!=expected[batch]:raise ValueError('database hash mismatch')
   conn=sqlite3.connect(Path(path).resolve().as_uri()+'?mode=ro',uri=True);conn.row_factory=sqlite3.Row;conns[batch]=conn
  cache={}
  def lookup(batch,accession):
   key=(batch,accession)
   if key not in cache:cache[key]=[dict(x) for x in conns[batch].execute('SELECT rowid,adsh,cik,name,filed FROM financial_sub WHERE adsh=?',(accession,))]
   return cache[key]
  d['records']=[attach(r,lookup) for r in d['records']]
  for batch,path in databases.items():
   if sha(path)!=expected[batch]:raise ValueError('database changed during read')
  d['version']=2;d['issuer_label_policy']='EXACT_ACCESSION_CIK_JOIN_AS_FILED_NOT_CURRENT_NAME_OR_SECURITY';return d
 finally:
  for conn in conns.values():conn.close()
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('candidate');p.add_argument('databases_json');p.add_argument('output');a=p.parse_args()
 result=enrich(a.candidate,json.loads(Path(a.databases_json).read_text()))
 with Path(a.output).open('x') as f:json.dump(result,f,separators=(',',':'));f.write('\n')
