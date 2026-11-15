# Connected candidate rehearsal report

The normal dashboard/readiness build now calls the offline candidate normalizer
on the **latest retained scan**, then records a bounded summary under
`candidate_rehearsal` in both public `research_report.json` copies. It reads the
actual hash-bound source files, not fabricated input. No extra network request,
workflow, schedule, private storage access, classification or trade is added.
The prospective protocol remains inactive.

The latest-only scope is explicit: immutable reports from other runs stay
retained, but are not all expanded into the dashboard build. This avoids
multiplying old filing rows across every poll and calling them extra samples.
The offline normalizer can separately reproduce detailed observations for
explicitly selected reports.

## Reproduce

Run `python3 backend/build_dashboard.py` followed by
`python3 backend/verify_public_state.py`. `build_research_report.build` accepts
an explicit report-time anchor for deterministic reproduction. The summary
requires semantic equality between latest_scan and its retained per-run report;
a missing or mismatched receipt produces UNAVAILABLE with null counts, not a
successful zero-event cohort. A report later than the summary anchor is rejected.

Each available summary includes exact input hashes, report start/finish clocks,
per-source request/retrieval clocks and validation outcomes, the digest of the
full canonical normalized output, candidate/observation/old-row counts, conflict
counts, and every family's missing/invalid-field counts. Source failures and
scan errors are preserved; partial coverage is labeled PARTIAL_REHEARSAL.
The full normalized JSON can be reproduced with `normalize_candidates.py`.

The November 15 02:17 UTC manual report yields 1,591 metadata accession candidates,
1,580 older than 96 hours, ten validated metadata sources and UNKNOWN family
facts for every candidate. They are not 1,591 qualified financial examples or
new announcements. The separately reviewed ten-filing sample and its saved
private-original checks remain separate. No family classification or outcome
join is run by this summary.

## What still blocks actual freeze

- This is an offline retrospective rehearsal, not the binding/receipt of a
  prospective study. Source time claims remain unauthenticated metadata.
- The scheduled scanner still emits its existing recent-window view. This
  connected report recovers all observed recent-response rows but neither
  establishes complete SEC history nor fetches all original filings.
- General source-grounded financial extraction, verified underlying-event
  grouping, strict fact admission and actual classification-completion receipts
  must be connected before the relevant proposed study can be activated.
- Exact rules, extractor versions, source scope, inclusion policy and future
  window need a verified pre-observation freeze. Do not backdate a missed start.
- Corporate actions/dividends, session/security mapping, benchmark and halt
  coverage remain required before valid outcome labels. Raw daily prices are
  not a substitute for total returns or executable fills.

The private frozen mechanical comparison is unaffected and cannot establish
catalyst prediction skill.
