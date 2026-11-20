"""Pure illustrative fixtures; no market data or private/legacy account."""
from dataclasses import replace
import unittest

import synthetic_paper as paper
from synthetic_quote_fill import Quote, preview_fill, FillRefused


def utc(second):
    return f"2031-01-02T14:30:{second:02d}Z"


def intent(at, side="BUY", quantity=6, limit=10_000_000, fee_cap=100_000):
    return {"kind": "INTENT", "at": at, "decision_at": at, "event_id": f"SYNTH_INTENT_{side}",
            "order_id": f"SYNTH_ORDER_{side}", "session_id": "SYNTH_REGULAR",
            "instrument_id": "SYNTH_INSTRUMENT", "candidate_id": "SYNTH_CANDIDATE",
            "side": side, "quantity": quantity, "limit_units": limit, "fee_cap_units": fee_cap}


class SyntheticQuoteFillTests(unittest.TestCase):
    def setUp(self):
        self.journal = paper.append((), {
            "kind": "INIT", "at": utc(0), "event_id": "SYNTH_INIT", "cash_units": 500_000_000,
        })
        self.opened = paper.append(self.journal, intent(utc(1)))
        self.quote = Quote("SYNTH_INSTRUMENT", "SYNTH_REGULAR", utc(2), utc(3),
                           9_800_000, 9_900_000, 99, 4, "TRADABLE", utc(3))

    def preview(self, **changes):
        opened = changes.pop("journal", self.opened)
        return preview_fill(opened, **(dict(order_id="SYNTH_ORDER_BUY",
                            event_id="SYNTH_FILL_1", fill_at=utc(4), quote=self.quote) | changes))

    def refusal(self, code, **changes):
        with self.assertRaises(FillRefused) as error:
            self.preview(**changes)
        self.assertEqual(error.exception.code, code)

    def test_buy_ask_size_fee_and_remaining_then_fresh_quote(self):
        start = self.opened
        event = self.preview()
        self.assertEqual((event["quantity"], event["price_units"], event["fee_units"]),
                         (4, self.quote.ask_units, 40_000))
        self.assertEqual(self.opened, start)
        self.assertEqual(paper.replay(self.opened)["positions"], {})
        committed = paper.append(self.opened, event)
        self.assertEqual(paper.replay(committed)["orders"]["SYNTH_ORDER_BUY"]["remaining"], 2)
        self.refusal("QUOTE_CLOCK_ORDER", journal=committed, event_id="SYNTH_FILL_2")
        update = replace(self.quote, quote_at=utc(5), observed_at=utc(5), halt_observed_at=utc(5),
                         ask_size=50)
        next_event = self.preview(journal=committed, quote=update, fill_at=utc(6),
                                  event_id="SYNTH_FILL_2")
        self.assertEqual((next_event["quantity"], next_event["fee_units"]), (2, 20_000))
        state = paper.replay(paper.append(committed, next_event))
        self.assertEqual(state["positions"]["SYNTH_INSTRUMENT"]["quantity"], 6)
        self.assertEqual(state["orders"]["SYNTH_ORDER_BUY"]["status"], "FILLED")
        self.assertEqual(state["cash_units"], 440_540_000)

    def test_sell_uses_bid_not_ask_and_caps_by_bid_size(self):
        committed = paper.append(self.opened, self.preview())
        sold = paper.append(committed, intent(utc(5), "SELL", quantity=4, limit=9_800_000))
        q = replace(self.quote, quote_at=utc(6), observed_at=utc(6),
                    halt_observed_at=utc(6), bid_size=1, ask_size=100)
        event = self.preview(journal=sold, order_id="SYNTH_ORDER_SELL", event_id="SYNTH_SELL_FILL",
                             quote=q, fill_at=utc(7))
        self.assertEqual((event["quantity"], event["price_units"], event["fee_units"]),
                         (1, q.bid_units, 10_000))
        self.refusal("LIMIT_NOT_CROSSING", journal=sold, order_id="SYNTH_ORDER_SELL",
                     quote=replace(q, bid_units=9_799_999), fill_at=utc(7))

    def test_quote_clocks_and_missing(self):
        self.refusal("MISSING_QUOTE", quote=None)
        self.refusal("STALE_QUOTE", fill_at=utc(5))
        for changes in (dict(quote_at=utc(1)), dict(quote_at=utc(4), observed_at=utc(3)),
                        dict(quote_at=utc(5), observed_at=utc(5)), dict(observed_at=utc(5))):
            self.refusal("QUOTE_CLOCK_ORDER", quote=replace(self.quote, **changes))

    def test_halt_state_missing_stale_or_future(self):
        for state in ("HALTED", "UNKNOWN", "", True):
            self.refusal("TRADABILITY_NOT_CONFIRMED", quote=replace(self.quote, halt_state=state))
        self.refusal("TRADABILITY_NOT_CONFIRMED", quote=replace(self.quote, halt_observed_at=None))
        for clock in (utc(2), utc(5)):
            self.refusal("TRADABILITY_CLOCK_ORDER", quote=replace(self.quote, halt_observed_at=clock))

    def test_limit_size_input_scope_and_fees(self):
        self.refusal("LIMIT_NOT_CROSSING", quote=replace(self.quote, ask_units=10_000_001))
        self.refusal("NO_OPPOSITE_SIZE", quote=replace(self.quote, ask_size=0))
        self.refusal("CROSSED_QUOTE", quote=replace(self.quote, bid_units=10_000_000))
        for changes in (dict(bid_size=-1), dict(ask_size=True), dict(ask_units=9.9),
                        dict(bid_units=0), dict(instrument_id="COHR")):
            self.refusal("MALFORMED_QUOTE", quote=replace(self.quote, **changes))
        for changes in (dict(instrument_id="SYNTH_OTHER"), dict(session_id="SYNTH_OTHER")):
            self.refusal("QUOTE_SCOPE_MISMATCH", quote=replace(self.quote, **changes))
        self.refusal("FEE_NOT_COVERED",
                     journal=paper.append(self.journal, intent(utc(1), fee_cap=39_999)))

    def test_terminal_kill_invalid_journal_and_duplicate_event(self):
        self.refusal("INVALID_JOURNAL", journal=("{}",))
        self.refusal("ORDER_NOT_ACTIVE", order_id="SYNTH_ABSENT")
        self.refusal("MALFORMED_REQUEST", event_id="NOT_SYNTH")
        self.refusal("LIFECYCLE_REFUSED", event_id="SYNTH_INIT")
        killed = paper.append(self.opened, {"kind": "KILL", "at": utc(2), "event_id": "SYNTH_KILL"})
        self.refusal("ORDER_NOT_ACTIVE", journal=killed)
        cancelled = paper.append(self.opened, {"kind": "CANCEL", "at": utc(2),
                                 "event_id": "SYNTH_CANCEL", "order_id": "SYNTH_ORDER_BUY"})
        self.refusal("ORDER_NOT_ACTIVE", journal=cancelled)
