# Structural split audit, not historical forecast validation

`backend/study_split_audit.py` is a pure, bounded utility. It takes an explicitly supplied cohort, assigns chronological training/holdout/gap/purged/unresolved buckets, and checks related-event leakage. It does not fetch data, fit a model, change a schedule or admit any price feed. Its tests use synthetic observations only.

Required identifiers are a globally unique event ID, stable issuer ID and issuer-scoped event-group ID. Amendments and repeated reports about the same underlying event must share the group ID. The utility cannot discover this grouping from names, tickers or filing codes. Independently audited identity/grouping is still required.

Decision time must precede the outcome window. Training requires both window completion and actual label observation by the cutoff. Holdout labels are checked for invalid timing/nonfinite values too, but missing holdout labels stay in the cohort. Losses, missing labels and purged records remain explicit. Related groups cannot appear in both training and holdout, even when their windows do not overlap. Chronological purging already prevents an admitted training outcome window from overlapping a later holdout window; the issuer-window check is a defensive invariant.

A clean structural report does **not** establish a point-in-time universe, source authenticity, feature availability, data rights, corporate-action-adjusted outcomes, calibrated forecasts or profitable execution. `source_truth_verified` and `trade_eligible` stay false; predicted probability and expected return stay null. Run this alongside source/feature admission, not instead of it.

The main project still lacks a verified labeled historical cohort and a fitted, out-of-sample validated forecasting model. A catalog of filings and today's price histories are not substitutes. The next data milestone is a traceable cohort containing eligible events and negative/missing outcomes, with frozen features, historically valid security membership and comparable total-return labels before any statistical performance claims.


## Declared feature-timing audit

`audit_study(rows, required_features=[...], training_cutoff_utc=..., holdout_start_utc=...)`
adds feature observation/calculation checks to the existing structural split audit.
Declare the numeric feature names before inspecting outcomes. Each row's `features`
list must supply those names, finite numeric values, a timezone-aware `computed_utc`,
and a nonempty `sources` list. Each source records `source_ref`, a lower-case SHA-256
`sha256`, and timezone-aware `observed_utc`. These fields bind the declared source
vintage; they are not provider entitlement or automatic content verification.

A source cannot be observed after its feature was computed. Sources observed or
features computed after the decision fail the timing check, including in holdout,
purged and unresolved rows. A past filing date cannot override a later retrieval.
Missing features remain explicit failures, not zero imputation or silent deletion.
Assignments and losses/missing outcomes are retained unchanged; inspect both the
original split assignments and `feature_checks`. `all_declared_checks_passed` is
false for an empty cohort and combines structural and declared-clock checks.

This is deliberately conservative: retrospectively calculated features fail even
if the underlying disclosure predates the decision. A separate, independently
qualified historical-reconstruction protocol would be needed to relax that rule.
The original `audit_partition` remains structural-only for compatibility; it is
not a substitute for feature validation. Neither function is currently a live
trading or model-training gate.

Caller-supplied clocks and hashes are claims, not proof of source availability,
feature correctness, a timestamped pre-registration, complete coverage, or a
profitable forecast. `source_truth_verified`, `feature_source_bytes_verified`
and `trade_eligible` remain false. No real cohort, provider calls, orders, workflow
activation, or changes to the frozen private comparison are introduced here.
