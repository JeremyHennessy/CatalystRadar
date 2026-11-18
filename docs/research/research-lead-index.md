# Deterministic company research queue

This small index makes existing research findable by company, question, metric and evidence type. It is not another underlying source dataset or a signal generator. It points back to existing company investigation and IEH’s source-backed reported comparison.

## Scope and useful questions

There are **107 company entries**: all 106 issuers in the released financial-review workspace, plus IEH (which is not in that cohort). These contain references to all 605 financial contexts. Of the financial cohort, 36 issuers have selected insider filing evidence and five have selected acquisition/disposal disclosure evidence. Neither presence nor absence is a trading recommendation. IEH’s insider/disclosure coverage is **not evaluated in this cohort**, not “none.”

Each entry asks what needs original-source review. Financial entries require exact duration, accounting scope and amendment checks before interpreting numerical context differences. Linked insider evidence requires its own original filing/footnote review; P/S means open-market **or private** activity. Linked acquisition/disposal concepts are historical unadjudicated disclosure records, not proven deals. IEH’s reported revenue arithmetic is consistent, but currency, duration, accounting comparability, original 10-Q and novelty remain unresolved.

The index includes source-associated labels, stable issuer IDs, financial case IDs, metric labels, source dates, insider references and disclosure accessions. It does not copy financial amounts, narratives, transaction values, owner information or raw archives. Existing source-specific warnings remain in the linked investigation. No event deduplication is performed: one company entry is navigational grouping, not one event or one independent training sample.

## Determinism, provenance and missing states

`backend/research_lead_index.py` reads five bounded strict JSON inputs under exact supplied SHA-256 pins. Financial cases are validated with the existing validator. The historical disclosure projection uses its existing schema/selection validator. Insider company references are checked for full-cohort coverage, unique filing references, exact source CIK associations and the same financial input version. The known reviewed IEH comparison must retain its supported values, periods and missing fields; changed facts require renewed review.

`web/company-findings/research-lead-index.json` contains all input paths/hashes/byte counts. The financial source pin is shared across both cross-evidence views. Rebuilding with identical inputs produces identical bytes: no wall-clock timestamp or nondeterministic rank is injected. Input-source clocks remain in their evidence documents. IEH’s recorded retrieval is retained as retrospective provenance; first-public time is null. Financial filing dates are as filed, not publication instants or decision-time availability.

Ordering is ascending padded issuer CIK. No profitability, strength, return, novelty or recency score exists. Every entry retains false accounting-comparability/training/execution flags and unknown first-public timing. This index neither qualifies outcomes nor changes the disabled paper book.

## Existing-app consumer

Search/filter these small entries in the existing research workspace, then open the existing `financial-review.html?cik=...` company investigation or `company-ieh.html`. Search source labels/CIK/metric/research type, using inert text and exact supported link destinations. Keep historical status, specific missing requirements, source coverage and next review action visible. Do not label entry count as signals, verified events, opportunities or independent samples. Browser integration is a separately reviewed change; this release alone adds no UI.

Rebuild: `python3 backend/research_lead_index.py --root REPO --financial-sha HASH --catalog-sha HASH --manifest-sha HASH --insider-sha HASH --ieh-sha HASH --out NEW_PATH`. Use the exact released `sources` pins. All validation completes before writing, and an existing output is refused. Tests cover deterministic reconstruction, full union, scoped unknowns, duplicate/missing references, changed input versions, changed reported facts, pin failures and no raw-value copying. Held reports, source snapshots, ledger and schedules are unchanged; no network requests or costs are incurred.
