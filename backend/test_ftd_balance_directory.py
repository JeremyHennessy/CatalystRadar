import json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import ftd_balance_directory as d
from ftd_balance_series import project
from test_ftd_balance_series import rows

class FTDBalanceDirectoryTest(unittest.TestCase):
 def payloads(self,source=None):
  with patch.object(d,'audit',return_value=project(source or rows(),all_cusips=True)):return d.build('zip','db')
 def test_default_unchanged_and_sparse_all_reconstructs_sample(self):
  source=rows()+[['20261015',str(i).zfill(9),'SHARED','1','SOURCE','.'] for i in range(3,8)]
  sample=project(source);full=project(source,all_cusips=True)
  self.assertEqual(len(sample['series']),5);self.assertEqual(len(full['series']),7)
  for series in sample['series']:
   other=next(x for x in full['series'] if x['cusip_as_reported']==series['cusip_as_reported'])
   self.assertEqual([o for o in series['observations'] if o['status']=='REPORTED_BALANCE'],other['observations'])
  self.assertEqual(sum(len(s['observations']) for s in full['series']),len(source))
  with self.assertRaises(ValueError):project(source,all_cusips=1)
 def test_directory_shard_bijection_and_hashes(self):
  payloads=self.payloads();index=json.loads(payloads['index.json']);seen=[];total=0
  self.assertEqual(len(index['shards']),64)
  for bucket,meta in index['shards'].items():
   raw=payloads[meta['path']];self.assertEqual(d.digest(raw),meta['sha256']);self.assertEqual(len(raw),meta['bytes']);shard=json.loads(raw);self.assertEqual(shard['bucket'],bucket)
   for s in shard['series']:
    self.assertEqual(d.bucket(s['cusip_as_reported']),bucket);seen.append(s['cusip_as_reported']);total+=len(s['observations'])
    self.assertTrue(all(o['status']=='REPORTED_BALANCE' for o in s['observations']))
  self.assertEqual(sorted(seen),[e[0] for e in index['entries']]);self.assertEqual(total,index['counts']['source_rows'])
 def test_symbol_filter_not_identity_and_ambiguity_before_paging(self):
  source=rows();source[0][2]='A';index=json.loads(self.payloads(source)['index.json'])
  r=d.search(index,'A',field='symbol',limit=1);self.assertEqual(r['total_matching_cusips'],2);self.assertTrue(r['multiple_cusips_match']);self.assertEqual(r['next_offset'],1)
  r=d.search(index,'A',field='symbol',offset=20);self.assertEqual(r['results'],[]);self.assertEqual(r['total_matching_cusips'],2)
  self.assertEqual(d.search(index,'000000001')['total_matching_cusips'],1)
  self.assertEqual(d.search(index,'000',field='cusip_prefix')['total_matching_cusips'],2)
  self.assertEqual(d.search(index,'000000999')['status'],'NO_MATCH_IN_RETAINED_FILE_NOT_ZERO_BALANCE')
 def test_literal_query_validation(self):
  index=json.loads(self.payloads()['index.json'])
  for q in ('A.*','<script>','A OR 1=1'):
   self.assertEqual(d.search(index,q,field='symbol')['total_matching_cusips'],0)
  for q in ('',' ','A\x00','Ａ','A'*33):
   with self.assertRaises(ValueError):d.search(index,q,field='symbol')
  for opts in ({'limit':True},{'offset':-1},{'limit':101},{'field':'issuer'}):
   with self.assertRaises(ValueError):d.search(index,'000000001',**opts)
  for q in ('1','000*.*','0000000000'):
   with self.assertRaises(ValueError):d.search(index,q)
 def test_sizes_and_completed_persistence(self):
  p=self.payloads()
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp)/'out';d.save(p,root);self.assertFalse((root/'INCOMPLETE').exists());self.assertEqual(json.loads((root/'COMPLETE.json').read_bytes())['index.json']['sha256'],d.digest(p['index.json']))
   with self.assertRaises(ValueError):d.save(p,root)
   bad=Path(tmp)/'bad'
   with self.assertRaises(ValueError):d.save({'../unsafe':b'x'},bad)
   self.assertTrue((bad/'INCOMPLETE').exists());self.assertFalse((bad/'COMPLETE.json').exists())
  with patch.object(d,'MAX_INDEX',1):
   with self.assertRaises(ValueError):self.payloads()
  with patch.object(d,'MAX_SHARD',1):
   with self.assertRaises(ValueError):self.payloads()
if __name__=='__main__':unittest.main()
