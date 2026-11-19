# Corporate-action and halt evidence coverage

Research checked 2026-11-14. **Design/research only; no registered production adapter, new subscription, key request, release, or paper fill.** Source documentation was read through web retrieval; no event-feed acquisition or vendor entitlement was tested in this task.

## Findings and source rights

1. [Nasdaq halt RSS documentation](https://classic.nasdaqtrader.com/Trader.aspx?id=TradeHaltRSS) offers a free feed for Nasdaq and other exchange-listed securities and permits a custom reader. Updates are once per trading minute; requests must not exceed one per minute. This is a candidate for prospective evidence, not an unconditional completeness warranty.
2. [Official query examples](https://classic.nasdaqtrader.com/snippets/tradehaltaccordion.html) establish an important distinction: `haltdate` selects the date a halt STARTED. It does not select every halt active during that day. `resumedate` selects resumptions. The combined form includes matching starts/resumptions; it is not an interval-overlap query. An older unresolved halt can be absent from every same-day query.
3. [Halt field definitions](https://classic.nasdaqtrader.com/Trader.aspx?id=TradeHaltCodes) distinguish quotation resumption from trade resumption. Resumption times are scheduled times, not proof an ordinary closing transaction occurred. Codes include corporate-action, suspension, market-wide circuit-breaker, and deletion cases. [Current halt display](https://nasdaqtrader.com/trader.aspx?id=TradeHalts) labels times Eastern. Parse with `America/New_York`, not a permanent UTC offset.
4. [Feed terms](https://classic.nasdaqtrader.com/content/administrationsupport/agreementstrading/THRSSFeedTermsCond.pdf) require preserving source meaning and disclaim accuracy, completeness and timeliness. Free access is not a blanket raw-data redistribution license. Retain original evidence separately; do not imply derived scores or normalized timestamps are exchange-issued. Before enabling ingestion, review applicable terms/acceptance scope; do not assume permission to publicly mirror raw feed archives.
5. [Alpha Vantage documentation](https://www.alphavantage.co/documentation/) lists `DIVIDENDS` (historical and declared future distributions) and `SPLITS` (historical splits), separately from raw daily prices. Neither section is marked premium in the reviewed documentation. This does NOT establish entitlement, exhaustive coverage, update delay, or point-in-time history for our key. Two endpoints for eleven symbols means 22 requests before prices, exceeding the 25/day budget when combined with eleven price requests. Use the existing single quota owner if a reviewed test is later performed. Raw daily bars alone cannot establish action absence.
6. [Nasdaq Daily List](https://www.nasdaqtrader.com/Trader.aspx?id=dailylistpd) is a subscription product covering listing/security changes and distributions. [NYSE corporate actions](https://www.nyse.com/market-data/corporate-actions) includes wider event types than splits/dividends. Its [Events Summary](https://www.nyse.com/data-products/catalog/events-summary) is an email product with a purchase route, not an established free API. No purchase or signup performed.

## Recommended implementation contract

The existing runner expects `interval(symbol,start_session,end_session)` returning symbol, start, end, complete, actions, ordinary_close, observed_utc and provenance. Keep `complete=false` and `ordinary_close=null` until every required dimension has verified evidence. Do not let a caller-created assertion make itself trusted.

Retained source envelope:
- Exact request parameters, source identity and applicable market/security identifier; symbol mappings with effective dates.
- Raw-byte SHA-256, actual UTC retrieval time, response status and validation result. Store source publication/update time separately; unknown stays null.
- Covered interval, pagination/truncation checks, watermark and unresolved carry-in status. Retrieval success is not coverage success.
- Event IDs/version hashes, actual first-observed timestamps, original timezone/date fields, normalized UTC fields and transformation version.
- Rights decision for storage/display, confidence category and explicit missing dimensions. Avoid invented numerical confidence probabilities.

### Halt gate

Bootstrap unresolved halts predating the proposed holding interval from an appropriate verified source. Maintain a carry-forward state machine; reconcile date-specific starts, date-specific resumptions and unresolved events. Preserve every observed revision. A scheduled quotation resumption must not clear a trade halt. Unknown bootstrap, malformed data, missing day, ambiguous identity or incomplete response remains unknown. A valid positive halt observation is useful immediately; a negative claim needs all coverage prerequisites.

Even a complete halt check is not proof of an ordinary close. Require separate eligible-close evidence, session calendar and any relevant exchange disruption/closing-process status. Do not convert nonzero daily volume or a vendor bar into proof of an ordinary close. Corporate actions and halted/missing closes must not fabricate fills or returns.

### Corporate-action gate

Track announcement/publication, first observation, ex-date/effective date, record date and payment date separately. Do not use current historical responses as pre-event forecasting features. Preserve split numerator/denominator, dividend amount/currency, corrections, cancellations, symbol changes, mergers, spin-offs and delistings. Splits/dividends-only coverage must be labeled as such, not all-actions complete.

Initial safe simulation behavior: if a material action intersects the holding window and its treatment is not explicitly supported/tested, retain the reserved or open position as pending and explain why; do not silently rewrite shares, remove a position or mark cash received. A paid dividend date is not its ex-date, and an unpaid receivable is not spendable cash. Consider a separately documented exclusion policy for action-bearing candidates only before selection is frozen, never retroactively select winners.

## Minimum acceptance tests before registration

- Previous-day halt remains active despite empty target-day start query.
- Quote-only resumption does not clear trade halt; scheduled trade resumption does not certify close.
- Missing/truncated/HTTP-error response cannot become an empty successful interval.
- DST conversions; early-close sessions; market-wide halt and no ordinary closing print.
- Symbol reuse/rename and duplicate/corrected events remain distinguishable.
- Split spanning entry/exit, cash dividend across ex/pay dates, merger/delisting and unknown event type.
- Future observation unavailable to earlier decisions; later corrections append rather than overwrite evidence.
- Raw hashes match retained bytes; private-only vendor evidence never enters public files/logs.
- Existing runner leaves unknown coverage pending; no live trading capability introduced.

## Practical next step

Build a bounded, disabled ingestion module for the documented Nasdaq source with conservative carry-in state and synthetic tests. Separately add a quota-accounted private AV action entitlement probe only after collector coordination. This improves evidence without falsely asserting the present dataset can support an execution-ready paper book. Keep production adapter registration blocked until source rights, complete interval coverage, and ordinary-close evidence pass independent review.

## Follow-up implementation and baseline decision

**Unpublished local prototype, not included in this public release:** `halt_interval_observations.py` reconciles raw envelopes as of an explicit clock, rechecks hashes, excludes later observations, preserves revision evidence and known potential carry-in halts despite subsequent empty feeds. Caller-supplied completeness flags are ignored. Scheduled resumptions never erase a potential overlap. It is not registered as an execution adapter and does not assert source authentication from a hash.

A complete initial baseline remains **unverified**. [Nasdaq historical search](https://classic.nasdaqtrader.com/Trader.aspx?id=TradingHaltSearch) explicitly limits display to the last year and warns an empty result can also mean invalid criteria. [NYSE historical halts](https://www.nyse.com/trade/trading-halts) describes one-year news/LULD history, not a general all-cause, unlimited-age unresolved baseline. Therefore neither the reviewed historical page nor same-day RSS justifies a complete carry-in claim. No live source receipt or historical bootstrap was acquired here. That unshipped local implementation records source-authentication, baseline, interval-completeness and ordinary-close gaps separately and remains fail-closed. The published release contains only the observation parser and its synthetic tests, not interval reconciliation or live ingestion.

## Bounded ordinary-close feasibility check (2026-11-14)

**Result: no no-cost, permitted, automated source was verified here that proves an ordinary close and complete halt status for an arbitrary US symbol/session.** This is a scoped research conclusion, not proof no such source exists.

- [Nasdaq Cross FAQ](https://www.nasdaqtrader.com/content/productsservices/trading/crosses/openclose_faqs.pdf), question 6, explicitly allows the official stock close to use the last eligible pre-close trade if no closing cross occurred. Question 9 describes an NBBO-midpoint fallback for Nasdaq-listed ETPs. Therefore an official closing-price value alone is not proof an actual closing auction executed. Do not confuse `official_reference_close` with `verified_closing_trade`.
- [NYSE Auction Data](https://www.nyse.com/nyse-auction-data) has closing symbol/date controls and is a candidate for narrow human-verifiable positive auction evidence. Web retrieval exposed controls but no queried result in this check. No specific symbol/session, retention guarantee, machine-use license or stable automated interface was verified. Public visibility is not automatic permission to scrape or redistribute.
- [NYSE TAQ Closing Prices](https://www.nyse.com/data-products/catalog/taq-nyse-closing-prices) describes daily summary files with a purchase route and samples. Samples are useful for parser tests, not coverage of the upcoming paper week. Summary fields alone still need semantic validation for the execution model.
- [Nasdaq Fundamental Data](https://www.nasdaqtrader.com/Trader.aspx?id=FD) offers T+1 official closing-price fields; entitlement and acquisition were not established. Even successful acquisition would not resolve the fallback-price ambiguity above.

Pragmatic separation: publish observed vendor daily marks and `no halt found in these exact checked sources` as research metadata. Keep that distinct from `no halt occurred` or `ordinary close verified`. A close-to-close hypothetical return study can use explicitly labeled vendor marks with limitations; it must not be presented as an execution-realistic filled-trade book. Existing execution gates should remain closed until actual qualifying evidence arrives. No subscriptions, account changes, quota calls or feed scraping performed in this check.

### Input hardening follow-up

The parser now decodes only UTF-8/ASCII XML before checking forbidden DTD/entity declarations, preventing UTF-16/32 byte-encoding bypass. It rejects duplicate RSS channels, out-of-channel items, nested scalar values and duplicate local field names. These malformed responses cannot become valid negative evidence. Seven new tests cover these cases. The published parser has 22 passing synthetic tests. The exact isolated release containing it passed 198 backend tests, plus UI and public-state checks. Additional local interval-module tests are not part of that release. Synthetic fixture coverage does not establish live-source schema compatibility or source authenticity.

### Offline halt-window review

`backend/halt_window_review.py` adds a research-only review of already retained
response bytes. It does not use a feed, qualify any exchange session, or make an
execution decision. Its completed UTC window includes the start and excludes the
end. A match is to literal symbol text only, not a verified security mapping.

| Review label | What it means |
| --- | --- |
| `REPORTED_START_IN_WINDOW` | A hash-checked response supplied by the caller reports a start within the window. The response's origin and instrument remain unverified. |
| `POSSIBLE_CARRY_IN_NOT_VERIFIED` | An older matching start was reported; the review cannot rule out overlap. No scheduled resumption proves that trading actually resumed. |
| `NO_MATCH_COVERAGE_UNKNOWN` | No eligible supplied row matched. This includes empty input and is not evidence that trading was uninterrupted. |

Receipt checks distinguish genuine parsed-empty structure, malformed or
hash-mismatched input, date-filter inconsistencies, exact duplicates and
observations after the review cutoff. Matching observations retain their receipt
index; later revisions do not erase earlier reports. Per [Nasdaq's query
examples](https://classic.nasdaqtrader.com/snippets/tradehaltaccordion.html),
halt-date and resumption-date filters select events on their respective dates,
not interval overlap. Nasdaq's [field
definitions](https://classic.nasdaqtrader.com/Trader.aspx?id=TradeHaltCodes)
distinguish scheduled quote from scheduled trade resumption. Neither clears
carry-in in this review.

The tests use synthetic RSS and verify refusal to certify coverage, actual
resumption, security identity or an ordinary close. No source authentication,
access rights, live halt observations, or market-data coverage have been added.
The module is not registered in the app, collectors or the protected ledger.
