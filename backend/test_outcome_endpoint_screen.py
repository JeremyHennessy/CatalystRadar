from pathlib import Path
import tempfile
import unittest

from outcome_endpoint_screen import coherent_pinned, screen

OLD = ('2022-06-30', 'COHR', 'NASDAQ')
ACQUIRER = ('2022-09-08', 'COHR', 'NASDAQ')
NYSE = ('2023-02-23', 'COHR', 'NYSE')


class OutcomeEndpointScreenTests(unittest.TestCase):
    def test_union_across_two_series_cannot_pass_same_series_coverage(self):
        x = screen(ACQUIRER, NYSE, (frozenset({ACQUIRER[0]}), frozenset({NYSE[0]})))
        self.assertEqual(x['missing_from_all_series'], [])
        self.assertEqual(x['date_pair_series_count'], 0)
        self.assertEqual(x['screen_rejections'], ['ENDPOINTS_NEVER_COOCCUR_IN_ONE_AUDITED_SERIES'])

    def test_both_dates_present_cannot_override_wrong_issuer_or_class(self):
        for first, second, reason in (
            (OLD, ACQUIRER, 'DIFFERENT_ISSUER'),
            (('2022-07-01', 'IIVI', 'NASDAQ'), ('2023-02-23', 'IIVI', 'NYSE'),
             'DIFFERENT_SHARE_CLASS'),
        ):
            x = screen(first, second, (frozenset({first[0], second[0]}),))
            self.assertEqual(x['date_pair_series_count'], 1)
            self.assertEqual(x['screen_rejections'], [reason])
            self.assertIsNone(x['return_value'])

    def test_even_consistent_dated_anchors_and_dates_never_qualify(self):
        x = screen(ACQUIRER, NYSE, (frozenset({ACQUIRER[0], NYSE[0]}),))
        self.assertEqual(x['identity_status'], 'SAME_ISSUER_CLASS_AT_ANCHORS_ONLY')
        self.assertEqual(x['screen_rejections'], [])
        for field in ('provider_instrument_verified', 'listing_continuity_verified',
                      'actual_session_verified', 'halt_status_verified', 'corporate_actions_verified',
                      'price_rights_verified', 'qualified', 'execution_ready'):
            self.assertIs(x[field], False)
        self.assertIsNone(x['return_value'])

    def test_frozen_coherent_dates_missing_and_unmapped(self):
        x = coherent_pinned(Path(__file__).resolve().parents[1])
        self.assertEqual(x['endpoint_dates'], ['2026-11-20', '2026-11-23'])
        self.assertEqual(x['missing_from_all_series'], x['endpoint_dates'])
        self.assertEqual(x['audited_series'], 11)
        self.assertEqual(x['date_pair_series_count'], 0)
        self.assertEqual(x['screen_rejections'], ['UNVERIFIED_LISTING_ANCHOR',
                                                 'ENDPOINT_MISSING_FROM_AUDITED_SERIES'])

    def test_bad_pin_shape_dates_and_order_refused(self):
        with self.assertRaises(ValueError):
            screen(None, ACQUIRER, ())
        with self.assertRaises(ValueError):
            screen(NYSE, ACQUIRER, ())
        with self.assertRaises(ValueError):
            screen(ACQUIRER, NYSE, ({ACQUIRER[0], NYSE[0]},))
        with self.assertRaises(ValueError):
            screen(ACQUIRER, NYSE, (frozenset({'20220908'}),))
        with tempfile.TemporaryDirectory() as t:
            p = Path(t) / 'docs/research/price-session-audit-2026-11-17.json'
            p.parent.mkdir(parents=True)
            p.write_text('{}')
            with self.assertRaisesRegex(ValueError, 'pin'):
                coherent_pinned(t)
