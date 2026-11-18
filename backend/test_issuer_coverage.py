import copy, json, sqlite3, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
import issuer_coverage as m

class CoverageTests(unittest.TestCase):
 def row(self,cik='1',name='Example',date='20260701',acc='0000000001-26-000001',ticker=''):
  return (acc,cik,name,ticker,date)
 def test_identity_names_and_ticker_are_source_associated(self):
  a=m.build_rows('financial_2026q3',[self.row(),self.row(cik='0000000001',name='Former',acc='0000000001-26-000002')])
  self.assertEqual(a['0000000001']['names'],['Example','Former']);self.assertEqual(a['0000000001']['submissions'],2)
  b=m.build_rows('insider_2026q3',[self.row(date='01-JUL-2026',ticker='NONE')]);self.assertEqual(b['0000000001']['reported_tickers'],['NONE'])
 def test_bad_identity_duplicates_and_boundaries(self):
  for rows in [[],[self.row(cik='0')],[self.row(cik=' 1')],[self.row(),self.row()],[self.row(date='20260630')],[self.row(date='20261001')],[self.row(name='bad\nvalue')]]:
   with self.assertRaises(ValueError):m.build_rows('financial_2026q3',rows)
 def test_union_not_sum_and_all_names_retained(self):
  batches={k:m.build_rows(k,[self.row(cik=('2' if k=='financial_2026q1' else '1'),date=(m.dt.date.fromisoformat(v[1]).strftime('%d-%b-%Y') if k.startswith('insider') else v[1].replace('-','')))]) for k,v in m.BATCHES.items()}
  rows,s=m.combine(batches);self.assertEqual(s['issuer_ciks'],2);self.assertEqual(s['previous_three_batch_issuer_ciks'],1);self.assertEqual(s['added_issuer_coverage'],1)
  self.assertEqual(len(rows[0]['sources']),5)
  del batches['notes_2026_10']
  with self.assertRaises(ValueError):m.combine(batches)
 def fixture(self,root):
  cfg={}
  for k,(table,start,end) in m.BATCHES.items():
   p=root/(k+'.sqlite');db=sqlite3.connect(p)
   cols=('ACCESSION_NUMBER,ISSUERCIK,ISSUERNAME,ISSUERTRADINGSYMBOL,FILING_DATE' if k.startswith('insider') else 'adsh,cik,name,unused,filed')
   db.execute('create table '+table+' ('+','.join(c+' TEXT' for c in cols.split(','))+')')
   day=m.dt.date.fromisoformat(start).strftime('%d-%b-%Y') if k.startswith('insider') else start.replace('-','')
   db.execute('insert into '+table+' values (?,?,?,?,?)',self.row(date=day,ticker='TEST' if k.startswith('insider') else ''));db.commit();db.close()
   z=root/(k+'.zip');z.write_bytes(b'synthetic hash fixture; not a real SEC archive')
   cfg[k]={'database':str(p),'database_sha256':m.sha(p),'archive':str(z),'archive_sha256':m.sha(z),'source_url':'https://www.sec.gov/files/synthetic/'+k+'.zip'}
  return cfg
 def test_end_to_end_allowlist_persistence_and_hash_failure(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);cfg=self.fixture(root);out=root/'out';s=m.save(cfg,out)
   self.assertFalse((out/'INCOMPLETE').exists());self.assertEqual(s['issuer_ciks'],1)
   rows=json.loads((out/'issuers.json').read_text());self.assertEqual(set(rows[0]),{'cik','sources'})
   for n,h in json.loads((out/'COMPLETE.json').read_text()).items():self.assertEqual(m.sha(out/n),h)
   self.assertEqual(out.stat().st_mode&0o777,0o700)
   cfg['financial_2026q1']['database_sha256']='0'*64
   with self.assertRaises(ValueError):m.save(cfg,root/'failed')
   self.assertTrue((root/'failed'/'INCOMPLETE').exists());self.assertFalse((root/'failed'/'COMPLETE.json').exists())
 def test_failure_does_not_leave_completion(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);cfg=self.fixture(root)
   with patch.object(m,'audit',side_effect=ValueError('synthetic failure')):
    with self.assertRaises(ValueError):m.save(cfg,root/'out')
   self.assertTrue((root/'out'/'INCOMPLETE').exists())
if __name__=='__main__':unittest.main()
