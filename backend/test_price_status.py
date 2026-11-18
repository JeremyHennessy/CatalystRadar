import unittest,tempfile,shutil,json
from pathlib import Path
from build_dashboard import build,ROOT
class TestPriceStatus(unittest.TestCase):
 def test_public_metadata_only(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);shutil.copytree(ROOT/'data',root/'data');(root/'web').mkdir()
   s=build(root);p=s['feeds'][1]
   self.assertEqual(p['status'],'snapshot_only');self.assertIn('11 stored snapshots',p['detail']);self.assertIn('Execution remains disabled',p['detail'])
   self.assertIn('current storage and redistribution eligibility',s['blockers'][0])
   self.assertNotIn('Private daily histories are stored',s['blockers'][0])
   self.assertEqual(s['portfolio']['cash'],500);self.assertEqual(s['portfolio']['trades'],[])
   self.assertEqual(s['discovery']['eligible_signals'],0)
   self.assertNotIn('No authorized reliable price feed connected',json.dumps(s))
   status=root/'data/price_feed_status.json';x=json.loads(status.read_text());x['raw_prices']=[123];status.write_text(json.dumps(x))
   self.assertRaises(ValueError,build,root)

 def test_historical_receipt_not_current_privacy(self):
  from price_status import summarize_price_status
  import copy
  p=json.loads((ROOT/'data/price_feed_status.json').read_text());before=copy.deepcopy(p)
  result=summarize_price_status(p)
  self.assertEqual(p,before)
  self.assertEqual(result['as_of'],p['latest_collection']['observed_at'])
  self.assertIn('historical receipts do not establish current storage privacy',result['detail'])
  self.assertIn('permission to redistribute prices',result['detail'])
  self.assertNotIn('private snapshots',result['detail'])
  self.assertNotIn('Initial private',result['detail'])
  del p['latest_collection'];p['scheduled_collection_verified']=False
  initial=summarize_price_status(p)
  self.assertEqual(initial['as_of'],p['verified_at'])
  self.assertIn('Scheduled collection not yet verified',initial['detail'])
  self.assertIn('current storage privacy',initial['detail'])
