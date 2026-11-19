from hashlib import sha256
import unittest

from halt_window_review import review_window
from test_halts_observation import feed, fixture


def receipt(raw, at='2026-11-14T19:00:00Z', kind='current', day=None):
    return dict(raw=raw, sha256=sha256(raw).hexdigest(), retrieved_utc=at,
                query_kind=kind, query_date=day)


def review(*receipts, **overrides):
    options = dict(symbol='TEST', start_utc='2026-11-13T20:59:00Z',
                   end_utc='2026-11-13T21:00:00Z', as_of_utc='2026-11-14T20:00:00Z')
    return review_window(receipts, **{**options, **overrides})


class WindowTests(unittest.TestCase):
    def test_start_inclusive_end_exclusive_and_literal_symbol(self):
        for raw, status in (
                (fixture(), 'REPORTED_START_IN_WINDOW'),
                (fixture(HaltTime='16:00:00'), 'NO_MATCH_COVERAGE_UNKNOWN'),
                (fixture(IssueSymbol='test'), 'NO_MATCH_COVERAGE_UNKNOWN')):
            result = review(receipt(raw))
            self.assertEqual(result['status'], status)
            self.assertIs(result['complete'], False)
            self.assertIs(result['source_authenticated'], False)
            self.assertIs(result['effective_dated_identity_verified'], False)

    def test_carry_in_preserved_across_empty_and_scheduled_resumptions(self):
        old = receipt(fixture(HaltDate='11/12/2026', ResumptionDate='11/13/2026',
                              ResumptionQuoteTime='09:30:00', ResumptionTradeTime='09:35:00'),
                      kind='resumedate', day='11132026')
        empty = receipt(feed(), at='2026-11-14T19:05:00Z', kind='haltdate', day='11132026')
        result = review(old, empty)
        self.assertEqual(result['status'], 'POSSIBLE_CARRY_IN_NOT_VERIFIED')
        self.assertEqual(result['matches'][0]['scheduled_trade_resume_utc'], '2026-11-13T14:35:00Z')
        self.assertEqual(result['receipts'][1]['status'], 'PARSED_EMPTY_NOT_CLEAR')
        self.assertFalse(result['carry_in_baseline_verified'])
        self.assertFalse(result['actual_trade_resumption_verified'])
        self.assertFalse(result['execution_authorized'])
        self.assertIsNone(result['ordinary_close'])

    def test_cutoff_hash_xml_and_query_mismatch_are_distinct(self):
        live = fixture()
        late = receipt(live, at='2026-11-14T20:00:01Z')
        mismatch = receipt(live, kind='haltdate', day='11142026')
        invalid = {**receipt(live), 'raw': feed()}
        result = review(late, mismatch, invalid, receipt(b'<rss>'), receipt(feed()))
        self.assertEqual(result['status'], 'NO_MATCH_COVERAGE_UNKNOWN')
        self.assertEqual(result['matches'], [])
        self.assertEqual([r['status'] for r in result['receipts']], ['AFTER_CUTOFF',
                         'PARTIAL_OR_INVALID_ROWS', 'INVALID_RECEIPT_OR_RESPONSE',
                         'INVALID_RECEIPT_OR_RESPONSE', 'PARSED_EMPTY_NOT_CLEAR'])
        self.assertEqual(result['receipts'][1]['invalid_rows'], 1)

    def test_duplicate_receipt_and_rows_do_not_hide_distinct_revision(self):
        base_raw = fixture()
        part = base_raw.split(b'<channel>')[1].split(b'</channel>')[0]
        duplicated = base_raw.replace(b'</channel>', part + b'</channel>')
        a = receipt(duplicated)
        b = receipt(fixture(ReasonCode='T2'), at='2026-11-14T20:00:00Z')
        result = review(a, a, b)
        self.assertEqual([row['reason_code'] for row in result['matches']], ['T1', 'T2'])
        self.assertEqual([row['receipt_index'] for row in result['matches']], [0, 2])
        self.assertEqual(result['receipts'][1]['status'], 'DUPLICATE_RECEIPT')
        self.assertEqual(result['receipts'][2]['sha256'], b['sha256'])
        self.assertNotIn('source_fields', result['matches'][0])

    def test_only_absence_is_unknown_even_when_no_input(self):
        result = review()
        self.assertEqual(result['status'], 'NO_MATCH_COVERAGE_UNKNOWN')
        self.assertFalse(result['complete'])
        self.assertIsNone(result['ordinary_close'])

    def test_out_of_range_eastern_date_does_not_discard_valid_sibling(self):
        result = review(receipt(fixture(HaltDate='12/31/9999', HaltTime='23:59:59')),
                        receipt(fixture()))
        self.assertEqual(result['receipts'][0]['status'], 'INVALID_RECEIPT_OR_RESPONSE')
        self.assertEqual(result['status'], 'REPORTED_START_IN_WINDOW')
        self.assertEqual(result['matches'][0]['receipt_index'], 1)
        self.assertFalse(result['complete'])

    def test_invalid_window_and_aggregate_resource_bounds(self):
        with self.assertRaisesRegex(ValueError, 'completed nonempty'):
            review(end_utc='2026-11-14T20:00:01Z')
        with self.assertRaisesRegex(ValueError, 'bounded receipt'):
            review(*([receipt(feed())] * 25))
        with self.assertRaisesRegex(ValueError, 'byte cap'):
            review(*([receipt(b' ' * 1_400_000)] * 3))
