# Source-bound header feature rows, not financial signals

`filing_feature_rows.py` reopens the privately retained original documents and
recomputes five mechanical SEC-header features: item count; explicit results,
Regulation FD and material-agreement markers; and an8-K/A amendment flag. Each
value binds the full-document hash, exact header byte span and span hash, actual
retrieval clock and a **current** computation clock. No raw document content or
private storage identifiers appear in the public derived artifact.

These features describe what a complete filed header explicitly says. A results
marker does not establish growth; a RegFD marker does not establish a guidance
raise; an agreement marker does not establish a customer contract. A0 means only
that exact marker is absent from the complete header. Comparators, first-public
availability, decisions and outcomes remain null. Manual review reasons and all
missing/invalid cases remain visible. No catalyst score or admission gate changes.

Reproduce locally after restoring the private originals:

```
python3 backend/filing_feature_rows.py --reviews data/filing_reviews.json --archive-dir PRIVATE-DIRECTORY --output NEW-FEATURE-ROWS.json
```

The new output must not already exist. New analysis gets a new computation clock;
never rewrite it as if extracted before the event. This selected retrospective
sample is not a prospectively frozen training cohort. Financial extraction remains
unverified: TXMD's rounded prior EPS/quarter discrepancy and the pending guidance
comparators have not been resolved by these structural features.

The public readiness builder checks saved feature rows against exact review and
original-checkpoint bindings. It labels them **header feature rows (saved
analysis)**, not newly recomputed private bytes. The original files are unavailable
to a public build; structural metadata checks cannot authenticate the artifact.
Any stale/invalid binding removes the saved count, without changing the paper book.

The recorded computation clock is the analysis invocation timestamp (or an
explicit timestamp supplied to reproduce a saved artifact), not an authenticated
completion receipt. It must not be used to prove prospective decision readiness.
