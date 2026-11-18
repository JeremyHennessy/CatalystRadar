# Source adjudication of the unchanged frozen outcome case

The historical outcome policy `results-header-next-session-close-v1` selects one retained results-of-operations header: TherapeuticsMD, CIK 0000025743, accession 0001213900-26-119681. This new sidecar resolves a narrower dependency: what does its original results exhibit actually report? It does not select a replacement event, rewrite the frozen features/report, establish a first-public clock or construct a return.

## Actual finding, including an unresolved source conflict

The retained EX-99.1 body headline says **Third Quarter 2026 Financial Results**. Its introductory paragraph says the results cover the **three months ended September 30, 2026**. Exact period start remains unknown; no July 1 date is inferred.

The SGML exhibit description instead calls the release **Second Quarter 2026 Financial Results**. Both declarations and their exact original-byte spans/hashes are preserved. The mismatch is not silently repaired, and body wording is not promoted to independently verified accounting truth.

Within that exhibit, the reviewed headings identify continuing-operations results. The existing exact-paragraph parser reports continuing-operations income of 501 thousand versus 50 thousand reported dollars, and combined basic/diluted common-share amounts of 0.04 versus 0.00. These are not total-company GAAP/comparability proof. Rounded 0.00 does not prove an exact zero denominator. No percentage growth is calculated. The existing parser's `current_period=null` remains unchanged; the separate annotation explicitly represents what the surrounding body declares, not a new numeric fact admission.

This is meaningful source-content evidence beyond the prior results-header-only record. Novelty, independent economic-event identity, exact accounting scope, first-public availability and outcome qualification remain unresolved. November 13 is a release date, not an authenticated publication instant. The receipt records retrieval November 14 at 23:33:13.530724 UTC; this is not backdated to November 13.

## Source and reproduction

The fixed original ZIP, manifest and complete filing are pinned. Exact accession/CIK is matched to the unchanged frozen policy before inspection. The source link is the retained receipt's original SEC submission URL, not a new fetch. The public sidecar is `web/company-findings/frozen-outcome-txmd-source-review.json`.

```
python3 backend/frozen_outcome_source_review.py CHECKOUT RETAINED_ORIGINALS.zip NEW_OUTPUT.json
python3 -m unittest discover -s backend -p test_frozen_outcome_source_review.py
```

The source parser requires the exact reviewed description, unique body anchors in order, a unique original exhibit and one source-bound continuing-operations paragraph. Changed/duplicate/malformed anchors require review. Scripts, comments and styles cannot supply body context. Source excerpts are narrowly limited to reviewed anchors; contact details and the remainder of the original document are not republished. Output refuses overwrite.

The frozen audit files, continuing-operations parser, collector/schedules and private raw prices are untouched. The sidecar retains all original missing dependencies, null decision/entry/endpoint/return and zero qualified outcomes. The new method is a bounded immutable-source adjudication, not a general earnings parser or qualification gate.

## Independent retained-price blocker reproduction

The existing `observed_outcome_coverage.py` was rerun against the same seven pinned scan receipts, original archive and all eleven pinned private daily snapshots. It again found 14 issuer/accession pairs, 13 unique accessions, dates June 26–November 16, zero date-coverage passes and zero qualified outcomes. Thirteen pairs lack November 17; one lacks November 17 and 18. This is a union-of-series necessary exclusion with no ticker join and no published prices.

A newly retained, independently verified November 17 observation could remove only the first missing-date exclusion for some cases. Historical class identity, corporate-action treatment, actual session evidence, intended-use rights and source-specific interpretation still need qualification. This is a scoped local retained-input check, not a claim about every possible remote/private dataset or permission to request provider data.
