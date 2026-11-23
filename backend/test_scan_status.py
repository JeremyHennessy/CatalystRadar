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

class DashboardSchedulePolicyTests(unittest.TestCase):
    def test_exact_workflow_identity_and_expiry(self):
        from pathlib import Path
        from build_dashboard import sec_schedule
        retired = (Path(__file__).resolve().parent.parent / '.github/workflows/sec-observations.yml').read_bytes()
        old_lines = b"  schedule:\n    - cron: '17,47 11-23 16-20 11 *'\n"
        if old_lines in retired:  # Allow running against the reviewed pre-retirement workflow too.
            retired = retired.replace(old_lines, b'', 1)
        original = retired.replace(b'on:\n', b'on:\n' + old_lines, 1)
        before, cutoff = '2026-11-20T23:59:59Z', '2026-11-21T00:00:00Z'
        self.assertEqual(sec_schedule(original, before), 'TRIAL_CONFIGURED')
        self.assertEqual(sec_schedule(original, cutoff), 'TRIAL_EXPIRED')
        self.assertEqual(sec_schedule(retired, before), 'UNVERIFIED')
        self.assertEqual(sec_schedule(retired, cutoff), 'SCHEDULE_RETIRED')
        for unknown in (None, retired + b'\n', b'workflow_dispatch:'):
            self.assertEqual(sec_schedule(unknown, cutoff), 'UNVERIFIED')

    def test_saved_projection_separates_schedule_from_receipt(self):
        import json
        from pathlib import Path
        root = Path(__file__).resolve().parent.parent
        state = json.loads((root / 'web/app-data.json').read_bytes())
        scan = json.loads((root / 'data/latest_scan.json').read_bytes())
        sec = state['feeds'][0]
        self.assertEqual(sec['schedule_state'], 'SCHEDULE_RETIRED')
        self.assertEqual(sec['as_of'], scan['finished_at'])
        self.assertNotIn('schedule configured', sec['detail'])
        self.assertTrue(any('not live health' in text for text in state['blockers']))
