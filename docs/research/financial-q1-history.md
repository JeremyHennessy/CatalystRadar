# Earlier financial filing baseline: Q1 2026

Starting HEAD: `108e252825101f884d69d342771866d353c62495`.

Purpose: extend the retained Q2/Q3 filing-date baseline into January–March 2026, retaining earlier annual and interim financial disclosures for future source comparison. This is historical evidence acquisition, not a new training sample, growth result or predictive experiment. No approved UI, ledger, held report or scheduled collector changes.

## Actual retained and persisted evidence

The ordinary download linked from the official [Financial Statement Data Sets page](https://www.sec.gov/data-research/sec-markets-data/financial-statement-data-sets) supplied [2026q1.zip](https://www.sec.gov/files/dera/data/financial-statement-data-sets/2026q1.zip): 85,259,424 bytes, SHA256 `d18c01c615da8f5cd46273b0dacaeee5b1163f4089171da0f84153a5f3c362f6`. All five ZIP members passed CRC validation; expanded size is 671,659,462 bytes. No private contact was supplied. Exact HTTP status and download clock are unavailable; the local verification timestamp is not a first-public timestamp.

The importer committed, closed and reopened the private SQLite database, checked integrity and verified all persisted table counts:

- 6,169 submission rows, 5,750 normalized issuer CIKs.
- 91,794 taxonomy rows.
- 733,134 presentation rows.
- 3,690,955 numeric rows, including 139,723 blank values preserved as blank, not zero.
- Zero missing accession or tag/version joins in this batch.

Actual filing dates range January 2–March 31, 2026. The submission fiscal-period field is FY for 4,831 rows, Q1 for 353, Q2 for 377, Q3 for 331, and blank for 277. Thus **Q1 filing batch is not Q1 financial results**. The numeric table retains 2,185,031 rows with nonblank segments and 44,515 with nonblank co-registrants. These counts can overlap. Units, taxonomy versions, durations, footnotes and all source fields remain private and unmodified, including unusual duration values; no automatic comparability or financial totals are inferred.

Issuer counts are not added to earlier batches without deduplication. Numeric rows are not unique economic facts, and filed-date coverage does not establish full EDGAR coverage or past decision-time availability. The SEC warns that extracted datasets may contain source/extraction errors and are not substitutes for original filings.

## Rebuild and safeguards

`backend/sec_financial_history.py` now accepts explicit `--quarter 2026q1` or `2026q2`. Existing default Q2 behavior is retained. Each selected quarter requires its exact filename, official URL, pinned byte count/hash and filing-date bounds; mismatched or unsupported quarters fail closed. Source schemas and dimension preservation are unchanged. No downloader was added.

Run against the privately retained archive and normalized receipt, with a new output directory outside any publication checkout:

```sh
python3 backend/sec_financial_history.py --root PRIVATE_INPUT --out NEW_PRIVATE_OUTPUT --quarter 2026q1
```

The original browser observation and normalized receipt are both retained. Private database SHA256 at this checkpoint: `ce306b9ec556b3687fc4e1b5e0da53d2a1c2a36a119356f90b73bf9eb08fcea6` (728,780,800 bytes). The database is local and reproducible from retained source bytes plus importer; it is not claimed to be a durable Library database or byte-deterministic across SQLite versions. Public JSON is the exact aggregate completion summary, not raw values or issuer addresses. A failed ingest retains `INCOMPLETE` and does not publish a successful summary.

Tests cover Q1 start/end boundaries, rejection outside the quarter, wrong-quarter receipt selection and unsupported quarters, while all existing Q2 tests remain. Research qualification, model training and execution remain disabled. This earlier filing baseline does not solve price/action/identity/availability blockers in the [six-horizon readiness assessment](horizon-readiness.md).
