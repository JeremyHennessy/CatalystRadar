# Complete rows for three selected as-filed 13F disclosures

This extends the fixed PR101 selection, not the covered-manager universe: all 103 Adams Diversified, 6 AMD and 507 Fred Alger rows in the same three June 30, 2026 filings. Selection remains first three numeric reporting-manager CIKs and first two accession-sorted filings each; no outcome or value selection. It is not representative. Exactly 616 holding rows and nine submission/cover/summary rows are compared field-for-field against the pinned original SEC ZIP and retained database.

Reuse the [sample methodology](manager-holdings-sample.md) and its source-only rights/privacy boundary. The same allowlist publishes as-filed name, class, CUSIP, FIGI, put/call, shares/principal type, discretion, other-manager reference and original row IDs. No values, quantities, voting amounts, contacts or narratives. Reported identifier strings are not verified security identities; manager CIKs do not identify held issuers. No position aggregation, value conversion, trading inference or current holdings claim.

Complete means **all retained rows within each selected as-filed filing**, not complete economic portfolio or complete amendment history. Amendments, restatement/additions type and confidential omissions remain as filed. No automatic full replacement, chronological confidential-release reconstruction, deduplication or look-through. Separate source rows may describe the same security. No period comparisons. Filing URLs remain constructed/not fetched. Dates remain raw filing/report dates, not first-public evidence.

`manager_holdings_sample.build(..., all_selected_rows=True)` reuses the exact source/schema/row checker, with a fail-closed 1,000-row per-filing cap (not silent truncation). The default ten-row sample is unchanged. `manager_holdings_full.py` creates three per-filing shards and a small manifest with each shard's exact byte count and SHA256. Each shard is under 1MB. Source checks and serialization complete before exclusive creation of a new output directory. A filesystem write failure can leave a partial directory; consumers must verify manifest and shard integrity, not infer completion from directory existence.

```
python3 backend/manager_holdings_full.py HOLDINGS.sqlite ORIGINAL_SEC.zip NEW_DIRECTORY
```

The app integration is separate: load only the requested filing, validate exact manifest/shard integrity and matching manager/accession/report period, then show bounded pages. These artifacts alone do not implement or claim browser pagination. Existing sample and full-directory artifacts are preserved. No new provider calls, collector changes or paper controls.
