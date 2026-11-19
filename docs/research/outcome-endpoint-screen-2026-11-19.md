# Offline outcome endpoint screen

The previous union-of-dates audit provides a weak necessary condition: every
endpoint must occur somewhere. The new research helper also requires that
both candidate endpoints occur in **one supplied anonymous series**. Dates
provided by different series must never be combined to fill a gap. This is
a date-only test; it does not decide which series belongs to a security.

The known COHR ticker collision and IIVI class collision are explicit rejection
tests, even when the supplied dates happen to appear together. Exact listing
anchors for the same class are not evidence of continuity, actions, provider
identity, actual trading, a valid closing price, or data-use rights. Unknown
anchors are not substituted with a ticker match. An empty rejection list does
not confer approval: the helper never returns a qualified outcome or a return.

On the frozen Coherent example, the fixed November 20 and 23, 2026 dates have
**0 of 11** audited series covering both; neither date appears in any audited
series. The dates are also outside the exact 2022–23 listing anchors. The
pinned November 17 date-only audit can reproduce that scope but says nothing
about a later independent source. No raw prices, halt records or new market
data were used. This does not change the November 23 follow-up or the protected
paper ledger.

Run `python3 -m unittest discover -s backend -p test_outcome_endpoint_screen.py`.
