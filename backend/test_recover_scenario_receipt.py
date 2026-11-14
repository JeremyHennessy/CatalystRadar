import unittest,tempfile,os
from pathlib import Path
from unittest.mock import patch
import recover_scenario_receipt as r
class TestRecover(unittest.TestCase):
 def test_existing_only_and_private(self):
  with tempfile.TemporaryDirectory()as d,patch.object(r,'gate',return_value=(Path(d),'a'*40)),patch.object(r,'privacy'),patch.dict(os.environ,{'EXISTING_RECEIPT_RUN_ID':'43632065122','FROZEN_PLAN_COMMIT':'b'*40,'FROZEN_PLAN_SHA256':'c'*64,'EXPECTED_RECEIPT_WORKFLOW_BLOB_SHA':'d'*40}),patch.object(r,'verify',return_value={'verified':True,'plan_sha256':'c'*64})as verify:
   result=r.recover();self.assertEqual(result['new_dispatches'],0);self.assertEqual(verify.call_args.kwargs['run_id'],43632065122);self.assertEqual(len(list((Path(d)/'data/scenario-receipts').glob('*.json'))),1)
 def test_verification_failure_no_write(self):
  with tempfile.TemporaryDirectory()as d,patch.object(r,'gate',return_value=(Path(d),'a'*40)),patch.object(r,'privacy'),patch.dict(os.environ,{'EXISTING_RECEIPT_RUN_ID':'43632065122','FROZEN_PLAN_COMMIT':'b'*40,'FROZEN_PLAN_SHA256':'c'*64,'EXPECTED_RECEIPT_WORKFLOW_BLOB_SHA':'d'*40}),patch.object(r,'verify',side_effect=ValueError('invalid')):
   self.assertRaises(ValueError,r.recover);self.assertEqual(list(Path(d).iterdir()),[])
