# Manager-period source-row reconciliation

This bounded research view reconciles exact prepared-source rows between selected original and first-restatement filings. It does not reconstruct a portfolio, infer trading, identify a security, establish legal supersession or measure economic changes.

## Retrospective fixed selection

The policy covers **all eligible groups in one exact retained June–August 2026 Form 13F prepared archive**, not all historical amendments or all manager activity. It groups normalized valid filing-manager CIK and parsed SUBMISSION report period. It is retrospective and informed by prior inspection, not a statistically unbiased sample or authenticated preregistration.

The policy was saved locally before the first reconciliation build, with SHA-256 `fcea0677bd05820f69d72095bc8a7189ed8aa7bbe6fb9ff068fcb527f7f90237`. It is embedded in the output and hashed with sorted-key compact ASCII-escaped JSON plus newline.

Of 11,852 submissions, there are 11,655 manager/report-period groups:

- 11,474 do not have exactly two submissions.
- 145 do not have exactly one 13F-HR with explicit COVER ISAMENDMENT=N and one 13F-HR/A with explicit Y, AMENDMENTTYPE=RESTATEMENT and AMENDMENTNO=1.
- 36 satisfy that candidate policy.
- Two candidates have same-day filing dates, so the original date is not strictly earlier.
- Two candidates include a combination report rather than two `13F HOLDINGS REPORT` filings.
- **32 eligible pairs remain**. All candidate identities and exclusion reasons are public. Cover/submission report-period equality is required; no period mismatch occurs in this sample.

Selected report periods are September 30, 2025, March 31, 2026 and June 30, 2026; the June–August archive names filing coverage, not a single holdings quarter.

No value, outcome, row-difference or confidentiality filter changes this cohort. All 32 remain of **unknown completeness**. Only seven have explicit N for both omitted-confidentiality flags; even those seven are not complete-holdings qualified. Blank flags are UNKNOWN, not N.

The grouping does not establish an explicit predecessor accession, complete amendment chain, legally superseding filing or reconstructed complete holding set. Filing dates and report periods remain distinct; no exact acceptance or first-public clock is inferred.

## What the reconciliation does

Across the selected 64 filings, 14,640 INFO source rows are retained. Each row is represented by the exact tuple of **13 raw text fields**, excluding only ACCESSION_NUMBER and INFOTABLE_SK:

NAMEOFISSUER, TITLEOFCLASS, CUSIP, FIGI, VALUE, SSHPRNAMT, SSHPRNAMTTYPE, PUTCALL, INVESTMENTDISCRETION, OTHERMANAGER, VOTING_AUTH_SOLE, VOTING_AUTH_SHARED, VOTING_AUTH_NONE.

The tuple is a source-record signature, **not a security or economic-position key**. No trimming, numeric parsing, name normalization, rounding, identifier repair or other normalization is performed. For each distinct tuple, matched multiplicity is the lesser occurrence count in the two filings. Duplicate multiplicity remains intact. Unmatched counts equal each source row count minus matched multiplicity. No rows are combined into purported unique securities.

Examples from this bounded selection:

- Manager CIK 0000765443: 340 source rows in each filing, 282 exact matched occurrences, 58 unmatched on each side.
- Manager CIK 0001123320: 62 original rows and 83 amendment rows; no exact matches.
- Manager CIK 0001180391: 54 rows on each side, all exact matches.

These numbers do **not** imply purchases, sales, exposure changes or stable economic holdings. Any field difference can cause an unmatched row. Equal rows are identical reported source text, not independent confirmation of the same security or position.

Missing INFO rows are explicitly `NO_SOURCE_ROWS_NOT_VERIFIED_ZERO_HOLDINGS`, never a zero-portfolio claim. Missing or invalid summary count values remain unknown; a summary count mismatch remains a diagnostic and does not silently remove the pair. Actual selected filings all have INFO rows and their stated TABLEENTRYTOTAL values match retained source-row counts; this still does not prove completeness.

## Source proof and boundaries

The original ZIP SHA is `4db97d5652e262de51617971104e06313211de4d092e6bcb5d7bf34ee7efe054`; database SHA is `5117bb2573288481d336dde11232ffb8bc64cb04a495f0fc179a64bf0e2aafda`. The receipt and ingestion summary are pinned separately.

Every field of all SUBMISSION, COVERPAGE and SUMMARYPAGE rows is independently compared ZIP-to-reopened-read-only SQLite. The entire INFOTABLE is streamed and its 3,830,274-row count checked; **every field of each selected INFO row** is compared to its exact persisted source row ID. Nonselected INFO rows are not newly compared to SQLite by this utility. ZIP schema, inventory, selected member CRC/hash, source keys, accession joins, DB quick-check and before/after archive/database hashes are verified.

Private evidence preserves all selected raw rows, source-row hashes and complete duplicate-aware matching lineage. Public pair metadata contains filing-manager CIK, accession, form, filing/report dates, explicit amendment/confidentiality states, source row counts and reconciliation counts. It does not expose holdings, names, CUSIPs/FIGIs, shares, values, votes, people or addresses. Full-row hashes and a private-lineage aggregate hash bind evidence without publishing those fields.

The manager CIK is not a held-company CIK. No company, ticker, security or owner join is made. The official prepared archive is the verified citation; accession-only SEC search URLs are constructed, **unfetched and unverified** original-document lookups. Original download/HTTP and first-public clocks remain unknown. Local verification is not decision-time availability.

## Consumer contract

Public artifact `web/manager-restatement-reconciliation.json` is 104,219 bytes for this version (hard bound 300,000). A consumer must pin bytes/SHA and validate policy, unique pair IDs, candidate/eligible relationships, exact manager/accession membership, source states and row-count conservation before use. A manager or period outside these pairs is **not evaluated under this policy**, not evidence of no amendments.

Integrate within the existing manager research workflow, keeping both source filings navigable. The appropriate next step for unmatched rows or completeness questions is original-filing review; public counts alone cannot identify changed positions. Do not rank managers, sum across report periods or infer trade flows.

```sh
python3 backend/manager_restatement_reconciliation.py \
  --archive /path/to/sec-13f17/01jun2026-31aug2026_form13f.zip \
  --database /path/to/sec-13f-ingested17-v2/holdings.sqlite \
  --summary /path/to/sec-13f-ingested17-v2/summary.json \
  --out /trusted/new-private-directory
python3 -m unittest discover -s backend -p test_manager_restatement_reconciliation.py
```

The new output directory is 0700 and files 0600. INCOMPLETE is written before source work; private evidence and public candidate precede COMPLETE hashes. Failures leave INCOMPLETE. Output is deterministic; no source requests, scheduler changes, orders, economic calculations or paper-engine activation occur.
