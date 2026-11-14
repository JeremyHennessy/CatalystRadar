# Feature evidence byte-integrity audit

`backend/study_archive_audit.py` adds exact-byte comparison to the declared clock and chronological split audit. `audit_archived_study` accepts the same study rows, required features and cutoffs as `audit_study`, plus an `archives` dictionary mapping `(source_ref, sha256)` tuples to raw `bytes`.

The caller loads authorized archived bytes privately. This function does not open files, follow URLs, call providers, access secrets, write data or change the paper book. Do not publish vendor-restricted bytes or private evidence in this repository. Output contains references, hashes and status, never the input payloads; references themselves still need a privacy review before publication.

Every feature source must have its exact reference and hash pair in the mapping. Distinct revisions remain distinct, even at one URL. Missing or changed bytes produce `MISSING_ARCHIVE` or `HASH_MISMATCH`, including holdout, purged and unresolved rows. Extra unused archives are counted, not substituted for missing evidence. Losses and all partition assignments remain unchanged. Empty cohorts and missing required features cannot pass.

Limits: 1,000 archives, 8 MiB each, 64 MiB total. Inputs exceeding these limits fail explicitly rather than truncate. Raw bytes only: a path or string is not loaded or implicitly encoded. Multiple references to a vintage reuse its digest calculation but each evidence link remains in the report.

`feature_source_bytes_verified` means the supplied bytes match the declared references/hashes for all required feature evidence. It does **not** prove that those references hosted the bytes, that the claimed observation timestamps are authentic, that the numeric feature was calculated correctly, or that selected inputs include every relevant source. A caller can fabricate both bytes and a matching hash. Source authenticity, observation-receipt verification and feature recomputation therefore remain explicitly false.

`all_integrity_checks_passed` also requires the existing declared clock/split checks. Bytes cannot override late or missing features or related-event leakage. This is a standalone audit utility, not yet a live ingestion, model-training or trading gate. All tests are synthetic; no historical cohort, return forecast, entitlement or executable price has been established. The frozen private comparison and its schedule remain unchanged.
