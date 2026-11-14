# Prospective SEC cohort v1: proposed, not activated

`research/prospective-cohort-v1.json` is a bounded **draft protocol**, not a
pre-registration receipt, automated collector, fitted score or active experiment.
The existing private alphabetic $500 mechanical comparison is unchanged and is
not a catalyst-skill test. This protocol makes no provider calls or orders.

## Scope and activation gate

The proposed convenience universe is the ten issuer/CIK pairs already in
`data/watchlist.json`. This is not the entire stock market, a representative
sample or a historically survivor-bias-free universe. Include every 8-K and 8-K/A
first observed from those issuers in the proposed November 16–20 UTC window,
including irrelevant, rejected, ambiguous and unclassified filings. Preserve
accession IDs and issuer-scoped underlying-event groups; amendments are not
independent discoveries. This is an observed-candidate cohort: polling gaps,
request failures and truncated feeds remain visible, and no complete-market or
complete-filing coverage is claimed. A filing accepted earlier but only now discovered is
marked rediscovered, not presented as a fresh announcement.

**Before any qualifying observations**, archive the exact universe, source list,
full rule definitions, extractor/version, protocol bytes/hash and activation time
with an independently verified immutable receipt. Four family names in the JSON
are not complete extraction rules. Bind the existing detailed definitions and
resolve any ambiguity before freezing. Do not claim the draft is frozen merely
because it was committed to Git. If the receipt is late or source capture cannot
start, retain the proposed dates as a missed plan and create a new prospective
version with future dates. Never backdate activation or add observed outcomes to
an allegedly untouched cohort. No automatic activation is implemented here.

The current retrospective readiness report of ten reviewed filings is separate.
Its report-time audit anchor is not a historical decision. Old catalog paths and
newly retrieved prices are not prospective observations.

## One reproducible event record

Retain original bytes and hashes, source/request/retrieval times, SEC acceptance
and filing dates separately, source revisions, identity mapping, event group,
classification status/reasons and the feature computation time. Original bytes
must be available for the byte audit; metadata hash matches do not authenticate a
filing's contents. Missing or ambiguous original material is held, not silently
substituted. Features are finite source-grounded values or explicit nulls, not
invented zeroes. Unknown grouping blocks split admission.

The actual observation-driven decision time is the latest of source observation,
feature calculation and classification recording. Freeze the feature row and
its rejection/missing status then, before querying or inspecting outcome labels.
Subsequent correction creates another version and preserves the old one. A
source missing from a later feed is not proof of deletion. Scheduling delays
shift the observation/decision, not the historical clock.

## Outcomes, not claimed fills

For admitted feature rows, define the measurement anchor as the first complete
regular-session close **strictly after** the actual decision, using a verified
exchange calendar. A decision at or after the close advances to the next session.
Measure the primary outcome at the fifth subsequent regular-session close and
a secondary outcome at the first. The fixed primary is five-session total return
minus SPY total return over the identical interval. Store both gross returns and
the difference. This is a price/return measurement, not an auction-fill claim.

Do not treat raw daily closes as total-return labels. Admission requires correct
security mapping, sessions, corporate-action coverage, dividend amount/currency
and treatment, benchmark data and halt/missing-close review. A positive split or
dividend record is useful evidence, not proof there are no other actions. Unknown
fractional-share settlement, currency, payment/reinvestment convention or a
missing endpoint stays unresolved. A known affected symbol remains held unless
its precise treatment is independently validated. Do not infer execution or an
exit during a halt. No universal reverse-split rounding policy is assumed.

All missing labels stay null with reasons and their original cohort membership.
Do not replace them with zero, stale prices or a more convenient symbol/date.
Late labels retain observation time; a training cutoff cannot use labels learned
later. Five-session labels for late-week events require subsequent sessions;
Friday is not a promise that all outcomes will be available.

## Comparisons and interpretation

Report the fixed primary and secondary separately, alongside:

- Zero gross cash return as a no-position reference, without claiming measured
  cash interest.
- Same-window SPY total return; excess return already subtracts this benchmark.
- Equal-weight descriptive returns of all source-qualified cohort events with
  valid labels, not only rule-positive events. Show qualifying/missing counts
  for each rule and comparator so denominator changes cannot hide failures.

Repeated/overlapping issuer events are dependent observations. Retain them and
report both event and issuer-group counts; do not treat them as independent bets
or add overlapping returns into a $500 portfolio. Report missingness and the
number of distinct issuers beside any average. A complete-case mean is explicitly
conditional on observable outcomes, not the whole cohort's performance.

Show gross marks and optional 0/10/25/50 bps round-trip cost sensitivities as
illustrations, not realistic execution costs or promised profits. No actual
spread/slippage data or fills are established by those deductions. Do not select
the best rule/horizon/cost after observing results and present it as prespecified.

This one-week pilot is an operational shakedown. It cannot establish calibrated
probabilities, forecasting skill or deployable returns. No fitted model is
introduced. Any later score study needs a separate pre-outcome protocol, adequate
independent event groups, training-only tuning, chronological purging and a
subsequent untouched holdout. An absence of events is a valid zero-event report,
not permission to broaden the universe after the fact.

## Completion checklist

1. Verify freeze receipt and capture start; otherwise report NOT ACTIVATED.
2. Preserve every observed candidate and all source/rejection statuses.
3. Run source-byte, feature-clock and grouping audits; report every failure.
4. Join only valid outcome evidence when available, with source and label clocks.
5. Produce versioned counts, baselines and missingness, never fabricated returns.
6. Keep protocol, feature rows, revisions and outcome report hashes together.

The existing automated price collection/evaluator schedules are not modified by
this document. Wider collection, corporate-action probes and private execution
still require safe quota accounting and the applicable authorization.
