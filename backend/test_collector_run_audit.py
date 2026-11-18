import copy
import json
from pathlib import Path
import tempfile
import shutil
import unittest
from collector_run_audit import build, INPUT

class AuditTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(); self.root=Path(self.temp.name)
        original=Path(__file__).resolve().parent.parent
        for path in [INPUT]+[str(p.relative_to(original)) for p in (original/'data/sec-observations').glob('*.json')]:
            target=self.root/path; target.parent.mkdir(parents=True,exist_ok=True); shutil.copyfile(original/path,target)
    def tearDown(self): self.temp.cleanup()
    def mutate(self,fn):
        p=self.root/INPUT; d=json.loads(p.read_text()); fn(d); p.write_text(json.dumps(d))
    def test_latest_skip_not_success(self):
        result=build(self.root); row=result['collectors'][0]['latest_workflow_execution']
        self.assertEqual(row['job_conclusion'],'success'); self.assertEqual(row['source_response'],'NOT_REQUESTED'); self.assertEqual(row['publication'],'SKIPPED'); self.assertIsNone(row['source_observed_at']); self.assertFalse(result['collection_enabled'])
    def test_historical_green_denial(self):
        row=build(self.root)['collectors'][0]['runs'][-1]
        self.assertEqual(row['job_conclusion'],'success'); self.assertEqual(row['source_response'],'SOURCE_DENIED_403'); self.assertEqual(row['successful_issuers'],0); self.assertEqual(row['persistence'],'RECEIPT_PERSISTED')
    def test_private_and_unlinked(self):
        d=build(self.root); rows=d['collectors'][1]['runs']; self.assertEqual(len(rows),3); self.assertEqual(rows[0]['saved_snapshots'],11); self.assertEqual(rows[1]['source_response'],'UNVERIFIED_PER_RUN'); self.assertEqual(d['unlinked_sec_receipt_count'],3)
    def test_incomplete_history_rejected(self):
        self.mutate(lambda d:d['public_history'].update(total_count=7))
        with self.assertRaises(ValueError): build(self.root)
    def test_skip_contradiction_rejected(self):
        self.mutate(lambda d:d['public_history']['runs'][0].update(receipt_path='data/latest_scan.json'))
        with self.assertRaises(ValueError): build(self.root)
    def test_duplicate_rejected(self):
        self.mutate(lambda d:d['public_history']['runs'][1].update(run_id=44223484988))
        with self.assertRaises(ValueError): build(self.root)
    def test_mismatched_receipt_rejected(self):
        self.mutate(lambda d:d['public_history']['runs'][1].update(receipt_path=d['public_history']['runs'][2]['receipt_path']))
        with self.assertRaises(ValueError): build(self.root)
    def test_reproducible(self): self.assertEqual(build(self.root),build(self.root))

    def test_saved_projection_matches(self):
        original=Path(__file__).resolve().parent.parent
        self.assertEqual(build(original),json.loads((original/'web/collector-run-audit.json').read_text()))
    def test_private_stages_contradiction(self):
        self.mutate(lambda d:d['private_history']['runs'][0]['job']['steps'][3].update(conclusion='skipped'))
        with self.assertRaises(ValueError): build(self.root)
    def test_private_listing_incomplete(self):
        self.mutate(lambda d:d['private_history'].update(listed_count=4))
        with self.assertRaises(ValueError): build(self.root)
    def test_unlinked_receipt_mismatch(self):
        self.mutate(lambda d:d['unlinked_sec_receipts'].append(d['public_history']['runs'][1]['receipt_path']))
        with self.assertRaises(ValueError): build(self.root)
    def test_public_order_does_not_change_latest(self):
        self.mutate(lambda d:d['public_history']['runs'].reverse())
        self.assertEqual(build(self.root)['collectors'][0]['latest_workflow_execution']['run_id'],44223484988)
    def test_private_order_does_not_change_latest(self):
        self.mutate(lambda d:d['private_history']['runs'].reverse())
        self.assertEqual(build(self.root)['collectors'][1]['latest_workflow_execution']['run_id'],44172913902)
    def test_strict_public_fields(self):
        mutations=[lambda d:d['private_history']['latest_receipt'].update(saved_snapshots='private@example.test'),
            lambda d:d['private_history']['latest_receipt'].update(blob='secret'),
            lambda d:d['private_history']['latest_receipt'].update(sessions_per_snapshot=True),
            lambda d:d['public_history']['runs'][0].update(created_at='2027-01-01T00:00:00Z'),
            lambda d:d['public_history']['runs'][0].update(created_at='2026-11-18T03:20:00Z'),
            lambda d:d['public_history']['runs'][0]['job'].update(conclusion='private@example.test'),
            lambda d:d['public_history']['runs'][0]['job'].update(id='secret')]
        for fn in mutations:
            with self.subTest(fn=fn):
                original=(self.root/INPUT).read_bytes();self.mutate(fn)
                with self.assertRaises(ValueError):build(self.root)
                (self.root/INPUT).write_bytes(original)
    def test_duplicate_steps_rejected(self):
        self.mutate(lambda d:d['public_history']['runs'][0]['job']['steps'].append(d['public_history']['runs'][0]['job']['steps'][0]))
        with self.assertRaises(ValueError):build(self.root)
    def test_contradictory_complete_not_promoted(self):
        audit=json.loads((self.root/INPUT).read_text());p=self.root/audit['public_history']['runs'][1]['receipt_path'];d=json.loads(p.read_text())
        d['sources'][0].update(validation_status='FETCH_FAILED',error='HTTP 403 from public source');p.write_text(json.dumps(d))
        row=build(self.root)['collectors'][0]['runs'][1]
        self.assertEqual(row['source_response'],'SOURCE_DENIED_403')
    def test_input_bound(self):
        (self.root/INPUT).write_text(' '*200001)
        with self.assertRaises(ValueError):build(self.root)
