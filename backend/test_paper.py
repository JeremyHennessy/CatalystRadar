import unittest,json,tempfile,hashlib
from pathlib import Path
from datetime import datetime
from unittest.mock import patch
import paper
from paper import plan,settle_entry,plan_exit,settle_exit
class TestPaper(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
  self.patches=[patch.object(paper,'APPROVED_PROVIDERS',{'SYNTHETIC':'https://fixture.invalid/'}),patch.object(paper,'EVIDENCE_ROOT',self.root),patch.object(paper,'clock',return_value=datetime.fromisoformat('2026-11-16T13:00:00+00:00'))]
  for p in self.patches:p.start()
  self.l={'simulation_enabled':True,'cash':10000,'orders':[],'positions':[],'fills':[]}
  self.prior=self.save('prior.json','2026-11-13',100,'2026-11-13T21:10:00Z')
  self.e={'status':'OBSERVE','coverage_complete':True,'price_entitlement_verified':True,'halt_status_verified':True,'auction_data_verified':True,'corporate_actions_verified':True,'eligibility_review_passed':True,'evidence_hashes':['a'*64],'knowledge_utc':'2026-11-16T12:00:00Z','halted':False,'ticker':'SYNTHETIC','event_id':'SYNTHETIC_ONLY','prior_close':100,'prior_session':'2026-11-13','expected_prior_session':'2026-11-13','prior_evidence':self.prior}
 def tearDown(self):
  for p in reversed(self.patches):p.stop()
  self.temp.cleanup()
 def save(self,name,session,price,observed,**fields):
  q={'provider_id':'SYNTHETIC','source_url':'https://fixture.invalid/quote','ticker':'SYNTHETIC','session':session,'close':price,'observed_utc':observed,'official_auction_verified':True,'halt_status_verified':True,'corporate_actions_verified':True,'no_corporate_action_since_entry':True,'halted':False,'auction_occurred':True,**fields}
  raw=json.dumps(q).encode();(self.root/name).write_bytes(raw);return {'provider_id':'SYNTHETIC','source_sha256':hashlib.sha256(raw).hexdigest(),'source_path':name}
 def p(self):return plan(self.l,self.e,'2026-11-16T13:00:00Z','2026-11-16')
 def settle(self,l,price=100,**fields):
  q=self.save('entry.json','2026-11-16',price,'2026-11-16T21:10:00Z',**fields)
  with patch.object(paper,'clock',return_value=datetime.fromisoformat('2026-11-16T21:11:00+00:00')):return settle_entry(l,l['orders'][0]['id'],q)
 def test_disabled(self):self.l['simulation_enabled']=False;self.assertRaises(ValueError,self.p)
 def test_registry_lock(self):
  with patch.object(paper,'APPROVED_PROVIDERS',{}):self.assertRaises(ValueError,self.p)
 def test_reserved(self):self.assertEqual(self.p()['orders'][0]['quantity'],4)
 def test_future_knowledge(self):self.e['knowledge_utc']='2026-11-16T14:00:00Z';self.assertRaises(ValueError,self.p)
 def test_fake_clock(self):self.assertRaises(ValueError,plan,self.l,self.e,'2026-11-16T12:59:00Z','2026-11-16')
 def test_window(self):self.assertRaises(ValueError,plan,self.l,self.e,'2026-11-20T13:00:00Z','2026-11-20')
 def test_no_gate(self):self.e['price_entitlement_verified']=False;self.assertRaises(ValueError,self.p)
 def test_fill(self):r=self.settle(self.p());self.assertEqual(r['cash'],9599.6);self.assertEqual(len(r['fills']),1)
 def test_gap(self):r=self.settle(self.p(),110);self.assertEqual(r['cash'],10000);self.assertEqual(r['fills'],[])
 def test_no_price(self):r=self.settle(self.p(),official_auction_verified=False);self.assertEqual(r['orders'][0]['status'],'PENDING_PRICE')
 def test_wrong_ticker(self):self.assertRaises(ValueError,self.settle,self.p(),ticker='WRONG')
 def test_bad_hash(self):self.e['prior_evidence']['source_sha256']='not-a-hash';self.assertRaises(ValueError,self.p)
 def test_corrupted_evidence(self):(self.root/'prior.json').write_text('{}');self.assertRaises(ValueError,self.p)
 def test_source_ledger_disabled(self):r=json.loads((Path(__file__).parent.parent/'data/paper_ledger.json').read_text());self.assertFalse(r['simulation_enabled']);self.assertEqual(r['fills'],[])
 def test_exit(self):
  l=self.settle(self.p())
  with patch.object(paper,'clock',return_value=datetime.fromisoformat('2026-11-20T13:00:00+00:00')):l=plan_exit(l,'SYNTHETIC','2026-11-20T13:00:00Z')
  q=self.save('exit.json','2026-11-20',100,'2026-11-20T21:10:00Z')
  with patch.object(paper,'clock',return_value=datetime.fromisoformat('2026-11-20T21:11:00+00:00')):r=settle_exit(l,'SYNTHETIC',q)
  self.assertEqual(r['positions'],[]);self.assertEqual(r['cash'],9999.2)
if __name__=='__main__':unittest.main()
