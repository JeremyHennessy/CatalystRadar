"""Independent static UI bindings for the narrow retained TXMD cover assertion."""
import hashlib
import json
import re
import unittest
from html.parser import HTMLParser
from pathlib import Path
from historical_outcome_audit import build

ROOT = Path(__file__).resolve().parents[1]
PIN = 'c316937c4eb802c7123b6dbde3c53a4aa5ad6999da164cd73ad56cb7e1f81be1'

class CoverAnnotation(HTMLParser):
    def __init__(self):
        super().__init__()
        self.depth = 0
        self.details = []
        self.nested_in_outcome = False
        self.attrs = {}
        self.tags = []
        self.text = []
        self.links = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'details':
            if a.get('id') == 'txmd-cover-class':
                self.nested_in_outcome = 'txmd-source-review' in self.details
                self.depth = 1
            elif self.depth:
                self.depth += 1
            self.details.append(a.get('id'))
        if self.depth:
            self.tags.append(tag)
            for key, value in attrs:
                if key.startswith('data-cover-'):
                    self.attrs.setdefault(key, []).append(value)
                if key.startswith('on'):
                    raise AssertionError('Inline action in static annotation')
            if tag == 'a':
                self.links.append(a['href'])

    def handle_endtag(self, tag):
        if tag == 'details':
            if self.depth:
                self.depth -= 1
            if self.details:
                self.details.pop()

    def handle_data(self, value):
        if self.depth:
            self.text.append(value)

class TxmdCoverWorkspaceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = (ROOT / 'web/company-findings/txmd-retained-cover-class.json').read_bytes()
        cls.data = json.loads(cls.raw)
        cls.page = (ROOT / 'web/financial-review.html').read_text()
        cls.parsed = CoverAnnotation()
        cls.parsed.feed(cls.page)
        cls.text = ' '.join(cls.parsed.text)

    def test_exact_source_and_static_rendered_bindings(self):
        self.assertEqual(len(self.raw), 4465)
        self.assertEqual(hashlib.sha256(self.raw).hexdigest(), PIN)
        d = self.data
        f = d['finding']
        expected = {'cik': d['issuer_cik'], 'accession': d['accession'],
                    'title': f['fields']['Security12bTitle']['text_as_reported'],
                    'symbol': f['fields']['TradingSymbol']['text_as_reported'],
                    'exchange': f['fields']['SecurityExchangeName']['text_as_reported'],
                    'exchange-cell': f['exchange_cell_text_as_reported'],
                    'transform': f['inline_exchange_transformation'],
                    'context': f['fields']['Security12bTitle']['context_ref'],
                    'start': f['context']['start_date_as_reported'],
                    'end': f['context']['end_date_as_reported'],
                    'observation': d['source']['recorded_retrieved_utc']}
        self.assertEqual(self.parsed.attrs, {'data-cover-' + k: [v] for k, v in expected.items()})
        for value in expected.values():
            self.assertIn(value, self.text)
        for value in [PIN, d['source']['filing_sha256'], f['primary_document_sha256']]:
            self.assertIn(value, self.text)
        self.assertIn(d['source']['url'], self.parsed.links)
        for link in ['company-findings/txmd-retained-cover-class.json', '../docs/research/retained-security-class.md']:
            self.assertIn(link, self.parsed.links)
            self.assertTrue((ROOT / 'web' / link).is_file())
        self.assertTrue(self.parsed.nested_in_outcome)
        self.assertEqual(self.page.count('id="txmd-cover-class"'), 1)
        for tag in ['script', 'button', 'input', 'form', 'iframe']:
            self.assertNotIn(tag, self.parsed.tags)

    def test_context_and_exchange_semantics_not_identity_or_market_price(self):
        f = self.data['finding']
        self.assertEqual(f['context']['period_kind'], 'DURATION_AS_FILED_NOT_EFFECTIVE_INTERVAL')
        self.assertEqual(f['context']['start_date_as_reported'], f['context']['end_date_as_reported'])
        self.assertEqual(f['context']['issuer_cik_as_reported'], self.data['issuer_cik'])
        self.assertEqual({r['context_ref'] for r in f['fields'].values()}, {'AsOf2026-11-13'})
        self.assertEqual(f['fields']['SecurityExchangeName']['text_as_reported'], 'Nasdaq')
        self.assertEqual(f['exchange_cell_text_as_reported'], 'The Nasdaq Stock Market LLC')
        self.assertEqual(f['inline_exchange_transformation'], 'ixt-sec:exchnameen (not evaluated)')
        registrant = f['registrant_evidence']
        self.assertEqual(registrant['filers'][0]['cik'], self.data['issuer_cik'])
        for key in ['multiple_filers', 'entities_interchangeable', 'facts_propagated_between_filers', 'security_mapping_verified']:
            self.assertFalse(registrant[key])
        for phrase in ['reported par value, not a market price or a quote', 'not independently verified present-day trading',
                       'as-filed duration, not an instant, listing date, verified effective-date interval or proof of continuous listing',
                       'context identifier itself does not supply historical identity evidence',
                       'No absence of splits, dividends, symbol changes, delisting or trading halts is established']:
            self.assertIn(phrase, self.text)

    def test_unknown_mapping_clocks_prices_and_outcomes_preserved(self):
        d = self.data
        for key in ['security_id', 'effective_from', 'effective_to', 'first_public_utc']:
            self.assertIsNone(d[key])
        for key in ['selection_changed', 'historical_mapping_verified', 'corporate_action_continuity_verified',
                    'price_join_performed', 'execution_ready', 'training_ready']:
            self.assertFalse(d[key])
        self.assertEqual(d['qualified_outcomes'], 0)
        self.assertFalse(d['source']['retrieval_clock_independently_authenticated'])
        self.assertEqual(d['source']['link_status'], 'RETAINED_RECEIPT_NOT_NEW_FETCH')
        for phrase in ['Security ID, effective-from and effective-to remain unknown',
                       'No CUSIP/FIGI mapping or ticker join to private prices is performed',
                       'First-public time remains unknown; price join remains unperformed',
                       'not independently authenticated and is not first-public time',
                       'not a new fetch or current-availability check', 'Original filing bytes remain private',
                       'No new quote, return, fill, order, collector activation or outcome eligibility is introduced',
                       'opening it does not fetch or revalidate the original or perform a price join']:
            self.assertIn(phrase, self.text)

    def test_frozen_selection_six_dependencies_and_conflict_unchanged(self):
        audit = build(ROOT)
        prior = json.loads((ROOT / 'web/company-findings/frozen-outcome-txmd-source-review.json').read_bytes())
        self.assertEqual((audit['universe_count'], audit['selection_count'], audit['qualified_outcomes']), (10, 1, 0))
        selected = audit['selected'][0]
        self.assertEqual(selected['event_id'], self.data['accession'])
        self.assertEqual(selected['issuer_cik'], self.data['issuer_cik'])
        self.assertEqual(len(selected['missing_dependencies']), 6)
        self.assertEqual(selected['missing_dependencies'], prior['remaining_dependencies'])
        self.assertEqual(re.findall('data-outcome-dependency="([^"]+)"', self.page), prior['remaining_dependencies'])
        self.assertTrue(prior['finding']['description_body_period_conflict'])
        self.assertEqual(prior['finding']['conflict_resolution'], 'UNRESOLVED_NO_SILENT_CORRECTION')
        for phrase in ['all six frozen dependencies still apply', '10 reviewed rows / 1 selected case / 0 qualified outcomes',
                       'separate second-versus-third-quarter conflict also remains unresolved']:
            self.assertIn(phrase, self.text)
