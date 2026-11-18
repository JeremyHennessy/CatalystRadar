# Retained Treasury par-yield context

This is a real, single-request public-data snapshot, not a simulated rate series. The documented Treasury November 2026 XML route returned HTTP 200 and 17,668 exact bytes. The request began at **2026-11-18 18:00:37.919178 UTC** and finished at **18:00:43.499761 UTC**. No credentials, account, spending, retries or redirects were used. The source XML and original capture receipt are retained verbatim for reproduction; the receipt's `RETAINED_RESPONSE_NOT_YET_VALIDATED` is its original capture-stage status, not the later parser's validation result.

The response has 11 observation dates: November 2, 3, 4, 5, 6, 9, 10, 12, 13, 16 and 17. It is a **partial month snapshot**, not the completed November series or a live feed. No observation dated November 18 is present. Missing dates are not created, explained, forward-filled or treated as zero.

## Useful rate context, not executable prices

All 14 source maturity fields are retained as exact decimal text, alongside the separate `BC_30YEARDISPLAY` field. That display field is not counted as a fifteenth maturity, nor is its value silently substituted for `BC_30YEAR`. Explicit source nulls stay null; none occur in this response. Missing required fields instead fail schema validation.

The only derived statistic is `(10-year reported par yield − 2-year reported par yield) × 100`, expressed in basis points with exact Decimal arithmetic and no intermediate rounding. The observed sequence is **32, 34, 32, 38, 35, 32, 25, 24, 27, 29, 30 basis points**. On the final source date, November 17, the reported 2-year rate is **4.80%**, the 10-year rate **5.10%**, and their difference **30 basis points**. A missing/null input makes the spread unavailable, not zero.

These agency fitted par yields are macro rate context, not executable bond quotes, transaction prices, equity returns, a trading recommendation or a forecast. No bond/security linkage, interpolation, annualized return, price target or training/outcome admission is added.

## Clocks and rights

`NEW_DATE` is a source observation-date field represented as midnight with no timezone. It is not interpreted as a midnight UTC publication. The feed and all entry `updated` fields equal **2026-11-18T01:02:21Z**; this does not establish individual observation release times, first-public availability or historical data vintages. The actual request/finish clocks are separate. Earlier availability and revisions remain unknown.

The [dataset-specific federal catalog record](https://catalog.data.gov/dataset/interest-rate-statistics-daily-treasury-yield-curve-rates), identifier **015-DO-020**, identifies the Treasury Office of Debt Management dataset and its CC0 license. The [official XML documentation](https://home.treasury.gov/treasury-daily-interest-rate-xml-feed) specifies the route and monthly parameter. This rights basis applies to this numerical government dataset, not a blanket grant over website pages, logos, photographs or unrelated third-party series. No page HTML or copyrighted prose is republished.

## Reproduction and fail-closed behavior

```sh
python backend/treasury_yield_context.py \
  --raw web/market-context/treasury-202611/response.xml \
  --receipt web/market-context/treasury-202611/receipt.json \
  --out /tmp/treasury-context-rebuild
```

The destination must not already exist. The build checks the exact XML and receipt SHA256 pins, capture metadata and observed date consistency. Its reusable parser performs no HTTP requests: it accepts only bounded UTF-8 XML, rejects DTD/entity declarations and NUL/other encodings, validates Atom/OData namespaces and exact field/type/identity schemas, and rejects duplicate properties, source IDs and dates. Unexpected text in title/author fields is rejected rather than published. XML values are finite decimals with at most four fractional digits and an absolute bound of 100 percent; unsupported values fail instead of rounding. The parser neither follows links nor evaluates embedded content.

Input caps are 1,000,000 bytes of XML, 10,000 receipt bytes, 31 entries and 1,500 parsed elements. Output is at most 100,000 bytes. Private reproduction directories use 0700 and files 0600. An `INCOMPLETE` marker precedes validation; the output is written before a hash-bearing `COMPLETE` marker, and failures retain `INCOMPLETE`. Published artifacts are only the reviewed raw numerical XML, capture receipt and resulting context JSON.

Tests reproduce every actual source rate/date field and all spreads, and cover explicit nulls, missing fields, duplicate properties/IDs/dates, namespace/type mismatches, malformed clocks, out-of-month dates, nonfinite/excess-precision values, UTF-16/32 DTD bypass attempts, changed source/receipt pins, changed HTTP/redirect metadata, duplicate JSON keys and failed-build completion behavior. Existing collectors, schedules, company evidence, frozen research reports and disabled paper ledger are untouched.
