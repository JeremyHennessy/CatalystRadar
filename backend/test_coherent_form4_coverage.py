"""Offline proof that retained Form 4 metadata does not imply scan coverage."""
from datetime import datetime
import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

import scan_watchlist

ROOT = Path(__file__).resolve().parents[1]
OBS = 'data/sec-observations/20261119T114159492631Z.json'
PIN = 'c0f3a419d2d23b0966097f86fc70ae90bdceeb911620a4674c07e60937591d52'
CIK = '0000820318'
FORMS = {
    '0000899140-26-001275': ('2026-11-10', '2026-11-12T11:01:02.000Z'),
    '0000899140-26-001276': ('2026-11-09', '2026-11-12T11:02:52.000Z'),
}


class CoherentForm4Coverage(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.receipt = json.loads((ROOT / OBS).read_bytes())
        cls.source = next(s for s in cls.receipt['sources'] if s['ticker'] == 'COHR')
        cls.raw = (ROOT / cls.source['archive_path']).read_bytes()

    def test_retained_rows_are_not_actual_discoveries(self):
        self.assertEqual(hashlib.sha256(self.raw).hexdigest(), PIN)
        self.assertEqual(self.source['sha256'], PIN)
        self.assertEqual(self.source['retrieved_utc'], '2026-11-19T11:41:59.642713+00:00')
        issuer = json.loads(self.raw)
        self.assertEqual(str(issuer['cik']).zfill(10), CIK)
        filings = issuer['filings']['recent']
        for accession, (date, acceptance) in FORMS.items():
            with self.subTest(accession=accession):
                self.assertEqual(filings['accessionNumber'].count(accession), 1)
                i = filings['accessionNumber'].index(accession)
                self.assertEqual(
                    tuple(filings[k][i] for k in
                          ('form', 'reportDate', 'filingDate', 'acceptanceDateTime', 'primaryDocument')),
                    ('4', date, '2026-11-12', acceptance, 'xslF345X06/form4.xml'),
                )
                self.assertLess(scan_watchlist.parse(acceptance),
                                datetime.fromisoformat(self.receipt['window_start']))
        self.assertTrue(FORMS.keys().isdisjoint(e['accession'] for e in self.receipt['events']))
        self.assertEqual((self.receipt['eligible_count'], self.receipt['orders_created']), (0, 0))

    def test_form_filter_even_when_acceptances_are_inside_the_window(self):
        now = datetime.fromisoformat('2026-11-12T12:00:00+00:00')
        with TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'data').mkdir()
            (root / 'data/watchlist.json').write_text(json.dumps([{'cik': CIK, 'ticker': 'COHR'}]))
            with (patch.object(scan_watchlist, 'contact_email', return_value='audit@example.invalid'),
                  patch.object(scan_watchlist, 'datetime', wraps=datetime) as clock,
                  patch.object(scan_watchlist, 'stamp', return_value=now.isoformat()),
                  patch.object(scan_watchlist, 'Archive') as provider):
                clock.now.return_value = now
                provider.return_value.get.return_value = self.raw, {
                    'url': self.source['url'], 'sha256': PIN, 'status': 200,
                    'byte_count': len(self.raw), 'retrieved_utc': now.isoformat(),
                }
                report = scan_watchlist.scan(root)
                provider.return_value.get.assert_called_once_with(self.source['url'], f'{CIK}.json')
        for _, acceptance in FORMS.values():
            self.assertLessEqual(datetime.fromisoformat(report['window_start']),
                                 scan_watchlist.parse(acceptance))
            self.assertLessEqual(scan_watchlist.parse(acceptance), now)
        self.assertTrue(report['metadata_window_complete'], report['errors'])
        self.assertTrue(FORMS.keys().isdisjoint(e['accession'] for e in report['events']))
        self.assertEqual((report['orders_created'], report['eligible_count']), (0, 0))

    def test_dashboard_labels_are_scoped_and_source_linked(self):
        html = (ROOT / 'web/collectors.html').read_text()
        self.assertEqual(html.count('id="coherent-form4-coverage"'), 1)
        detail = html.split('id="coherent-form4-coverage">', 1)[1].split('</details>', 1)[0]
        for accession in FORMS:
            self.assertIn(f'https://www.sec.gov/Archives/edgar/data/820318/'
                          f'{accession.replace("-", "")}/xslF345X06/form4.xml', detail)
        for fact in ('96-hour window', '11:41:59.642713 UTC', '11:01:02 UTC', '11:02:52 UTC',
                     'US$222.885', 'US$997,400', 'US$222,885', 'CEO and director',
                     'not marked as an officer', 'the venue is not established',
                     'no signal, outcome or paper trade follows', '../' + OBS):
            self.assertIn(fact, detail)
        for interactive in ('<script', '<form', '<button', '<input', '<iframe'):
            self.assertNotIn(interactive, detail)
