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
The [attachment in EDGAR accession 9999999997-26-001635](https://www.sec.gov/Archives/edgar/data/1969928/999999999726001635/filename1.pdf)
contains the same identified order 34-106668, including CIK 0001969928 and the
October suspension dates. The earlier description of that record as unrelated
was incorrect. This is a document-content comparison, not a claim of byte
identity between the two PDF URLs. The separate EDGAR accession and its
acceptance metadata are not the order's first-public time, effective start or
end, or our historical observation clock.

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

## Separate May–June interruption: scheduled resumption is event-specific

[Nasdaq's June 3, 2026 announcement](https://ir.nasdaq.com/node/110496/pdf)
reports that TJGC ordinary-share trading was halted on May 15, 2026 at
18:50:47 Eastern Time, and announces a scheduled resumption on June 3, 2026
at 12:00 p.m. Eastern Time. The precise halt time and noon scheduled time
come from Nasdaq, not from the issuer's filing. An announced schedule is not
independent evidence of an actual trade or execution at that time.

The [issuer's June 3 Form 6-K](https://www.sec.gov/Archives/edgar/data/1969928/000118518526002314/tjgc6k060326.htm)
identifies the May 15 interruption as T12, additional information requested by
Nasdaq. Its expected-resumption description is only a time **after 10:00 a.m.
Eastern Time on June 3**, not an exact noon timestamp. Preserve these separate
source claims rather than replacing the issuer's less precise statement.

Both June sources concern that earlier May interruption only. They cannot
establish resumption from the later October SEC suspension or the separate
October 29 Nasdaq halt, and establish no current trading status. This contrast
is documentation only: it does not extend the single October fixture, create a
continuous halt history, prove historical first-public availability, or change
any trading/qualification gate.

## Verification

Run `python3 -m unittest discover -s backend -p 'test_sec_suspension_fixture.py'`.
Nine tests cover multiple dates, weekends, both boundary minutes, adjacent
interior instants, UTC/ET equivalence, mismatched identities, invalid timestamps,
post-window unknowns, strict ASCII offset-component validation and copy isolation. All returned states preserve execution
ineligibility; none establish historical knowledge or complete halt coverage.
