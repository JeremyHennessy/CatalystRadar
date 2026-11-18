# Financial investigation → historical acquisition/disposal disclosures

This package extends company investigation with **exact reporting-issuer CIK navigation**, not a transaction signal. It projects the existing 106-issuer / 605-context financial review cohort against every filing in the retained October 2026 disclosure catalog. All 106 issuers remain present, including scoped negative results.

## Actual retained evidence

Five issuers match five filings containing eight selected disclosure records: CENTERPOINT ENERGY, VSEE HEALTH, KINRG, UNIFIRST, and TRANSGLOBAL MANAGEMENT GROUP (names as filed). These issuers have 28 financial review contexts. The other 101 financial issuers have no selected disclosure in this particular catalog. That is not evidence of no acquisition or disposal.

The full source catalog remains 466 filings, 454 CIKs and 546 records selected by four standard acquisition/disposal text-block concepts in us-gaap/2025 and us-gaap/2026. Its October filing dates are not announcement, completion, effective or first-public times. The source may describe prior transactions, negation, continuing accounting or repeated disclosure. Eight records do not establish eight deals. The five selected filings have no dimension-populated records; that does not establish economic comparability.

## Reproducibility and boundaries

`backend/company_disclosure_links.py` reads three bounded, strict JSON inputs once under supplied SHA-256 pins: the existing financial review manifest, disclosure filing metadata and its source manifest. The catalog's internal metadata hash/byte count must match the exact supplied catalog bytes. It validates identities, duplicate accessions, allowed fields/concepts/forms, dates, totals and SEC URL construction before joining. The original catalog's ZIP→database→projection derivation was independently audited earlier; input hashes alone are not a new raw-source audit.

`web/company-findings/financial-disclosure-links.json` records the exact input hashes and underlying notes archive/database provenance. Processing time is not source retrieval or first-public time. No provider request, new account, cost or source download is involved.

The projection includes all cohort CIKs, existing financial case IDs, selected disclosure accession references and the five original public filing metadata records. No narrative, owner information, transaction amount, target, private contact or restricted price data is copied. Labels must be rendered as inert text. SEC index URLs are constructed source lookups, not newly fetched or verified available links.

The relationship is issuer identity only. It does not establish the same event, a tradable security, historical availability, causality, materiality, a financial explanation or a predictive result. Financial context dates remain coarse prepared-data keys; no period alignment is performed. Existing financial cases remain unqualified. Training and execution stay disabled. Held reports, ledger, source snapshots and schedules are unchanged.

## Consumer integration

Use this as an additional section in the existing company investigation, keyed by padded issuer CIK. Keep source filing dates, concepts, versions and independent original-review questions visible. Pin the financial input version before connecting case IDs. Display the explicit scoped absence for an unmatched cohort issuer, not “no deals.” Preserve each source's own issuer name rather than selecting a preferred current name. This release supplies metadata; browser UI integration is separate.

Rebuild with `python3 backend/company_disclosure_links.py --root REPOSITORY --financial-sha HASH --catalog-sha HASH --manifest-sha HASH --out NEW_PATH`. Use the hashes in the released projection's `sources` object. The command refuses an existing output and writes only after complete validation. Tests include exact full-cohort coverage, name-independent joining, corrupt counts/URLs/identities, duplicate accessions, extra private fields, qualification flags and pin failures.
