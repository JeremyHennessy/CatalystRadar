# Exact-CIK company Form D notice history

This optional sidecar connects the existing 8,035-company investigation cohort to issuer associations in the retained Q3 2026 SEC Form D prepared batch. It does not alter the directory, scanner, reports or filing histories. No new collection occurred.

## Actual scope and conservation

- 16,160 issuer rows examined across 15,952 submissions.
- 223 issuer associations, 223 distinct submissions and 187 exact cohort CIKs selected. All selected issuer roles are primary as reported.
- 15,937 issuer rows are outside this cohort; zero rows silently dropped.
- 7,848 cohort CIKs have no selected issuer notice in this pinned batch. This does not mean no financing, no filing in other periods or no activity. A CIK outside the 8,035 list is **not evaluated**.
- Selected forms: 175 D and 48 D/A. All selected amendment flags agree with these forms; zero direction or investment conclusions are made.
- Previous accession: 175 missing as reported, 45 outside the retained batch, three present in the batch. The three present references have the same exact issuer CIK and primary role. There are no selected self-references or retained-reference cycles.

A declared predecessor present with the same issuer is not proof of supersession, complete history or a valid consolidated offering. Blank does not mean first-ever; outside the batch does not mean invalid. Form D notices are not completed financing rounds, SEC approval, registered public offerings or securities recommendations.

## Source proof and privacy

The source ZIP is pinned to `03669a23e724645a8bbcad51822cf7f4b27f91c3f2bedac9dcff3c23e68e84bf`; the reopened read-only database is pinned to `20a5492b9f0997c40397f504fa5dcc3df88cbb538e7275665cec603eaeb772b8`. The ingestion summary and original company index have separate exact pins. The receipt retains null HTTP status and exact download clock. Local verification is not first-public time.

Before projection, every field in every FORMDSUBMISSION, ISSUERS and OFFERING row is compared in source order with its persisted database row. Exact schemas, ZIP inventory/bounds/CRC, database quick-check, accession joins, duplicate identities and one primary issuer per submission are checked. Database and archive hashes are checked again after reads. This is a three-table correspondence audit, not a new re-audit of owner/person tables.

Each public notice cites original row IDs and full-row canonical hashes. Serialization is UTF-8 of sorted-key, compact, ASCII-escaped JSON plus one newline. These hashes include the complete source row, but its private fields are never projected. Raw rows stay in private evidence, not the repository.

The public allowlist contains issuer CIK/name as filed, accession, form, filing date, primary role, amendment/previous-accession diagnostics, and fixed security-type checkbox states. No people, addresses, contacts, amounts, descriptions, signatures, prices or quantities are published. Names must be rendered as inert text. These issuer identifiers are not security/ticker/manager mappings. Type flags are filer assertions, not eligibility checks; blanks are missing as reported, not verified false.

Malformed identity, duplicate/ambiguous issuer join, invalid selected date/form, changed source or unsafe issuer label aborts the whole build. No affected row is silently excluded. Unknown checkbox/amendment strings and malformed previous-accession text are redacted to fixed categories; valid references preserve separate missing/external/in-batch states. Self/cycle/form-flag conflicts are diagnostics, never automatic lifecycle repairs.

## Consumer contract

Public artifact: `web/company-findings/formd-notice-history.json` (450,574 bytes for this reviewed version). The consumer must pin its full byte length/SHA-256, validate schema, unique sorted cohort CIKs, unique company records and exact company/notice CIK membership, and account for aggregate totals before use. This artifact is bounded to 900,000 bytes by the generator. The file is a single lazy-loaded sidecar; there is no need to fetch thousands of issuer records.

For an exact CIK:
1. Not in `cohort_ciks`: `NOT_EVALUATED`.
2. In cohort but no `companies` entry: `NO_SELECTED_ISSUER_NOTICE_IN_PINNED_Q3_FORM_D_BATCH`.
3. Present: display its source notice records, with separate filing dates and amendment diagnostics.

Do not select by name/ticker, merge previous accessions, sum notices into transactions or interpret absent records as zero financing. The official prepared archive is the verified citation. Each SEC accession search URL is constructed from a validated accession and explicitly **unfetched/unverified**. It is not a verified original-filing URL and does not assume an issuer-CIK archive directory.

## Reproduction

```sh
python3 backend/company_offering_notices.py --root . \
  --archive /path/to/sec-formd17/2026q3_d.zip \
  --database /path/to/sec-formd-ingested17/offerings.sqlite \
  --summary /path/to/sec-formd-ingested17/summary.json \
  --out /trusted/new-private-directory
python3 -m unittest discover -s backend -p test_company_offering_notices.py
```

Output is deterministic. The destination must be new and outside the checkout. The directory is 0700 and files 0600. INCOMPLETE precedes source work; private evidence and public metadata precede the final COMPLETE hashes. Failed builds retain INCOMPLETE and cannot claim completion. No workflow, account, order or execution state is changed.
