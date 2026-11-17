# Six-horizon evidence-to-label readiness

Checkpoint HEAD: `0cd71613ece31536a187eb132222994acb35c9fa`. Assessment clock: 2026-11-17T23:54:00.411132+00:00. This is a scoped research assessment, not a new training/execution gate or complete $0-stage report.

## What the evidence establishes

The existing inventory was rerun at this HEAD: 10 retained header-feature rows / 50 values, zero decisions, zero first-public times and zero outcomes. Thus this specific feature set has zero usable decision/outcome pairs. The qualified count across all conceivable cohorts is unknown, not zero by assertion. No model or return study was run.

The independently audited retained price receipt covers 11 series × 100 daily dates, June 26 through November 16. All dates match the fixed scheduled-session window. November 17 collection occurred before the regular close; it did not contain a November 17 bar. This package references those prior hash-bound audits, not a new raw-price audit. Date coverage does not establish price correctness, corporate actions, historical identity, licensing or intraday coverage.

## First common failure

Before horizon-specific prices matter, the retained feature set has no source-bound frozen decisions/outcomes. Restored historical filings, source publication declarations and ingestion clocks must remain distinct. The later acquisition of a document is not proof we possessed it before a past decision.

## Horizon matrix

### 15 minutes

Status: BLOCKED. Additional horizon-specific blocker: `NO_VERIFIED_INTRADAY_PRICE_ENDPOINTS`.

Retained support: Daily date coverage only; no intraday decision-to-endpoint path.

Next action: Obtain permitted, timestamped entry and +15-minute observations with explicit session/overnight policy. Daily OHLC cannot reconstruct the path.

Dependency: Requires source rights/access and shared prerequisites; no authorized data route currently verified by this checkpoint.

### 60 minutes

Status: BLOCKED. Additional horizon-specific blocker: `NO_VERIFIED_INTRADAY_PRICE_ENDPOINTS`.

Retained support: Daily date coverage only; no intraday decision-to-endpoint path.

Next action: Obtain permitted, timestamped entry and +60-minute observations; predeclare handling of closes, halts and session boundaries. No daily-bar interpolation.

Dependency: Requires source rights/access and shared prerequisites; no authorized data route currently verified by this checkpoint.

### Same-day close

Status: BLOCKED. Additional horizon-specific blocker: `NO_FROZEN_DECISION_TIME_ENTRY_PRICE`.

Retained support: Daily date coverage only; no intraday decision-to-endpoint path.

Next action: Define whether decision occurs before the same session close and retain an identified entry observation. A daily open/low/high is not a price available at an arbitrary news time; do not manufacture same-day returns.

Dependency: Requires source rights/access and shared prerequisites; no authorized data route currently verified by this checkpoint.

### Next trading-session close

Status: BLOCKED. Additional horizon-specific blocker: `NO_QUALIFIED_ENTRY_ANCHOR_AND_ACTION_CONSISTENT_PRICE_LABEL`.

Retained support: 100 daily session dates per symbol support calendar indexing within fixed endpoints, not 1-session returns or known-at-time prices. No cross-window endpoints beyond Nov16 are present.

Next action: Predeclare decision-to-entry convention, then identify the first subsequent trading-session close from verified calendar and actual observations. For a close-to-close study, explicitly adopt that different entry convention before examining outcomes; require identity/actions/rights and exclude missing endpoints.

Dependency: Calendar indexing is feasible offline now; meaningful label construction remains blocked by shared prerequisites. Do not compute unqualified returns.

### Three trading sessions

Status: BLOCKED. Additional horizon-specific blocker: `NO_QUALIFIED_ENTRY_ANCHOR_AND_ACTION_CONSISTENT_PRICE_LABEL`.

Retained support: 100 daily session dates per symbol support calendar indexing within fixed endpoints, not 3-session returns or known-at-time prices. No cross-window endpoints beyond Nov16 are present.

Next action: Predeclare decision-to-entry convention, then identify the third subsequent trading-session close from verified calendar and actual observations. For a close-to-close study, explicitly adopt that different entry convention before examining outcomes; require identity/actions/rights and exclude missing endpoints.

Dependency: Calendar indexing is feasible offline now; meaningful label construction remains blocked by shared prerequisites. Do not compute unqualified returns.

### Five trading sessions

Status: BLOCKED. Additional horizon-specific blocker: `NO_QUALIFIED_ENTRY_ANCHOR_AND_ACTION_CONSISTENT_PRICE_LABEL`.

Retained support: 100 daily session dates per symbol support calendar indexing within fixed endpoints, not 5-session returns or known-at-time prices. No cross-window endpoints beyond Nov16 are present.

Next action: Predeclare decision-to-entry convention, then identify the fifth subsequent trading-session close from verified calendar and actual observations. For a close-to-close study, explicitly adopt that different entry convention before examining outcomes; require identity/actions/rights and exclude missing endpoints.

Dependency: Calendar indexing is feasible offline now; meaningful label construction remains blocked by shared prerequisites. Do not compute unqualified returns.

## Shared dependencies and executable next steps

- **event_decision (MISSING)**: Ten header-feature rows contain no decision, first-public time or outcome. Currently retained historical bytes and SEC acceptance times do not authenticate past availability. Next: Select from existing predeclared cohorts or predeclare one, and specify a deterministic decision rule; use already retained primary evidence only where availability can be justified. If it cannot, retain as retrospective research and do not invent a decision clock.
- **identity (PARTIAL)**: OpenFIGI query and Nasdaq Listed snapshot are current observations, not historical security identity or continuous listing proof. Issuer CIK is not a unique share class. Next: Require exact security/class and effective-date evidence for each proposed label interval; do not use ticker-only or current-mapping fallback.
- **rights (UNVERIFIED)**: AV account/intended-use training rights and broader redistribution are not established; free access and vendor training examples are not account entitlement. Next: Review applicable existing account terms without exposing credentials; absent verified intended-use permission, retain metadata audits only. No new account, plan or extra quota request.
- **action_consistency (MISSING)**: Raw daily prices have no validated split/dividend adjustment history. The 81 split-ratio rows in retained notes are issuer disclosure contexts, not effective-date events or watchlist-wide action coverage. Next: Find an authorized official action source with effective dates and class identity before constructing a raw-price exclusion or adjustment policy; no inferred dates, guessed ratios or zero-action default.
- **research_evaluation (NOT_REACHED)**: No qualified labels or predictive metrics. Related-event groups, temporal splits, overlapping-window purging, survivorship and delisting review, benchmark identity and costs remain necessary. Next: Reuse existing structural split/receipt audits once genuine examples exist; do not train a baseline merely to produce metrics.

## Acquisition route disposition

- alpha_vantage: Retained raw daily evidence only. Defer optional split probe: exclusive global key usage unknown; preserve existing collector and quota.
- alpaca: Documented free plan is not usable access: no authorized new credential/account or account-specific training rights verified.
- iex_hist: Official direct download unavailable; no current free equities HIST availability claim.
- stooq: Observed browser-verification challenge; do not retry or bypass. Rights unverified.
- dukascopy: User-aborted lookup remains cancelled; no coverage or rights claim.

The highest-value currently executable work is offline cohort/evidence adjudication and source-specific rights/availability review, not a model or additional unqualified price requests. No fully permitted and qualified label acquisition route is established here; this is not proof none exists. If an approved route later becomes available, independently verify a bounded real sample before broad ingestion.

## Research versus execution

A hypothetical close-based research label is not an auction execution or simulated fill. Research label prerequisites do not override separate quote, halt, liquidity, auction and risk controls. Paper engine remains disabled.

## Reproduce and inspect

Run `python3 backend/training_evidence_inventory.py --root . --output NEW_REPORT.json` at the checkpoint. The companion JSON records its exact SHA256, observed counts, and SHA256s for the price/calendar/reference/rights/feature/report/ledger evidence used. The inventory output is deterministic for unchanged inputs and HEAD. The assessment creation clock is not a source availability clock. Public evidence contains no raw OHLCV or private receipt paths.

The companion JSON is a manually adjudicated matrix, not a general validator; future input changes require re-review, not automatic admission. `qualified_label_count: null` for each horizon means no horizon-specific qualification census was performed. The narrowly scoped zero applies only to the retained feature-row inventory. All training/execution flags remain false.

Evidence: [source registry](source-registry.md), [retained-session audit](price-session-audit.md), [training inventory](training-readiness.md), [split-basis warnings](split-basis-evidence.md), [OpenFIGI limitations](openfigi-watchlist.md).
