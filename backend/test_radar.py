import unittest,tempfile,hashlib,copy
from pathlib import Path
from radar import classify,run,growth_at_least
class Tests(unittest.TestCase):
 def setUp(self):
  self.d=tempfile.TemporaryDirectory();self.root=self.d.name
  Path(self.root,'synthetic.txt').write_text('SYNTHETIC TEST ONLY')
  self.e={'event_id':'synthetic-1','ticker':'TEST','event_type':'EARNINGS','observed_utc':'2026-11-14T16:00:00Z','review_complete_utc':'2026-11-14T16:30:00Z','market_data_asof_session':'2026-11-13','session_calendar_verified':True,'first_public_utc':'2026-11-13T21:00:00Z','source_verified_primary':True,'timestamp_verified':True,'extraction_verified':True,'sources':[{'path':'synthetic.txt','sha256':hashlib.sha256(b'SYNTHETIC TEST ONLY').hexdigest(),'retrieved_utc':'2026-11-14T16:00:00Z'}],'same_event_deduplicated':True,'amendment_unresolved':False,'security_type':'COMMON_STOCK','exchange':'NYSE','previous_close':100,'adv20_usd':20000000,'market_data_observed_utc':'2026-11-14T16:00:00Z','market_data_verified':True,'halt_status_verified':True,'halted':False,'corporate_action_unresolved':False,'facts':{'comparable_periods':True,'total_gaap_diluted_eps_basis':True,'same_share_basis':True,'gaap_revenue':120,'prior_gaap_revenue':100,'gaap_eps':1,'prior_gaap_eps':.85}}
  self.cut='2026-11-14T17:00:00Z'
 def tearDown(self): self.d.cleanup()
 def test_signal(self):self.assertEqual(classify(self.e,self.cut,self.root,'2026-11-13')['signals'],['EARNINGS_GROWTH'])
 def test_future(self):self.assertEqual(classify(self.e,'2026-11-14T15:00:00Z',self.root,'2026-11-13')['status'],'BLOCKED')
 def test_stale(self):self.assertEqual(classify(self.e,'2026-11-19T17:00:00Z',self.root,'2026-11-13')['status'],'BLOCKED')
 def test_hash(self):self.e['sources'][0]['sha256']='bad';self.assertEqual(classify(self.e,self.cut,self.root,'2026-11-13')['status'],'BLOCKED')
 def test_negative_eps(self):self.e['facts']['gaap_eps']=-1;self.assertEqual(classify(self.e,self.cut,self.root,'2026-11-13')['status'],'NO_SIGNAL')
 def test_halt(self):self.e['halted']=True;self.assertEqual(classify(self.e,self.cut,self.root,'2026-11-13')['status'],'BLOCKED')
 def test_unknown_halt(self):self.e['halt_status_verified']=False;self.assertEqual(classify(self.e,self.cut,self.root,'2026-11-13')['status'],'BLOCKED')
 def test_duplicate(self):self.assertRaises(ValueError,run,[self.e,self.e],self.cut,self.root,'2026-11-13')
 def test_guidance_basis(self):self.e['facts']={'guidance_same_basis_horizon':False,'prior_guidance_midpoint':100,'new_guidance_midpoint':200};self.assertEqual(classify(self.e,self.cut,self.root,'2026-11-13')['status'],'NO_SIGNAL')
 def test_contract_options(self):self.e['event_type']='CONTRACT';self.e['facts']={'binding':True,'firm_minimum_not_options':False,'firm_minimum_value':100,'annual_revenue':100};self.assertEqual(classify(self.e,self.cut,self.root,'2026-11-13')['status'],'NO_SIGNAL')
 def test_truthy_false(self):self.e['facts']['comparable_periods']='false';self.assertEqual(classify(self.e,self.cut,self.root,'2026-11-13')['status'],'NO_SIGNAL')
 def test_nan(self):self.e['previous_close']=float('nan');self.assertEqual(classify(self.e,self.cut,self.root,'2026-11-13')['status'],'BLOCKED')
 def test_stale_session(self):self.e['market_data_asof_session']='2020-01-01';self.assertEqual(classify(self.e,self.cut,self.root,'2026-11-13')['status'],'BLOCKED')
 def test_review_before_source(self):self.e['sources'][0]['retrieved_utc']='2026-11-14T16:59:00Z';self.assertEqual(classify(self.e,self.cut,self.root,'2026-11-13')['status'],'BLOCKED')
 def test_knowledge(self):self.assertEqual(classify(self.e,self.cut,self.root,'2026-11-13')['knowledge_utc'],'2026-11-14T16:30:00+00:00')
 def test_market_evidence_after_review(self):self.e['market_data_observed_utc']='2026-11-14T16:59:00Z';self.assertEqual(classify(self.e,self.cut,self.root,'2026-11-13')['status'],'BLOCKED')
 def test_zero_prior_eps(self):self.e['facts']['prior_gaap_eps']=0;self.assertEqual(classify(self.e,self.cut,self.root,'2026-11-13')['status'],'NO_SIGNAL')
 def test_financing_not_contract(self):self.e['event_type']='CONTRACT';self.e['facts']={'customer_revenue_contract':False,'issuer_is_seller':False,'financing_or_recapitalization':True,'binding':True,'firm_minimum_not_options':True,'firm_minimum_value':100,'annual_revenue':100};self.assertEqual(classify(self.e,self.cut,self.root,'2026-11-13')['status'],'NO_SIGNAL')
 def test_preferred_not_buyback(self):self.e['event_type']='BUYBACK';self.e['facts']={'common_stock_authorization':False,'incremental_authorization':True,'new_authorization_value':100,'pre_event_market_cap':100};self.assertEqual(classify(self.e,self.cut,self.root,'2026-11-13')['status'],'NO_SIGNAL')
 def test_exact_growth_boundary(self):self.assertTrue(growth_at_least(.22,.20,.10))
 def test_no_fills(self):self.assertNotIn('fills',classify(self.e,self.cut,self.root,'2026-11-13'))
if __name__=='__main__':unittest.main()
