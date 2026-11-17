# SEC prepared-data baseline

Actual retained public SEC Data Library ZIPs, not search snippets:
- Q3 2026 Financial Statement Data Sets (65,148,008 bytes).
- Q3 2026 Insider Transactions Forms 3/4/5 (8,660,776 bytes).
- October 2026 second-half Fails-to-Deliver (1,435,614 bytes).

Official landing page: https://www.sec.gov/data-research/sec-markets-data . Exact file URLs and SHA256 hashes appear in `web/prepared/summary.json`. Standard public-browser link downloads used no private contact address. Browser HTTP response status and exact download timestamps were not exposed; recorded local verification times do not claim either, or first-public availability.

## Actual baseline and UI

`web/datasets.html` displays coverage and searches 6,787 distinct issuer CIKs across the financial and insider baseline. Financial data has 6,516 submissions from 6,008 CIKs and 3,905,397 numeric rows. Insider data has 38,152 submissions covering 4,716 issuer CIKs; 59,885 nonderivative and 19,205 derivative transaction rows. Both submission filing-date ranges are July1–September30,2026. Counts overlap across datasets; union is not their sum.

The FTD source has 63,157 rows across 12 settlement dates October15–30,2026. Its second-half filename does not justify dropping October15. Both trailer counts/checksums reconcile. There are 412 missing price fields, one blank ticker and two 11-character ticker rows exceeding the published ten-character specification. All are retained and flagged. Outstanding balances across different settlement dates must not be added as a current total or daily-new-fails quantity. This data does not establish short selling or abuse. Its previous-day price column is not a trading execution feed.

Financial NUM includes `segments` (schema revised December2024), `coreg`, taxonomy/version, unit, period and footnote context. All remain source text in the private database; no dimensional values are silently treated as company-wide totals. Repeated/restated entries are retained. Numeric row count is not a count of unique comparable facts. Insider codes/footnotes/10b5-1 fields remain intact; transaction rows are not interpreted as only open-market buying/selling.

## Offline reproducibility

`python3 backend/sec_prepared_data.py --root PRIVATE_RETAINED_ARCHIVES --out NEW_PRIVATE_OUTPUT`

The input browser-receipts.json contains an exact allowlisted schema, fixed official URLs, bytecounts/hashes, local verification time, and explicit null HTTP status/download time. No network function is present. ZIP names are exact-allowlisted with no extra/duplicate/traversal members, no encryption, at most100MB compressed each and1.2GB uncompressed per archive. The largest numeric member is~875MB, streamed with bounded batches to SQLite rather than loaded into memory. The exact table headers are pinned to the retained schema; quoted tabs/doubled quotes are parsed by strict TSV handling. UTF-8, complete row widths, accession joins, parent identities, dates, finite numeric fields and FTD checksums are validated. Archive reads to EOF verify ZIP CRC.

SQLite uses durable FULL synchronous writes. Every table is committed, connection closed, reopened read-only, and counts plus quick_check verified before writing a completion summary. INCOMPLETE exists until successful completion. Any failing build must not be published or treated as a usable baseline. Regression tests reopen the database and verify FTD persistence. Original failed intermediate builds are explicitly incomplete, not evidence.

Use a trusted private parent directory and restrictive process umask. The utility rejects output inside its own checkout; it cannot recognize every other publication checkout, so the caller must keep the destination private. Raw database, ZIPs, owner names/addresses/signatures and numeric values stay outside the public repository. Public outputs are issuer names/reported tickers/CIKs and submission counts plus aggregate coverage/provenance only. Issuer metadata has an exact hash in the summary; CI verifies it. Reported names/tickers are historical source associations, not a current symbol master.

## Scope and limits

No complete-company/universe, live market, full-history, legal-outcome or predictive claims. This does not fetch companyfacts.zip/submissions.zip, every financial filing, or original exhibits. The earlier all-CIK/index collector remains offline and unpublished pending separate collection. No real trade, fictional fill, gate relaxation, backdated evidence, held report regeneration or scheduler changes. These delayed baselines support research and future analysis; they cannot retroactively qualify a decision.
