# CatalystRadar

**Public-source catalyst research, a monitoring dashboard, and a disabled paper-accounting prototype. Never connected to a brokerage.**

## Current verified state
- 4,076 filing URLs catalogued from nine official SEC daily indexes covering November 2–13, 2026; 3,066 issuer CIKs. These are metadata discoveries, not trade signals.
- Eleven complete original filings archived during development; ten sample filings received targeted review.
- A separate real ten-issuer SEC metadata poll completed successfully. Its timestamps and content-addressed public snapshots are stored here.
- No validated price/liquidity/auction or halt feed. Zero eligible signals, orders, positions or fills.
- The illustrative book starts with **US$500 hypothetical cash**, not anyone's actual assets.

## Trial window: November 16–20, 2026
The goal is short-horizon research, not long-term investing. SEC metadata polling is configured approximately every 30 minutes during the bounded trial window; GitHub scheduling can be delayed. A hard 2026 date gate prevents collection outside the window. This is not high-frequency or realtime market data.

Paper entry/exit code is an **accounting prototype**, disabled by both the stored ledger and an empty approved-provider registry. Flipping one Boolean cannot enable it. Prices must be bound to verified archived bytes, security, session and actual observation time; decisions cannot be backdated. Missing evidence means no simulated trade.

Do not enable this prototype until independently reviewed provider-specific ingestion, complete source eligibility, exchange calendars, corporate actions/dividends and halt/exit-retry handling are implemented. Daily bars do not establish official auction execution. A halted position cannot be declared sold just because the trial ends.

## Run locally
Python 3.11+ and Node.js for UI checks; no Python packages required.

```sh
python3 -m unittest discover -s backend -p 'test_*.py'
node web/tests-ui.js
python3 backend/build_dashboard.py
python3 backend/verify_public_state.py
python3 backend/server.py --port 8000
```

Open `http://127.0.0.1:8000`. The server exposes a **read-only** `/api/status` snapshot. Refreshing the page does not run scans, submit orders or refresh prices. The `web/` directory also works on a static host using `app-data.json`. No hosted app URL is claimed until deployment is separately verified.

## Public SEC observations

```sh
python3 backend/scan_watchlist.py
python3 backend/build_dashboard.py
```

The scanner queries only the configured ten issuers at no faster than one request every two seconds. It validates ticker/CIK identity, preserves request/retrieval times and immutable response hashes, and blocks completeness claims if the recent-filings window is truncated. It stops further requests following access/rate denial. It does not classify metadata as a trade or provide prices.

`.github/workflows/sec-observations.yml` is a bounded trial-week polling workflow, with a read-only default token and contents-write permission only on the observation job. The workflow stages only public scan snapshots and dashboard data, preserving the separately dated research reports unchanged with `--preserve-research-report`. This is a code-level restriction, not a path-scoped token permission; the job token can write repository contents. CI runs tests and verifies that the live ledger remains disabled and empty. No secrets, paid APIs, trading credentials or new spending are configured.

**Operational caveat:** a configured workflow is not proof that it has run. Check Actions and the latest scan's provenance. The November cron recurs annually, but the worker's explicit 2026 gate prevents future-year network scans. Disable/remove the workflow after the trial as routine cleanup.

## Research rules
Four experimental families are documented: earnings growth, comparable guidance increases, firm customer contracts and incremental common-share repurchase authorizations. They are hypotheses, not a demonstrated edge. Debt issuance is not a sales contract; preferred redemption is not a common-share buyback; rediscovered old news is not a new catalyst. Keep rejected and pending records, not only apparent winners.

Source publication, SEC acceptance, retrieval and review timestamps remain distinct. The example reviews are not recommendations. There is no price chart or P&L history because no trades occurred.

## Repository layout
- `backend/`: source ingestion, evidence validation, classifier, read-only server and prototype accounting/tests.
- `data/filing_reviews.json`: ten source-linked reviews, none eligible.
- `data/provenance.json`, `data/sec-snapshots/`: public-source provenance and immutable metadata snapshots.
- `data/paper_ledger.json`: disabled hypothetical book.
- `web/`: dashboard; source text rendered safely without treating it as HTML.
- `docs/`: methodology, feed-access limitations and verification record.

Private financial information, user locations, account identifiers and credentials do not belong in this public repository. Nothing here guarantees profit or income.

## Small-account sizing
The requested illustrative capital is US$500. At most five positions reserve at most US$100 each including the 3% price-limit buffer and modeled 0.1% entry cost. Whole shares only: if one share cannot fit, the opportunity is skipped, not resized with invented fractional execution. Unallocated cash remains cash. The comparison baseline is US$500 non-interest-bearing cash, not SPY or a market-return benchmark; no fractional benchmark holdings are fabricated. The execution engine remains disabled and no holdings exist.

### Collection-status evidence

Public price-status metadata contains only an allowlisted collection receipt summary,
not private vendor bars or prices. Initial sample coverage and latest retrieval time
are separate: a successful scheduled download does not verify the most recent market
session, auction prices, halt clearance, or execution readiness. Updating this metadata
requires checking the private collection receipt and matching successful schedule event;
no private provider request is made by the dashboard builder.

The November 16 scheduled SEC runner reached the source but received HTTP 403 on
its first request and correctly skipped the remaining nine issuers. A green Actions
run means the failure receipt was published, not that source coverage succeeded.
Do not retry via alternate runners, IPs, or disguised clients. [SEC guidance](https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data) calls for
a declared organization/contact-email User-Agent. The scanner now requires an
approved contact in the private runtime variable `SEC_CONTACT_EMAIL`; the scheduled
workflow reads the same-named Actions secret. Configure it privately, never in code,
public variables, dashboard data, command output or logs. Missing/invalid contact
stops before network access. This compliance correction does not prove the 403's
cause or guarantee access. A future denial still stops the bounded scan without
retry, disguised identity or alternate-route attempts.
