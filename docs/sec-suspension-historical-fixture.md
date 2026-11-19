# Historical SEC suspension interval fixture

This isolated offline research example adds no network calls, workflow changes,
provider registration, paper orders, ledger changes, dashboard output or live feed.
It is not connected to the existing Nasdaq RSS observation parser.

## Primary evidence

- [SEC order 34-106668, dated October 14, 2026](https://www.sec.gov/files/litigation/suspensions/2026/34-106668.pdf), pages 1–2.
- [SEC suspension announcement](https://www.sec.gov/files/litigation/suspensions/2026/34-106668-ts.pdf), page 1.

Both identify TJGC Group Limited, CIK `0001969928`, and an ordered suspension
from October 15, 2026 at 04:00 ET through October 28, 2026 at 23:59 ET.
The order identifies its common stock as listed on Nasdaq Capital Market with
symbol TJGC **as of October 14**. That is not an initial listing date.
The stated reason concerns potential manipulation, not an adjudicated finding.

The fixture is a manual review of these primary documents, not a PDF parser or
byte-preserved archive. PDF hashes, first-public time and historical observation
time remain null. The order date is not substituted for any observation clock.
Do not use the unrelated EDGAR stop-order record as evidence for this interval.

## Conservative positive-only matching

`historical_order_match` accepts an exact ten-digit CIK and a timezone-aware
instant. It returns a positive historical order match only for the matching CIK
strictly inside the source's minute-level boundaries. The entirety of both
boundary minutes remains unknown: no implied second-level precision. This
includes the exact 23:59 endpoint. Outside the ordered interval, or for another
CIK, the answer is unknown, never clear/not halted/resumed.

The interval spans multiple dates, including a weekend; this is not a session
calendar. Matching the issuer does not resolve a particular security/share class.
Converting the historical ET minutes through America/New_York gives 08:00 UTC
on October 15 and 03:59 UTC on October 29. These are boundary labels, not
higher-precision source evidence.

Expiration is not resumption. A separate [Nasdaq October 29 announcement](https://ir.nasdaq.com/news-releases/news-release-details/nasdaq-halts-tjgc-group-limited-0)
reports a halt pending additional information after the SEC suspension window.
This is a counterexample only: it is not folded into the SEC matcher, and neither
an exact Nasdaq halt start nor current trading status is inferred here.

## Verification

Run `python3 -m unittest discover -s backend -p 'test_sec_suspension_fixture.py'`.
Eight tests cover multiple dates, weekends, both boundary minutes, adjacent
interior instants, UTC/ET equivalence, mismatched identities, invalid timestamps,
post-window unknowns and copy isolation. All returned states preserve execution
ineligibility; none establish historical knowledge or complete halt coverage.
