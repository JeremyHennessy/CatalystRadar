import copy,hashlib,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import training_evidence_inventory as m

def row():
 return {'event_id':'synthetic-event','eligible':False,'financial_extraction_verified':False,'decision_utc':None,'outcome':None,'first_public_utc':None,'features':[{'name':'synthetic-fixture'}]}
class TrainingInventoryTests(unittest.TestCase):
 def fixture(self,root):
  def save(path,obj):
   p=root/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(obj));return p
  save(m.FEATURES,{'rows':[row()]});save(m.FROZEN,{'mode':'REAL_ARCHIVE_READINESS_NOT_FORECAST','generated_at':'2026-01-01T00:00:00Z','counts':{'reviewed_records':1,'qualified_observations':0,'outcomes_available':0},'candidate_rehearsal':{'counts':{'metadata_candidates':0}}});save(m.LEDGER,{'orders':[],'fills':[],'positions':[],'simulation_enabled':False})
  report={'run_id':'synthetic-run','started_at':'2026-01-02T00:00:00Z','finished_at':'2026-01-02T00:00:00Z','sources':[]};save(m.LATEST,report);save('data/sec-observations/synthetic.json',report)
 def test_zero_only_with_missing_pairs(self):
  self.assertEqual(m.assess_features({'rows':[row()]})['qualified_example_count'],0)
  r=row();r.update(decision_utc='not-yet-validated',outcome={'unverified':True},eligible=True)
  s=m.assess_features({'rows':[r]});self.assertIsNone(s['qualified_example_count']);self.assertFalse(s['qualification_verified']);self.assertFalse(s['model_training_performed']);self.assertIsNone(s['predictive_metrics'])
 def test_missing_schema_not_zero(self):
  for doc in [{},{'rows':None},{'rows':{}},{'rows':[row(),row()]}]:
   with self.assertRaises(ValueError):m.assess_features(doc)
  for key in ['eligible','outcome','decision_utc','first_public_utc','features','financial_extraction_verified']:
   r=row();r.pop(key)
   with self.assertRaises(ValueError):m.assess_features({'rows':[r]})
 def test_inventory_readonly_and_deterministic(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);self.fixture(root);before={str(p.relative_to(root)):p.read_bytes() for p in root.rglob('*') if p.is_file()};a=m.build_inventory(root);b=m.build_inventory(root);self.assertEqual(a,b)
   self.assertEqual(before,{str(p.relative_to(root)):p.read_bytes() for p in root.rglob('*') if p.is_file()});self.assertEqual(a['metadata']['retained_scan_receipts'],1);self.assertEqual(a['feature_evidence']['qualified_example_count'],0);self.assertTrue(all(s['status']=='MISSING' and s['table_rows'] is None for s in a['prepared_sources']))
   for p,h in a['input_sha256'].items():self.assertEqual(h,hashlib.sha256((root/p).read_bytes()).hexdigest())
 def test_duplicate_keys_and_missing_ledger(self):
  for mode in ['duplicate','ledger','latest']:
   with tempfile.TemporaryDirectory() as td:
    root=Path(td);self.fixture(root)
    if mode=='duplicate':(root/m.FEATURES).write_text('{"rows":[],"rows":[]}')
    elif mode=='ledger':(root/m.LEDGER).write_text('{"simulation_enabled":false,"orders":[],"positions":[]}')
    else:(root/m.LATEST).write_text('{"run_id":"another","sources":[]}')
    with self.assertRaises(ValueError):m.build_inventory(root)
 def test_concurrent_input_change_rejected(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);self.fixture(root);original=m.normalize
   def mutate(reports,base):
    answer=original(reports,base);(root/m.FEATURES).write_text('{"rows":[]}');return answer
   with patch.object(m,'normalize',mutate),self.assertRaises(ValueError):m.build_inventory(root)
 def test_strict_snapshot_decode_before_normalizing(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);self.fixture(root);raw=b'{"cik":1,"cik":2}';sha=hashlib.sha256(raw).hexdigest();rel='data/sec-snapshots/'+sha+'.json';p=root/rel;p.parent.mkdir();p.write_bytes(raw)
   for path in [m.LATEST,'data/sec-observations/synthetic.json']:
    r=json.loads((root/path).read_text());r['sources']=[{'archive_path':rel,'sha256':sha}];(root/path).write_text(json.dumps(r))
   with self.assertRaises(ValueError):m.build_inventory(root)

 def test_nonstandard_json_constants_rejected(self):
  for constant in ['NaN','Infinity','-Infinity']:
   with self.subTest(constant=constant),tempfile.TemporaryDirectory() as td:
    root=Path(td);self.fixture(root);p=root/m.FEATURES;p.write_text(p.read_text()[:-1]+',"unused":'+constant+'}')
    with self.assertRaisesRegex(ValueError,'nonstandard JSON'):m.build_inventory(root)
