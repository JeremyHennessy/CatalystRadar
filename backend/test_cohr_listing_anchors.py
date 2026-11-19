import unittest

from cohr_listing_anchors import compare, lookup


class ListingAnchors(unittest.TestCase):
    def test_same_symbol_and_venue_do_not_identify_same_issuer(self):
        self.assertEqual(compare(('2022-06-30', 'COHR', 'NASDAQ'),
                                 ('2022-09-08', 'COHR', 'NASDAQ'))['status'],
                         'DIFFERENT_ISSUER')
        self.assertEqual(lookup('2022-06-30', 'COHR', 'NASDAQ')['cusip_as_reported'],
                         '192479103')
        self.assertEqual(lookup('2022-09-08', 'COHR', 'NASDAQ')['cusip_as_reported'],
                         '19247G107')

    def test_same_issuer_and_symbol_do_not_identify_same_share_class(self):
        x = compare(('2022-07-01', 'IIVI', 'NASDAQ'), ('2023-02-23', 'IIVI', 'NYSE'))
        self.assertEqual(x['first']['issuer_cik'], x['second']['issuer_cik'])
        self.assertEqual(x['status'], 'DIFFERENT_SHARE_CLASS')

    def test_transfer_connects_dated_anchors_not_continuity_or_price(self):
        x = compare(('2022-09-08', 'COHR', 'NASDAQ'), ('2023-02-23', 'COHR', 'NYSE'))
        self.assertEqual(x['status'], 'SAME_ISSUER_CLASS_AT_ANCHORS_ONLY')
        self.assertFalse(x['listing_continuity_verified'])
        self.assertFalse(x['provider_join_verified'])
        self.assertFalse(x['outcome_qualified'])
        self.assertIsNone(x['second']['cusip_as_reported'])

    def test_unknown_date_venue_or_gap_does_not_fall_back_to_symbol(self):
        for key in (('2022-07-01', 'COHR', 'NASDAQ'), ('2022-09-07', 'COHR', 'NASDAQ'),
                    ('2023-02-23', 'COHR', 'NASDAQ'), ('2026-11-20', 'COHR', 'NYSE')):
            self.assertIsNone(lookup(*key)['issuer_cik'])
            self.assertEqual(compare(key, ('2022-06-30', 'COHR', 'NASDAQ'))['status'],
                             'UNVERIFIED_ANCHOR')

    def test_dates_are_canonical(self):
        for bad in ('20220908', '2022-02-30', None):
            with self.assertRaises(ValueError):
                lookup(bad, 'COHR', 'NASDAQ')
