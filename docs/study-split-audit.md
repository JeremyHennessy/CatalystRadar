# Structural split audit, not historical forecast validation

`backend/study_split_audit.py` is a pure, bounded utility. It takes an explicitly supplied cohort, assigns chronological training/holdout/gap/purged/unresolved buckets, and checks related-event leakage. It does not fetch data, fit a model, change a schedule or admit any price feed. Its tests use synthetic observations only.

Required identifiers are a globally unique event ID, stable issuer ID and issuer-scoped event-group ID. Amendments and repeated reports about the same underlying event must share the group ID. The utility cannot discover this grouping from names, tickers or filing codes. Independently audited identity/grouping is still required.

Decision time must precede the outcome window. Training requires both window completion and actual label observation by the cutoff. Holdout labels are checked for invalid timing/nonfinite values too, but missing holdout labels stay in the cohort. Losses, missing labels and purged records remain explicit. Related groups cannot appear in both training and holdout, even when their windows do not overlap. Chronological purging already prevents an admitted training outcome window from overlapping a later holdout window; the issuer-window check is a defensive invariant.

A clean structural report does **not** establish a point-in-time universe, source authenticity, feature availability, data rights, corporate-action-adjusted outcomes, calibrated forecasts or profitable execution. `source_truth_verified` and `trade_eligible` stay false; predicted probability and expected return stay null. Run this alongside source/feature admission, not instead of it.

The main project still lacks a verified labeled historical cohort and a fitted, out-of-sample validated forecasting model. A catalog of filings and today's price histories are not substitutes. The next data milestone is a traceable cohort containing eligible events and negative/missing outcomes, with frozen features, historically valid security membership and comparable total-return labels before any statistical performance claims.
