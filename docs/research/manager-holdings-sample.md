# Bounded as-filed manager holdings review

This demonstrates institutional disclosures without pretending reporting-manager CIKs identify held companies. The source is the retained SEC June–August 2026 Form13F prepared filing archive, not an OpenFIGI/ticker join or licensed securities master.

Selection is fixed and mechanical: first three numeric reporting-manager CIKs among HR/HR-A submissions, first two accession-ordered filings for each, first ten numeric INFOTABLE_SK rows per filing. It is a UI-sized diagnostic, not a representative sample, ranking or recommended portfolio. All three selected managers have one filing in this batch. Whole-filing row counts and omitted sample counts are explicit; no period comparison occurs.

## Actual result

- Manager0000002230, Adams Diversified Equity Fund:103 source holding rows,10 shown.
- Manager0000002488, Advanced Micro Devices:6 source holding rows,all6 shown.
- Manager0000003520, Fred Alger Management:507 source holding rows,10 shown.

These are **reporting managers**, not a held-issuer list. The three filings report June30,2026 positions. Twenty-six sample rows preserve as-filed issuer name, class title, CUSIP, FIGI, put/call, shares/principal type, discretion and other-manager references. No quantities or values are published. Exact source strings are not repaired or promoted to verified security identity. Blank option flags do not establish common shares.

The source recheck pins ZIP and database, validates schemas, directly compares every column of selected original SUBMISSION/COVERPAGE/SUMMARYPAGE/INFOTABLE rows to the retained database, and checks both pins after processing. Private columns are examined for correspondence but omitted from output. All projected rows include original data-row and filing provenance.

## Privacy, rights and interpretation

The public projection is limited to source-reported institutional filing metadata and identifier strings. It does not republish the separately licensed official13(f) securities list or commercial enrichment. SEC public-filing reuse guidance distinguishes public filing content from third-party material: [SEC Webmaster FAQ](https://www.sec.gov/about/webmaster-frequently-asked-questions). Contacts, signatures, street addresses and raw narratives remain private; no market-price rights are assumed.

Amendment fields/conflicts and confidentiality omissions remain as filed. Sample truncation is not confidential omission. No rows are treated as purchases/sales, new positions or real-time holdings; no economic position consolidation, option exposure or portfolio totals. A single historical filing batch does not establish comparable-period history.

## Reproduce

```
python3 backend/manager_holdings_sample.py HOLDINGS.sqlite ORIGINAL_SEC.zip NEW_OUTPUT.json
```

Output is generated only after validation; exclusive creation prevents overwrite. Public app integration requires independent source/privacy review and an integrity-pinned bounded viewer. No provider requests, credentials, quotas, collector schedules or paper controls change.

Filing-index URLs are constructed from retained manager/accession identifiers, explicitly marked `CONSTRUCTED_FROM_RETAINED_IDENTIFIERS_NOT_FETCHED`; this package does not verify those live pages or treat links as retrieval evidence. The archive URL and pinned retained source bytes are separate provenance.
