# Retrospective share-basis review warnings

This offline package links already-retained SEC split-related disclosures to existing unqualified financial candidates at the **issuer level only**. Its purpose is to identify where share-basis review is necessary before any EPS comparison or outcome research. It does not certify a split, apply adjustments, establish security identity or create training examples.

## Inputs and scope

- Previously independently ingested October 2026 [SEC Financial Statement and Notes Data](https://www.sec.gov/data-research/sec-markets-data/financial-statement-notes-data-sets): 6,670 filings, 1,488,444 numeric rows and 271,414 text rows. Original ZIP and SQLite SHA-256 hashes are in the aggregate JSON.
- Completed Q2/Q3 financial candidate artifacts, pinned through `financial-pair-audit-2026-11-17.json`, their exact private hashes and completion markers. These are filing-quarter batches, not uniformly Q2/Q3 financial results.
- Only standard us-gaap/2025 and us-gaap/2026 concepts `StockholdersEquityNoteStockSplitConversionRatio1`, `StockholdersEquityNoteStockSplit` and `StockholdersEquityReverseStockSplit` are selected. Custom concepts, other taxonomies and other split-related tags are deliberately outside this narrow audit.

No new source requests, account, key or provider quota were used. The original notes ZIP was retained through the approved public SEC download, without private contact. Its exact network retrieval/first-public time remains unknown. `audit_completed_at` records this local audit's completion in UTC, not when the underlying information became available.

## Actual retained evidence

- 81 ratio rows, all positive numeric literals with `pure` units, across 40 filings and 40 issuer CIKs.
- 220 standard split/reverse-split narrative rows retained separately.
- Only 2 of the 40 ratio filings, containing 4 ratio rows, also have one of the selected standard narratives. Other narrative concepts may exist; this is not a complete disclosure inventory.
- The ratio rows' context dates range from October 2023 through November 2026 and include instant and duration contexts. These are not assumed to be split ex-dates. Repeated raw rows and dimensions are preserved, not collapsed into events.

The same issuer CIKs appear among **94 Q2 candidates (36 issuers)** and **77 Q3 candidates (30 issuers)**, including **33 and 26 diluted-EPS pairs**, respectively. Thus 59 existing diluted-EPS candidate records are flagged for retrospective review. These counts are candidate records, not independent issuers, unique events, corrected comparisons or additional qualified examples. No raw ratio, narrative or EPS value is published.

## Interpretation limits

The standard ratio concept describes conversion ratios, but a literal alone does not establish orientation, actual implementation, security class or effective date. A ratio may be repeated across contexts and filings. A narrative in the same filing may describe another event, a proposal, negation or historical adjustment. This utility deliberately does not semantically interpret that text.

CIK equality identifies a reporting entity, not a tradable share class. Even an actual later split need not apply to a particular earlier EPS fact. Later October material is **retrospective audit evidence only** and must never be fed into a model as if it were known at a Q2/Q3 decision. Candidates can remain unusable for many unrelated reasons.

Consequently, corporate-action events verified = 0, adjustment factors verified = 0, and training/execution readiness remain false. Nothing changes in the approved paper ledger, held report, dashboard or existing candidate datasets.

## Reproduction and integrity

`backend/split_basis_evidence.py` opens the retained SQLite database read-only, checks integrity, enforces exact imported schemas, and binds DB and archive hashes before/after processing. Numeric/text rows retain every original field and rowid, exact taxonomy definitions, dimension rows and selected filing context. Issuer addresses and other unnecessary SUB metadata are not selected. The earlier ingestion audit, not this utility, established that the DB faithfully derives from the ZIP.

Missing or ambiguous taxonomy, filing or dimensional joins fail closed. Unsupported numeric literals remain private and explicitly unusable rather than silently repaired. Limits cap selected rows, field length, cumulative retained text and parsed input sizes. Candidate hashes, summary checkpoints, completion markers, unqualified status and source bindings are verified before use. No network, HTML/XML evaluation, event-date inference, numerical scaling, growth or return computation occurs.

The private completion protocol writes INCOMPLETE before work and COMPLETE hashes only after evidence and summary persist. The trusted private parent must be outside this checkout; this is not immutable storage or protection against an unrelated publication checkout. Private evidence is stored in the shared `candidate-pairs.json` container, which does not mean all contained source rows are financial pairs.

Tests use synthetic cases for duplicate/missing joins, taxonomy mismatches, repeated observations, blank/invalid ratios, negated narratives, issuer-only correspondence and incomplete/tampered input checkpoints. A negative or missing standard-tag result never certifies absence of a split.

## Next required evidence

For any flagged candidate, inspect the original filing's relevant narrative, class and contexts; independently establish the actual corporate-action terms and effective date; verify the historical security mapping and price adjustment convention. Only then could a separate qualification process consider whether a comparison or outcome is usable. This package does none of those steps automatically.
