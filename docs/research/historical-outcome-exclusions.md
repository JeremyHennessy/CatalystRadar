# One-session descriptive research: reproducible exclusions

This offline audit operationalizes the existing six-horizon readiness checkpoint for one narrow question: what descriptive close-to-close changes follow retained results-of-operations headers? It is not a profitability forecast, causal study, or backtest.

Policy `results-header-next-session-close-v1` selects every retained header row reporting results of operations, excluding amendments, ordered by accession. Selection does not use prices, ticker coverage, observed returns or financial direction. All ten rows are accounted for. The policy is declared retrospectively now, not claimed to have existed at historical event time.

Entry convention for a future qualified study: the first regular-session close strictly after verified first-public event time; endpoint is the next actual trading-session close. This is a descriptive price convention, not an executable fill. No convention is applied until time, security/class, rights, corporate actions and actual endpoints are qualified.

## Actual result

The pinned retained feature snapshot contains ten rows; one matches the header policy (accession `0001213900-26-119681`), nine do not. The selected row has no first-public or decision timestamp and is excluded with first dependency `VERIFIED_EVENT_FIRST_PUBLIC_TIME`. It is a reported header, not independently verified earnings content or a novel economic event. Qualified outcomes: **zero**.

Further dependencies remain visible: source-bound entry convention/decision evidence, historical security/share class, intended-use price rights, effective corporate actions and qualified endpoint observations. Populating a timestamp or eligible flag cannot make this audit admit a row.

The prior checkpoint records eleven daily series with 100 sessions each, June 26–November 16, 2026. It does not verify intraday evidence, corporate actions, historical identity or training rights. This audit references that metadata, not new raw-price decoding or renewed entitlement verification. No ticker join is attempted; current ticker matches would not prove historical security identity. No licensed quotes/derived returns, downloads, orders or workflow changes occur.

## Reproduce

```
python3 backend/historical_outcome_audit.py . NEW_OUTPUT.json
python3 -m unittest discover -s backend -p 'test_historical_outcome_audit.py'
```

Both inputs are pinned in code. Changed snapshots fail for review rather than silently extending the cohort. Every selected/excluded accession is retained in the local output. The output is a diagnostic artifact, not an app admission API or a new public data feed.

Next useful evidence: establish a source-bound first-public clock and original event-content/novelty assessment for the single selected accession. Do not substitute its filing acceptance time, later collection time, or another easier event. Price-use permission and historical class/action evidence remain independent blockers even after timing is resolved.
