# Retained public observation history

Future completed SEC metadata scans now append a complete report to
`data/sec-observations/<run_id>.json` before replacing `latest_scan.json`.
The existing trial workflow stages these JSON reports with the content-addressed
SEC snapshots. This adds no requests, issuers, schedule or trading activation.
The prospective study protocol remains draft and inactive.

Previously, complete per-run reports lived only under ignored `.data/scans`;
only the latest report and source bytes were published. No old observation
receipts are invented or reconstructed by this change. The directory starts
when the next actual scan completes, not when this code is released.

Each report preserves source request/retrieval clocks, hashes, observed events,
errors and skipped issuers. Repeated accessions across runs remain separate
observations, not independent samples. A later disappearance or changed metadata
does not delete an earlier report and does not establish SEC deletion. A
first retained observation is not necessarily first public availability or even
this scanner's first-ever observation.

Reports use bounded (4 MiB), finite canonical JSON. Exclusive atomic hard-link
publication prevents replacing a run ID or exposing partially written final
reports. Identical retry bytes are idempotent; a reused ID with changed bytes
fails closed. Temporary files have no `.json` suffix and are never staged by the
workflow. Git publication is separate: local persistence alone does not prove
remote retention, and a failed run or process interruption before finalization
may leave no completed report. Actions run history is needed to identify missing
polls. These are not authenticated receipts or completeness guarantees.

This history retains public SEC metadata only. Raw complete filings, restricted
price data, credentials and local diagnostics are not included. Source errors
remain sanitized. The disabled book, frozen private mechanical comparison and
its code pins are unchanged. No decision-time or forecasting eligibility is
raised by this history.
