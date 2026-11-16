"""Public snapshot updates must not regenerate held research artifacts."""
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import build_dashboard

ROOT=Path(__file__).resolve().parents[1]

class ObservationRefreshTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        (self.root/'data').mkdir();(self.root/'web').mkdir()
        for name in ('paper_ledger.json','filing_reviews.json','price_feed_status.json',
                     'latest_scan.json','scan_schedule.json','provenance.json',
                     'filing_comparisons.json','financial_admission_rehearsal.json','research_report.json'):
            shutil.copyfile(ROOT/'data'/name,self.root/'data'/name)
        for name in ('app-data.json','research_report.json'):
            shutil.copyfile(ROOT/'web'/name,self.root/'web'/name)
        self.before={str(p.relative_to(self.root)):p.read_bytes() for p in self.root.rglob('*.json')}
    def tearDown(self):self.temp.cleanup()
    def test_fresh_scan_updates_only_dashboard_without_building_research(self):
        scan=json.loads((self.root/'data/latest_scan.json').read_text())
        scan.update(finished_at='2026-11-16T13:06:53Z',schedule_status='MANUAL_RUN',github_event_name=None)
        (self.root/'data/latest_scan.json').write_text(json.dumps(scan))
        with patch.object(build_dashboard,'build_research_report',side_effect=AssertionError('held report called')):
            state=build_dashboard.build(self.root,preserve_research_report=True)
        self.assertEqual(state['feeds'][0]['as_of'],scan['finished_at'])
        self.assertTrue(state['activity'][0]['detail'].startswith('Manual SEC poll'))
        self.assertEqual(state['portfolio']['orders'],[])
        for name in ('data/research_report.json','web/research_report.json','data/paper_ledger.json'):
            self.assertEqual((self.root/name).read_bytes(),self.before[name])
    def test_scheduled_scan_is_not_relabelled_manual(self):
        scan=json.loads((self.root/'data/latest_scan.json').read_text())
        scan.update(finished_at='2026-11-16T13:47:53Z',schedule_status='GITHUB_RUN',github_event_name='schedule')
        (self.root/'data/latest_scan.json').write_text(json.dumps(scan))
        with patch.object(build_dashboard,'build_research_report',side_effect=AssertionError('held report called')):
            state=build_dashboard.build(self.root,preserve_research_report=True)
        self.assertTrue(state['activity'][0]['detail'].startswith('Schedule-triggered SEC poll'))
        for name in ('data/research_report.json','web/research_report.json'):
            self.assertEqual((self.root/name).read_bytes(),self.before[name])
    def test_mismatching_copies_fail_before_any_output(self):
        (self.root/'web/research_report.json').write_text('{}')
        with self.assertRaises(ValueError):build_dashboard.build(self.root,preserve_research_report=True)
        self.assertEqual((self.root/'web/app-data.json').read_bytes(),self.before['web/app-data.json'])
    def test_missing_report_fails_before_any_output(self):
        (self.root/'web/research_report.json').unlink()
        with self.assertRaises(FileNotFoundError):build_dashboard.build(self.root,preserve_research_report=True)
        self.assertEqual((self.root/'web/app-data.json').read_bytes(),self.before['web/app-data.json'])
    def test_matching_invalid_reports_fail(self):
        for content in ('not json','[]','null'):
            for name in ('data/research_report.json','web/research_report.json'):
                (self.root/name).write_text(content)
            with self.assertRaises(ValueError):build_dashboard.build(self.root,preserve_research_report=True)
        self.assertEqual((self.root/'web/app-data.json').read_bytes(),self.before['web/app-data.json'])
    def test_default_mode_remains_explicit_research_rebuild(self):
        report={'generated_at':'2026-11-16T13:00:00Z','test_only':True}
        with patch.object(build_dashboard,'build_research_report',return_value=report) as rebuild:
            build_dashboard.build(self.root)
        rebuild.assert_called_once()
        for name in ('data/research_report.json','web/research_report.json'):
            self.assertEqual(json.loads((self.root/name).read_text()),report)
    def test_scheduled_workflow_preserves_reports_and_scope(self):
        workflow=(ROOT/'.github/workflows/sec-observations.yml').read_text()
        self.assertIn('python3 backend/build_dashboard.py --preserve-research-report',workflow)
        stage=next(line for line in workflow.splitlines() if 'git add --' in line)
        self.assertNotIn('research_report',stage)
        self.assertIn("cron: '17,47 11-23 16-20 11 *'",workflow)
        self.assertNotIn('paper_ledger',stage)

if __name__=='__main__':unittest.main()
