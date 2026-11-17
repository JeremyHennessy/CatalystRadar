import hashlib
import json
from pathlib import Path
import unittest
from unittest.mock import patch
from datetime import datetime, timezone
import test_filing_feature_rows
import record_feature_extraction as capture


class CaptureTests(unittest.TestCase):
    def setUp(self):
        self.fixture=test_filing_feature_rows.FeatureTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.dest=self.fixture.root/'private-captures'
        self.start=datetime(2026,11,17,12,0,tzinfo=timezone.utc)
        self.end=datetime(2026,11,17,12,0,1,tzinfo=timezone.utc)

    def record(self):
        with patch.object(capture,'clock',side_effect=[self.start,self.end]):
            return capture.record(self.fixture.reviews,self.fixture.archive,self.dest)

    def test_exact_bytes_actual_completion_clock_no_activation(self):
        run,receipt=self.record()
        self.assertEqual((run/'sources/manifest.jsonl').read_bytes(),(self.fixture.archive/'manifest.jsonl').read_bytes())
        features=json.loads((run/'features.json').read_bytes())
        self.assertEqual(features['computed_at'],self.end.isoformat())
        self.assertEqual(features['rows'][0]['features'][0]['computed_utc'],self.end.isoformat())
        self.assertEqual(features['rows'][0]['features'][0]['sources'][0]['observed_utc'],'2026-11-14T10:00:00Z')
        self.assertEqual(receipt['features_sha256'],hashlib.sha256((run/'features.json').read_bytes()).hexdigest())
        self.assertFalse(receipt['trusted_clock_verified']);self.assertFalse(receipt['trade_eligible'])
        self.assertIsNone(features['rows'][0]['decision_utc'])
        self.assertEqual((run/'complete.json').stat().st_mode & 0o777,0o600)
        self.assertEqual(run.stat().st_mode & 0o777,0o700)

    def test_no_overwrite(self):
        run,_=self.record();before=(run/'complete.json').read_bytes()
        with self.assertRaises(FileExistsError):self.record()
        self.assertEqual(before,(run/'complete.json').read_bytes())

    def test_changed_source_and_future_receipt_refused(self):
        source=next(self.fixture.archive.glob('*.txt'));source.write_bytes(b'changed')
        with self.assertRaises(ValueError):self.record()
        self.assertFalse(self.dest.exists())

    def test_future_observation_refused(self):
        self.start=datetime(2026,11,13,tzinfo=timezone.utc)
        with self.assertRaises(ValueError):self.record()

    def test_clock_rollback_leaves_no_complete_marker(self):
        self.end=datetime(2026,11,16,tzinfo=timezone.utc)
        with self.assertRaises(ValueError):self.record()
        self.assertEqual(list(self.dest.glob('*/complete.json')),[])

    def test_public_output_and_symlink_forbidden(self):
        self.dest=capture.CODE_ROOT/'data/forbidden'
        with self.assertRaises(ValueError):self.record()
        self.dest=self.fixture.root/'link';self.dest.symlink_to(self.fixture.archive,target_is_directory=True)
        with self.assertRaises(ValueError):self.record()

    def test_size_bound_and_private_permissions(self):
        with patch.object(capture,'MAX_TOTAL_BYTES',0):
            with self.assertRaises(ValueError):self.record()
        self.dest.mkdir(mode=0o755)
        with self.assertRaises(ValueError):self.record()

    def test_extraction_failure_leaves_no_complete_marker(self):
        with patch.object(capture,'build',side_effect=ValueError('synthetic extraction failure')):
            with self.assertRaises(ValueError):self.record()
        self.assertEqual(list(self.dest.glob('*/complete.json')),[])

    def test_source_symlink_refused(self):
        source=next(self.fixture.archive.glob('*.txt'))
        external=self.fixture.root/'other.txt';external.write_bytes(source.read_bytes())
        source.unlink();source.symlink_to(external)
        with self.assertRaises(ValueError):self.record()
        self.assertFalse(self.dest.exists())
