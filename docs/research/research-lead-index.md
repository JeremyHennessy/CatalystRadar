# Deterministic company research queue

This small index makes existing research findable by company, question, metric and evidence type. It is not another underlying source dataset or a signal generator. It points back to existing company investigation and IEH’s source-backed reported comparison.

## Scope and useful questions

There are **108 company entries in version 3**: all 106 issuers in the released financial-review workspace, plus IEH and Emerson (neither is in that financial cohort). These contain references to all 605 financial contexts. Of the financial cohort, 36 issuers have selected insider filing evidence and five have selected acquisition/disposal disclosure evidence. Neither presence nor absence is a trading recommendation. IEH’s insider/disclosure coverage is **not evaluated in this cohort**, not “none.”

Each entry asks what needs original-source review. Financial entries require exact duration, accounting scope and amendment checks before interpreting numerical context differences. Linked insider evidence requires its own original filing/footnote review; P/S means open-market **or private** activity. Linked acquisition/disposal concepts are historical unadjudicated disclosure records, not proven deals. IEH’s reported revenue arithmetic is consistent, but currency, duration, accounting comparability, original 10-Q and novelty remain unresolved.

The index includes source-associated labels, stable issuer IDs, financial case IDs, metric labels, source dates, insider references and disclosure accessions. It does not copy financial amounts, narratives, transaction values, owner information or raw archives. Existing source-specific warnings remain in the linked investigation. No event deduplication is performed: one company entry is navigational grouping, not one event or one independent training sample.

## Determinism, provenance and missing states

`backend/research_lead_index.py` reads nine bounded strict JSON inputs under exact supplied SHA-256 pins. Financial cases are validated with the existing validator. The historical disclosure projection uses its existing schema/selection validator. Insider company references are checked for full-cohort coverage, unique filing references, exact source CIK associations and the same financial input version. The known reviewed IEH comparison must retain its supported values, periods and missing fields; changed facts require renewed review.

`web/company-findings/research-lead-index-v3.json` contains all input paths/hashes/byte counts. The financial source pin is shared across both cross-evidence views. Rebuilding with identical inputs produces identical bytes: no wall-clock timestamp or nondeterministic rank is injected. Input-source clocks remain in their evidence documents. IEH’s recorded retrieval is retained as retrospective provenance; first-public time is null. Financial filing dates are as filed, not publication instants or decision-time availability.

Ordering is ascending padded issuer CIK. No profitability, strength, return, novelty or recency score exists. Every entry retains false accounting-comparability/training/execution flags and unknown first-public timing. This index neither qualifies outcomes nor changes the disabled paper book.

## Existing-app consumer

Search/filter these small entries in the existing research workspace, then open the existing `financial-review.html?cik=...` company investigation or `company-ieh.html`. Search source labels/CIK/metric/research type, using inert text and exact supported link destinations. Keep historical status, specific missing requirements, source coverage and next review action visible. Do not label entry count as signals, verified events, opportunities or independent samples. Browser integration is a separately reviewed change; this release alone adds no UI.

Rebuild: `python3 backend/research_lead_index.py --root REPO --financial-sha HASH --catalog-sha HASH --manifest-sha HASH --insider-sha HASH --ieh-sha HASH --holdings-sha HASH --mapping-sha HASH --emerson-sha HASH --watchlist-insider-sha HASH --out NEW_PATH`. Use the exact released `sources` pins. All validation completes before writing, and an existing output is refused. Tests cover deterministic reconstruction, full union, scoped unknowns, duplicate/missing references, changed input versions, changed reported facts, pin failures and no raw-value copying. Held reports, source snapshots, ledger and schedules are unchanged; no network requests or costs are incurred.


## Why institutional holdings are not linked yet

The retained 13F information table has CUSIP, FIGI, issuer-name and class fields, but no held-issuer CIK. Its submission CIK belongs to the **reporting manager**. It cannot be used to attach the manager’s holdings to that issuer’s company investigation. Names or ticker similarity are not a substitute.

The existing separately audited 3,830,274-row holding census and 1,507 exact FIGI correspondences remain useful identifier evidence, not verified holdings of this company research cohort. The ten retained OpenFIGI ticker-query mappings explicitly have unverified issuer-CIK and historical ticker associations. No retained verified CUSIP-to-company mapping has been established by these sources. Checksum validity does not authenticate identity; FIGI, composite and share-class scopes cannot be silently interchanged. Source report periods and options/amendments must remain distinct.

The existing index now pins both released evidence manifests and verifies their request/response/receipt hashes and observation clock agree. It exposes a shared `holdings_linkage` blocker and a per-company `NOT_ASSESSED_MISSING_VERIFIED_ISSUER_SECURITY_MAPPING` state. **Company position count is null, not zero.** No raw CUSIP, holding value, manager identity or false company association is published. This bounded inspection uses retained schemas and already audited source evidence, not new provider calls or a claim to have searched all possible mappings.

The next executable prerequisite is a permitted source explicitly binding issuer CIK to the correct held security/class with effective historical dates. That association requires independent review before any filing rows can attach to a company. Temporal identity, corporate actions, options/debt scope, amendments and decision-time availability remain separate gates. No ownership, exposure or signal is inferred while this prerequisite is absent.

Version 2 introduced the holdings blocker while preserving the original index. Version 3 now preserves both earlier snapshots; consumers must select one reviewed version. Never sum the snapshots.


## Version 3: Emerson financing discoverability

The prior version 1 and version 2 files remain byte-identical for their pinned consumers. Version 3 preserves all 107 existing entries exactly and adds one distinct CIK, 0000032604, for the separately reviewed Emerson note-completion finding. The financial cohort remains 106 issuers and 605 contexts. The earlier 107 total was correct for its scope; this version has 108, not a replacement claim that the earlier count was wrong. Never add the version totals together.

The new research question links directly to `company.html#debt-offering`. Its source reports completion of previously announced notes; no new announcement, independent settlement, proceeds, equity dilution or current balance is inferred. Amounts and coupon are not duplicated in the queue. The original finding retains them with their source context.

Three historical insider filing references from the separately released watchlist cards match the same issuer CIK: one Q2 and two Q3 filings. Each has its own accession, filing date and transaction-date range, and links to its existing detail via `insider-review.html#ACCESSION`. This is reporting-issuer identity only. It does not establish any relationship to the November financing, current security identity, insider intent, causal effect or decision-time availability. The original insider filings/footnotes remain unreviewed; transaction codes include private or open-market activity.

The queue now has 37 issuers with selected insider references: the original 36 financial-cohort issuers plus Emerson. The five acquisition/disposal matches are unchanged. Emerson's financial status is explicitly not in the financial review cohort, and disclosure coverage is not evaluated in that cohort. These are not zero-financial-activity or no-deals conclusions. Holdings remain unassessed under the existing mapping blocker.

Two additional input pins bind the released Emerson finding and watchlist insider cards. The generator rejects changed supported financing facts, changed issuer, duplicate/missing insider references and newly asserted qualification. It preserves source-associated issuer names and as-filed ticker labels without promoting a current ticker mapping. UI migration to the new version is separately reviewed; publishing this artifact does not by itself change search results in the browser.
