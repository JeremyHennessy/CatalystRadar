import unittest
from scan_status import summarize_scan

class ScanStatusTests(unittest.TestCase):
    def scan(self, **changes):
        value = dict(schedule_status="GITHUB_RUN", github_event_name="schedule", configured_issuers=10,
                     successful_issuers=10, metadata_window_complete=True, errors=[])
        value.update(changes)
        return value
    def test_schedule_is_not_manual_or_punctuality_proof(self):
        result = summarize_scan(self.scan())
        self.assertIn("Schedule-triggered", result["activity"])
        self.assertNotIn("Manual", result["activity"])
        self.assertIn("punctuality", result["schedule_note"])
        self.assertNotIn("has run on schedule", result["schedule_note"])
    def test_failed_scheduled_run_not_success(self):
        result = summarize_scan(self.scan(successful_issuers=0, metadata_window_complete=False, errors=[{}]))
        self.assertIn("coverage is not verified", result["schedule_note"])
        self.assertNotIn("reported complete issuer", result["schedule_note"])
    def test_partial_scheduled_run_not_success(self):
        self.assertIn("coverage is not verified", summarize_scan(self.scan(successful_issuers=9))["schedule_note"])
    def test_false_complete_flag_or_errors_prevents_success(self):
        for changes in ({"metadata_window_complete":False}, {"errors":[{}]}, {"errors":None}):
            self.assertIn("coverage is not verified", summarize_scan(self.scan(**changes))["schedule_note"])
    def test_counts_require_integers_and_valid_range(self):
        for changes in ({"configured_issuers":True}, {"successful_issuers":10.0}, {"configured_issuers":0},
                        {"successful_issuers":11}, {"successful_issuers":-1}):
            self.assertIn("coverage is not verified", summarize_scan(self.scan(**changes))["schedule_note"])
    def test_local_manual_does_not_verify_schedule(self):
        result = summarize_scan(self.scan(schedule_status="MANUAL_RUN", github_event_name=None))
        self.assertTrue(result["activity"].startswith("Manual SEC"))
        self.assertIn("not yet verified", result["schedule_note"])
    def test_dispatch_not_schedule(self):
        result = summarize_scan(self.scan(github_event_name="workflow_dispatch"))
        self.assertIn("Manually dispatched", result["activity"])
        self.assertIn("not yet verified", result["schedule_note"])
    def test_inconsistent_context_not_schedule(self):
        self.assertIn("not yet verified", summarize_scan(self.scan(schedule_status="MANUAL_RUN"))["schedule_note"])
    def test_missing_report(self):
        self.assertIn("not yet verified", summarize_scan(None)["schedule_note"])
    def test_other_event_not_claimed_manual(self):
        self.assertIn("Other GitHub", summarize_scan(self.scan(github_event_name="repository_dispatch"))["activity"])

if __name__ == "__main__": unittest.main()

class DashboardStatusIntegrationTests(unittest.TestCase):
    def test_builder_uses_failed_scheduled_status_without_writing_reports(self):
        import json
        from pathlib import Path
        from unittest.mock import patch
        from build_dashboard import build
        original_read = Path.read_text
        def read(path, *args, **kwargs):
            text = original_read(path, *args, **kwargs)
            if path.name == 'latest_scan.json':
                scan = json.loads(text)
                scan.update(schedule_status='GITHUB_RUN', github_event_name='schedule',
                            successful_issuers=0, metadata_window_complete=False, errors=[{}])
                return json.dumps(scan)
            return text
        with patch.object(Path, 'read_text', read), patch.object(Path, 'write_text'):
            state = build()
        self.assertIn('Schedule-triggered', state['activity'][0]['detail'])
        self.assertTrue(any('complete issuer coverage is not verified' in x for x in state['blockers']))
        self.assertFalse(any('has run on schedule' in x for x in state['blockers']))

class FallbackLabelTests(unittest.TestCase):
    def test_push_is_fallback_not_scheduled(self):
        result = summarize_scan(dict(schedule_status='GITHUB_RUN', github_event_name='push', configured_issuers=10, successful_issuers=10, metadata_window_complete=True, errors=[]))
        self.assertTrue(result['activity'].startswith('Request-triggered fallback SEC poll'))
        self.assertIn('not yet verified', result['schedule_note'])
