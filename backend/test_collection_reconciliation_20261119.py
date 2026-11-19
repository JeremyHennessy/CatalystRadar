"""Protect the saved Nov 19 status checkpoint and its evidence boundaries."""
from datetime import datetime
import hashlib
import json
from pathlib import Path
import unittest

from sec_collection_control import plan

ROOT = Path(__file__).resolve().parents[1]
OBS = 'data/sec-observations/20261119T114159492631Z.json'
PIN = '10b3c74b4949b1d23d850a9c822f052343dac979fa1112f3723c37fda81100bc'


class CollectionReconciliation(unittest.TestCase):
    def test_published_checkpoint_matches_saved_receipt(self):
        saved = (ROOT / OBS).read_bytes()
        self.assertEqual(hashlib.sha256(saved).hexdigest(), PIN)
        receipt = json.loads(saved)
        self.assertEqual(receipt['github_event_name'], 'push')
        self.assertEqual(receipt['github_run_url'].split('/')[-1], '44516963966')
        self.assertEqual(receipt['finished_at'], '2026-11-19T11:42:17.525628+00:00')
        self.assertTrue(receipt['metadata_window_complete'])
        self.assertEqual(receipt['successful_issuers'], receipt['configured_issuers'])
        self.assertEqual([source['status'] for source in receipt['sources']], [200] * 10)
        self.assertEqual(len(receipt['events']), 2)
        self.assertEqual((receipt['eligible_count'], receipt['orders_created']), (0, 0))

    def test_logged_skip_precedes_reservation(self):
        result = plan(now=datetime.fromisoformat('2026-11-19T01:32:29.382275+00:00'),
                      event='schedule', actor='JeremyHennessy', run_id='44437552657',
                      attempt='1', request=None, receipts=[], reservations=[])
        self.assertEqual(result, ('OUTSIDE_TRIAL_WINDOW', None))
        self.assertFalse((ROOT / 'data/sec-control/attempts/44437552657.json').exists())

    def test_operational_stages_and_unknowns_are_separate(self):
        page = (ROOT / 'web/collectors.html').read_text()
        self.assertEqual(page.count('id="collection-reconciliation-20261119"'), 1)
        section = page.split('id="collection-reconciliation-20261119"', 1)[1].split('</section>', 1)[0]
        for value in ('2026-11-19T13:20:22Z', '44437552657', 'skipped outside the trial window',
                      '44516963966', 'Request-triggered fallback, not a scheduled collection',
                      '../' + OBS, '44517197609', '44390572185', '44172913902', '44392445041',
                      'whether a provider request was made or quota was used',
                      'not the exact cause on November 18', 'main paper book remains disabled'):
            self.assertIn(value, section)
        for forbidden in ('<script', '<button', '<form', '<iframe', '<input'):
            self.assertNotIn(forbidden, section)
        self.assertIn('collector-observation-20261118T1233Z.json', page)
        self.assertIn('id="collector-published-sec"', page)

    def test_evening_scheduled_observation_repeats_fallback_events(self):
        path = 'data/sec-observations/20261119T193148867794Z.json'
        saved = (ROOT / path).read_bytes()
        self.assertEqual(hashlib.sha256(saved).hexdigest(),
                         'be97f6b0e9ee936072bab704619bdebd2b2d962f0929590422153ed6969bfadc')
        receipt = json.loads(saved)
        fallback = json.loads((ROOT / OBS).read_bytes())
        self.assertEqual(receipt['github_event_name'], 'schedule')
        self.assertTrue(receipt['metadata_window_complete'])
        self.assertEqual(receipt['github_run_url'].split('/')[-1], '44599095597')
        self.assertEqual(receipt['finished_at'], '2026-11-19T19:32:06.964007+00:00')
        self.assertEqual((receipt['successful_issuers'], receipt['configured_issuers']), (10, 10))
        self.assertEqual([source['status'] for source in receipt['sources']], [200] * 10)
        def evidence_identity(record):
            keys = ('issuer_cik', 'accession', 'source_metadata_sha256')
            return sorted(tuple(event[key] for key in keys) for event in record['events'])
        self.assertEqual(len(receipt['events']), 2)
        self.assertEqual(evidence_identity(receipt), evidence_identity(fallback))
        self.assertEqual((receipt['eligible_count'], receipt['orders_created']), (0, 0))
        page = (ROOT / 'web/collectors.html').read_text()
        self.assertEqual(page.count('id="collection-review-20261119-evening"'), 1)
        section = page.split('id="collection-review-20261119-evening"', 1)[1].split('</section>', 1)[0]
        for value in ('44599095597', '44599331583', '../' + path, '19:32:06.964007Z',
                      '44608790032', '20:27:07Z', '44172913902', '2026-11-17T20:49:18.653849Z',
                      'November 16 session', '44610949703', '20:39:52Z',
                      'whether a provider request was sent', 'No workflow was rerun'):
            self.assertIn(value, section)
        self.assertIn('Historical checkpoint: November 19 morning reconciliation', page)
        self.assertIn('Historical checkpoint: November 18 midday collection check', page)
        for forbidden in ('<script', '<button', '<form', '<iframe', '<input'):
            self.assertNotIn(forbidden, section)
