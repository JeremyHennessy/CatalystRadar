# Offline observation-receipt binding

`backend/study_receipt_audit.py` extends the declared study split, timing and
raw-byte audit with a join to retained observation receipt bytes. It makes no
network requests, reads no files itself, and is not registered with execution.

Each feature source supplies `observation_receipt_sha256`. The caller passes a
mapping from this digest to exact retained JSON bytes. Version 1 receipts have
exactly `version` (integer 1), `source_ref`, `sha256` (the source-byte digest),
and timezone-aware `observed_utc`. Receipt and source reference, source digest
and observation instant must agree. Equivalent timezone offsets are accepted;
duplicate JSON keys, invalid schema, missing receipts and changed bytes fail.
A later receipt cannot justify an earlier declared observation. Later revisions
need distinct source and receipt hashes rather than overwriting a prior vintage.

Only fixed check labels and existing source identities/hashes appear in the
report. Receipt content and source bytes remain with the caller. Both receipt
count and per-receipt/aggregate byte sizes are bounded. Missing observations,
features and holdout outcomes remain missing rather than becoming zero values.

## Limits and next integration step

This checks consistency of supplied evidence, not its authenticity. Matching a
hash does not prove that a receipt existed at the declared time. A caller can
invent matching bytes and dates, so `observation_receipts_verified`,
`trusted_clock_verified`, `source_authenticity_verified`, and `trade_eligible`
remain false even when every integrity check passes. Feature calculations are
not recomputed. The existing declared timing checks still apply independently.

Do not manufacture historical receipts from current downloads. Before use in a
prospective study, add a reviewed adapter from actual retained collector receipts
and independent immutable timing evidence, preserving source and receipt vintages.
Then validate extraction/calculation provenance and study eligibility separately.
No current research report, private collector pin, public observation, paper
ledger or trading gate is changed by this module. Tests use explicitly synthetic
receipts; they are engineering checks, not market evidence or model validation.
