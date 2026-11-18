# Insider filing review cards: historical evidence, not signals

This bounded review follows all reported P/S nonderivative transaction rows for the existing ten issuer CIKs in the retained SEC 2026 Q2 and Q3 insider filing batches. It is not a ranked buying or selling screen. Selection does not use prices, returns or outcomes.

## What a researcher can actually review

The resulting 27 filing cards cover 41 source transaction rows and six watchlist issuer CIKs. They preserve accession, source-associated issuer names and reported ticker text, filing date, transaction-date bounds, reported code counts, diagnostic counts and source row hashes. Each card supplies concrete original-filing questions. The exact-accession SEC search link is a constructed lookup, not a verified original document URL. The verified source is the prepared SEC archive cited for each batch.

- Q2: 10 selected rows across seven filings.
- Q3: 31 selected rows across 20 filings.
- 40 rows use S and one uses P. **P/S means open-market OR private**, not necessarily exchange trades. These counts do not establish net economic activity, insider sentiment, ownership changes or investment merit.
- One of the 27 filings is Form 4/A; its one selected row is kept separate and unreconciled. The remaining 26 filings are Form 4.
- 32 selected rows contain footnote references requiring original context. Identifier resolution does not mean the footnote interpretation was reviewed.
- No P/S acquisition/disposition-code contradiction occurs in this selected cohort. This does not overturn the wider Q2/Q3 diagnostic counts or validate the selected rows.
- Four watchlist CIKs have no selected P/S rows in these two batches. This is not a claim that no insiders traded, that there were no other forms/codes, or that there was no later activity.

The submission-level plan flag is kept with that limited scope; it is not a row-specific 10b5-1 determination, a compliance assessment or evidence of intent. Counts are reported source rows/filings, not unique people or economic trades. No quantities, prices, transaction amounts, owner names/addresses or footnote narratives are public.

## Identity, dates and qualification

CIKs are matched exactly after validated zero normalization. Research watchlist ticker labels do not prove current or historical security identity. Issuer names and ticker text remain source-associated as-filed labels and must be rendered as inert text by the UI. No ticker-only join, owner join or filing deduplication changes counts.

Filing and transaction fields are date-only source fields. The output generation timestamp records this audit, not download time or first-public availability. First-public and decision clocks remain null. Original filings have not been retrieved for these cards. No returns, timing advantage, trading recommendation, probability, training readiness or execution permission are inferred.

## Reproducibility and boundaries

`backend/insider_review_cards.py` reuses the audited raw-code classifier and requires exact SHA-256 pins on each source ZIP and SQLite database. Both are verified before/after the source audit; exact source-table schemas, unique source keys and submission references are checked. The card projection rechecks the complete selected submission fields, rowid and filing-quarter range. Previously independent whole-table ZIP-to-database audits establish derivation; merely supplying two hashes does not establish it independently.

Only Q2 and Q3 are accepted. The ten-CIK cohort is fixed in code. All P/S records for those CIKs are retained, including amendments and warnings. Unknown/missing contexts fail closed where required; all diagnostic interpretation stays bounded by the existing classifier. Full selected classifier records are private. The public projection omits transaction values, owners and narrative text. SEC search links are built only from validated accession syntax, never from source-provided URLs or assumed ownership-filing archive directories.

The CLI creates a private output directory with INCOMPLETE first. It writes private selected evidence and the public projection, then a COMPLETE manifest with both exact hashes; failed runs must not be used. Private directory/file modes are 0700/0600. Public `web/insider-review/cards.json` is a byte copy of the completed projection. Original research reports, paper ledger, schedules, provider credentials and source datasets remain unchanged. UI integration is a separate reviewed release.

Sources: [SEC Insider Transactions Data Sets](https://www.sec.gov/data-research/sec-markets-data/insider-transactions-data-sets), retained Q2/Q3 archive readme and source rows. No new provider requests were made for this package.
