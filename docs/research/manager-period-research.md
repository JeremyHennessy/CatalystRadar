# Reporting-manager period research

This capability answers a narrow useful question: **which reported periods, filing dates and amendment/confidentiality contexts are present for a reporting-manager CIK in the retained 13F batch?** It does not require, and does not invent, a manager-to-held-company security mapping.

## Actual source and diagnostic cohort

The retained June–August 2026 SEC filing batch contains 11,852 submissions from 10,807 manager CIKs. Of those managers, 230 have more than one distinct report-period label in this batch. This is not 230 managers with observed purchases or complete historical portfolios.

The small public example selects the numerically smallest five manager CIKs meeting that multi-period condition, and retains **all 38 filings** for those managers: 0000051762 (2), 0000072971 (2), 0000275484 (21), 0000733986 (6), and 0000753967 (7). Selection follows a deterministic diagnostic rule after coverage inspection; it is not a preregistered sample, manager ranking or signal. No manager names or raw holdings are published.

For example, manager CIK 0000051762 has two original 13F-HR records in this batch: a March 31, 2026 report period filed August 6 and a June 30, 2026 report period filed August 7. This establishes the two as-filed period/date pairs only, not when the holdings were actually established, their changes, or complete availability at an earlier decision time.

`web/holdings/manager-period-research.json` is a bounded source-backed example (five managers, 38 filings), not a feed of all managers. An exact-manager query can inspect any manager represented in the same retained database, bounded to 100 filings. An absent manager is scoped absence in the batch, never zero holdings or no activity.

## Read-only query and provenance

`backend/manager_period_research.py` verifies the complete retained ZIP and SQLite hashes before and after reading. It opens SQLite read-only, checks integrity, validates unique submission/cover/summary joins, source categories and dates, and preserves filing row identifiers. The earlier independent full-field ZIP-to-database audit establishes derivation; hashes alone do not prove it. No source HTTP request occurs.

```sh
python3 backend/manager_period_research.py \
  --database PRIVATE_HOLDINGS_SQLITE \
  --database-sha 5117bb2573288481d336dde11232ffb8bc64cb04a495f0fc179a64bf0e2aafda \
  --archive PRIVATE_RETAINED_13F_ZIP \
  --archive-sha 4db97d5652e262de51617971104e06313211de4d092e6bcb5d7bf34ee7efe054 \
  --manager-cik 51762
```

Omit `--manager-cik` for the first-five diagnostic cohort; `--cohort-limit` supports 1–10. Output is JSON to stdout only, after validation. No file-writing or provider capability is exposed. Raw data paths stay local and are not included in output. The published source URL and archive/database hashes identify the retained inputs. Exact download and first-public clocks remain unknown.

## Required interpretation

Manager CIK identifies the reporting entity, **not an issuer of a held security**. Do not merge these managers into the company research queue by CIK, name or ticker. Holdings values, shares, identifiers, names, addresses, signatures and contacts remain private. No portfolio value, ownership, trade flow, strategy, forecast or qualified outcome is calculated.

Each source filing remains distinct, including amendments, restatements, added-holdings amendments and notices. A form/cover amendment mismatch is explicitly retained rather than resolved. Blank flags are preserved as blank, and missing summary records use null with a presence flag. Confidentiality flags are declarations, not assurance of complete disclosure. Dates are report-period and filing-date labels, not transaction or first-public instants. Constructed SEC accession lookup links have not been fetched or authenticated as original filing URLs.

UI may expose this small example alongside the existing 13F coverage, with clear diagnostic scope and original-review links; no new broad manager browser or security cross-link is implied. Tests cover full selected history, numeric CIK ordering, unknown queries, notice context, amendment contradictions, malformed joins/dates/flags, bounds, deterministic output and privacy field exclusions. Held reports, ledger, source files, collectors and current UI are unchanged.
