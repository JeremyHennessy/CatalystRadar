import unittest
from tjgc_corporate_action_fixture import fixture, review_window


class CorporateActionFixtureTests(unittest.TestCase):
    def query(self, start, end, cik='0001969928'):
        return review_window(issuer_cik=cik, start_date=start, end_date=end)

    def test_split_day_and_spanning_window(self):
        for start, end in [('2026-05-26', '2026-05-26'), ('2026-05-25', '2026-05-27'),
                           ('2026-05-26', '2026-05-27'), ('2026-05-25', '2026-05-26')]:
            r = self.query(start, end)
            self.assertEqual(r['status'], 'ISSUER_DATE_REVIEW_REQUIRED')
            e = r['matched_events'][0]
            self.assertEqual(e['share_ratio'], {'old_shares': 3, 'new_shares': 1})
            self.assertEqual(e['post_split_cusip_as_reported'], 'G2588N116')
            self.assertFalse(e['symbol_change_announced'])

    def test_redesignation_separate_not_a_second_split(self):
        e = self.query('2026-08-12', '2026-08-12')['matched_events'][0]
        self.assertEqual(e['type'], 'SHARE_REDESIGNATION')
        self.assertIsNone(e['share_ratio'])
        self.assertEqual(len(self.query('2026-05-01', '2026-09-01')['matched_events']), 2)

    def test_no_match_is_unknown_never_cleared(self):
        for start, end, cik in [('2026-05-25', '2026-05-25', '0001969928'),
                                ('2026-05-27', '2026-08-11', '0001969928'),
                                ('2026-08-13', '2026-11-19', '0001969928'),
                                ('2026-05-01', '2026-09-01', '0001969929')]:
            r = self.query(start, end, cik)
            self.assertEqual(r['status'], 'UNKNOWN')
            self.assertEqual(r['matched_events'], [])

    def test_never_adjust_or_admit_any_query(self):
        for start, end in [('2026-05-01', '2026-09-01'), ('2026-11-19', '2026-11-19')]:
            r = self.query(start, end)
            for k in ('same_share_class_verified', 'known_at_window_time_verified',
                      'complete_corporate_action_coverage', 'training_ready', 'execution_ready'):
                self.assertIs(r[k], False)
            self.assertIsNone(r['vendor_adjustment_factor'])
            self.assertIsNone(r['adjusted_return'])

    def test_rounding_and_presentation_not_vendor_math(self):
        f = fixture()
        e = f['events'][0]
        self.assertEqual(e['nominal_post_split_issued_shares'], 10100000)
        self.assertEqual(e['later_reported_post_rounding_issued_shares'], 10100023)
        self.assertIn('do not adjust twice', f['financial_presentation'])
        self.assertIn('no trade on May 26 inferred', f['halt_context'])
        for k in ('source_bytes_sha256', 'first_public_utc', 'historical_observation_utc'):
            self.assertIsNone(f[k])

    def test_copy_isolation(self):
        fixture()['events'][0]['share_ratio']['old_shares'] = 99
        self.query('2026-05-26', '2026-05-26')['matched_events'][0]['share_ratio']['old_shares'] = 88
        self.assertEqual(fixture()['events'][0]['share_ratio']['old_shares'], 3)

    def test_invalid_dates_and_identity(self):
        for d in ('2026-02-30', '20260526', '2026-05-26T00:00:00Z', None, '２０２６-05-26'):
            with self.assertRaises(ValueError):
                self.query(d, '2026-09-01')
        with self.assertRaises(ValueError):
            self.query('2026-09-01', '2026-05-01')
        for cik in (1969928, '1969928', 'TJGC', None, '０００１９６９９２８'):
            with self.assertRaises(ValueError):
                self.query('2026-05-01', '2026-09-01', cik)


if __name__ == '__main__':
    unittest.main()
