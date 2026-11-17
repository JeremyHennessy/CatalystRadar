import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch
import sec_collection_control as c


class ControlTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 11, 18, 12, 10, tzinfo=timezone.utc)
        self.request = dict(version=1, purpose='PUBLIC_SEC_OBSERVATION_ONLY',
            requested_at=self.now.isoformat(), expires_at=(self.now+timedelta(minutes=15)).isoformat(), session='2026-11-18')
        self.args = dict(now=self.now, event='push', actor='JeremyHennessy', run_id='123', attempt='1',
            request=self.request, receipts=[], reservations=[])

    def receipt(self, run='122', complete=True, when=None, event='schedule'):
        stamp = when or self.now-timedelta(hours=1)
        return dict(started_at=stamp.isoformat(), finished_at=stamp.isoformat(), configured_issuers=10,
            successful_issuers=10 if complete else 0, metadata_window_complete=complete,
            errors=[] if complete else [{'error':'HTTP403'}], github_event_name=event,
            github_run_url='https://github.com/'+c.REPO+'/actions/runs/'+run)

    def test_valid_request_reserves_without_trade_fields(self):
        reason, record = c.plan(**self.args)
        self.assertEqual(reason, 'RESERVE_BEFORE_COLLECTION')
        self.assertEqual(record['session'], '2026-11-18')
        self.assertEqual(len(record['request_sha256']), 64)
        self.assertNotIn('orders', record)

    def test_exact_actor_event_attempt(self):
        for key, value in [('actor','other'),('event','pull_request'),('attempt','2'),('run_id','../x')]:
            with self.subTest(key=key), self.assertRaises(ValueError):
                c.plan(**{**self.args,key:value})

    def test_strict_request(self):
        for change in [dict(version=True),dict(secret='SYNTHETIC'),dict(purpose='TRADE'),dict(session='2026-11-19'),
            dict(requested_at=(self.now+timedelta(seconds=1)).isoformat()),
            dict(expires_at=(self.now-timedelta(seconds=1)).isoformat()),
            dict(expires_at=(self.now+timedelta(minutes=16)).isoformat()),dict(requested_at='2026-11-18T12:10:00')]:
            with self.subTest(change=change),self.assertRaises(ValueError):
                c.plan(**{**self.args,'request':{**self.request,**change}})

    def test_trial_gate_applies_all_events(self):
        for event in ('push','schedule','workflow_dispatch'):
            for when in (datetime(2026,11,21,12,tzinfo=timezone.utc),datetime(2026,11,18,10,tzinfo=timezone.utc)):
                self.assertEqual(c.plan(**{**self.args,'event':event,'now':when})[1],None)

    def test_recent_receipt_deduplicates_all_triggers(self):
        for event in ('push','schedule','workflow_dispatch'):
            reason, record = c.plan(**{**self.args,'event':event,'receipts':[self.receipt(when=self.now-timedelta(minutes=29))]})
            self.assertEqual(reason,'RECENT_COMPLETE_OBSERVATION'); self.assertIsNone(record)

    def test_old_failure_before_new_success_does_not_poison_state(self):
        old = self.receipt(run='121',complete=False,when=self.now-timedelta(hours=2))
        self.assertIsNotNone(c.plan(**{**self.args,'receipts':[old,self.receipt()]})[1])

    def test_failed_latest_scan_blocks_all_triggers_even_after_cooldown(self):
        for event in ('push','schedule','workflow_dispatch'):
            with self.assertRaisesRegex(ValueError,'latest source scan incomplete'):
                c.plan(**{**self.args,'event':event,'receipts':[self.receipt(complete=False)]})

    def test_unresolved_reservation_blocks_all_future_scans(self):
        reservation=c.plan(**self.args)[1]
        for event in ('push','schedule','workflow_dispatch'):
            with self.assertRaisesRegex(ValueError,'unresolved'):
                c.plan(**{**self.args,'run_id':'124','event':event,'reservations':[reservation]})

    def test_fallback_once_per_day_after_completed_attempt(self):
        reservation=c.plan(**{**self.args,'now':self.now-timedelta(hours=1),'event':'workflow_dispatch'})[1]
        reservation['event']='push'; reservation['request_sha256']='a'*64
        receipt=self.receipt(run='123',event='push')
        args={**self.args,'run_id':'124','reservations':[reservation],'receipts':[receipt]}
        self.assertEqual(c.plan(**args)[0],'FALLBACK_ALREADY_RESERVED_TODAY')
        self.assertIsNotNone(c.plan(**{**args,'event':'schedule'})[1])

    def test_receipt_identity_timing_and_duplicates_fail_closed(self):
        reservation=c.plan(**{**self.args,'now':self.now-timedelta(hours=1),'event':'schedule'})[1]
        wrong=self.receipt(run='123',event='workflow_dispatch')
        with self.assertRaises(ValueError): c.plan(**{**self.args,'run_id':'124','reservations':[reservation],'receipts':[wrong]})
        for receipts in ([self.receipt(),self.receipt()], [self.receipt(when=self.now+timedelta(seconds=1))]):
            with self.assertRaises(ValueError): c.plan(**{**self.args,'receipts':receipts})

    def test_duplicate_control_fields(self):
        with self.assertRaises(ValueError):c.decode(b'{"version":1,"version":1}')

    def env(self):
        return dict(GITHUB_ACTIONS='true',GITHUB_REPOSITORY=c.REPO,GITHUB_REF='refs/heads/main',
            GITHUB_ACTOR='JeremyHennessy',GITHUB_RUN_ID='123',GITHUB_RUN_ATTEMPT='1',GITHUB_EVENT_NAME='push',GITHUB_SHA='a'*40)

    def setup_root(self, directory):
        root=Path(directory); path=root/c.REQUEST;path.parent.mkdir(parents=True)
        path.write_text(json.dumps(self.request));return root

    def fake_git(self, log, fail_push=False):
        def fake(*args):
            log.append(args)
            if args[0]=='status':return ''
            if args[0]=='rev-parse':return 'a'*40
            if args[0]=='rev-list':return 'a'*40+' '+'b'*40
            if args[0]=='diff-tree':return c.REQUEST
            if args[0]=='ls-remote':return 'a'*40+'\trefs/heads/main'
            if args[0]=='push' and fail_push:raise RuntimeError('SYNTHETIC_SECRET')
            return ''
        return fake

    def test_reservation_persisted_and_pushed_before_scanner(self):
        with tempfile.TemporaryDirectory() as directory:
            root=self.setup_root(directory); log=[]
            def scan(_):
                self.assertTrue((root/'data/sec-control/attempts/123.json').exists())
                self.assertIn(('push','origin','HEAD:main'),log)
                self.assertEqual(log[-1],('rev-parse','HEAD'))
            with patch.object(c,'git',side_effect=self.fake_git(log)),patch('sec_identity.contact_email',return_value='fixture@example.invalid'),patch('scan_watchlist.scan',side_effect=scan) as mocked:
                self.assertEqual(c.run(root,self.env(),clock=lambda:self.now),('COLLECTION_RECORDED',True))
                mocked.assert_called_once()

    def test_failed_reservation_push_never_calls_scanner(self):
        with tempfile.TemporaryDirectory() as directory:
            root=self.setup_root(directory)
            with patch.object(c,'git',side_effect=self.fake_git([],True)),patch('sec_identity.contact_email',return_value='fixture@example.invalid'),patch('scan_watchlist.scan') as scan:
                with self.assertRaises(RuntimeError):c.run(root,self.env(),clock=lambda:self.now)
                scan.assert_not_called()

    def test_superseded_or_bundled_request_never_calls_scanner(self):
        for kind in ('superseded','bundle','dirty'):
            with tempfile.TemporaryDirectory()as directory:
                root=self.setup_root(directory);base=self.fake_git([])
                def fake(*args):
                    if kind=='bundle' and args[0]=='diff-tree':return c.REQUEST+'\nbackend/paper.py'
                    if kind=='dirty' and args[0]=='status':return 'M file'
                    return base(*args)
                env=self.env()
                if kind=='superseded':env['GITHUB_SHA']='c'*40
                with patch.object(c,'git',side_effect=fake),patch('scan_watchlist.scan')as scan:
                    with self.assertRaises(ValueError):c.run(root,env,clock=lambda:self.now)
                    scan.assert_not_called()

    def test_expiry_after_push_blocks_scanner(self):
        with tempfile.TemporaryDirectory()as directory:
            root=self.setup_root(directory)
            times=iter([self.now,self.now+timedelta(minutes=16)])
            with patch.object(c,'git',side_effect=self.fake_git([])),patch('sec_identity.contact_email',return_value='fixture@example.invalid'),patch('scan_watchlist.scan')as scan:
                with self.assertRaises(ValueError):c.run(root,self.env(),clock=lambda:next(times))
                scan.assert_not_called()
