# Q2 insider issuer-source extension

A separate, reviewed metadata projection connects the retained Q2 2026 insider filing batch to issuer research. Original six-batch `web/issuer-coverage` files remain unchanged.

- 56,102 source submissions, 5,065 distinct normalized issuer CIKs.
- Existing six-batch baseline: 7,912 CIKs, metadata SHA-256 `d2f865683fca6681b54295b144efc1e62d9950ae5ec0ac2d2290ffd08a01ef58`.
- 122 Q2 issuer CIKs are absent from that baseline. Deduplicated combined coverage: **8,034 issuer CIKs**. This extends retained issuer metadata coverage, not newly listed companies or securities; UI integration is separate.

`web/issuer-coverage-q2-insider/issuers.json` uses the existing source-associated row shape: `cik`, then `sources` with batch_id `insider_2026q2`, submissions, names, reported_tickers, filing_date_min and filing_date_max. All reported names remain associated with this batch, including conflicting names. Tickers include as-filed placeholders, not validated/current ticker mappings. Consumers must render strings inertly, not as HTML, and combine by CIK without summing overlapping issuer counts.

Only issuer metadata is projected. No owner names/addresses/signatures, transaction amounts, footnote narratives or inferred insider intent appear. The quarter describes filing dates, not transaction dates. Amendments remain source submissions, not silently consolidated events. No current ownership, security mapping, training admission, returns or trading signals are established.

The summary pins the independently audited original archive and complete private SQLite build plus baseline metadata. The builder checks the completed ingestion marker and absence of INCOMPLETE, exact submission schema, unique accession, numeric nonzero CIK, bounded text, quarter dates and source counts. Source and baseline hashes are checked before/after, including completion artifacts. Prior full-field ingestion review establishes archive-to-database lineage; hashes alone are not semantic proof.

Run `python backend/insider_issuer_extension.py --config PRIVATE_CONFIG --out NEW_PRIVATE_DIRECTORY`. Config fields: database, database_sha256, archive, archive_sha256, baseline, completed_ingest. Output must be new, private, outside this checkout, under a trusted parent. Files are 0600, directory 0700; consumers require COMPLETE.json and no INCOMPLETE. The public projection and summary are copied only after independent review. Generation clock is local audit time, not download, first-public or decision time.

No original six-batch builder, existing data snapshot, UI, report, ledger, source request or execution gate is changed by this package.
