import unittest,tempfile
from datetime import datetime
from unittest.mock import patch
from decimal import Decimal
import proxy_runner as p
class TestRunner(unittest.TestCase):
 def setUp(self):
  self.now=datetime.fromisoformat('2026-11-16T12:59:00+00:00')
  self.adapters={'calendar':lambda s:{'session':s,'regular_session':True,'previous_session':'2026-11-13','close_utc':s+'T21:00:00Z'},'candidate':lambda r:{'event_id':r,'issuer_id':r,'symbol':r,'knowledge_utc':'2026-11-16T12:00:00Z','review_passed':True,'source_hashes':['a'*64],'source_observed_utc':['2026-11-16T11:00:00Z'],'reviewed_utc':'2026-11-16T11:30:00Z'},'close':self.close,'interval':self.interval,'committed_freeze':self.receipt}
  self.patches=[patch.object(p,'clock',side_effect=lambda:self.now),patch.object(p,'ADAPTERS',self.adapters)]
  for x in self.patches:x.start()
 def tearDown(self):
  for x in self.patches:x.stop()
 def receipt(self,oid,h,session):return {'verified':True,'order_id':oid,'freeze_hash':h,'repository':'JeremyHennessy/CatalystRadar-Private','receipt_basis':'TRUSTED_SERVER_RECEIPT','receipt_sha256':'b'*64,'server_received_utc':session+'T12:59:30Z'}
 def close(self,s,d):return {'symbol':s,'session':d,'close':'20','observed_utc':d+'T21:10:00Z','source_sha256':'a'*64}
 def interval(self,s,a,b):return {'symbol':s,'start':a,'end':b,'complete':True,'actions':[],'ordinary_close':True,'observed_utc':b+'T21:15:00Z'}
 def frozen(self):return p.freeze(p.initial(),'2026-11-16',['TEST'])
 def settle(self,s):
  self.now=datetime.fromisoformat('2026-11-17T12:00:00+00:00');return p.settle(s,s['orders'][0]['id'])
 def test_disabled(self):
  with patch.object(p,'ADAPTERS',{}):self.assertRaises(ValueError,self.frozen)
 def test_late(self):
  self.now=datetime.fromisoformat('2026-11-16T13:01:00+00:00');self.assertRaises(ValueError,self.frozen)
 def test_freeze_idempotency(self):self.assertRaises(ValueError,p.freeze,self.frozen(),'2026-11-16',['TEST'])
 def test_zero_candidates(self):self.assertEqual(p.freeze(p.initial(),'2026-11-16')['orders'],[])
 def test_global_cash(self):
  s=p.freeze(p.initial(),'2026-11-16',[str(i) for i in range(9)])
  self.assertEqual(len(s['orders']),5);self.assertEqual(len(s['decisions'][0]['candidates']),9)
  self.assertLessEqual(sum(Decimal(o['reserved']) for o in s['orders']),500)
 def test_round_trip_cost(self):
  s=self.settle(self.frozen());self.assertEqual(s['cash'],'419.7198000')
  self.now=datetime.fromisoformat('2026-11-20T12:59:00+00:00');s=p.freeze(s,'2026-11-20')
  self.now=datetime.fromisoformat('2026-11-21T12:00:00+00:00');s=p.settle(s,s['orders'][-1]['id'])
  self.assertEqual(s['positions'],[]);self.assertEqual(Decimal(s['cash']),Decimal('499.4400000'))
 def test_double_settlement(self):
  s=self.settle(self.frozen());self.assertRaises(ValueError,p.settle,s,s['orders'][0]['id'])
 def test_tampered_order(self):
  s=self.frozen();s['orders'][0]['quantity']=1;self.assertRaises(ValueError,self.settle,s)
 def test_wrong_symbol(self):
  self.adapters['close']=lambda s,d:{**self.close(s,d),'symbol':'WRONG'};self.assertRaises(ValueError,self.frozen)
 def test_missing_commit(self):
  s=self.frozen();self.adapters['committed_freeze']=lambda *a:(_ for _ in ()).throw(ValueError('no commit'));self.assertRaises(ValueError,self.settle,s)
 def test_actions_hold_not_delete(self):
  s=self.frozen();self.adapters['interval']=lambda s,a,b:{**self.interval(s,a,b),'actions':['split']}
  s=self.settle(s);self.assertEqual(s['orders'][0]['state'],'PENDING');self.assertEqual(len(s['decisions'][0]['candidates']),1);self.assertEqual(s['cash'],'500')
 def test_halt_unfilled(self):
  s=self.frozen();self.adapters['interval']=lambda s,a,b:{**self.interval(s,a,b),'ordinary_close':False}
  s=self.settle(s);self.assertEqual(s['orders'][0]['state'],'UNFILLED');self.assertEqual(s['fills'],[])
 def test_append(self):
  with tempfile.TemporaryDirectory() as d:
   kw={'verified_repository':{'full_name':'JeremyHennessy/CatalystRadar-Private','visibility':'private'}}
   a=p.transaction(d,lambda s:p.freeze(s,'2026-11-16'),**kw)
   b=p.transaction(d,lambda s:s,**kw)
   self.assertEqual(b['previous_hash'],p.digest(a));self.assertEqual(b['sequence'],2)

 def test_false_receipt(self):
  for value in (False,None,{}, {'verified':True}):
   self.now=datetime.fromisoformat('2026-11-16T12:59:00+00:00');s=self.frozen()
   self.adapters['committed_freeze']=lambda *a:value
   self.assertRaises(ValueError,self.settle,s)
 def test_late_receipt(self):
  s=self.frozen();self.adapters['committed_freeze']=lambda *a:{**self.receipt(*a),'server_received_utc':'2026-11-16T13:01:00Z'}
  self.assertRaises(ValueError,self.settle,s)
 def test_no_source_hashes(self):
  original=self.adapters['candidate'];self.adapters['candidate']=lambda r:{**original(r),'source_hashes':[]}
  self.assertRaises(ValueError,self.frozen)
 def test_source_after_review(self):
  original=self.adapters['candidate'];self.adapters['candidate']=lambda r:{**original(r),'source_observed_utc':['2026-11-16T11:31:00Z']}
  self.assertRaises(ValueError,self.frozen)
 def test_no_issuer_retry_after_unfilled(self):
  s=self.frozen();self.adapters['interval']=lambda s,a,b:{**self.interval(s,a,b),'ordinary_close':False};s=self.settle(s)
  self.now=datetime.fromisoformat('2026-11-17T12:59:00+00:00');original=self.adapters['candidate']
  self.adapters['candidate']=lambda r:{**original(r),'issuer_id':'TEST'}
  s=p.freeze(s,'2026-11-17',['SECOND_EVENT']);self.assertEqual(len(s['orders']),1)
  self.assertEqual(s['decisions'][-1]['candidates'][0]['reason'],'duplicate event or issuer')

 def test_adapter_crosses_deadline(self):
  original=self.adapters['candidate']
  def late(r):
   self.now=datetime.fromisoformat('2026-11-16T13:01:00+00:00');return original(r)
  self.adapters['candidate']=late;self.assertRaises(ValueError,self.frozen)
 def test_persistence_crosses_deadline(self):
  with tempfile.TemporaryDirectory() as d:
   def op(s):
    r=p.freeze(s,'2026-11-16');self.now=datetime.fromisoformat('2026-11-16T13:01:00+00:00');return r
   self.assertRaises(ValueError,p.transaction,d,op,verified_repository={'full_name':'JeremyHennessy/CatalystRadar-Private','visibility':'private'})

 def test_unknown_close_pending_with_evidence(self):
  s=self.frozen();self.adapters['interval']=lambda s,a,b:{**self.interval(s,a,b),'ordinary_close':None}
  s=self.settle(s);o=s['orders'][0]
  self.assertEqual(o['state'],'PENDING');self.assertIn('interval_evidence',o);self.assertIn('commit_receipt',o)

 def test_limit_rejection_retains_price(self):
  s=self.frozen();self.adapters['close']=lambda symbol,day:{**self.close(symbol,day),'close':'25'}
  s=self.settle(s);o=s['orders'][0]
  self.assertEqual(o['state'],'UNFILLED');self.assertEqual(o['close_evidence']['close'],'25');self.assertIn('commit_receipt',o)
