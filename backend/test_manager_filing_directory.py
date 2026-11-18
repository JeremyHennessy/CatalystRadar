import copy,json,sqlite3,tempfile,unittest,zipfile
from pathlib import Path
from unittest.mock import patch
from manager_filing_directory import build,search,write,digest,bucket
from manager_period_research import project
from test_manager_period_research import fixture
from financial_pair_candidates import sha

class ManagerDirectoryTest(unittest.TestCase):
 def payloads(self):
  a=project(*fixture(),all_managers=True)
  with patch('manager_filing_directory.audit',return_value=a):return build('db','hash','zip','hash')
 def test_all_selection_and_default_unchanged(self):
  s,c,q=fixture();s[1]['CIK']='3'
  a=project(s,c,q,all_managers=True);self.assertEqual([m['manager_cik'] for m in a['managers']],['0000000002','0000000003','0000000010'])
  self.assertEqual(a['counts']['selected_filings'],4)
  self.assertEqual(len(project(s,c,q)['managers']),1)
  with self.assertRaises(ValueError):project(s,c,q,all_managers=True,manager_cik='2')
 def test_index_shard_bijection_counts_hashes(self):
  p=self.payloads();d=json.loads(p['index.json']);seen=[]
  for b,meta in d['shards'].items():
   data=p[meta['path']];self.assertEqual(len(data),meta['bytes']);self.assertEqual(digest(data),meta['sha256'])
   shard=json.loads(data);self.assertEqual(shard['bucket'],b)
   for m in shard['managers']:self.assertEqual(bucket(m['manager_cik']),b);seen.append(m['manager_cik'])
  self.assertEqual(sorted(seen),[e[0] for e in d['entries']]);self.assertEqual(sum(e[1] for e in d['entries']),4)
  for forbidden in ('FILINGMANAGER_NAME','TABLEVALUETOTAL','SIGNATURE','STREET'):
   self.assertNotIn(forbidden,p['index.json'].decode()+''.join(v.decode() for k,v in p.items() if k!='index.json'))
 def test_exact_prefix_empty_page_and_literal_bounds(self):
  d=json.loads(self.payloads()['index.json']);self.assertEqual(search(d,'0002')['total_matches'],1)
  self.assertEqual(search(d,'1',exact=False)['results'][0]['manager_cik'],'0000000010')
  self.assertEqual(search(d,'2',offset=20)['total_matches'],1);self.assertEqual(search(d,'2',offset=20)['results'],[])
  self.assertEqual(search(d,'999')['status'],'NO_MATCH_IN_RETAINED_BATCH_NOT_NO_HOLDINGS')
  for q in ('0','2.*','EMR','２','<script>','-1',' 2','12345678901'):
   with self.subTest(q=q),self.assertRaises(ValueError):search(d,q)
  for opts in ({'limit':True},{'limit':101},{'offset':-1},{'exact':1}):
   with self.assertRaises(ValueError):search(d,'2',**opts)
 def test_persistence_completion_and_refuse_overwrite(self):
  p=self.payloads()
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp)/'output';write(p,root);self.assertFalse((root/'INCOMPLETE').exists())
   self.assertEqual(json.loads((root/'COMPLETE.json').read_text())['index.json']['sha256'],digest(p['index.json']))
   self.assertEqual((root/'index.json').stat().st_mode&0o777,0o600)
   with self.assertRaises(FileExistsError):write(p,root)
   bad={'../escape.json':b'bad'};failed=Path(tmp)/'failed'
   with self.assertRaises(ValueError):write(bad,failed)
   self.assertTrue((failed/'INCOMPLETE').exists());self.assertFalse((failed/'COMPLETE.json').exists())
 def test_real_sqlite_pipeline_and_input_hash(self):
  with tempfile.TemporaryDirectory() as tmp:
   db=Path(tmp)/'source.sqlite';z=Path(tmp)/'source.zip';conn=sqlite3.connect(db)
   for table,rows in zip(('holdings_submission','holdings_coverpage','holdings_summarypage'),fixture()):
    cols=[k for k in rows[0] if k!='rowid'];conn.execute('CREATE TABLE '+table+' ('+','.join(k+' TEXT' for k in cols)+')');conn.executemany('INSERT INTO '+table+' VALUES ('+','.join('?' for _ in cols)+')',[[r[k] for k in cols] for r in rows])
   conn.commit();conn.close()
   with zipfile.ZipFile(z,'w') as f:f.writestr('fixture','synthetic')
   p=build(db,sha(db),z,sha(z));d=json.loads(p['index.json']);self.assertEqual(d['counts']['selected_managers'],2)
   with self.assertRaises(ValueError):build(db,'0'*64,z,sha(z))
 def test_size_cap(self):
  with patch('manager_filing_directory.MAX_SHARD',1):
   with self.assertRaises(ValueError):self.payloads()
  with patch('manager_filing_directory.MAX_DIRECTORY',1):
   with self.assertRaises(ValueError):self.payloads()
if __name__=='__main__':unittest.main()
