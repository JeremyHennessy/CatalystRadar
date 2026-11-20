"""Quote-derived synthetic partial fill under an actual process interruption.

Uses the disposable SQLite test fixture. Not a production order store, broker,
provider, source validation or Paper V2 activation path.
"""
from dataclasses import replace
import json
import multiprocessing as mp
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

import synthetic_paper as ledger
from synthetic_quote_fill import FillRefused, Quote, preview_fill
from test_synthetic_restart import JournalFixture


def _preview_and_commit_without_ack(path, prior, request):
    event = preview_fill(prior, **request)
    JournalFixture(path).submit(prior, event)
    os._exit(23)


class SyntheticQuoteRetryTests(unittest.TestCase):
    def test_refusals_leave_no_events_then_size_limited_fill_survives_lost_ack(self):
        with TemporaryDirectory() as folder:
            path = str(Path(folder) / "fixture.sqlite")
            store = JournalFixture(path)
            start = "2030-01-02T14:30:00Z"
            prior = store.submit((), {"kind": "INIT", "event_id": "SYNTH_INIT",
                                      "at": start, "cash_units": 500_000_000})
            prior = store.submit(prior, {
                "kind": "INTENT", "event_id": "SYNTH_INTENT", "at": start,
                "order_id": "SYNTH_ORDER", "candidate_id": "SYNTH_CASE",
                "instrument_id": "SYNTH_ASSET", "side": "BUY", "quantity": 10,
                "limit_units": 9_500_000, "fee_cap_units": 100_000,
                "decision_at": start, "session_id": "SYNTH_REGULAR"})
            quote = Quote(
                instrument_id="SYNTH_ASSET", session_id="SYNTH_REGULAR",
                quote_at="2030-01-02T14:30:01Z", observed_at="2030-01-02T14:30:02Z",
                bid_units=8_900_000, ask_units=9_000_000, bid_size=8, ask_size=4,
                halt_state="TRADABLE", halt_observed_at="2030-01-02T14:30:02Z")
            req = {"order_id": "SYNTH_ORDER", "event_id": "SYNTH_FILL",
                   "fill_at": "2030-01-02T14:30:03Z", "quote": quote}

            for bad in (None, replace(quote, halt_state="HALTED"),
                        replace(quote, halt_state="UNKNOWN"),
                        replace(quote, ask_size=0)):
                with self.subTest(quote=bad):
                    with self.assertRaises(FillRefused):
                        preview_fill(prior, **{**req, "quote": bad})
                    self.assertEqual(JournalFixture(path).restart(), prior)
            with self.assertRaises(FillRefused):
                preview_fill(prior, **{**req, "fill_at": "2030-01-02T14:30:08Z"})
            self.assertEqual(JournalFixture(path).restart(), prior)

            child = mp.get_context("spawn").Process(
                target=_preview_and_commit_without_ack, args=(path, prior, req))
            try:
                child.start()
                child.join(15)
                self.assertEqual(child.exitcode, 23)
            finally:
                if child.is_alive():
                    child.terminate()
                    child.join(5)
            reopened = JournalFixture(path)
            committed = reopened.restart()
            event = preview_fill(prior, **req)  # exact original prefix/quote/clock
            self.assertEqual(json.loads(committed[-1])["event"], event)
            self.assertEqual(event["quantity"], 4)
            self.assertEqual(event["fee_units"], 40_000)
            for _ in range(2):
                self.assertEqual(reopened.submit(prior, event), committed)
            self.assertEqual(len(reopened.restart()), 3)

            # A different decision from the old prefix is not a retry.
            altered = preview_fill(prior, **{**req, "quote": replace(quote, ask_size=3)})
            with self.assertRaisesRegex(ValueError, "competing event"):
                reopened.submit(prior, altered)
            # A new event cannot recycle the already-consumed old observation.
            with self.assertRaises(FillRefused):
                preview_fill(committed, **{**req, "event_id": "SYNTH_REUSE"})
            self.assertEqual(reopened.restart(), committed)

            state = ledger.replay(committed)
            self.assertEqual(state["orders"]["SYNTH_ORDER"]["remaining"], 6)
            self.assertEqual(state["positions"]["SYNTH_ASSET"], {
                "quantity": 4, "cost_units": 36_040_000})
            self.assertEqual(state["cash_units"], 463_960_000)
            self.assertEqual(state["fees_units"], 40_000)
            self.assertEqual(ledger.reservations(state), 57_060_000)
