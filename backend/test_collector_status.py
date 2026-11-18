import copy
import json
from pathlib import Path
import tempfile
import unittest
from collector_status import build, next_slot, instant, load

class CollectorStatusTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(); self.root=Path(self.temp.name)
        for folder in ('.github/workflows','backend','data'): (self.root/folder).mkdir(parents=True)
        original=Path(__file__).resolve().parent.parent
        for name in ('.github/workflows/sec-observations.yml','backend/trial_gate.py','data/price_feed_status.json'):
            (self.root/name).write_bytes((original/name).read_bytes())
        # Freeze the observation used by this historical clock; latest_scan is mutable.
        frozen_sec = original/'data/sec-observations/20261117T195421146121Z.json'
        (self.root/'data/latest_scan.json').write_bytes(frozen_sec.read_bytes())
        import shutil
        shutil.copytree(original/'data/sec-snapshots', self.root/'data/sec-snapshots')
        self.now='2026-11-18T02:00:00+00:00'
    def tearDown(self): self.temp.cleanup()
    def rows(self): return build(self.root,self.now)['collectors']
    def mutate(self,path,fn):
        p=self.root/path; value=json.loads(p.read_text()); fn(value); p.write_text(json.dumps(value))
    def test_actual_receipt_projection(self):
        sec,av,manual=self.rows()
        self.assertEqual(sec['successful_issuers'],10)
        self.assertEqual(sec['next_configured_slot'],'2026-11-18T11:17:00+00:00')
        self.assertEqual(av['next_configured_slot'],'2026-11-18T12:10:00+00:00')
        self.assertEqual(av['saved_snapshots'],11)
        self.assertIsNone(sec['last_attempt']); self.assertIsNone(av['last_attempt'])
        self.assertEqual(manual['mode'],'MANUAL_OFFLINE_IMPORTS')
    def test_historical_fixture_is_not_mutable_latest(self):
        sec = self.rows()[0]
        self.assertEqual(sec['last_successful_observation'], '2026-11-17T19:54:39.231235+00:00')
        self.mutate('data/latest_scan.json', lambda x:x.update(finished_at='2026-11-18T19:26:45+00:00'))
        with self.assertRaisesRegex(ValueError, 'invalid/future SEC receipt'):
            self.rows()
    def test_expiry_and_no_future_year(self):
        for row in build(self.root,'2027-11-18T02:00:00+00:00')['collectors'][:2]:
            self.assertEqual(row['policy_state'],'EXPIRED'); self.assertIsNone(row['next_configured_slot'])
    def test_different_expiries(self):
        sec,av,_=build(self.root,'2026-11-21T01:00:00+00:00')['collectors']
        self.assertEqual(sec['policy_state'],'EXPIRED'); self.assertEqual(av['policy_state'],'BOUNDED_TRIAL')
    def test_incomplete_is_not_success(self):
        self.mutate('data/latest_scan.json',lambda x:x.update(successful_issuers=9,errors=['secret provider text']))
        sec=self.rows()[0]; self.assertEqual(sec['source_status'],'INCOMPLETE_RETAINED_RECEIPT'); self.assertIsNone(sec['last_successful_observation'])
        self.assertNotIn('secret provider text',json.dumps(sec))
    def test_missing_receipts_not_empty_success(self):
        (self.root/'data/latest_scan.json').unlink(); (self.root/'data/price_feed_status.json').unlink()
        for row in self.rows()[:2]: self.assertEqual(row['source_status'],'NO_VERIFIED_RECEIPT')
    def test_no_private_unknown_fields(self):
        self.mutate('data/price_feed_status.json',lambda x:x.update(raw_prices='DO_NOT_PUBLISH',api_key='SECRET'))
        output=json.dumps(self.rows()); self.assertNotIn('DO_NOT_PUBLISH',output); self.assertNotIn('SECRET',output)
    def test_future_fails(self):
        self.mutate('data/latest_scan.json',lambda x:x.update(finished_at='2027-01-01T00:00:00+00:00'))
        with self.assertRaises(ValueError): self.rows()
    def test_malformed_counts_fail(self):
        self.mutate('data/latest_scan.json',lambda x:x.update(configured_issuers=True))
        with self.assertRaises(ValueError): self.rows()
    def test_scope_change_fails(self):
        self.mutate('data/price_feed_status.json',lambda x:x['latest_collection'].update(saved_snapshots=12))
        with self.assertRaises(ValueError): self.rows()
    def test_schedule_change_fails(self):
        (self.root/'.github/workflows/sec-observations.yml').write_text('new schedule')
        with self.assertRaises(ValueError): self.rows()
    def test_duplicate_fields_fail(self):
        (self.root/'data/latest_scan.json').write_text('{"errors":[],"errors":[]}')
        with self.assertRaises(ValueError): self.rows()
    def test_unsafe_run_link_not_emitted(self):
        self.mutate('data/latest_scan.json',lambda x:x.update(github_run_url='javascript:alert(1)'))
        self.assertIsNone(self.rows()[0]['last_verified_complete_run'])
    def test_reservation_not_attempt_or_success(self):
        folder=self.root/'data/sec-control/attempts'; folder.mkdir(parents=True)
        (folder/'123.json').write_text(json.dumps({'reserved_at':'2026-11-18T01:00:00+00:00','run_id':'123','event':'schedule'}))
        row=self.rows()[0]
        self.assertEqual(row['last_retained_reservation']['run_id'],'123')
        self.assertIsNone(row['last_attempt'])
        self.assertNotEqual(row['last_successful_observation'],'2026-11-18T01:00:00+00:00')
    def test_sec_scope_change_fails(self):
        self.mutate('data/latest_scan.json',lambda x:x.update(configured_issuers=20,successful_issuers=20))
        with self.assertRaises(ValueError): self.rows()
    def test_sec_missing_sources_fail(self):
        self.mutate('data/latest_scan.json',lambda x:x.update(sources=[]))
        with self.assertRaises(ValueError): self.rows()
    def test_sec_duplicate_source_fails(self):
        self.mutate('data/latest_scan.json',lambda x:x['sources'].__setitem__(1,x['sources'][0]))
        with self.assertRaises(ValueError): self.rows()
    def test_sec_ticker_cik_mismatch_fails(self):
        self.mutate('data/latest_scan.json',lambda x:x['sources'][0].update(ticker='XRX'))
        with self.assertRaises(ValueError): self.rows()
    def test_sec_substituted_issuer_fails(self):
        self.mutate('data/latest_scan.json',lambda x:x['sources'][0].update(url='https://data.sec.gov/submissions/CIK0000000001.json'))
        with self.assertRaises(ValueError): self.rows()
    def test_sec_duplicate_archive_distinct_urls_fails(self):
        def substitute(x):
            for field in ('archive_path','sha256','byte_count'):
                x['sources'][1][field]=x['sources'][0][field]
        self.mutate('data/latest_scan.json',substitute)
        with self.assertRaises(ValueError): self.rows()
    def test_sec_failed_source_fails(self):
        self.mutate('data/latest_scan.json',lambda x:x['sources'][0].update(status=403))
        with self.assertRaises(ValueError): self.rows()
    def test_sec_corrupt_archive_fails(self):
        receipt=json.loads((self.root/'data/latest_scan.json').read_text())
        (self.root/receipt['sources'][0]['archive_path']).write_bytes(b'corrupt')
        with self.assertRaises(ValueError): self.rows()
    def test_sec_invalid_source_clock_fails(self):
        self.mutate('data/latest_scan.json',lambda x:x['sources'][0].update(retrieved_utc='2027-01-01T00:00:00Z'))
        with self.assertRaises(ValueError): self.rows()
    def test_private_unverified_schedule_fails(self):
        self.mutate('data/price_feed_status.json',lambda x:x['latest_collection'].update(scheduled_run_verified=False))
        with self.assertRaises(ValueError): self.rows()
    def test_private_unverified_hashes_fail(self):
        self.mutate('data/price_feed_status.json',lambda x:x['latest_collection']['coverage_audit'].update(hashes_and_symbols_verified=False))
        with self.assertRaises(ValueError): self.rows()
    def test_private_missing_verification_fails(self):
        self.mutate('data/price_feed_status.json',lambda x:x['latest_collection'].pop('coverage_audit'))
        with self.assertRaises(ValueError): self.rows()
    def test_private_future_verification_fails(self):
        self.mutate('data/price_feed_status.json',lambda x:x['latest_collection']['coverage_audit'].update(verified_at='2027-01-01T00:00:00Z'))
        with self.assertRaises(ValueError): self.rows()
    def test_naive_time_and_backdating_fail(self):
        for stamp in ['2026-11-18T02:00:00','2026-11-17T02:00:00+00:00']:
            with self.assertRaises(ValueError): build(self.root,stamp)

if __name__=='__main__': unittest.main()
