import unittest,tempfile,os,json
from pathlib import Path
from unittest.mock import patch
import private_scenario as s
class TestPrivateScenario(unittest.TestCase):
 def test_no_context_no_privacy_call(self):
  with patch.dict(os.environ,{},clear=True),patch.object(s,'privacy') as api:self.assertRaises(ValueError,s.gate);api.assert_not_called()
 def test_destination_guard(self):
  with tempfile.TemporaryDirectory() as d,patch.dict(os.environ,{'GITHUB_REPOSITORY':'JeremyHennessy/CatalystRadar-Private','GITHUB_ACTIONS':'true','GITHUB_RUN_ATTEMPT':'1','GITHUB_WORKSPACE':d,'EXPECTED_PUBLIC_CODE_SHA':'a'*40},clear=True),patch.object(s,'privacy') as api:
   self.assertRaises(ValueError,s.gate);api.assert_not_called()
 def test_private_append_only(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);(root/'data/prices').mkdir(parents=True)
   plan={'records':[{'symbol':'SYNTHETIC','state':'SELECTED'}],'plan_sha256':'old'}
   with patch.object(s,'gate',return_value=(root,'a'*40)),patch.object(s,'privacy') as api,patch.object(s,'freeze',return_value=plan):
    r=s.prepare();files=list((root/'data/scenarios').glob('*.json'));self.assertEqual(len(files),1)
    data=json.loads(files[0].read_text());self.assertEqual(data['reviewed_public_code_sha'],'a'*40);self.assertFalse(r['trusted_receipt_obtained']);api.assert_called_once()
    self.assertRaises(ValueError,s.prepare)
 def test_recheck_failure_zero_plan(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);(root/'data/prices').mkdir(parents=True)
   with patch.object(s,'gate',return_value=(root,'a'*40)),patch.object(s,'privacy',side_effect=ValueError('access changed')),patch.object(s,'freeze',return_value={'records':[],'plan_sha256':'old'}):
    self.assertRaises(ValueError,s.prepare);self.assertEqual(list((root/'data/scenarios').glob('*.json')),[])
 def test_wrong_or_dirty_pin_rejected(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);file=root/'.collector/backend/private_scenario.py';file.parent.mkdir(parents=True);file.touch()
   env={'GITHUB_REPOSITORY':'JeremyHennessy/CatalystRadar-Private','GITHUB_ACTIONS':'true','GITHUB_RUN_ATTEMPT':'1','GITHUB_WORKSPACE':d,'EXPECTED_PUBLIC_CODE_SHA':'a'*40}
   for outputs in (['b'*40],['a'*40,' M backend/private_scenario.py']):
    with patch.dict(os.environ,env,clear=True),patch.object(s,'__file__',str(file)),patch.object(s.subprocess,'check_output',side_effect=outputs),patch.object(s,'privacy') as api:
     self.assertRaises(ValueError,s.gate);api.assert_not_called()
 def test_good_context_verifies_privacy(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);file=root/'.collector/backend/private_scenario.py';file.parent.mkdir(parents=True);file.touch()
   env={'GITHUB_REPOSITORY':'JeremyHennessy/CatalystRadar-Private','GITHUB_ACTIONS':'true','GITHUB_RUN_ATTEMPT':'1','GITHUB_WORKSPACE':d,'EXPECTED_PUBLIC_CODE_SHA':'a'*40}
   with patch.dict(os.environ,env,clear=True),patch.object(s,'__file__',str(file)),patch.object(s.subprocess,'check_output',side_effect=['a'*40,'']),patch.object(s,'privacy') as api:
    self.assertEqual(s.gate(),(root,'a'*40));api.assert_called_once()
