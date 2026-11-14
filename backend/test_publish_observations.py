import unittest
from unittest.mock import Mock
from publish_observations import publish

SHA='a'*40
PAYLOAD=b'{"paper_only":true}'
CONFIG={'build_type':'legacy','source':{'branch':'main','path':'/'}}
REF={'object':{'sha':SHA}}
BUILT={'commit':SHA,'status':'built','error':{'message':None}}

class PublishTests(unittest.TestCase):
    def run_publish(self, responses, fetch=None, attempts=2):
        api=Mock(side_effect=responses)
        result=publish(SHA,PAYLOAD,api,fetch or Mock(return_value=PAYLOAD),Mock(),attempts)
        return result,api
    def test_success_and_explicit_request(self):
        result,api=self.run_publish([CONFIG,REF,{'status':'queued'},BUILT])
        self.assertEqual(result,SHA)
        self.assertIn(unittest.mock.call('POST','/pages/builds'),api.call_args_list)
    def test_workflow_mode_rejected_without_mutation(self):
        api=Mock(return_value=dict(CONFIG,build_type='workflow'))
        with self.assertRaises(RuntimeError):publish(SHA,PAYLOAD,api,Mock())
        self.assertEqual(api.call_count,1)
    def test_wrong_source_rejected(self):
        with self.assertRaises(RuntimeError):self.run_publish([dict(CONFIG,source={'branch':'other','path':'/'})])
    def test_advanced_main_rejected(self):
        with self.assertRaises(RuntimeError):self.run_publish([CONFIG,{'object':{'sha':'b'*40}}])
    def test_old_build_not_accepted(self):
        old=dict(BUILT,commit='b'*40)
        with self.assertRaises(RuntimeError):self.run_publish([CONFIG,REF,{},old,old])
    def test_live_payload_must_match(self):
        with self.assertRaises(RuntimeError):self.run_publish([CONFIG,REF,{},BUILT,BUILT],Mock(return_value=b'stale'))
    def test_failed_build_rejected(self):
        with self.assertRaises(RuntimeError):self.run_publish([CONFIG,REF,{},dict(BUILT,status='errored')])
    def test_queued_then_success(self):
        self.assertEqual(self.run_publish([CONFIG,REF,{},dict(BUILT,status='building'),BUILT])[0],SHA)
    def test_api_failure_propagates(self):
        with self.assertRaises(PermissionError):self.run_publish([PermissionError('403')])
    def test_invalid_sha_no_api(self):
        api=Mock()
        with self.assertRaises(ValueError):publish('main',PAYLOAD,api,Mock())
        api.assert_not_called()

if __name__=='__main__':unittest.main()
