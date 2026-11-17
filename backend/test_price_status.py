import unittest,tempfile,shutil,json
from pathlib import Path
from build_dashboard import build,ROOT
class TestPriceStatus(unittest.TestCase):
 def test_public_metadata_only(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);shutil.copytree(ROOT/'data',root/'data');(root/'web').mkdir()
   s=build(root);p=s['feeds'][1]
   self.assertEqual(p['status'],'snapshot_only');self.assertIn('11 private snapshots',p['detail']);self.assertIn('Execution remains disabled',p['detail'])
   self.assertEqual(s['portfolio']['cash'],500);self.assertEqual(s['portfolio']['trades'],[])
   self.assertEqual(s['discovery']['eligible_signals'],0)
   self.assertNotIn('No authorized reliable price feed connected',json.dumps(s))
   status=root/'data/price_feed_status.json';x=json.loads(status.read_text());x['raw_prices']=[123];status.write_text(json.dumps(x))
   self.assertRaises(ValueError,build,root)
