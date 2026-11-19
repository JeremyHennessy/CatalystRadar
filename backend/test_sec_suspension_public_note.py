"""Static readiness disclosure contract; no collection or trading integration."""
from html.parser import HTMLParser
from pathlib import Path
import unittest
from sec_suspension_fixture import fixture
from tjgc_corporate_action_fixture import fixture as action_fixture

ROOT = Path(__file__).resolve().parents[1]


class Note(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.active = False
        self.count = 0
        self.attributes = {}
        self.text = []
        self.links = []
        self.tags = []
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if attrs.get('id') == 'historical-suspension-case':
            self.active = True
            self.count += 1
            self.attributes = attrs
        if self.active:
            self.tags.append(tag)
            if tag == 'a':
                self.links.append(attrs.get('href'))

    def handle_endtag(self, tag):
        if self.active and tag == 'details':
            self.active = False

    def handle_data(self, text):
        if self.active:
            self.text.append(text)


class HistoricalSuspensionPublicNote(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = (ROOT / 'web/index.html').read_text()
        cls.note = Note(cls.html)
        cls.words = ' '.join(cls.note.text)

    def test_existing_readiness_collapsed_note_only(self):
        self.assertEqual(self.note.count, 1)
        self.assertEqual(self.note.attributes['class'], 'details')
        self.assertNotIn('open', self.note.attributes)
        self.assertIn('summary', self.note.tags)
        self.assertNotIn('script', self.note.tags)
        self.assertNotIn('input', self.note.tags)
        self.assertNotIn('button', self.note.tags)
        readiness = self.html.index('id="readiness"')
        note = self.html.index('id="historical-suspension-case"')
        sources = self.html.index('id="sources"')
        self.assertLess(readiness, note)
        self.assertLess(note, sources)

    def test_exact_identity_and_order_dates(self):
        f = fixture()
        self.assertIn(f['issuer_name'], self.words)
        self.assertIn('CIK ' + f['issuer_cik'], self.words)
        self.assertIn(f['order_release'], self.words)
        self.assertIn('October 14, 2026', self.words)
        self.assertIn('October 15, 2026 at 04:00 ET', self.words)
        self.assertIn('October 28, 2026 at 23:59 ET', self.words)
        self.assertIn('as of October 14, 2026', self.words)
        self.assertIn('not its initial listing date', self.words)

    def test_primary_links_are_exact_not_derived_from_user_input(self):
        self.assertEqual(self.note.links, fixture()['source_urls'] + [
            'https://ir.nasdaq.com/news-releases/news-release-details/nasdaq-halts-tjgc-group-limited-0',
            'https://github.com/JeremyHennessy/CatalystRadar/blob/main/docs/sec-suspension-historical-fixture.md'] + list(action_fixture()['sources'].values()) + [
            'https://github.com/JeremyHennessy/CatalystRadar/blob/main/docs/tjgc-corporate-action-fixture.md'])

    def test_corporate_action_identity_and_counts(self):
        f = action_fixture()
        e = f['events'][0]
        self.assertEqual(f['issuer_cik'], fixture()['issuer_cik'])
        for phrase in ('1-for-3', 'May 26, 2026', e['post_split_cusip_as_reported'],
                       format(e['nominal_post_split_issued_shares'], ','),
                       format(e['later_reported_post_rounding_issued_shares'], ','),
                       'August 12, 2026', 'Class A/Class B'):
            self.assertIn(phrase, self.words)

    def test_action_warnings_never_adjust_or_clear(self):
        for phrase in ('Do not apply the ratio twice', 'vendor-price adjustment factor',
                       'no May 26 trade or fill is established',
                       'not another reverse split', 'does not verify the same share class',
                       'No match means unknown, not corporate-action-free',
                       'complete corporate-action coverage are established'):
            self.assertIn(phrase, self.words)

    def test_no_clearance_or_unproven_clock(self):
        for phrase in ('not current trading status', 'not a live or complete halt feed',
                       'both boundary minutes unknown', 'outside the window remain unknown',
                       'expiry does not establish resumption',
                       'current trading status are not established',
                       'First-public time and historical observation time remain unknown',
                       'not a retained PDF-byte archive', 'not an adjudicated finding',
                       'changes none of the qualification gates'):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, self.words)


if __name__ == '__main__':
    unittest.main()
