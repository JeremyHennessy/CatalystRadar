import unittest,tempfile,json,base64,hashlib,os
from pathlib import Path
from unittest.mock import patch
from contextlib import ExitStack
from datetime import datetime,timezone
import scenario_receipt_dispatch as d
class TestDispatch(unittest.TestCase):
 def setUp(self):
  self.t=tempfile.TemporaryDirectory();self.root=Path(self.t.name);p=self.root/'data/scenarios';p.mkdir(parents=True)
  self.plan={'plan_sha256':'a'*64,'entry_session':'2026-11-16'};self.raw=json.dumps(self.plan).encode();(p/('a'*64+'.json')).write_bytes(self.raw)
  self.runs=0;self.receipt={'verified':True,'plan_sha256':'a'*64};self.stack=ExitStack()
  self.stack.enter_context(patch.object(d,'gate',return_value=(self.root,'b'*40)));self.stack.enter_context(patch.object(d,'privacy'))
  self.stack.enter_context(patch.object(d.subprocess,'check_output',return_value='c'*40))
  self.stack.enter_context(patch.dict(os.environ,{'EXPECTED_RECEIPT_WORKFLOW_BLOB_SHA':'d'*40}))
  self.api=self.stack.enter_context(patch.object(d,'api',side_effect=self.fetch));self.send=self.stack.enter_context(patch.object(d,'dispatch_once'))
  self.stack.enter_context(patch.object(d,'verify',return_value=self.receipt));self.stack.enter_context(patch.object(d,'time'))
  dt=self.stack.enter_context(patch.object(d,'datetime',wraps=datetime));dt.now.return_value=datetime(2026,11,14,21,tzinfo=timezone.utc)
 def tearDown(self):self.stack.close();self.t.cleanup()
 def fetch(self,path):
  if '/git/ref/' in path:return {'object':{'sha':'c'*40}}
  if '/contents/.github' in path:return {'sha':'d'*40}
  if '/contents/data' in path:return {'encoding':'base64','content':base64.b64encode(self.raw).decode(),'sha':hashlib.sha1(b'blob '+str(len(self.raw)).encode()+b'\0'+self.raw).hexdigest()}
  if '/runs?' in path:
   self.runs+=1;return {'total_count':0 if self.runs==1 else 1,'workflow_runs':[] if self.runs==1 else [{'id':7,'head_sha':'c'*40,'event':'workflow_dispatch','run_attempt':1}]}
  raise AssertionError('unexpected endpoint')
 def test_exactly_one_dispatch(self):
  r=d.record_receipt();self.assertTrue(r['trusted_receipt_obtained']);self.send.assert_called_once();self.assertEqual(len(list((self.root/'data/scenario-receipts').glob('*.json'))),1)
 def test_existing_attempt_no_dispatch(self):
  self.runs=1;self.assertRaises(ValueError,d.record_receipt);self.send.assert_not_called()
 def test_timeout_not_retried(self):
  self.send.side_effect=TimeoutError();self.assertRaises(TimeoutError,d.record_receipt);self.send.assert_called_once()
 def test_wrong_main_no_dispatch(self):
  original=self.fetch;self.api.side_effect=lambda p:{'object':{'sha':'e'*40}} if '/git/ref/' in p else original(p)
  self.assertRaises(ValueError,d.record_receipt);self.send.assert_not_called()
 def test_receipt_verification_fails_no_file(self):
  with patch.object(d,'verify',side_effect=ValueError('late')):self.assertRaises(ValueError,d.record_receipt)
  self.assertFalse((self.root/'data/scenario-receipts').exists());self.send.assert_called_once()

 def test_malformed_history_never_dispatch(self):
  original=self.fetch
  for response in ({'workflow_runs':None},{'workflow_runs':{}},{'workflow_runs':[],'total_count':1},{'workflow_runs':[]}):
   self.api.side_effect=lambda p:response if '/runs?' in p else original(p)
   self.assertRaises(ValueError,d.record_receipt)
  self.send.assert_not_called()
 def test_deadline_after_prechecks_no_dispatch(self):
  with patch.object(d,'datetime',wraps=datetime) as dt:
   dt.now.side_effect=[datetime(2026,11,16,12,59,tzinfo=timezone.utc),datetime(2026,11,16,13,1,tzinfo=timezone.utc)]
   self.assertRaises(ValueError,d.record_receipt)
  self.send.assert_not_called()
 def test_main_advanced_dispatch_has_no_matching_receipt(self):
  original=self.fetch
  def fetch(p):
   result=original(p)
   if '/runs?' in p and result['workflow_runs']:result['workflow_runs'][0]['head_sha']='e'*40
   return result
  self.api.side_effect=fetch;self.assertRaises(ValueError,d.record_receipt);self.send.assert_called_once()
  self.assertFalse((self.root/'data/scenario-receipts').exists())
