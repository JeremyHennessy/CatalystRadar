# Daily-close proxy study v0.1 (proposed, not activated)

Separate from the disabled auction engine. This is an explicitly idealized research simulation, not a claim an order could be executed at the reported daily close. Original auction protocol and ledger are preserved. Initial cash is hypothetical USD500; no brokerage connection.

## Precommitment
For the Nov16–20,2026 trial, freeze every entry by08:00 America/New_York on the intended session. Use the authoritative execution clock; do not accept backdated caller time. Persist immutable event/source hashes, eligibility review, prior-session data and ordering before observing the target close. No retrospective orders. Monday through Thursday entry, Friday planned liquidation. Each event/issuer is considered once; no replacement of losing or unfilled observations.

The published NYSE2026 calendar and Nasdaq holiday schedule show normal sessions Nov16–20; these planned sessions do not establish absence of an unscheduled closure or a security halt. Runtime exchange-status and corporate-action evidence remain necessary.

## Sizing and modeled price
Five USD100 maximum slots, whole shares only. Freeze quantity using prior raw close times1.03, rounded down to cents, with0.10% fee reservation. Actual modeled buy price is target daily close times1.0025 (25bp adverse slippage), plus0.10% fee. If this exceeds the frozen3% limit or reserved cash, mark unfilled, not partial fill. This is an idealized all-or-none close proxy, NOT a conservative executable-fill guarantee. Exit price is daily close times0.9975 (25bp adverse sell slippage), followed by0.10% fee. No intraday stops inferred from OHLC. Leave unallocated cash unchanged.

Price evidence must be the exact hashed provider response, bound to the selected symbol and target session and retrieved after that session's close. Today's history cannot prove when historical quotes were available. No corporate-action normalization is inferred from raw prices. Exact-price fields and derived returns remain private under provider terms.

## Corporate actions and interruption
Require dated, archived split/dividend/security-identity evidence covering the holding interval. Unknown is unresolved, never 'no action'. Initial supported scope excludes a security with any split, merger, spin-off, symbol change or cash/stock distribution during the interval; affected positions are marked unresolved with no fabricated exit or return. Keep them in the selected-event denominator, including actions first learned after freeze; never drop losing/affected observations. This conservative exclusion is a coverage limitation, not zero return. Future dividend support must separately track ex-date entitlement and unpaid receivables, not treat pay date as entitlement. If status/price evidence is missing or a halt prevents an ordinary close, retain unresolved position and defer exit to the next verified ordinary session with an order frozen before that session. Never erase exposure, force liquidation at a stale price, or invent a loss cap.

## Comparator and evaluation
Primary comparator is the same USD500 non-interest-bearing cash, reported explicitly as cash, not market alpha. Add a separately labelled idealized fractional SPY total-return research comparator only after adjusted/corporate-action evidence is admitted. No five USD100 whole-share SPY sleeves and no implied executable fractional access. Keep fixed-Friday book returns distinct from the independent five-session forecast-study horizon. Report every selected, rejected, unfilled and unresolved event, fees, unallocated cash, source delays and denominator. No win-rate/probability claim from this small pilot.

## Admission and scoring
Source-evidence readiness points only, never jump probability or predicted direction. Every necessary source must be observed and reviewed before freeze. Issuer guidance must match metric, period and accounting basis against archived prior guidance; no analyst 'beat' without point-in-time consensus. Insider P-code purchases exclude amendments/duplicates, grants and automatic plans unless explicitly reviewed. Contract/buyback cues require original binding terms, not keyword matches. No eligibility derived merely from high readiness score.

## Current status
Implementation is a local draft; no orders generated. Eleven private100-row raw daily histories are stored, but corporate-action/security-halt completeness and eligible catalyst reviews are not admitted. Simulation stays disabled until independent review of data bindings and runner, and prospective freezes are operational. Scheduled collector at12:10UTC(07:10ET) Nov16–21 should fetch prior session; actual delayed execution may miss08:00 freeze and must skip rather than backdate. GitHub cron is best-effort, not timing guaranteed.

Sources:
- https://www.nyse.com/publicdocs/nyse/ICE_NYSE_2026_Yearly_Trading_Calendar.pdf
- https://www.nasdaq.com/market-activity/stock-market-holiday-schedule
- https://www.alphavantage.co/documentation/#daily
- https://www.alphavantage.co/documentation/#dailyadj

## Isolated receipt verifier (not activated)
`freeze_receipt.py` verifies an authenticated GitHub REST workflow-run response and exact commit contents. The receipt timestamp is GitHub's run `created_at`, NOT an asserted git author/committer date or precise push time. It bounds existence of the referenced head SHA by run creation. Require first-attempt manual-dispatch receipt workflow on main, exact reviewed workflow blob, exact immutable ledger blob and order hash, and run creation after freeze but by08:00ET. Absence, delay, mismatched ref or unreviewed workflow returns no admission. The deployment must pin the expected workflow hash in reviewed configuration, never accept it from an untrusted candidate.

A commit made with GITHUB_TOKEN normally does not cause a new push workflow. Therefore this design would explicitly dispatch a minimal receipt workflow after committing the freeze. Such dispatch, permissions and scheduling are NOT implemented/activated yet. No actual receipt has been obtained. API timestamp semantics are documented at https://docs.github.com/en/rest/actions/workflow-runs and workflow trigger behavior at https://docs.github.com/en/actions/how-tos/writing-workflows/choosing-when-your-workflow-runs/triggering-a-workflow . Local hash chaining alone is not a trusted server anchor.
