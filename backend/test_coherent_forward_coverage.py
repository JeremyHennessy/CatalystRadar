import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import coherent_forward_coverage as case

ROOT = Path(__file__).resolve().parents[1]


class CoherentForwardTests(unittest.TestCase):
    def test_cutoff_is_after_scheduled_close_and_crosses_weekend(self):
        self.assertEqual(case.candidate_dates(case.CUTOFF_UTC), ["2026-11-20", "2026-11-23"])
        self.assertEqual(case.candidate_dates("2026-11-19T20:59:59Z"), ["2026-11-19", "2026-11-20"])
        self.assertEqual(case.candidate_dates("2026-11-19T21:00:00Z"), ["2026-11-20", "2026-11-23"])

    def test_unsourced_original_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            original = Path(tmp) / "fabricated"
            original.write_bytes(b"0000820318 COHR")
            with self.assertRaisesRegex(ValueError, "input pin/bound"):
                case.build(ROOT, original)

    def test_exact_receipts_retain_unknown_first_public(self):
        first = case._event(ROOT, "20261119T114159492631Z.json", case.PUSH_SHA)
        repeat = case._event(ROOT, "20261119T193148867794Z.json", case.REPEAT_SHA)
        self.assertEqual(first["source_metadata_sha256"], repeat["source_metadata_sha256"])
        self.assertIsNone(first["first_public_utc"])
        self.assertLess(first["observed_utc"], repeat["observed_utc"])

    def test_exclusion_uses_audited_bound_not_matching_ticker_assumption(self):
        raw = b"0000820318 0001193125-26-467737 Common Stock, no par value >COHR< >New York Stock Exchange<"
        actual = case.read

        def mock_original(path, pin, size):
            if path == "synthetic-original":
                return raw.ljust(case.ORIGINAL_SIZE, b" ")
            return actual(path, pin, size)

        with patch.object(case, "read", mock_original):
            out = case.build(ROOT, "synthetic-original")
        self.assertEqual(out["candidate_dates_beyond_all_audited_series"], ["2026-11-20", "2026-11-23"])
        self.assertEqual(out["provider_security_join"], "UNVERIFIED")
        self.assertIsNone(out["return"])
        self.assertFalse(out["qualified_outcome"])
        self.assertFalse(out["execution_ready"])
