# Historical issuer coverage: six retained filing batches

This searchable metadata package expands coverage from 7,093 to **7,912 distinct normalized issuer CIKs**, adding **819 CIKs** with retained source evidence. These are not newly listed companies, unique stocks, current security identities, or model-training examples.

Starting release HEAD: `80ae11c2fb8f832f5a142739249b28a9abcd0080`. Previous public `web/prepared` and `web/notes` snapshots remain untouched. The new versioned schema is in `web/issuer-coverage/summary.json` and `issuers.json`. No paper engine, account, collector, workflow, or held research report changed.

## Verified input coverage

| Source filing batch | Submissions | Distinct issuer CIKs |
|---|---:|---:|
| Financial 2025 Q4 | 6,304 | 5,786 |
| Financial 2026 Q1 | 6,169 | 5,750 |
| Financial 2026 Q2 | 7,714 | 6,179 |
| Financial 2026 Q3 | 6,516 | 6,008 |
| Insider 2026 Q3 | 38,152 | 4,716 |
| Statements and notes October 2026 | 6,670 | 3,555 |

The union is computed from issuer CIK, not names or ticker strings. No prior CIK is lost. Do not sum issuer counts. Submission counts remain separate: an accession may occur in more than one dataset family. Filing quarters are not fiscal-result quarters. Amendments and repeated financial reporting remain included.

## Source-associated names and tickers

Each record has exactly `cik` and `sources`. Every source association contains batch ID, submission count, all reported issuer names, all reported issuer ticker strings, and that issuer's minimum/maximum filing dates in the batch. **2,851 CIKs have multiple distinct reported name strings across these inputs.** Name variation may reflect casing, punctuation, historic names, or other differences; it is not automatically a conflict, merger, or rename event. No preferred/current name is selected.

Only the insider submission source supplies ticker strings here. Placeholders such as `NONE` are retained as source text, not validated symbols. A financial-only issuer's empty ticker array means no ticker is supplied by this metadata source, not that the issuer has no listing. No ticker-to-CIK temporal/security mapping is inferred. Consumers must render all strings as inert text, not HTML, and label them as reported in historical filings.

## Integrity and privacy

`backend/issuer_coverage.py` accepts exactly six declared batches, pins archive and database SHA-256 before and after reading, opens SQLite read-only, checks database integrity, and rejects malformed/zero CIKs, duplicate accessions within a batch, out-of-batch filing dates, empty batches, excessive rows, and malformed source strings. Output is bounded to 10 MB. The public summary pins the exact metadata bytes and records source URLs, source tables, input hashes, batch windows, and a separate local generation timestamp.

Hash pins prove which retained bytes were used; they do not by themselves prove database derivation. Prior independently reviewed ingestion compared the relevant source TSVs to persisted databases. This package's independent source-association audit is a separate release gate. Local generation time is not retrieval or first-public timing.

Only issuer-level names/tickers/counts/date ranges are selected. Reporting-owner tables, people, addresses, signatures, remarks, footnote text, financial values, and transaction rows are not published or joined. CIKs are issuer identifiers, not reporting-owner identities. All six original archives were previously retained privately; no new provider request or quota use was needed.

The output writer uses a new private 0700 directory and 0600 files, leaves `INCOMPLETE` on failure, and writes a hash-bearing `COMPLETE.json` only after both metadata files exist. This is completion bookkeeping, not immutable or independently timestamped storage. Previous output directories are never overwritten.

## Reproduction

Use the original reviewed archive/database hashes from the public summary and private paths for the six retained inputs. The private config maps each batch ID to `database`, `database_sha256`, `archive`, `archive_sha256`, and `source_url`; it must not be committed with private paths.

```sh
python3 backend/issuer_coverage.py --config PRIVATE_CONFIG.json --out NEW_PRIVATE_DIRECTORY
python3 -m unittest discover -s backend -p 'test_issuer_coverage.py'
```

Synthetic tests cover normalized CIK identity, source-associated names/placeholders, duplicate/empty/invalid records, batch boundaries, union versus sum, missing batches, output allowlists, input hash failure and incomplete output. Synthetic archives in tests exercise hash binding only, not SEC archive validity.

Public metadata has no predictive qualification. `training_ready` and `simulation_enabled` remain false, with zero orders created. A subsequent reviewed explorer integration can consume this schema without changing historical source snapshots.
