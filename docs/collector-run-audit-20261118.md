# Named collector workflow audit, 18 November 2026

This supplements, rather than rewrites, the saved collector-status receipt snapshot. Its audit clock is separate. Build with `python3 backend/collector_run_audit.py`. It does not collect data, authorize requests, change schedules, enable trading, or establish complete global history.

## Observation provenance

Public GitHub workflow runs API `/repos/JeremyHennessy/CatalystRadar/actions/workflows/sec-observations.yml/runs?per_page=100` returned total_count 6, all six records and no Link header during this audit. Latest-attempt job steps were read separately for each listed run. This is a named-workflow snapshot, not an assertion about other workflows or consumers. Current job metadata is retained in the sanitized audit input. The input is a manually captured observation, not authenticated by the offline builder.

Run 44223484988 log explicitly prints `OUTSIDE_TRIAL_WINDOW` at 2026-11-18T02:28:28.6932015Z. Build, commit and publication steps skipped. Run 44013891129 uses the earlier window-gate conditional: build/scanner, commit and publication skipped. Its reason is reconstructed from the gate and skipped stages, not an explicit OUTSIDE_TRIAL_WINDOW log label. Neither execution is counted as a source request. Latest successful retained SEC receipt remains 2026-11-17T19:54:39.231235+00:00.

Run 43956540805 is successful at the job level but its retained receipt reports zero successful issuers: first source HTTP 403, nine not attempted after denial. The failed receipt was persisted and the publication step succeeded. Publication-step success is not an independent check of bytes served at that time. Three other retained SEC receipts have no workflow URL; they are not invented Actions runs.

Private workflow list was inspected in signed-in GitHub because the connector does not enumerate scheduled runs. The list showed exactly three runs: 44172913902, 43964984450 and 43628448789. Each latest-attempt job's collection and private retention steps succeeded. Latest run's UI datetime was 2026-11-17T15:46:59-05:00. Its retained receipt observed clock is 2026-11-17T20:49:18.653849+00:00, with eleven snapshots, each one hundred daily sessions. Commit 972b9be retained the private snapshots. Older source responses and exact start clocks are not reconstructed from green jobs. No private quotes, raw source bodies or logs are published by this audit.

## Interpretation limits

These are reported receipt counts, not new independent source-byte validation. Existing collector-status validation remains separate. A job execution is not admission; admission is not retrieval; retrieval is not persistence; a publication step is not deployed-byte verification. Snapshot history can become stale. GitHub-listed jobs do not prove the absence of external consumers or globally reserve any quota. No schedule, source request, protected workflow or continuation activation changed.

The public projection validates bounded input size, integer counts/IDs, enum status values, unique step numbers, UTC clocks no later than the audit and receipt/run clock consistency. Public latest execution is selected by timestamp, never array position. Private latest run is the explicitly observed fixed snapshot run 44172913902, not inferred from missing older clocks. Contradictory denied/non-success source statuses cannot become reported-complete metadata. This is deliberately a frozen audit, not a general live monitor.
