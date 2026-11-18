# Offline private daily-series calendar compatibility

This separately tested helper is not imported by the collector and does not change its pin, workflow, schedule, credentials, trial dates, quota reservation or archive. No source request is made. No raw or derived price data is emitted. It does not authorize continuation.

## Exact production compatibility reviewed

Private `.github/workflows/collect.yml` blob `094a279366d11bfb3972b24d36535df8ff08f35c` still pins public collector commit `2cc42023deddf3ad275848d6631e59b21ca80680`. Its schedule is `10 12 16-21 11 *`; `collect.py` stops at exclusive November 22 00:00 UTC and requires first-attempt owner-only private Actions context. Eleven symbols, thirteen-second spacing, shared public-retired/private named-workflow reservation and repeated privacy checks remain intact. The workflow's private Actions cost is not independently verified here; external key consumers remain unknown.

Pinned `private_prices.py` blob `3edb0fdc9de3021931a80a5cd5840dd8bf6fd641` derives an expected date from weekdays and 16:00 New York time, with an explicit no-holidays-in-trial caveat. `collect.py` blob `225de6adac1173ff6c92655543ee7ec71a4b6b8c` invokes the pinned archive, which invokes this validator. A public helper release alone cannot update that private runtime. The trial is not broken by a hypothetical post-expiry calendar mismatch.

## Verified reference and bounded change

Read the official [NYSE hours and calendar](https://www.nyse.com/trade/hours-calendars) on November 18, 2026. Thanksgiving November 26 is closed. November 27 equity core trading closes at 13:00 Eastern; regular core sessions close at 16:00. Options and late sessions differ. This is an exchange core-session reference, not an Alpha Vantage publication promise or verified security-specific calendar.

`private_session_context.inspect` accepts an aware observation clock and optional reported date, returning safe calendar context only. Reviewed observations are New York dates November 14–30, with November 13 as prior-session anchor. Outside that bounded interval it fails closed. At November 27 12:10 UTC the latest closed core session is November 25; at 18:00 UTC it is November 27. The legacy weekday expression instead expects November 26 until 16:00 Eastern. Tests cover the exact early-close microsecond boundary, holiday, weekends, timezone equivalence and invalid inputs.

Matching a reference date does not qualify a receipt. Earlier dates are not labelled provider failures. Provider end-of-day update latency, daily-bar/session definition, real availability and security/calendar association are unverified. The helper always returns collection disabled, receipt unqualified and trade ineligible. No current receipt is reclassified or rewritten.

## Still required before any continuation

Independently verify provider rights/availability, shared key consumers and quota ledger, private Actions zero-cost capacity, and actual retained-response compatibility. A separately reviewed runner must maintain original protection semantics and use an explicit new bounded policy. Do not merely move the old trial date or production pin. The offline NYSE reference is one prerequisite, not authorization or proof that extended collection will work.

## Existing retained metadata compatibility check

The public saved `data/price_feed_status.json` coverage audit reports latest observations at November 17 20:49:18.653849 UTC and a June 26–November 16 session span, with hashes/symbols verified by that earlier audit. Evaluating this observation clock with the new reference returns November 16, agreeing with the pinned weekday expression. This processes an existing metadata clock, not raw private prices, and does not independently repeat the earlier hash audit. November 17 receipt freshness must not be presented as a November 17 closing bar.
