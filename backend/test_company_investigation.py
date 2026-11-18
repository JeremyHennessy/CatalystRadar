import copy,hashlib,json,tempfile,unittest
from pathlib import Path
import company_investigation as m
ROOT=Path(__file__).resolve().parents[1]
class CompanyInvestigationTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.data={k:json.loads((ROOT/v['path']).read_bytes()) for k,v in m.PINS.items()};cls.index,cls.payloads=m.build(ROOT)
 def test_exact_complete_public_rebuild(self):
  self.assertEqual(len(self.payloads),129)
  for path,raw in self.payloads.items():self.assertEqual(raw,(ROOT/path).read_bytes())
  self.assertEqual(self.index['counts']['company_ciks'],8035);self.assertEqual(self.index['counts']['prepared_ciks'],8034);self.assertEqual(self.index['counts']['scanner_company_associations'],907)
  self.assertLess(len(self.payloads[m.BASE+'index.json']),m.LIMITS['index_bytes']);self.assertLess(sum(map(len,self.payloads.values())),m.LIMITS['package_bytes'])
 def test_every_company_directory_and_all_source_objects_exact(self):
  directory={r['issuer_cik']:r for r in self.index['directory']};seen=set();source_counts={'prepared':0,'insider':0,'disclosure':0,'scanner':0}
  def pointer(obj,path):
   for part in path.strip('/').split('/'):
    obj=obj[int(part)] if isinstance(obj,list) else obj[part]
   return obj
  for meta in self.index['detail_shards']:
   raw=self.payloads[meta['path']];self.assertEqual(len(raw),meta['bytes']);self.assertEqual(hashlib.sha256(raw).hexdigest(),meta['sha256']);shard=json.loads(raw)
   self.assertEqual([r['issuer_cik'] for r in shard['companies']],meta['issuer_ciks']);self.assertEqual(shard['bucket'],meta['bucket'])
   for company in shard['companies']:
    ci=company['issuer_cik'];self.assertNotIn(ci,seen);seen.add(ci);self.assertEqual(directory[ci]['detail_bucket'],meta['bucket']);names=set()
    for family in source_counts:
     section=company[family];rows=([section['record']] if section['record'] else []) if family=='insider' else section['records']
     source_counts[family]+=len(rows)
     for r in rows:
      ref=r['source_ref'];original=pointer(self.data[ref['key']],ref['json_pointer']);self.assertEqual(original,r['source_record']);self.assertEqual(m.digest(original),ref['object_sha256'])
      if family=='prepared':
       self.assertEqual(original['cik'],ci)
       for s in original['sources']:names.update(s['names'])
      elif family=='insider':self.assertEqual(original['issuer_cik'],ci);names.update(original['issuer_names_as_filed'])
      elif family=='disclosure':self.assertEqual(original['issuer_cik'],ci);names.add(original['issuer_name_as_filed'])
      else:
       matches=[a for a in original['issuer_associations'] if a['issuer_cik']==ci];self.assertEqual(len(matches),1);names.update(matches[0]['names_as_reported'])
    self.assertEqual(sorted(names),directory[ci]['names_as_reported']);self.assertFalse(company['training_ready']);self.assertFalse(company['execution_ready']);self.assertIsNone(company['first_public_utc'])
  self.assertEqual(seen,set(directory));self.assertEqual(source_counts,{'prepared':7912+5065,'insider':3809,'disclosure':466,'scanner':907})
 def test_xerox_source_only_and_no_identity_merge(self):
  entries={r['issuer_cik']:r for r in self.index['directory']}
  self.assertIn('0000108772',entries);self.assertIn('0001770450',entries)
  meta=next(m for m in self.index['detail_shards'] if '0000108772' in m['issuer_ciks']);d=next(r for r in json.loads(self.payloads[meta['path']])['companies'] if r['issuer_cik']=='0000108772')
  self.assertEqual(d['prepared'],{'status':'NO_ENTRY_IN_FIXED_PREPARED_INDEX','records':[]});self.assertIsNone(d['insider']['record']);self.assertEqual(len(d['scanner']['records']),2)
  for r in d['scanner']['records']:self.assertEqual({a['issuer_cik'] for a in r['source_record']['issuer_associations']},{'0000108772','0001770450'})
 def test_duplicate_prepared_and_source_batch_rejected(self):
  for change in ('row','batch'):
   d=copy.deepcopy(self.data)
   if change=='row':d['prepared'][1]=copy.deepcopy(d['prepared'][0])
   else:d['prepared'][0]['sources'].append(copy.deepcopy(d['prepared'][0]['sources'][0]))
   with self.assertRaises(ValueError):m.project(d)
 def test_invalid_identity_not_quietly_dropped(self):
  for ci in ('0000000000','１２３４５６７８９０','../1750'):
   d=copy.deepcopy(self.data);d['prepared'][0]['cik']=ci
   with self.assertRaises(ValueError):m.project(d)
 def test_wrong_insider_cik_or_shard_rejected(self):
  d=copy.deepcopy(self.data);d['insider']['issuers'][0]['issuer_cik']='0000108772'
  with self.assertRaises(ValueError):m.project(d)
  d=copy.deepcopy(self.data);d['insider']['issuers'][0]['shard']='00'
  with self.assertRaises(ValueError):m.project(d)
 def test_unexpected_union_or_quarantine_rejected(self):
  d=copy.deepcopy(self.data);r=next(r for r in d['scanner']['records'] if any(a['issuer_cik']=='0000108772' for a in r['issuer_associations']));next(a for a in r['issuer_associations'] if a['issuer_cik']=='0000108772')['issuer_cik']='9999999999'
  with self.assertRaises(ValueError):m.project(d)
  d=copy.deepcopy(self.data);d['insider']['quarantine']=[{'unassessable':True}]
  with self.assertRaises(ValueError):m.project(d)
 def test_conservation_and_duplicate_disclosure_reference(self):
  d=copy.deepcopy(self.data);d['prepared'][0]['sources'][0]['submissions']+=1
  with self.assertRaises(ValueError):m.project(d)
  d=copy.deepcopy(self.data);d['disclosure'][1]['accession']=d['disclosure'][0]['accession']
  with self.assertRaises(ValueError):m.project(d)
 def test_changed_input_hash_fails_before_output(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/m.PINS['prepared']['path'];p.parent.mkdir(parents=True);p.write_bytes((ROOT/m.PINS['prepared']['path']).read_bytes()+b' ')
   with self.assertRaises(ValueError):m.build(td)
 def test_source_name_strings_inert_not_identity_resolution(self):
  self.assertEqual(m.labels(['<script>literal</script>']),['<script>literal</script>'])
  for xs in (['a','a'],['bad\x00name'],['bad\u200bname']):
   with self.assertRaises(ValueError):m.labels(xs)
if __name__=='__main__':unittest.main()
