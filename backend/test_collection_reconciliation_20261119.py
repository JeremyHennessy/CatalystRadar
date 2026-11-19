"""Protect the saved Nov 19 status checkpoint and its evidence boundaries."""
import hashlib
import json
from pathlib import Path
import unittest

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
