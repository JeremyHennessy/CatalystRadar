# Q2 2026 insider filing history

This offline, retained-source batch extends the existing Q3 insider evidence. It supports review of repeated records and amendments, not automated trading or inferred insider sentiment.

## Verified persisted coverage

| Table | Rows |
|---|---:|
| SUBMISSION | 56,102 |
| DERIV_HOLDING | 12,021 |
| DERIV_TRANS | 30,370 |
| FOOTNOTES | 129,689 |
| NONDERIV_HOLDING | 22,746 |
| NONDERIV_TRANS | 78,328 |
| OWNER_SIGNATURE | 59,580 |
| REPORTINGOWNER | 60,153 |

There are 5,065 distinct normalized issuer CIKs in submissions filed April 1–June 30, 2026. This is a filing-date quarter, not a transaction quarter or a current-holdings snapshot. Submission forms include 5,284 Form 3, 212 Form 3/A, 49,832 Form 4, 713 Form 4/A, 58 Form 5 and 3 Form 5/A. Amendments are retained separately; no replacement or event consolidation is inferred.

The raw non-derivative codes include 5,326 P and 27,601 S rows. P/S means open-market **or private** purchases/sales. All 35 P/disposition and 30 S/acquisition combinations remain unchanged. These are source-record inconsistencies to review, not repaired events or signals. Submission-level AFF10B5ONE does not prove a particular row's plan applicability. Footnotes and owner information remain private.

## Source and lineage

- [Official dataset page](https://www.sec.gov/data-research/sec-markets-data/insider-transactions-data-sets)
- [Prepared archive](https://www.sec.gov/files/datastandardsinnovation/data/insider-transactions-data-sets/2026q2_form345.zip)
- Archive SHA-256: `11f1b2bbbdcbe6347a34437c02d04202fda0eca1dbb023726e4b56504b802e27`
- 11,498,860 compressed bytes; 10 members; 73,638,826 expanded bytes. All member CRC checks pass.
- Normal browser download with no private contact or credentials. Local verification was November 18, 2026 at 01:08:41 UTC; exact HTTP status/download time was not exposed and remains null. This is not historical first-public evidence.

The private database preserves every source field as TEXT, including blank strings, owner addresses/signatures, footnotes, raw form/code spelling and transaction dates. All eight exact schemas and row widths are checked; submission identities, filing bounds, child accession joins and table-specific source keys are validated. OWNER_SIGNATURE and REPORTINGOWNER have no invented unique-row key; their repeated rows are preserved.

After synchronous FULL commits and close, the importer reopens read-only, runs SQLite quick_check, and compares row counts and canonical full-field row hashes in source order. This verifies persistence, not the truth of a filing. Source archive hashes are checked before and after processing. The public aggregate includes coverage and integrity metadata only, never owners, narrative or transaction amounts. Public form/code/direction categories use documented allowlists and fixed UNKNOWN/MISSING buckets; arbitrary raw category strings remain private.

## Rebuild and failure behavior

Run `python backend/sec_insider_history.py --root PRIVATE_SOURCE_DIRECTORY --out NEW_PRIVATE_OUTPUT_DIRECTORY`. The retained root must contain the exact archive and its browser receipt. Receipt extras are omitted from public output; its complete raw hash remains pinned. Output must be new and outside this checkout, under a trusted private parent. Directory permissions are 0700; files are 0600. No immutable-storage guarantee is implied.

`INCOMPLETE` is created before database ingestion and remains on failure. Successful summary is written only after reopened full-field verification. `COMPLETE.json` pins database and summary hashes before INCOMPLETE is removed. Consumers require COMPLETE and absence of INCOMPLETE. The SQLite checksum pins this build, not a guarantee of identical SQLite bytes across environments; the canonical table hashes support field-level reproduction.

No existing report, ledger, collector, dashboard or execution gate was changed. No orders, qualified training samples, historical decisions or outcomes were created. This batch is not added arithmetically to other issuer counts or the public issuer union.
