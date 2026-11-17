# Same-filing financial context candidates

Starting commit: `4755173fc52c0966d4f7d3be096593daf972b6b7`.

## Purpose and actual result

The retained Q2 and Q3 SEC financial filing batches contain a useful next layer of evidence beyond filing headers. This offline audit joins numerical rows to the exact filing, taxonomy definition and presentation rows. It asks only whether two source facts have matching declared context, **not whether they represent comparable economic performance**.

| Filing batch | Examined four-tag rows | Empty dimension, one-quarter rows | Context groups | Matched candidates | Candidate accessions | Candidate CIKs |
|---|---:|---:|---:|---:|---:|---:|
| Q2 2026 | 180,004 | 28,066 | 13,623 | 12,632 | 5,079 | 4,985 |
| Q3 2026 | 264,122 | 30,892 | 13,563 | 12,294 | 4,990 | 4,902 |

These are filing batches, not necessarily Q2/Q3 economic periods. Issuers, accessions, amended filings and related events can overlap; do not add batch counts as unique companies or independent examples. The four predefined standard concepts are Revenues, RevenueFromContractWithCustomerExcludingAssessedTax, NetIncomeLoss and EarningsPerShareDiluted. These alternatives are not summed or treated as interchangeable.

The dated aggregate JSON includes exact input database/archive hashes, private candidate-file hashes, row exclusions and every terminal group disposition. It contains no financial values, names or owner details. The existing research reports, approved UI and ledger are unchanged. No provider request, additional data purchase or model training occurred.

## Conservative matching

- Use the exact same accession, standard US-GAAP tag and taxonomy version, raw unit, and `qtrs=1`. Require explicit empty `segments` and `coreg`; do not drop dimensions to manufacture a join.
- Require one SUB record, a single standard nonabstract duration TAG definition, and matching PRE context. Preserve PRE rows, including `inpth`, statement and line metadata, without interpreting them as proof of operations scope.
- Select `ddate=SUB.period` and its exact prior calendar-year date. Never shift a February 29 date or silently approximate a 52/53-week reporting calendar. An unsupported date remains a rejection.
- Reject duplicate fact dates within a context group, even equal-valued duplicates. Reject missing/nonfinite or oversized numerical strings and footnoted selected values. Zero is retained, not treated as missing.
- Preserve the original raw `uom=USD` and taxonomy datatype. The SEC extracts label these monetary concepts `monetary` and diluted EPS `perShare`. No unit rewriting, currency conversion or EPS arithmetic occurs.
- Preserve original values, row IDs, filing/accepted fields, fiscal fields and exact database/archive hashes in private candidate records. The hashes bind retained bytes, not authenticity or historical availability. Pinning a database and archive hash alone does not prove their derivation relationship; the prior independent field-for-field ingestion audit establishes that relationship for these exact retained inputs.

Every context group receives a terminal result, including rejection. Q2 rejects 45 groups for footnotes, 69 missing current periods, 196 invalid/missing values, 299 missing prior periods, 365 unsupported forms and 17 unsupported units. Q3 respectively rejects 143, 40, 155, 343, 572 and 16. Earlier row-level exclusions account separately for nonempty dimension/coreg and non-single-quarter rows. These are precedence-ordered reasons, not exhaustive counts of every possible defect in a rejected group.

## What this does not prove

`qtrs=1` does not supply exact start dates or equal duration. Empty dimensions do not prove consolidated total-company scope. Same-filing comparatives can be recast; reporting basis, acquisitions/disposals, restatements and continuing versus discontinued operations still require source review. Matching taxonomy is not a substitute for that review. The selected four-tag sample is not an unbiased event cohort.

Filed and accepted values are kept as source fields, never promoted to authenticated first-public timestamps. Current downloads cannot prove past decision-time availability. All candidates retain `comparability_verified=false`, `training_ready=false`, null decisions and outcomes. No growth rates, surprises, labels, performance, signals, predictions or simulated fills are generated. This package does not increase the count of qualified training examples.

## Reproduction and privacy

Run `backend/financial_pair_candidates.py` with a retained SQLite database, original ZIP, both independently verified expected SHA-256 hashes and a new private output directory. The process opens SQLite read-only, checks integrity and input hashes before and after processing, and never requests source data. Output must be outside this checkout under an existing trusted private parent; files are mode0600, directory0700 and existing output is refused. An INCOMPLETE marker is created before processing, candidate bytes are written and flushed before the summary, and COMPLETE.json records both hashes after writes succeed. Consumers must require COMPLETE.json with matching hashes and absence of INCOMPLETE; a summary alone never proves completion. Failures retain INCOMPLETE. This guards only this checkout, not every other public checkout or an untrusted parent. Hash rechecking is not immutable storage or independently trusted time.

The authoritative inputs are the Q2 financial history database and Q3 prepared v4 database documented in their ingestion checkpoints. Original archives are retained in private Library. The independently checked authoritative local outputs are the v3 completed pair directories; earlier exploratory v1/v2 outputs are superseded and must not be consumed as completed runs. Private generated candidates remain local derived artifacts and can be rebuilt; they are not claimed durably stored in Library. No raw candidate values belong in the public repository.

Next useful step is manual source-based comparability and availability review on predeclared cases, followed by permitted security/action-consistent outcomes. It is not a trainer fitted to these unqualified pairs.
