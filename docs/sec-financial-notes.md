# October 2026 financial statements and notes baseline

Official source: https://www.sec.gov/files/dera/data/financial-statement-notes-data-sets/2026_10_notes.zip, linked by https://www.sec.gov/data-research/sec-markets-data/financial-statement-notes-data-sets.

The complete ZIP was downloaded through the normal public browser, without a private contact address or sign-in. It contains 91,722,505 bytes and has SHA256 `44d1b48909babe6611fcf59ff5bd273281616acbf2b91567e9597a51f924cee1`. Its ten members total 643,981,573 uncompressed bytes. HTTP status and the exact download clock were not exposed and remain null. Local verification time is not publication evidence.

## What is actually retained

There are 6,670 submissions from 3,555 issuer CIKs, with filing dates October 1–30, 2026. All source rows are retained:

| Table | Rows |
| --- | ---: |
| TAG | 151,113 |
| DIM | 103,874 |
| REN | 86,822 |
| CAL | 141,562 |
| PRE | 984,961 |
| NUM | 1,488,444 |
| TXT | 271,414 |

Original note text and numeric values remain in private SQLite, not public HTML. No topic classifications, acquisition conclusions, financial growth estimates or legal outcomes are asserted.

**Source quality gap:** 49 NUM rows reference eight custom `(tag, version)` keys absent from the source TAG table. The original rows are retained, with flags in `notes_validation_gaps`, and are explicitly not qualified. `taxonomy_joins_complete` is false. Submission and dimension references, plus the other required joins, passed. Missing definitions are neither invented nor silently dropped.

The webpage merges issuer-level coverage with the previous Q3 financial/insider baseline: 7,093 combined issuer CIKs, including 306 newly covered CIKs. Submission counts remain separated by batch and period, rather than added into comparable financial results. Names are reported aliases; ticker mappings are not independently current. Both underlying issuer coverage files remain separately hashed and reproducible.

## Rebuild safely

```sh
python3 backend/sec_notes_data.py --root PRIVATE_SOURCE_DIRECTORY --out NEW_PRIVATE_OUTPUT_DIRECTORY
```

Inputs are the original `2026_10_notes.zip` and `browser-receipt.json`. The ingester performs no networking. It validates exact receipt fields, member names, schemas, source hash and size; enforces 100 MB compressed, 1.2 GB uncompressed and 20 MB per-field limits; and uses strict quoted TSV parsing, complete CRC reads and referential checks.

All source columns are retained, including numeric/text dimensions, units or language, duration and precision, taxonomy, co-registrant and footnote context. Input text is untrusted data, not instructions or rendered HTML.

SQLite uses FULL synchronous writes. Every table is committed, the connection is closed and reopened, and persisted counts plus `quick_check` pass before completion. Failed outputs retain `INCOMPLETE` and must never be published. Output inside the utility's own checkout is rejected; a trusted private parent and restrictive umask are still required because other publication checkouts cannot all be recognized.

Source files and the database stay private. Only allowlisted summary and issuer CIK/name/count metadata is public. No note text, numeric values or owner addresses are published.

This monthly prepared dataset is not all SEC companies or history, live market data, verified first-public timing, or trade-eligible evidence. Held reports, the ledger and trading gates are untouched.
