"""Consistency checks for a non-activated research plan, not trial execution."""
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]

class ProtocolTests(unittest.TestCase):
    def setUp(self):
        self.plan = json.loads((ROOT/'research/prospective-cohort-v1.json').read_text())
    def test_no_activation_or_trading(self):
        p=self.plan
        self.assertEqual(p['status'], 'DRAFT_NOT_ACTIVATED')
        self.assertIsNone(p['activation_receipt'])
        for key in ('execution_or_portfolio_claims','model_training_enabled','paper_or_real_orders_enabled','provider_calls_enabled','historical_backfill_eligible'):
            self.assertIs(p[key], False)
    def test_existing_bounded_universe(self):
        self.assertEqual(self.plan['universe'], json.loads((ROOT/'data/watchlist.json').read_text()))
        self.assertEqual(len({r['cik'] for r in self.plan['universe']}),10)
        self.assertEqual(self.plan['forms'], ['8-K','8-K/A'])
    def test_retains_cases_and_fixed_horizons(self):
        self.assertTrue(self.plan['include_all_observed_candidates'])
        self.assertTrue(self.plan['losses_retained'])
        self.assertEqual(self.plan['horizons_sessions'],[1,5])
        self.assertEqual(self.plan['primary_outcome'],'five_session_total_return_minus_SPY_same_window')
        for required in ('corporate_action_coverage','benchmark_same_window','halt_and_missing_close_review'):
            self.assertIn(required,self.plan['label_requirements'])

if __name__ == '__main__':
    unittest.main()
