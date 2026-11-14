import unittest
from datetime import datetime
from unittest.mock import patch
import mechanical_scenario as m
class TestScenario(unittest.TestCase):
 def setUp(self):
  self.now=datetime.fromisoformat('2026-11-14T19:00:00+00:00');self.p=patch.object(m,'clock',side_effect=lambda:self.now);self.p.start()
 def tearDown(self):self.p.stop()
 def q(self,s,d):return {'symbol':s,'session':d,'close':'20','observed_utc':d+'T21:10:00Z','source_sha256':'a'*64,'vintage_policy':'FIRST_OBSERVED'}
 def plan(self):return m.freeze(self.q)
 def receipt(self,p):return {'verified':True,'plan_sha256':p['plan_sha256'],'receipt_basis':'TRUSTED_SERVER_RECEIPT','server_received_utc':'2026-11-14T19:00:00Z','repository':'JeremyHennessy/CatalystRadar-Private','receipt_sha256':'b'*64}
 def test_fixed_selection(self):
  p=self.plan();self.assertEqual([r['symbol'] for r in p['records'] if r['state']=='SELECTED'],list(m.UNIVERSE[:5]));self.assertEqual(len(p['records']),10)
 def test_future_values_absent(self):
  p=self.plan();r=m.evaluate(p,self.q,receipt=self.receipt(p));self.assertEqual(r['records'][0]['status'],'AWAITING_FUTURE_ENTRY_DATA');self.assertIsNone(r['predictive_performance'])
 def test_no_receipt(self):self.assertRaises(ValueError,m.evaluate,self.plan(),self.q,receipt=False)
 def test_late_freeze(self):self.now=datetime.fromisoformat('2026-11-16T13:01:00+00:00');self.assertRaises(ValueError,self.plan)
 def test_changed_selection_rejected(self):
  p=self.plan();p['records'][0]['quantity']=999;self.assertRaises(ValueError,m.evaluate,p,self.q,receipt=self.receipt(p))
 def test_losses_retained_and_actions_suppressed(self):
  p=self.plan();self.now=datetime.fromisoformat('2026-11-21T12:00:00+00:00')
  def quotes(s,d):return {**self.q(s,d),'close':'18' if d==m.EXIT else '20'}
  r=m.evaluate(p,quotes,receipt=self.receipt(p),known_actions=('COHR',))
  self.assertLess(m.Decimal(r['records'][0]['hypothetical_cash_change']),0);self.assertEqual(r['records'][1]['status'],'SUPPRESSED_KNOWN_ACTION_INCOMPARABLE');self.assertEqual(len(r['records']),10)

 def test_late_receipt(self):
  p=self.plan();r={**self.receipt(p),'server_received_utc':'2026-11-16T13:01:00Z'};self.assertRaises(ValueError,m.evaluate,p,self.q,receipt=r)
 def test_missing_no_substitute(self):
  p=self.plan();self.now=datetime.fromisoformat('2026-11-21T12:00:00+00:00')
  def missing(s,d):
   if s=='CINF':raise ValueError('absent')
   return self.q(s,d)
  r=m.evaluate(p,missing,receipt=self.receipt(p));self.assertEqual(r['records'][0]['status'],'ENTRY_SOURCE_UNAVAILABLE');self.assertEqual(r['records'][5]['status'],'NOT_SELECTED')
 def test_unaffordable_skip_and_no_fractions(self):
  p=m.freeze(lambda s,d:{**self.q(s,d),'close':'200' if s=='CINF' else '20'})
  self.assertEqual(p['records'][0]['reason'],'WHOLE_SHARE_UNAFFORDABLE');self.assertEqual(sum(x['state']=='SELECTED' for x in p['records']),5)
 def test_prior_revision_does_not_resize(self):
  import copy
  p=self.plan();before=copy.deepcopy(p);self.now=datetime.fromisoformat('2026-11-21T12:00:00+00:00')
  m.evaluate(p,lambda s,d:{**self.q(s,d),'close':'25'},receipt=self.receipt(p));self.assertEqual(p,before)

 def test_future_receipt_rejected(self):
  p=self.plan();r={**self.receipt(p),'server_received_utc':'2026-11-14T19:01:00Z'};self.assertRaises(ValueError,m.evaluate,p,self.q,receipt=r)
 def test_changed_protocol_rejected(self):
  p=self.plan();p['protocol']['fee']='0';p['plan_sha256']=m.digest({k:v for k,v in p.items() if k!='plan_sha256'});self.assertRaises(ValueError,m.evaluate,p,self.q,receipt=self.receipt(p))
 def test_append_revisions_not_overwrite(self):
  import tempfile
  from pathlib import Path
  p=self.plan();r=m.evaluate(p,self.q,receipt=self.receipt(p))
  with tempfile.TemporaryDirectory() as d:
   a=m.append_evaluation(d,r);self.assertEqual(a,m.append_evaluation(d,r))
   r['evaluated_at']='2026-11-14T19:02:00Z';b=m.append_evaluation(d,r)
   self.assertNotEqual(a,b);self.assertEqual(len(list(Path(d).glob('*.json'))),2)
