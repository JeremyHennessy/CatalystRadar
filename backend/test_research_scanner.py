import copy, hashlib, json, subprocess, sys, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
import research_scanner as m
ROOT=Path(__file__).resolve().parents[1]
class ResearchScannerTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.data={k:json.loads((ROOT/v['path']).read_bytes()) for k,v in m.PINS.items()};cls.result=m.build(ROOT)
 def test_actual_rebuild_and_scope(self):
  raw=m.encoded(self.result);self.assertEqual(raw,(ROOT/m.OUTPUT).read_bytes());self.assertLess(len(raw),m.MAX_BYTES)
  self.assertEqual(self.result['counts']['evidence_records'],905);self.assertEqual(self.result['counts']['distinct_associated_issuer_ciks'],117)
  self.assertEqual(self.result['counts']['by_state'],{'ORIGINAL_REVIEW_REQUIRED':897,'SOURCE_REVIEWED_WITH_LIMITS':8})
  self.assertEqual(len(self.result['coverage']['existing_dossier_ciks']),108)
 def test_every_source_reference_and_exact_object_hash(self):
  refs=[]
  for r in self.result['records']:
   a=r['source_ref'];refs.append((a['key'],a['json_pointer']));obj=m.pointer(self.data[a['key']],a['json_pointer'])
   self.assertEqual(a['object_sha256'],m.digest(obj));self.assertFalse(r['training_ready']);self.assertFalse(r['execution_ready']);self.assertIsNone(r['first_public_utc'])
  self.assertEqual(len(refs),len(set(refs)))
 def test_exact_financial_insider_disclosure_memberships(self):
  q=self.data['queue']['records']
  expected_fin={x for e in q for x in e['financial_case_ids']};expected_ins={x for e in q for x in e['insider_filing_refs']};expected_disc={x for e in q for x in e['disclosure_accessions']}
  actual={'FINANCIAL_CONTEXT':set(),'INSIDER_FILING':set(),'ACQUISITION_DISPOSAL_DISCLOSURE':set()}
  for r in self.result['records']:
   if r['category'] not in actual:continue
   s=r['source_ref'];o=m.pointer(self.data[s['key']],s['json_pointer']);ci=r['issuer_associations'][0]['issuer_cik'];self.assertEqual(ci,o['issuer_cik'])
   actual[r['category']].add(o['id'] if r['category']=='FINANCIAL_CONTEXT' else o['batch_id']+':'+o['accession'] if r['category']=='INSIDER_FILING' else o['accession'])
  self.assertEqual(actual['FINANCIAL_CONTEXT'],expected_fin);self.assertEqual(actual['INSIDER_FILING'],expected_ins);self.assertEqual(actual['ACQUISITION_DISPOSAL_DISCLOSURE'],expected_disc)
 def test_duplicate_source_identity_rejected(self):
  d=copy.deepcopy(self.data);d['financial']['records'].append(d['financial']['records'][0])
  with self.assertRaises(ValueError):m.project(d)
 def test_wrong_cik_reference_rejected(self):
  d=copy.deepcopy(self.data);d['financial']['records'][0]['issuer_cik']='0000000001'
  with self.assertRaises(ValueError):m.project(d)
 def test_duplicate_queue_reference_rejected(self):
  d=copy.deepcopy(self.data);e=next(e for e in d['queue']['records'] if e['financial_case_ids']);e['financial_case_ids'].append(e['financial_case_ids'][0])
  with self.assertRaises(ValueError):m.project(d)
 def test_changed_pinned_source_rejected(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);meta=m.PINS['queue'];p=root/meta['path'];p.parent.mkdir(parents=True);p.write_bytes((ROOT/meta['path']).read_bytes()+b' ')
   with self.assertRaises(ValueError):m.build(root)
 def test_input_identity_and_unicode_controls(self):
  for ci in ['0','0000000000','１２３４５６７８９０','../123']:
   with self.assertRaises(ValueError):m.assoc(ci,['Name'])
  for name in ['bad\u200bname','bad\x00name','']:
   with self.assertRaises(ValueError):m.assoc('0000000001',[name])
  self.assertEqual(m.assoc('0000000001',['<script>literal</script>'])['names_as_reported'],['<script>literal</script>'])
 def test_xerox_distinct_entities_and_keycorp_limits(self):
  rows={r['category']:r for r in self.result['records'] if r['category'] in ('FILER_IDENTITY','REPORTED_EXCHANGE','SECURITY_CONTEXT')}
  for k in ('FILER_IDENTITY','REPORTED_EXCHANGE'):
   self.assertEqual({a['issuer_cik'] for a in rows[k]['issuer_associations']},{'0001770450','0000108772'})
  self.assertIn('not a verified historical identity', ' '.join(rows['SECURITY_CONTEXT']['unknowns']))
  self.assertEqual(rows['SECURITY_CONTEXT']['investigation_path'],'datasets.html#ftd-directory')
 def test_existing_routes_do_not_claim_record_selection(self):
  for r in self.result['records']:
   self.assertEqual(r['navigation_status'],'EXISTING_PAGE_OR_SECTION_NOT_AUTOMATIC_RECORD_SELECTION')
   self.assertNotIn('://',r['investigation_path']);self.assertNotIn('..',r['investigation_path'])
   if r['category']=='INSIDER_FILING':self.assertEqual(r['investigation_path'],'financial-review.html#research-queue')
 def test_revenue_no_arithmetic_and_separate_cohort(self):
  rs=[r for r in self.result['records'] if r['category']=='REVENUE_CANDIDATE'];self.assertEqual(len(rs),5)
  for r in rs:self.assertEqual(r['dossier_ciks'],[]);self.assertIn('No absolute or percentage change',r['summary'])
 def test_every_detail_shard_exact_public_objects_and_membership(self):
  index,payloads=m.build_package(ROOT);seen=set();records={r['id']:r for r in index['records']}
  self.assertEqual(len(payloads),65)
  for bucket,meta in index['detail_shards'].items():
   raw=payloads[meta['path']];self.assertEqual(raw,(ROOT/meta['path']).read_bytes());self.assertEqual(len(raw),meta['bytes']);self.assertEqual(hashlib.sha256(raw).hexdigest(),meta['sha256']);self.assertLess(len(raw),300000)
   shard=json.loads(raw);self.assertEqual(shard['bucket'],bucket);self.assertEqual([r['id'] for r in shard['records']],meta['record_ids'])
   for r in shard['records']:
    self.assertNotIn(r['id'],seen);seen.add(r['id']);self.assertEqual(records[r['id']]['detail_bucket'],bucket);self.assertEqual(records[r['id']]['source_ref'],r['source_ref'])
    ref=r['source_ref'];self.assertEqual(r['source_record'],m.pointer(self.data[ref['key']],ref['json_pointer']));self.assertEqual(m.digest(r['source_record']),ref['object_sha256'])
  self.assertEqual(seen,set(records))
 def test_changed_screen_census_rejected(self):
  d=copy.deepcopy(self.data);d['votes']['packages'][0]['reviewed_plan']=None
  with self.assertRaises(ValueError):m.project(d)
 def test_clock_fields_are_meaningful_not_hash_spans(self):
  for r in self.result['records']:
   for c in r['clocks']:
    self.assertNotIn('span',c['meaning']);self.assertTrue(isinstance(c['value_as_reported'],str) or (c['meaning']=='source_exact_period' and set(c['value_as_reported'])=={'start','end'}))
 def test_cli_exact_output(self):
  p=subprocess.run([sys.executable,str(ROOT/'backend/research_scanner.py'),'--root',str(ROOT)],capture_output=True,timeout=30)
  self.assertEqual(p.returncode,0);self.assertEqual(p.stdout,m.encoded(self.result));self.assertEqual(p.stderr,b'')
if __name__=='__main__':unittest.main()
