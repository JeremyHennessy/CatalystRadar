import unittest

from txmd_corporate_action import CIK, review_window, illustrative_whole_shares


class TxmdCorporateActionTest(unittest.TestCase):
    def query(self, start, end, cik=CIK, share_class='common'):
        return review_window(issuer_cik=cik, share_class=share_class, start_date=start, end_date=end)

    def test_legal_and_market_effective_dates_distinct(self):
        for start, end in [('2022-05-06', '2022-05-06'), ('2022-05-07', '2022-05-08'),
                           ('2022-05-09', '2022-05-09'), ('2022-04-01', '2022-05-10')]:
            result = self.query(start, end)
            self.assertEqual(result['status'], 'DOCUMENTED_ACTION_REVIEW_REQUIRED')
            event = result['action']
            self.assertEqual(event['issuer_reported_legal_effective_utc'], '2022-05-06T21:01:00Z')
            self.assertEqual(event['exchange_effective_date'], '2022-05-09')
            self.assertEqual(event['exchange_post_split_cusip'], '88338N206')
            self.assertEqual((event['old_shares'], event['new_shares']), (50, 1))
            self.assertEqual(len(event['sources']), 3)
            for field in ('first_public_utc', 'provider_adjustment_factor', 'adjusted_return'):
                self.assertIsNone(result[field])
            for field in ('provider_security_mapping_verified', 'outcome_qualified', 'execution_ready'):
                self.assertIs(result[field], False)

    def test_unmatched_is_unknown_not_action_free(self):
        for args in [('2022-05-01', '2022-05-05'), ('2022-05-10', '2022-05-10'),
                     ('2026-11-13', '2026-11-17'), ('2022-05-06', '2022-05-09', '0000000001'),
                     ('2022-05-06', '2022-05-09', CIK, 'preferred')]:
            result = self.query(*args)
            self.assertEqual(result['status'], 'UNKNOWN')
            self.assertIsNone(result['action'])

    def test_reject_invalid_range_or_identity(self):
        for args in [('2022-05-09', '2022-05-06'), ('2022-5-06', '2022-05-09'),
                     ('2022-05-06', '2022-05-09', 'TXMD'), ('2022-05-06', '2022-05-09', CIK, None)]:
            with self.assertRaises(ValueError):
                self.query(*args)

    def test_round_up_aggregate_not_each_lot(self):
        self.assertEqual([illustrative_whole_shares(n) for n in (0, 1, 49, 50, 51, 100, 101)],
                         [0, 1, 1, 1, 2, 2, 3])
        self.assertEqual(illustrative_whole_shares(20 + 30), 1)
        for value in (True, -1, 0.5, '50'):
            with self.assertRaises(ValueError):
                illustrative_whole_shares(value)
