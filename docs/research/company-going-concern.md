# Company going-concern disclosure review

This optional exact-CIK sidecar provides source-context records to investigate in original filings. It is **not a risk classifier**, going-concern conclusion, current warning, forecast, default/bankruptcy detector or trading signal. It does not rewrite the existing company directory or prior artifacts.

## Fixed scope

Selection uses five exact standard concepts in the pinned October 2026 SEC statements-and-notes batch:

- `DisclosureOfGoingConcernExplanatory`: IFRS 2025, `textBlock`.
- `SubstantialDoubtAboutGoingConcernTextBlock`: US GAAP 2025/2026, `textBlock`.
- `SubstantialDoubtAboutGoingConcernWithinOneYear`: US GAAP 2025/2026, `boolean`.
- `SubstantialDoubtAboutGoingConcernConditionsOrEvents`: US GAAP 2025/2026, `string`.
- `SubstantialDoubtAboutGoingConcernManagementsPlansSubstantialDoubtNotAlleviated`: US GAAP 2025/2026, `string`.

Custom or abstract definitions cannot enter these records. No value/outcome filter is applied. Of 271,414 TXT rows, 123 match this exact concept/version policy and 271,291 are outside it. The selected records belong to 108 filings and 97 distinct CIKs, all within the pinned 8,035-company cohort. The other 7,938 cohort CIKs have no selected context under this policy; this is **not no risk/no substantial doubt**. Outside-cohort CIKs are not evaluated.

The 123 selected contexts retain these separate source types:

| Status | Contexts | Meaning |
|---|---:|---|
| UNINTERPRETED_DISCLOSURE | 119 | A tagged narrative block exists; its text has not been classified as an affirmative conclusion. |
| FALSE_AS_REPORTED | 2 | The source boolean is false in its particular context; this does not establish absence of financial risk. |
| UNINTERPRETED_SPECIFIC_STRING_DISCLOSURE | 2 | Specific tagged narrative strings exist; no assertion is inferred from their concept names. |

There are 111 zero-dimension and 12 one-dimension contexts. Repeated contexts/filings are not deduplicated into events or propagated to an issuer-wide fact. The two false values belong separately to NCL Corporation CIK 0001318742 and Norwegian Cruise Line Holdings CIK 0001513761; their entities and source contexts remain separate.

## Temporal and dimensional limits

Prepared `ddate` and `qtrs` are retained verbatim. They are not independently established exact duration boundaries, event dates or knowledge times. Do not derive dates from context-ID strings. A historical-period context may contain later events or management plans: the specific-string records for CIK 0001530185 have a June context and an October filing, and their narrative must not be backdated to June. The public artifact does not publish or infer an event date.

Exact context IDs, dimension hashes/counts, language/escaping flags and the source `segt` marker are retained. Raw DIM segment strings stay private, represented publicly by a UTF-8 hash and the original DIM row identity. Verbatim context IDs may themselves contain member-like company cues; these are not interpreted as verified QNames or identity mappings. These prepared metadata do not verify original QName bindings or accounting scope. No unit is invented: the selected TXT schema has no `uom` field. All selected co-registrant fields are empty; unexpected nonempty fields fail closed rather than create an unreviewed association.

Every record is explicitly `PREPARED_SOURCE_NOT_ORIGINAL_QUALIFIED`. No original document is newly fetched or independently qualified. Source observation/download and HTTP status remain unknown as recorded; the old local verification time is not first-public evidence. Filing date, source period, local verification and possible later narrative events remain distinct.

## Lineage and privacy

Pinned sources:

- Notes ZIP SHA-256 `44d1b48909babe6611fcf59ff5bd273281616acbf2b91567e9597a51f924cee1`.
- SQLite SHA-256 `f2e9a91fb48a3c91fc47d2eff55d4cc63f77157cabab9e96278815621f10e597`.
- Existing company index SHA-256 `c488e6b0aab25ef2e8b0434e2a518bfb44c03af93c4bbba5ec6dd42682ada013`.

The builder independently streams and compares **every field of every TXT, SUB, TAG and DIM row** from the original ZIP against the reopened read-only database. It verifies schema, four member CRCs/hashes, row counts, complete row correspondence, unique selected joins and source pins before and after reading. Other note tables are not re-audited here. The original 49 numeric taxonomy gaps are neither repaired nor silently claimed resolved by this TXT-only selection.

Selected public records include issuer-only identity, accession/form/filing date, exact concept/version/type, limited context metadata, source row IDs/canonical hashes and a value hash. Full narratives, specific string values, footnotes, raw DIM segment strings, amounts, contacts and person information stay private. Full-row canonical hashes use sorted-key compact ASCII-escaped JSON plus newline, encoded UTF-8; value/member hashes use exact retained UTF-8 strings without HTML unescaping. Context IDs and issuer labels are inert text, never HTML or instructions.

False booleans are parsed strictly (`false`/`0` versus `true`/`1`), never by string truthiness. Unknown lexical forms fail closed. Duplicate joins, wrong identity, changed taxonomy/datatype, malformed context metadata, unsafe labels or source-pin mismatches abort the entire build rather than silently drop records.

## Consumer and reproduction contract

Artifact: `web/company-findings/going-concern-contexts.json` (hard maximum 700,000 bytes). Consumers must pin bytes/SHA, validate exact cohort/company/context membership, unique source record IDs, source-type/boolean correspondence and conservation counts before rendering. Lazy-load this optional review within the existing exact-CIK company workflow. For a cohort CIK without an entry, use the scoped no-selection label, not a zero-risk badge. Do not rank or color-code companies by assumed severity.

The official prepared ZIP is the verified source citation. Validated accession-only SEC search links are explicitly constructed and **unfetched/unverified**, not verified original documents or issuer-directory links.

```sh
python3 backend/company_going_concern.py --root . \
  --archive /path/to/sec-notes17/2026_10_notes.zip \
  --database /path/to/sec-notes-ingested17-v2/notes.sqlite \
  --summary /path/to/sec-notes-ingested17-v2/summary.json \
  --out /trusted/new-private-directory
python3 -m unittest discover -s backend -p test_company_going_concern.py
```

Output is deterministic. New private directories are 0700; evidence, public candidate and completion files are 0600. INCOMPLETE precedes source work; completion hashes are last and failed builds retain the marker. No provider requests, credentials, collection changes, orders or execution activation occur.
