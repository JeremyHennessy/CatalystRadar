# Reported insider transaction codes: evidence and review queue

Starting HEAD: `f265f1e1ad57ea25eb577c0cd19b7e6521f82403`. This offline package makes the previously retained Q3 Form 3/4/5 data usable as a source-context review queue. It does not download data, issue a trading signal, identify insider intent, calculate dollar flows or train a model.

## Source and scope

The retained [SEC insider-transactions archive](https://www.sec.gov/files/datastandardsinnovation/data/insider-transactions-data-sets/2026q3_form345.zip) has SHA256 `a4e6a681cfcfa43a3d9e4ca9cfec1fd26a59d0a01eac7e9f7b5a0122092c90f3`. Its bundled `FORM_345_readme.htm` SHA256 is `38a414683130ea5371267aec6279273d0184785ca3a26225f8af686b920c9186`; Appendix 6.2 is the source for transaction-code meanings. The existing private database SHA256 is `360491837fa5a8fd45d9d7c3b6b06a19324954bc839e203f2ad6235e88b14cae`. Source-to-database ingestion was independently verified earlier; hashes alone are not proof of derivation.

This audit covers all 59,885 **non-derivative transaction rows** in that retained batch, joining their submission and referenced footnote evidence. It does not cover derivative transactions or holdings and never joins reporting-owner rows, avoiding owner multiplication and unnecessary private owner names/addresses. Filing-quarter coverage is not transaction-quarter coverage.

## What was found

The source reports 5,184 P-coded purchases and 25,441 S-coded sales. The SEC definition permits **open-market OR private transactions** for both; calling all of them open-market buying or selling would overstate the evidence. Other codes include 9,817 grants/awards or related acquisitions (A), 7,433 exempt exercises/conversions (M), 6,802 exercise-price/tax-withholding transactions (F), and 1,035 gifts (G). All other codes and four missing codes remain separately counted in the companion JSON.

The review queue preserves every row and records overlapping diagnostics:

- 82 P/S rows have opposite acquired/disposed fields: 6 P+D and 76 S+A. No value is repaired or direction inferred.
- 979 transaction rows belong to amended Form 4/A submissions; original/amendment reconciliation is not performed.
- 49,551 rows reference footnote context. Multiple comma-separated IDs are resolved within the same accession, in source order. Missing, ambiguous or unsupported references are explicitly flagged rather than ignored; none of those resolution failures occurred in this actual batch.
- 3,939 rows have missing prices; 11,385 have zero prices and 48 have zero shares. These can be valid disclosures for gifts, grants or other events. A diagnostic is not a finding that the source is erroneous.
- 567 rows have deemed-execution-date context, 67 report an equity swap, and 562 have a transaction-form field different from the submission form. These differences require context, not automatic rejection as unlawful or fraudulent.
- Two source transaction dates are later than the corresponding filing date. They remain source anomalies to review, not repaired dates.

The transaction rows span 28,972 accession strings. By submission form: 58,855 rows are Form 4, 979 Form 4/A, and 51 Form 5. There are 7,745 rows without one of the listed diagnostics; **these are not qualified observations or trading signals**, and the rules are not a complete financial validation.

## Timing and intent remain unverified

Transaction dates and filing dates are preserved as date-only fields. Calendar-day lag buckets are descriptive: zero days 5,001; 1–7 days 52,228; 8–30 days 1,176; over 30 days 1,478; negative two. They are not business-day filing deadlines, legal-lateness findings or authenticated first-public timestamps. Do not backdate research availability to transaction dates.

The submission-level AFF10B5ONE field is preserved with its raw spelling. At the transaction-row level, 18,463 rows inherit a submission reporting true and 41,422 reporting false. This does **not** establish plan applicability, validity or intent for every transaction in that filing. No per-row 10b5-1 inference is made.

Prices/shares remain as filed. No currency or economic exposure is inferred; no shares-times-price aggregation, current ownership or investor intent is computed. A P/S code, positive value or byte-valid footnote link does not establish a verified executable market trade. This package adds no financial recommendation or predictive claim.

## Functional output and reproduction

`backend/insider_transaction_evidence.py` validates pinned input hashes, required database schemas, accession/transaction identity, complete private output and unchanged input hashes. Its private row-level queue contains source rowids and canonical full-row hashes; selected transaction/submission fields; reported-code category; raw date/plan fields; diagnostic reasons; and footnote row/hash references. It omits owner names, addresses and footnote text. Original raw fields remain in the retained private database/archive. Canonical row hashes are hashes of a defined JSON serialization, not raw TSV byte spans.

The public JSON is exactly the private completion summary: counts, source hashes and caveats only. Flags overlap and must not be summed into distinct-row totals. Output uses the existing private 0700/0600 INCOMPLETE/COMPLETE protocol and refuses overwriting. No new collector, workflow, paper action or dashboard change is included.

```sh
python3 backend/insider_transaction_evidence.py \
  --database PRIVATE_DATABASE \
  --database-sha256 360491837fa5a8fd45d9d7c3b6b06a19324954bc839e203f2ad6235e88b14cae \
  --archive PRIVATE_INSIDER_ZIP \
  --archive-sha256 a4e6a681cfcfa43a3d9e4ca9cfec1fd26a59d0a01eac7e9f7b5a0122092c90f3 \
  --output-directory NEW_PRIVATE_OUTPUT
```

Synthetic tests cover P/S scope and contradictory directions, amendments/form differences, zero/missing/nonfinite numeric fields, date-only lag interpretation, plan flags, multi-ID/missing/ambiguous footnotes, identity/schema failures and private output completion. They are not evidence of a profitable insider strategy.

Next: use a predeclared review sample to inspect primary filings/footnotes and reconcile amendments before considering materiality or historical event labels. Issuer CIK/ticker is not historical security identity. Licensed price/action coverage and source-bound decisions/outcomes are still absent; training and execution remain disabled.
