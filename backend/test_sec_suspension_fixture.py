import unittest
from sec_suspension_fixture import fixture, historical_order_match


class SuspensionFixtureTests(unittest.TestCase):
    def query(self, instant, cik='0001969928'):
        return historical_order_match(issuer_cik=cik, instant=instant)

    def test_multiple_dates_and_weekend_are_interval_not_calendar(self):
        for day in (15, 16, 17, 19, 26, 28):
            with self.subTest(day=day):
                r = self.query(f'2026-10-{day:02}T12:00:00-04:00')
                self.assertIs(r['positive_order_match'], True)
                self.assertFalse(r['execution_eligible'])
                self.assertFalse(r['historical_knowledge_verified'])

    def test_both_boundary_minutes_unknown(self):
        for at in ('2026-10-15T04:00:00-04:00', '2026-10-15T04:00:59.999999-04:00',
                   '2026-10-28T23:59:00-04:00', '2026-10-28T23:59:59.999999-04:00'):
            r = self.query(at)
            self.assertEqual(r['reason'], 'MINUTE_PRECISION_BOUNDARY_UNKNOWN')
            self.assertIsNone(r['positive_order_match'])

    def test_adjacent_interior(self):
        for at in ('2026-10-15T08:01:00Z', '2026-10-29T03:58:59.999999Z'):
            self.assertIs(self.query(at)['positive_order_match'], True)

    def test_outside_is_never_clearance(self):
        for at in ('2026-10-15T07:59:59Z', '2026-10-29T04:00:00Z', '2026-11-19T12:00:00Z'):
            r = self.query(at)
            self.assertEqual(r['status'], 'UNKNOWN')
            self.assertIsNone(r['positive_order_match'])
            self.assertIsNone(r['resumption_utc'])
            self.assertIsNone(r['current_trading_status'])
            self.assertFalse(r['complete_halt_coverage'])

    def test_exact_identity(self):
        self.assertIsNone(self.query('2026-10-20T12:00:00Z', '0001969929')['positive_order_match'])
        for cik in ('TJGC', '1969928', 1969928, None, True, '0001969928 '):
            with self.assertRaises(ValueError):
                self.query('2026-10-20T12:00:00Z', cik)

    def test_equivalent_timezone(self):
        self.assertEqual(self.query('2026-10-20T12:00:00Z'), self.query('2026-10-20T08:00:00-04:00'))

    def test_reject_ambiguous_or_invalid_query(self):
        for at in (None, 1, '2026-10-20', '2026-10-20T12:00:00', '2026-10-20T12:00Z',
                   '2026-02-30T12:00:00Z', '2026-10-20T12:00:00Zjunk'):
            with self.assertRaises(ValueError):
                self.query(at)

    def test_offset_components_reject_normalization(self):
        for offset in ('+00:99', '-00:99', '+01:60', '-04:60', '+24:00', '-24:00', '+99:00'):
            with self.subTest(offset=offset), self.assertRaises(ValueError):
                self.query('2026-10-20T12:00:00' + offset)
        for at in ('２０２６-10-20T12:00:00Z', '2026-10-20T12:00:00+００:00'):
            with self.assertRaises(ValueError):
                self.query(at)
        with self.assertRaises(ValueError):
            self.query('2026-10-20T12:00:00Z', '０００１９６９９２８')
        # Valid fractional-hour offsets still work without inventing clearance.
        self.assertEqual(self.query('2026-10-20T08:30:00-03:30'),
                         self.query('2026-10-20T12:00:00Z'))
        self.assertIsNone(self.query('2026-10-29T00:30:00-03:30')['positive_order_match'])

    def test_fixture_unknowns_and_independent_copy(self):
        f = fixture()
        for key in ('initial_listing_date', 'first_public_utc', 'historical_observation_utc',
                    'resumption_utc', 'current_trading_status', 'source_pdf_sha256'):
            self.assertIsNone(f[key])
        self.assertEqual(f['listing_as_of']['date'], '2026-10-14')
        f['listing_as_of']['symbol'] = 'WRONG'
        f['source_urls'].clear()
        self.assertEqual(fixture()['listing_as_of']['symbol'], 'TJGC')
        self.assertEqual(len(fixture()['source_urls']), 2)


if __name__ == '__main__':
    unittest.main()
