"""Synthetic-only top-of-book fill preview over the existing pure lifecycle.

No market, real or V2 account, IO, order placement, or liquidity guarantee.
The caller supplies hypothetical clocks, quote sizes and halt observations;
they do not authenticate sessions, external data or actual tradability.
A preview is not a reservation or a commit. Use committed lifecycle replay
before a new preview, and resolve identical command retries before re-preview.
"""
from dataclasses import dataclass
import json

import synthetic_paper as paper

MAX_QUOTE_AGE_SECONDS = 2
FEE_PER_SHARE_UNITS = 10_000  # Illustrative 0.01 synthetic currency/share.


class FillRefused(ValueError):
    def __init__(self, code):
        self.code = code
        super().__init__(code)


@dataclass(frozen=True)
class Quote:
    instrument_id: str
    session_id: str
    quote_at: str
    observed_at: str
    bid_units: int
    ask_units: int
    bid_size: int
    ask_size: int
    halt_state: str
    halt_observed_at: str | None


def preview_fill(journal, *, order_id, event_id, fill_at, quote):
    """Return one validated synthetic FILL event; do not append or mutate.

    Long-only inventory and cash reservations are checked by lifecycle replay.
    Whole-share quantity is min(open remainder, hypothetical opposite-side
    size); there is no queue, hidden liquidity or depth beyond that level.
    Buy at ask, sell at bid. Fees are in the existing millionth units and
    cannot exceed the order's remaining fee cap. No fee-driven resizing.
    Strict quote time after the latest committed journal event disallows
    reusing an already modeled book level after a committed fill.
    """
    try:
        paper.identifier(order_id)
        paper.identifier(event_id)
        fill_time = paper.instant(fill_at)
    except (ValueError, TypeError) as error:
        raise FillRefused("MALFORMED_REQUEST") from error
    try:
        state = paper.replay(journal)
        last_time = paper.instant(json.loads(journal[-1])["event"]["at"])
    except (ValueError, TypeError, KeyError) as error:
        raise FillRefused("INVALID_JOURNAL") from error
    order = state["orders"].get(order_id)
    if state["killed"] or order is None or order["status"] not in paper.ACTIVE:
        raise FillRefused("ORDER_NOT_ACTIVE")
    if quote is None:
        raise FillRefused("MISSING_QUOTE")
    if type(quote) is not Quote:
        raise FillRefused("MALFORMED_QUOTE")
    try:
        paper.identifier(quote.instrument_id)
        paper.identifier(quote.session_id)
        quote_time = paper.instant(quote.quote_at)
        observed = paper.instant(quote.observed_at)
        bid = paper.integer(quote.bid_units, 1)
        ask = paper.integer(quote.ask_units, 1)
        bid_size = paper.integer(quote.bid_size)
        ask_size = paper.integer(quote.ask_size)
    except (ValueError, TypeError) as error:
        raise FillRefused("MALFORMED_QUOTE") from error
    if (quote.instrument_id, quote.session_id) != (order["instrument_id"], order["session_id"]):
        raise FillRefused("QUOTE_SCOPE_MISMATCH")
    if not last_time < quote_time <= observed <= fill_time:
        raise FillRefused("QUOTE_CLOCK_ORDER")
    if (fill_time - quote_time).total_seconds() > MAX_QUOTE_AGE_SECONDS:
        raise FillRefused("STALE_QUOTE")
    if type(quote.halt_state) is not str or quote.halt_state != "TRADABLE" or quote.halt_observed_at is None:
        raise FillRefused("TRADABILITY_NOT_CONFIRMED")
    try:
        halt_time = paper.instant(quote.halt_observed_at)
    except (ValueError, TypeError) as error:
        raise FillRefused("TRADABILITY_NOT_CONFIRMED") from error
    if not observed <= halt_time <= fill_time:
        raise FillRefused("TRADABILITY_CLOCK_ORDER")
    if bid > ask:
        raise FillRefused("CROSSED_QUOTE")

    buy = order["side"] == "BUY"
    price, depth = (ask, ask_size) if buy else (bid, bid_size)
    if (buy and price > order["limit_units"]) or (not buy and price < order["limit_units"]):
        raise FillRefused("LIMIT_NOT_CROSSING")
    if depth == 0:
        raise FillRefused("NO_OPPOSITE_SIZE")
    quantity = min(order["remaining"], depth)
    fee = quantity * FEE_PER_SHARE_UNITS
    if fee > order["fee_cap_units"] - order["fees_used_units"] or (not buy and fee > quantity * price):
        raise FillRefused("FEE_NOT_COVERED")
    event = {"kind": "FILL", "at": fill_at, "event_id": event_id, "order_id": order_id,
             "session_id": quote.session_id, "quantity": quantity,
             "price_units": price, "fee_units": fee}
    try:
        paper.append(journal, event)  # Validate against exact reducer, discard hypothetical journal.
    except (ValueError, TypeError) as error:
        raise FillRefused("LIFECYCLE_REFUSED") from error
    return event
