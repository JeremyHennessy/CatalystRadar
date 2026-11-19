"""Prove the clock comparison uses the saved calendar without changing qualification."""
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo
import hashlib
import json
import unittest

from historical_outcome_audit import build
from observed_outcome_coverage import candidate_dates

ROOT = Path(__file__).resolve().parents[1]
PATH = 'company-findings/txmd-declared-publication-clocks.json'


class TXMDDeclaredClockTests(unittest.TestCase):
    def setUp(self):
        raw = (ROOT / 'web' / PATH).read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(),
                         '265f775ba3a9a693fa63fef78310b6bc6a5300ec59e727e086c7c16a2d8e5139')
        self.d = json.loads(raw)

    def test_same_schedule_for_independently_interpreted_clocks(self):
        clocks = self.d['clocks']
        self.assertEqual([(c['channel'], c['field']) for c in clocks],
                         [('Business Wire', 'NewsArticle.datePublished'),
                          ('TherapeuticsMD investor relations', 'NewsArticle.datePublished'),
                          ('SEC EDGAR', 'Accepted (America/New_York)')])
        for item in clocks:
            value = datetime.fromisoformat(item['as_reported'])
            if item['channel'] == 'SEC EDGAR':
                self.assertIsNone(value.tzinfo)
                value = value.replace(tzinfo=ZoneInfo('America/New_York'))
            self.assertEqual(value.astimezone(timezone.utc).isoformat(), item['utc'].replace('Z', '+00:00'))
            self.assertEqual(candidate_dates(item['utc']), ['2026-11-16', '2026-11-17'])
        self.assertEqual(self.d['candidate_scheduled_close_dates_for_all_three'], ['2026-11-16', '2026-11-17'])
        # Earlier than Friday's close would yield a different scheduled pair.
        self.assertEqual(candidate_dates('2026-11-13T20:59:59Z'), ['2026-11-13', '2026-11-16'])

    def test_frozen_outcome_and_price_boundary_survive(self):
        audit = build(ROOT)
        self.assertEqual((audit['universe_count'], audit['selection_count'], audit['qualified_outcomes']), (10, 1, 0))
        row = audit['selected'][0]
        self.assertEqual(row['event_id'], self.d['accession'])
        self.assertEqual(row['issuer_cik'], self.d['issuer_cik'])
        self.assertEqual(row['first_missing_dependency'], 'VERIFIED_EVENT_FIRST_PUBLIC_TIME')
        self.assertEqual(audit['price_evidence_reference']['last_session'], self.d['last_session_in_frozen_price_reference'])
        for key in ['entry_session', 'endpoint_session', 'return_value']:
            self.assertIsNone(row[key])
        self.assertIsNone(self.d['first_public_utc'])
        self.assertIsNone(self.d['return_value'])
        self.assertFalse(self.d['channel_availability_order_verified'])
        self.assertEqual(self.d['qualified_outcomes'], 0)

    def test_static_links_and_claim_boundaries(self):
        page = (ROOT / 'web/financial-review.html').read_text()
        self.assertEqual(page.count('id="txmd-declared-publication-clocks"'), 1)
        detail = page.split('id="txmd-declared-publication-clocks">', 1)[1].split('</details>', 1)[0]
        for item in self.d['clocks']:
            self.assertIn('href="' + item['source'] + '"', detail)
            self.assertIn('datetime="' + item['utc'] + '"', detail)
        for phrase in (PATH, self.d['calendar_source'], 'not SEC dissemination', 'actual availability',
                       'not a proven sequence', 'before the candidate endpoint', 'No return or trade'):
            self.assertIn(phrase, detail)
        for tag in ('<script', '<iframe', '<form', '<button'):
            self.assertNotIn(tag, detail)
