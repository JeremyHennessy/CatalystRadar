import copy
import unittest
from price_status import summarize_price_status


class PriceStatusTests(unittest.TestCase):
    def setUp(self):
        self.status = {'status': 'private_daily_snapshot_tested', 'verified_at': '2026-11-14T18:48:41+00:00', 'symbols_tested': 11, 'rows_per_symbol': 100, 'first_session': '2026-06-25', 'last_session': '2026-11-13', 'execution_ready': False, 'scheduled_collection_verified': True, 'latest_collection': {'observed_at': '2026-11-16T21:58:11+00:00', 'saved_snapshots': 11, 'rows_per_symbol': 100, 'scheduled_run_verified': True}}

    def test_scheduled_receipt_does_not_claim_price_freshness(self):
        out = summarize_price_status(self.status)
        self.assertEqual(out['as_of'], self.status['latest_collection']['observed_at'])
        self.assertIn('Latest covered session not independently verified', out['detail'])
        self.assertIn('Execution remains disabled', out['detail'])
        self.assertIn('2026-11-13', out['detail'])

    def test_legacy_snapshot(self):
        del self.status['latest_collection']
        self.status['scheduled_collection_verified'] = False
        out = summarize_price_status(self.status)
        self.assertEqual(out['as_of'], self.status['verified_at'])
        self.assertIn('Scheduled collection not yet verified', out['detail'])

    def test_fail_closed_metadata(self):
        for key, value in [('saved_snapshots', True), ('rows_per_symbol', 99),
                           ('scheduled_run_verified', False), ('observed_at', '2026-11-16'),
                           ('observed_at', '2999-01-01T00:00:00Z'),
                           ('observed_at', '2026-11-13T00:00:00Z'), ('prices', [123])]:
            with self.subTest(key=key, value=value):
                status = copy.deepcopy(self.status)
                status['latest_collection'][key] = value
                with self.assertRaises(ValueError):
                    summarize_price_status(status)
        self.status['execution_ready'] = True
        with self.assertRaises(ValueError):
            summarize_price_status(self.status)

    def test_audited_coverage_keeps_execution_blocked(self):
        a = {'verified_at': '2026-11-17T13:00:00Z', 'first_session': '2026-06-26', 'last_session': '2026-11-16', 'hashes_and_symbols_verified': True}
        self.status['latest_collection']['coverage_audit'] = a
        out = summarize_price_status(self.status)
        self.assertIn('through 2026-11-16', out['detail'])
        self.assertIn('Calendar completeness is not established', out['detail'])
        self.assertIn('Execution remains disabled', out['detail'])
        for key,value in [('last_session','2026-11-18'),('hashes_and_symbols_verified',False),('first_session','2026-11-20'),('verified_at','2026-11-15T00:00:00Z'),('prices',[123])]:
            with self.subTest(key=key):
                bad=copy.deepcopy(self.status)
                bad['latest_collection']['coverage_audit'][key]=value
                with self.assertRaises(ValueError):summarize_price_status(bad)
