# Four filing quarters of retained financial evidence

Starting HEAD: `c3a830b30d99f9b9f9287b184fb73996823a5b35`.

This package adds the prepared **2025 Q4 filing batch**, completing four consecutive downloaded financial filing quarters through 2026 Q3. The purpose is an earlier baseline for disclosure/revision comparisons, not a model, event novelty claim or financial-growth calculation. “Four quarters” describes archive filing-date buckets, not four comparable fiscal observations per company, a complete security universe or all EDGAR filings.

## New Q4 evidence

The ordinary official [Financial Statement Data Sets](https://www.sec.gov/data-research/sec-markets-data/financial-statement-data-sets) download for [2025q4.zip](https://www.sec.gov/files/dera/data/financial-statement-data-sets/2025q4.zip) yielded 65,830,170 bytes, SHA256 `2b36ac3850c022cf19edd882e31c3c453c7666677b9fdd2e1f7748fdb5768c6e`. All five member CRCs pass; expanded size is 675,934,365 bytes. Exact HTTP status and network download clock are unavailable; local verification was recorded separately. No private contact, new account or paid service was used.

All four source tables are retained privately and verified after commit, close and reopen:

- SUB: 6,304 submission rows, 5,786 normalized issuer CIKs.
- TAG: 84,907 taxonomy rows.
- PRE: 719,346 presentation rows.
- NUM: 3,832,977 numeric rows, including 182,388 blank values preserved as blank.
- Zero missing accession or tag/version joins in this batch.

Filing dates span October 1–December 31, 2025. Submission fiscal-period codes are Q3 for 4,681 rows, FY for 491, Q2 for 456, Q1 for 375, and blank for 301. It is emphatically **not a batch of fiscal Q4 results**. NUM has 2,255,614 nonblank segment contexts and 39,748 nonblank co-registrants; counts may overlap. All units, dates, durations, taxonomy versions, footnotes and raw source fields are retained without interpretation or consolidation.

## Contiguous archive baseline, separate counts

| Filing-date archive | Submissions | Issuer CIKs within batch | Numeric source rows |
|---|---:|---:|---:|
| 2025 Q4 | 6,304 | 5,786 | 3,832,977 |
| 2026 Q1 | 6,169 | 5,750 | 3,690,955 |
| 2026 Q2 | 7,714 | 6,179 | 3,608,711 |
| 2026 Q3 | 6,516 | 6,008 | 3,905,397 |

These are distinct scoped batch counts. **Do not sum issuer CIKs or treat numeric rows as independent comparable facts.** No new cross-batch issuer union is asserted here, and none replaces broader earlier SEC dataset coverage. Fiscal periods, amended/repeated filings, missing values and dimensions remain separate. Prior Q1/Q2/Q3 archive/data bytes are not changed or reimported by this package; their counts are taken from their previously verified manifests. The SEC cautions that prepared datasets may include source/extraction errors and are not substitutes for primary filings.

## Implementation and reproduction

The existing offline importer now accepts `--quarter 2025q4` alongside `2026q1` and `2026q2`, preserving the default Q2 behavior. It validates the selected exact archive/official URL and filing-date bounds. The summary caveat uses the selected year rather than hardcoding 2026. Tests cover both Q4 boundaries, outside-quarter rejection and wrong-quarter receipts. No downloader, recurring workflow or UI was added.

```sh
python3 backend/sec_financial_history.py --root PRIVATE_INPUT --out NEW_PRIVATE_OUTPUT --quarter 2025q4
```

Private database: 733,720,576 bytes, SHA256 `e63fa4c89bd3735fb15aa45b00dbb612a0324484e52c9ebd75d3cc0ffccdf7fa`. The DB is local/rebuildable from the retained source archive and receipt; it is not claimed to be Library-durable or byte-deterministic across SQLite versions. Public JSON is exactly the private aggregate completion summary, with no raw values, names or addresses. Source archive retention is separate from publication.

The next useful use is source-qualified filing/revision lineage, not automatic year-over-year growth or a larger unqualified model. Historical first-public clocks, security identity, actions, licensed prices and actual outcome labels remain unresolved. The [six-horizon assessment](horizon-readiness.md) and disabled trading controls are unchanged.
