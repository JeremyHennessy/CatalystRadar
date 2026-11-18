# Inspectable SEC archive-reported financial values

This additive capability exposes **802 checked archive-reported monetary observations in 395 repeated contexts across 103 issuer CIKs**. It supports Revenues, RevenueFromContractWithCustomerExcludingAssessedTax and NetIncomeLoss. The 210 EPS contexts remain excluded from numerical presentation because their source-reported USD unit is not verified as a per-share unit.

This is an extraction/correspondence qualification, **not financial comparability**, independently audited company accounting, original filing-text verification, a growth lead, prediction or trading signal. The exact start date is unknown. No absolute/percentage change is calculated, even when two displayed numbers differ. All outcome status remains INSUFFICIENT EVIDENCE.

## End-to-end evidence

`financial_archive_facts.audit` builds on the unchanged pinned four-quarter candidate projection and exact company-name joins. It checks the original retained SEC prepared-data ZIP and SQLite hashes before and after work. It reads the original ZIP NUM, SUB and TAG members using the existing bounded schema-aware parser, binds selected data-row numbers to exact database rows, and compares every source column for those selected rows. It preserves member-level SHA256 hashes in addition to the complete archive/database hashes.

It requires the exact accession, issuer CIK, source name, filing date, metric, taxonomy, reported end date, USD unit, raw qtrs=1, empty reported segment/co-registrant fields, no selected footnote and standard nonabstract monetary duration taxonomy. Unsupported/missing/ambiguous contexts fail. The raw finite decimal literal is retained as text, so source precision is not rounded by JavaScript or converted to floating-point display. The equal/different relation must agree with checked raw archive values.

The source row number is the 1-based data-row number excluding the header, not necessarily a physical text line if quoting spans lines. It is not an Inline XBRL context ID. All three raw members are hashed as retained decompressed bytes. No private addresses, contact details, tax identifiers, narratives or licensed market prices enter the allowlisted output. Complete source SUB/TAG rows are compared internally, but only selected identifiers and qualification metadata are published.

## What a user can investigate

Search for an issuer and open **Inspect archive-reported values**. Each selected filing observation shows its exact reported literal/unit, form, accession, filing date, reported end date, unknown start and NUM source row. Filing references and official SEC prepared-archive links remain available. Different reported numbers are questions to investigate, not verified restatements or economic changes. Amendment flags reflect /A forms only; revision lineage is not inferred.

For example, the two retained Astrotech source observations for NetIncomeLoss with reported end 2025-03-31 each contain the exact literal `-3633000.0000` in USD. This establishes repetition in the checked prepared archives, not independent confirmation, exact fiscal duration, novel news or a prospective investment conclusion. Source filings may contain accounting qualifications not represented by the extracted archive row.

## UI safeguards

The amount-free search index remains separate. The numerical evidence file loads only when a monetary review button is selected. The client requires complete issuer/context/source-row correspondence against the reviewed index, the exact qualification state and null unknown fields. It validates units, source hashes, archive links and restricted metrics, rejects malformed/partial/wrong-context payloads, and shows an explicit failure state rather than valid emptiness. Failed loads can be retried; no collection occurs. EPS cards have no numerical-values button.

The numerical artifact is bounded (395 contexts, 802 observations, approximately 1.08 MB); millions of source rows are not sent to the browser. The client pins the exact 1,076,405-byte artifact and SHA256 `116e6415d8551cee28d0733082787d1283e423dee8e1a8878fa9b27b22480547` before parsing or rendering, in addition to cardinality/schema checks. A numerically valid substituted value is rejected by the byte hash. Current archive links are official URLs derived from the verified batch identities; individual live archive/file URLs are not newly fetched by this offline change.

## Reproduce and verify

Run into a new output file, supplying the existing four-batch database/archive mappings:

```
python3 backend/financial_archive_facts.py PRIVATE/candidate-pairs.json PRIVATE/database-map.json PRIVATE/archive-map.json NEW_OUTPUT.json
```

Retained candidate SHA256: `19327178d9dbe5e8a2d5956bd51a717d4f7ce458ae7e7ee89b8fa77b52915ba1`. Per-batch archive/database identities are inherited from that pinned artifact and saved in the output. Earlier reports, raw evidence, existing collectors and the disabled paper book are unchanged. No network retrieval, account, spending or market-data requests are introduced.

Tests reject mismatched identity/dates, absent/nonfinite values, unsupported units/taxonomy/dimensions/footnotes and missing raw rows. Browser contracts reject changed source clocks, source-row IDs, hashes, units or qualification and test on-demand loading, failure/retry, exact precision and EPS exclusion. Independent source reconstruction and actual browser rendering remain required release gates.
