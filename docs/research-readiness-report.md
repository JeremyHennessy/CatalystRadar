# Connected real-evidence readiness report

Run `python3 backend/build_research_report.py` from the repository root. This
reads the ten manually reviewed records, saved provenance and the current saved
SEC submissions snapshots. It makes no network calls and never reads private
prices. Output is `data/research_report.json`.

The report hashes its inputs, reuses the study audit's byte verification,
parses matching submission bytes, checks issuer/accession identity and preserves
every reviewed record with explicit blockers. Original filing archive metadata
is not original filing content: those full-filing bytes are not published in this
repository. Missing and changed metadata cannot become qualified observations.

This is a real-data readiness audit, **not a historical training cohort**. It
never invents historical decision dates, event groups, features, outcome windows
or returns to make the standalone temporal and split checks pass. Those checks
are explicitly NOT RUN until real frozen inputs exist. Manual triage statuses
are not numerical predictive features. First-public availability, authentic
observation receipts, corporate actions, halts and outcome labels remain unproven.

The current report exposes the next acquisition/review work instead of silently
dropping cases. It does not change the frozen mechanical comparison or main
paper book. New filing data may change identity matches; provenance and input
hashes permit reproducing each saved report. `generated_at` is report execution
time, never an historical decision or source-publication time.

The existing `build_dashboard.py` run regenerates the report and identical web
copy (`web/research_report.json`). The existing SEC observation workflow commits
both copies with its saved snapshot. Its cadence, permissions and provider calls
are unchanged; a report-generation failure stops the existing pipeline. The
standalone report command updates only the canonical data copy; run the dashboard
builder to refresh the served copy too.
