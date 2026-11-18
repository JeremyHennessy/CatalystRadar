# Four-quarter financial context overlap: evidence, not model results

Starting HEAD: `64159e1108080419e57dc59a9a5bb801a6f19167`. This offline study reuses the existing reviewed pair extractor and context-overlap functions without changing their code or rules. It adds no provider requests, model, decision clocks, returns or trades.

## Why this is useful

A longer filing archive can multiply repeated observations without creating independent events. We applied the same narrow, pre-existing four-tag rules to the newly retained 2025 Q4 and 2026 Q1 batches, then compared them with the unchanged completed Q2/Q3 artifacts. The goal is to expose context duplication and potential temporal leakage, not maximize a training sample count or infer restatements.

## Fixed extraction scope and actual results

The four predefined tags are Revenues, RevenueFromContractWithCustomerExcludingAssessedTax, NetIncomeLoss and EarningsPerShareDiluted. The extractor requires supported 10-Q/10-K forms and amendments, standard taxonomy, exact unit/type, qtrs=1, empty segment/co-registrant fields, supported current/prior calendar-anniversary dates, unique fact context and no selected footnote requiring review. Blank/nonfinite values are not zero. Every considered group has an explicit disposition; rejected source rows remain in the private databases.

| Filing batch | Target-tag rows | Excluded dimension/co-registrant rows | Excluded non-single-quarter rows after dimension filter | Candidate pairs |
|---|---:|---:|---:|---:|
| 2025 Q4 | 276,499 | 210,954 | 30,593 | 12,874 |
| 2026 Q1 | 210,963 | 165,361 | 34,939 | 2,828 |
| 2026 Q2/Q3 | See original checkpoint | See original checkpoint | See original checkpoint | 12,632 / 12,294 |

The relatively few Q1 candidates are consistent with its annual-heavy filing mix; this is a selection effect, not poorer company quality. The explicit first two exclusion stages leave 34,952 Q4 and 10,663 Q1 rows. Their remaining context groups have these dispositions:

- Q4: 13,861 groups = 12,874 candidates + 22 footnote-review + 33 missing-current-period + 193 missing/invalid-value + 210 missing-prior-period + 510 unsupported-form + 19 unsupported-unit.
- Q1: 3,531 groups = 2,828 candidates + 5 footnote-review + 96 missing-current-period + 55 missing/invalid-value + 147 missing-prior-period + 392 unsupported-form + 8 unsupported-unit.

“Candidate pair” is two context-matched numerical observations within a filing, not comparable financial performance. qtrs=1 does not supply exact duration starts, an empty dimension string does not prove consolidated scope, and calendar anniversaries do not capture all 52/53-week or leap-year fiscal calendars. EPS retains raw unit USD with perShare taxonomy type; it is not silently combined with dollar profit or basic EPS.

## Four-batch overlap

Across 40,628 candidate pairs, the existing matcher examined 81,256 source fact observations from 16,364 unique accession strings:

- 80,636 exact issuer/tag/taxonomy-version/date/duration/unit/dimension keys.
- 605 contexts have observations in multiple accessions: 515 numerically equal and 90 with different reported numbers.
- 275 of those contexts cross filing-batch boundaries: 213 numerically equal and 62 different.
- 269 near-context groups differ in taxonomy version and remain explicitly unassessed.

These count units differ. The 275 cross-batch contexts are a subset of 605, not additional events. The excess of observations over exact keys is not an event count. Equality does not establish independent confirmation or identical accounting meaning; differences do not establish correction, restatement or economic change. CIK is issuer-level, not tradable-security identity. Exact matching deliberately misses some related facts/events; this is not an exhaustive leakage grouping or a ready train/test split.

The earlier Q2/Q3-only checkpoint remains unchanged. Expanding scope increased observed overlap, but did not improve verified first-public clocks, identity, corporate actions, price labels or training rights. No qualified sample count or predictive metric is inferred.

## Reproduction and provenance

The public `four-quarter-context-checkpoint-2026-11-18.json` contains the exact per-batch summary and SHA256 of each private candidate file, original archive and private database, plus unchanged tool-file hashes. The public `four-quarter-overlap-2026-11-18.json` is byte-identical to the private overlap summary and binds the checkpoint hash. Only aggregate counts and hashes are public; all values, identities and individual source-row references remain private.

Recreate Q1 and Q4 candidate outputs with the existing `backend/financial_pair_candidates.py` CLI using the database/archive hashes in the checkpoint and new private output directories. Reuse or reproduce the previously completed Q2/Q3 candidate outputs. All four must have matching COMPLETE hashes and no INCOMPLETE marker.

The existing overlap CLI names only Q2/Q3 directories; **do not pass four batches through those two CLI flags**. Its reviewed `audit(checkpoint, batch_directories)` Python API accepts an exact dictionary whose keys match the checkpoint. Invoke it with these four keys and private paths: `q4_2025_filing_batch`, `q1_2026_filing_batch`, `q2_2026_filing_batch`, `q3_2026_filing_batch`. Use the existing private output protocol: create a new trusted 0700 directory outside publication checkouts, write INCOMPLETE with `write_private`, call `audit`, then `publish` to write private evidence/summary/COMPLETE and remove INCOMPLETE. Source hashes and completion guards are rechecked by the existing functions. Do not bypass these guards or overwrite approved artifacts.

This package's checkpoint creation clock is an audit clock only. The source as-filed/accepted dates remain documentary fields, not proof of first-public availability or a decision made at that time. Private database-to-archive derivation was independently verified during the prior ingestion audits; pinning two hashes alone does not prove that derivation.

## Next meaningful step

Use repeated-context warnings when selecting or adjudicating a predeclared source-review cohort, preserving negative/unchanged/rejected cases and exact versions. Primary disclosure review is still needed to determine whether two observations refer to comparable operations or a genuinely new catalyst. Do not “deduplicate” away amendments or automatically label the 90 different contexts as restatements. The [six-horizon readiness blockers](horizon-readiness.md) remain in force; execution stays disabled.
