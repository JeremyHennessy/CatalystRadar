# Repeated financial contexts: a concrete leakage warning

Starting commit: `4006b68e4342d9f350caea7b7b9d09d75eb78492`.

The completed Q2/Q3 private fact-candidate artifacts were audited together before treating their rows as independent research observations. Both completion receipts, summary hashes and exact candidate-file hashes must match the previously published checkpoint. Database/archive lineage remains attached to each retained version. No original source is fetched or modified.

## Verified scope and result

- 49,852 current/prior fact observations from 10,069 accessions.
- 49,591 exact issuer/tag/taxonomy-version/date/quarter-count/unit/dimension/coreg context keys.
- 246 contexts appear in multiple accessions: 204 have numerically equal values; 42 contain different reported numbers.
- Of these, 86 contexts cross the Q2/Q3 filing batches: 61 numerically equal and 25 containing different numbers.
- Another 44 near-contexts differ in taxonomy version. They are **unassessed**, not merged or silently discarded as unrelated.

These count units are different. They are not 49,852 independent events or training examples, nor a union of distinct securities. One context can have more than two observations. A CIK identifies an issuer, not a tradable share class or historical symbol. The source cohort remains the selected four-tag feasibility sample, not an unbiased earnings dataset.

The dated JSON publishes aggregate counts and source hashes only. Private detailed groups preserve every observation's original CIK, accession, database/archive hash, source row ID, current/prior role, value and filing/accepted fields. No raw value or issuer identity is added to this public report.

## Exact meaning

The tool compares decimal values exactly, without floats, division, rounding or return calculations. Formatting-equivalent strings such as `1.0` and `1` are numerically equal. Missing or nonfinite values cannot count equal. An identical database-row reference supplied twice fails rather than manufacturing another observation. A single accession represented by different source artifacts is separately categorized, never counted as multiple filing events; none was observed in this run.

Different numbers do not establish a restatement, correction, error or economic change. Equal numbers do not prove identical accounting meaning or independent evidence. Repeated contexts can result from amendments, recast comparatives, recurring disclosures or other causes requiring original-source review. The output does not choose a preferred version or replace prior observations.

Exact context groups are narrower than real event families. Different taxonomy versions, durations, units, accounting scopes or related issuer events may still leak information across a model split. The 44 version-different near-contexts are counted as an explicit unresolved limitation. No complete event-grouping, securities mapping, temporal partition, public-availability proof, qualified label or model evaluation is produced.

## Reproduction and safety

Run `backend/financial_context_overlap.py` with the committed financial-pair checkpoint, both completed private pair directories, and a new private output directory. This is an offline read-only audit of retained inputs. Input hashes are checked again before output. The strict JSON reader rejects duplicate keys/nonstandard constants and bounds input size. Output uses the existing INCOMPLETE/COMPLETE protocol, modes0700/0600, outside this checkout under a trusted existing parent. This is not immutable storage or a guarantee against an untrusted parent; other publication checkouts are not detected.

Private groups are written under the shared protocol's `candidate-pairs.json` filename, though they contain repeated-context groups, not new paired economic observations. Consumers must verify both completion hashes and absence of INCOMPLETE. The derived private groups are local and reproducible; no new durable Library save is claimed. Original source archives remain retained separately.

## Consequence for future research

Do not randomly split these fact rows or assume filing-quarter boundaries prevent leakage. Preserve the versioned evidence and assess related-event families before a chronological split with suitable purge/embargo windows. Real first-public clocks, security-level identities and valid outcomes are still missing. Training and execution remain disabled, and the count of qualified examples is unchanged.
