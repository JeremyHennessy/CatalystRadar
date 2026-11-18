# One exact-CIK company investigation across retained sources

This static projection makes the existing public evidence navigable by one exact issuer CIK. It does not collect data, join securities, merge legal entities or construct events. Existing source artifacts, their prior scopes and all workflows remain unchanged.

## What is actually included

The directory contains **8,035 distinct associated issuer CIKs**:

- **8,034** from the fixed prepared-issuer union: the original 7,912 six-batch index plus the Q2 insider extension (5,065 CIKs, adding 122).
- **3,809** with selected reported nonderivative P/S records in the two retained insider filing batches: 26,827 filings and 63,552 source rows. All are within the prepared union.
- **454** with 466 selected filings in the narrow October acquisition/disposal concept catalog. All are within the prepared union.
- **117** with 905 evidence records in the fixed research scanner. One CIK, **0000108772 (Xerox Corporation)**, is outside the prepared index and is included solely through its separately reviewed scanner evidence.

The 905 scanner records have **907 company associations**, because the two Xerox records each explicitly name two separate registrants. These are not 907 unique events. Xerox Corporation and Xerox Holdings (0001770450) remain distinct. No prepared batch, financial value or obligation is fabricated or propagated to the other entity.

The 8,035 count is a directory union, **not 8,035 fully investigated companies**, current listed securities or complete SEC coverage. Counts across different source families must not be summed into economic activity or unique histories.

## A company-first workflow

Search exact CIK or literal source-reported names, select one result, and load only its bounded company-detail shard. The directory's name union is a search aid, not a preferred/current legal name; the detail keeps every name/ticker association under its original source and filing batch. Ticker strings are not identity keys.

Each company detail has four independent sections:

1. **Prepared batch associations:** unchanged original issuer records from the six-batch index and Q2 extension, retaining source-specific names, reported ticker strings, submission counts and filing-date ranges. These are coverage records, not individual financial results or comparable fiscal quarters.
2. **Full insider review:** unchanged original issuer summary and a precise byte/SHA-pinned upstream filing-shard locator. Consumers can load that existing shard and select exactly this CIK's filings. The company package does not duplicate the 26,827 filing payloads.
3. **Disclosure filings:** unchanged original catalog objects with exact accession, issuer, concepts and source link. These are filing review candidates, not confirmed acquisitions/disposals.
4. **Research scanner:** unchanged original evidence records, including original evidence state, source references, unknowns, clocks and all registrant associations. A company section means only that this exact CIK is explicitly associated with the record. It does not attribute every fact in a dual-filer document to every filer.

Every copied object carries its source key, JSON pointer and canonical object hash. Existing 108-company dossier availability is explicit; other companies do not silently enter that old cohort.

The UI route is `datasets.html?company_cik=CIK#company-investigation`. It must be integrated and verified separately before claiming that route is live. This data package alone does not change navigation behavior.

## Absence, unknowns and interpretation

- `NO_ENTRY_IN_FIXED_PREPARED_INDEX`: no entry in the two pinned prepared indexes, not no SEC records.
- `NO_SELECTED_P_S_FILINGS_IN_FIXED_RETAINED_BATCH_INDEX`: no selected P/S filing in those two fixed batch projections, not no trading or no filings.
- `NO_SELECTED_DISCLOSURE_IN_FIXED_OCTOBER_CATALOG`: no selected concept record, not no transaction.
- `NO_RECORD_IN_FIXED_SCANNER`: no record in the selected scanner, not no research evidence anywhere.
- A CIK outside this directory is **unassessed**. Do not create a zero-filled company profile.

Quarantined/unassessable insider records must not be mislabeled absent. The present source has zero quarantine; any new quarantine causes this version to fail closed for explicit review rather than silently drop it.

P/S means open-market **or private** reported activity. Amendment filings remain unreconciled. Footnote flags are diagnostics, not interpreted narratives. A submission-level 10b5-1 flag does not establish row-specific plan applicability; an unchecked/missing flag does not prove an unplanned transaction. No owner identity, shares, prices, transaction values, intent, compliance or signal is inferred. No new filtering based on plan interpretation is added.

Source-specific dates are retained unchanged. Filing quarter is not transaction quarter or fiscal quarter; source observation/audit time is not first-public time. Exact CIK is not historical security mapping. Manager CIKs, CUSIPs and ticker/name similarity are not used to join sources.

## Reproducibility and integrity

`backend/company_investigation.py` freezes eight public source artifacts by byte length and SHA-256. It:

- Validates all prepared CIKs/batches, source metadata hashes, filing bounds and exact per-batch submission/issuer conservation.
- Reads and verifies all 256 existing insider detail shards, checks their CIK membership and rebuilds the original full-insider index from those original filing objects. No private database is read.
- Rebuilds the existing scanner with its already pinned source validator; no new original-document or provider request occurs.
- Validates disclosure count/concept conservation, scanner references/associations, exact source subsets and the explicitly reviewed one-CIK exception.
- Rejects duplicate/invalid CIKs, duplicate references/batches, count mismatches, unexpected union expansion or new quarantine. No identity repair, implicit latest-version fallback or silent omission.

Object hashes use sorted-key, compact ASCII JSON plus newline. They bind the exact parsed public object, not raw SEC bytes. Original archive/database/source hashes remain in the untouched source records and metadata.

## Compact directory and bounded details

The measured index is about **1.83 MB**. There are 128 company-detail shards, maximum about **243 KB**, with a whole static package around **18.96 MB**. A browser loads the index once and only the selected company shard, then an existing insider filing shard only if that section is opened. The larger full package preserves unchanged source objects and per-source provenance rather than replacing them with untraceable summaries.

Hard bounds: 2.4 MB index, 500 KB company shard, 24 MB package. The bucket is the first SHA-256 byte of the normalized ten-digit CIK modulo 128. Every directory CIK appears in exactly one manifest shard.

Consumer requirements:

1. Pin index bytes/SHA, validate the fixed schema and counts, unique CIK directory and exact shard membership bijection before search.
2. Fetch selected shard only; verify bytes/SHA, schema/bucket and all CIK memberships before displaying any company.
3. Verify source references/canonical object hashes and exact CIK membership in each section. Retain original dual-filer roles and unknowns. Never render a partially valid shard.
4. When opening insider filings, verify the upstream shard pin/schema, then require exactly the selected CIK group and reconcile its filing/row counts with the retained issuer summary. Do not fall back to another issuer, ticker or unfiltered page.
5. Source strings are inert text, not HTML. Original source links have their existing constructed/unverified status. Opening local research should not fetch SEC originals automatically.
6. Preserve old research if the optional new projection fails validation. Do not substitute a different source version or invent zero coverage.

## Run without source calls

```sh
python3 backend/company_investigation.py --root . > /tmp/company-index.json
python3 -m unittest discover -s backend -p test_company_investigation.py
```

The CLI reads local public files, fully validates/builds, then emits the index to stdout. No successful JSON is emitted before completion. `build(root)` returns `(index, payloads)` for all 129 static paths; callers should write payloads only after successful full construction and compare every persisted byte/hash. This module does not modify public artifacts, collectors, schedules, held reports, paper ledger or any order state itself. No model or trading qualification is performed.
