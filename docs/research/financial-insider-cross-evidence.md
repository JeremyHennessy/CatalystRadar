# Company investigation: financial cases and insider filing evidence

This package connects existing financial-review cases to retained insider filing evidence using **validated issuer CIK only**. It supplies a company-level investigation index, not another score, trading signal or claim that two disclosures concern the same event.

The pinned existing financial review has **605 context-review cases for 106 issuer CIKs**. All reported P/S nonderivative transaction rows for those CIKs are selected from retained SEC Q2/Q3 insider filing batches, without ranking by amount, price, outcome or time proximity.

## Verified scope

| Source filing batch | Selected source rows | Filings | Issuer CIKs |
| --- | ---: | ---: | ---: |
| Q2 2026 insider | 243 | 133 | 22 |
| Q3 2026 insider | 228 | 146 | 30 |
| Combined | 471 | 279 | 36 |

Sixteen issuer CIKs occur in both quarters; issuer counts must not be summed. No selected accession overlaps these two batches. The 36 linked CIKs account for **171 of the financial-review contexts**. All 106 issuers remain represented, including **70 with no selected P/S rows in these two batches**. That is not a claim of no insider activity, no other forms or no other transactions.

The selected source rows retain 429 footnote-context warnings, two amendment warnings and four P/S direction-code contradictions, plus other existing classifier diagnostics. Warning categories overlap and must not be summed as unique transactions. All four direction contradictions are in Q3. None is automatically repaired, dismissed as a source error or interpreted as economic intent.

## Investigation workflow

For each issuer, the new public index provides:

1. Existing financial case IDs, source-associated financial names, metric, prepared context date, financial accessions and filing dates. A link returns to the existing financial review filtered by CIK.
2. References to each selected insider filing, carrying its own as-filed issuer name/ticker, filing date, transaction-date bounds, code/diagnostic counts, plan-flag scope, source row hashes and explicit original-review questions.
3. Clear unresolved relationship flags: security mapping, temporal alignment, same event and causality are all **false/not verified**.

A researcher can move from a company's financial accounting-context question to that issuer's independently reported insider filing context. The index does not imply insider transactions explain, anticipate or respond to the financial observation. It does not infer net buying/selling, dollar exposure, unique people or unique economic trades. P/S includes **open-market OR private** activity. Original filing links are exact-accession search lookups, not verified downloaded originals.

The prepared financial context date is a coarse as-reported key, not a verified exact duration or announcement date. Financial periods, financial filing dates, insider transaction dates and insider filing dates remain separate. Source retrieval and first-public times stay unknown; the generation timestamp is only this processing run. No historical availability, decision-time alignment or lead/lag test is claimed.

## Provenance and privacy

`backend/financial_insider_links.py` reads the bounded, strict-JSON financial manifest under its exact SHA256 and checks all existing case IDs/statuses/CIKs/date-only fields. It requires exactly the two retained insider source batches, reruns the source audit against pinned ZIP/database hashes, and projects all selected rows. Original whole-table ZIP-to-database derivation was independently audited in prior packages; merely pinning two hashes is not a substitute for that review.

`backend/insider_review_cards.py` gains an optional bounded canonical CIK cohort for this projection. Its default ten-CIK watchlist behavior and existing published cards remain unchanged. New public data is `web/company-findings/financial-insider-links.json`; all original financial, issuer and insider manifests are preserved byte-for-byte.

Public fields contain no owner names/addresses, transaction prices/quantities, raw footnote narrative or private contact information. Financial names and insider labels remain attached to their own sources, with no preferred/current name or ticker reconciliation. UI consumers must render strings as inert text and validate source-specific integrity before displaying related evidence.

Private selected evidence and public projection use INCOMPLETE-first/COMPLETE-last hash verification, with 0700 directory and 0600 files. A failed generation is unusable without its matching completion manifest. Existing held research reports, ledger, sources, schedules and disabled training/execution gates are unchanged.

User-facing integration belongs inside the existing issuer/financial investigation workflow and is a separately reviewed UI change. This data release alone does not claim navigation is already available in the app.

This is a pinned snapshot, not continuously refreshed evidence. A changed financial input requires regeneration and review before claiming current combined coverage; consumers must not silently mix different manifest versions.
