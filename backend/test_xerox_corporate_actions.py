from dataclasses import replace
from fractions import Fraction
import unittest

from xerox_corporate_actions import HOLDINGS_NASDAQ, HOLDINGS_NYSE, LEGACY, review


class XeroxActions(unittest.TestCase):
    def test_one_for_one_changes_legal_issuer_without_price_join(self):
        result = review('2019-07-31', LEGACY, HOLDINGS_NYSE)
        action = result['action']
        self.assertEqual(result['status'], 'SUCCESSOR_COMMON_CONVERSION')
        self.assertEqual((action.before.issuer_cik, action.after.issuer_cik),
                         ('0000108772', '0001770450'))
        self.assertEqual(action.successor_shares_per_old_share, Fraction(1))
        self.assertIsNone(action.nasdaq_transfer_cusip)
        self.assert_unqualified(result)

    def test_exchange_transfer_preserves_issuer_and_class_but_changes_feed(self):
        result = review('2021-09-21', HOLDINGS_NYSE, HOLDINGS_NASDAQ)
        action = result['action']
        self.assertEqual(result['status'], 'SAME_COMMON_LISTING_TRANSFER')
        self.assertEqual(action.before.issuer_cik, action.after.issuer_cik)
        self.assertEqual(action.before.share_class, action.after.share_class)
        self.assertNotEqual(action.before.venue, action.after.venue)
        self.assertEqual(action.nasdaq_transfer_cusip, '98421M106')
        self.assertIs(action.consolidated_feed_changed, True)
        self.assertIsNone(action.successor_shares_per_old_share)
        self.assert_unqualified(result)

    def test_day_venue_issuer_class_and_direction_must_match(self):
        for day, before, after in (
            ('2019-08-01', LEGACY, HOLDINGS_NYSE),
            ('2019-07-31', HOLDINGS_NYSE, LEGACY),
            ('2019-07-31', LEGACY, HOLDINGS_NASDAQ),
            ('2019-07-31', replace(LEGACY, share_class='preferred'), HOLDINGS_NYSE),
            ('2019-07-31', replace(LEGACY, symbol='xrx'), HOLDINGS_NYSE),
            ('2021-09-21', LEGACY, HOLDINGS_NASDAQ),
            ('2021-09-20', HOLDINGS_NYSE, HOLDINGS_NASDAQ),
        ):
            with self.subTest(day=day, before=before, after=after):
                result = review(day, before, after)
                self.assertEqual(result['status'], 'UNVERIFIED_ACTION')
                self.assertIsNone(result['action'])
                self.assert_unqualified(result)

    def test_wrong_types_or_noncanonical_dates_rejected(self):
        for day, before in (('20210921', HOLDINGS_NYSE),
                            ('2021-02-29', HOLDINGS_NYSE),
                            ('2021-09-21', 'XRX'),
                            ('2021-09-21', replace(HOLDINGS_NYSE, issuer_cik=[]))):
            with self.subTest(day=day, before=before), self.assertRaises(ValueError):
                review(day, before, HOLDINGS_NASDAQ)

    def assert_unqualified(self, result):
        for key in ('provider_join_verified', 'listing_continuity_verified',
                    'eligible_prices_verified', 'outcome_qualified'):
            self.assertIs(result[key], False)
