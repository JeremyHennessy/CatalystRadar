# Read-only company evidence retrieval

This CLI makes the existing fixed 8,035-CIK company investigation corpus usable by a research agent without an LLM, HTTP service, provider request or file output. It does not extend the cohort or qualify financial comparisons, security identity, events, trading or training.

```sh
python backend/company_evidence_retrieval.py search --name 'Emerson' --limit 20
python backend/company_evidence_retrieval.py search --cik 32604 --section insider
python backend/company_evidence_retrieval.py evidence --cik 32604 --section insider --limit 5 --offset 0
```

Search is literal NFC/casefold/whitespace-normalized **source-reported name** matching, not regex, ticker resolution or a current preferred name. Unicode controls, empty queries and overlong queries are rejected. Visually confusable letters are not transliterated. Exact CIK accepts only 1–10 ASCII digits and normalizes leading zeros. Each matched company appears once; matching source labels are retained. Global name ambiguity is computed before exact-CIK, section and pagination filters. A section search selects only companies with records in that fixed selected source, not companies with activity generally.

The original evidence sections are `prepared`, `insider`, `disclosure` and `scanner`. Prepared records preserve each original source object with its separate batch associations, dates, names and reported tickers; they are not a merged unique filing history. Insider retrieval hydrates actual unchanged public filing records from the source's pinned shard, not merely a category link. Its summary and source context preserve Q2/Q3 filing-batch scope, transaction dates and submission-level plan flag limitations. P/S includes open-market **or private** reported transactions. Missing or unchecked flags do not prove unplanned trades. Disclosure and scanner records retain their original interpretation and source references unchanged.

Every invocation verifies the published company index (1,834,945 bytes, SHA256 `c488e6b0aab25ef2e8b0434e2a518bfb44c03af93c4bbba5ec6dd42682ada013`) and independently rebuilds it through `company_investigation.build`, including all pinned upstream sources. Selected published company shards are checked for exact bytes/hash, fixed path, bucket, membership and unique identity before pagination. Insider source shards are separately pinned and checked for exact CIK, unique batch/accession references and filing/selected-row conservation. No persistent cache hides source changes. Python `search` and `evidence` functions require an index returned by `load`, not arbitrary caller dictionaries.

In evidence mode an out-of-cohort CIK returns `OUTSIDE_FIXED_COHORT_UNASSESSED` and a **null** total, not zero activity. Search mode returns zero matching directory records plus explicit `OUTSIDE_FIXED_COHORT_UNASSESSED` coverage; its zero is not evidence of no company activity. In-cohort zero means only no selected record in the named fixed source projection. Xerox Corporation's scanner-only membership does not fabricate prepared coverage or merge it with Xerox Holdings. All original source-specific dates and unknowns remain separate; the result's null first-public time is not the filing date or processing date.

Results contain snapshot/source pins, scope, limitations, original public records, source references, exact-company app navigation, totals, returned counts and next offset. Official source citations/lookup status already in source objects are preserved, not fetched or newly verified. Search limits are 1–20, evidence limits 1–5, offsets 0–100,000. The serialized response including newline is capped at 250,000 bytes. An oversize page fails entirely; request a smaller page rather than receiving truncated evidence. Source hashes and schemas are fixed; changed versions require review.

The command writes only complete JSON to stdout. It does not write artifacts, access private inputs, make requests or enable execution. Validation failures produce a fixed stderr message, exit 2 and no JSON. Argument syntax/choice failures use standard argparse stderr and exit 2. Filesystem reads are restricted by implementation to the selected repository's fixed public source paths; `--root` selects a repository checkout, not a data URL. Both execution and training flags are always false.

Tests cover complete directory pagination and category counts, actual source pages, Unicode/literal ambiguity, wrong identity/duplicate shard membership, source-pin mismatch, scoped absence, oversize output and CLI no-partial-result failure. No existing static payload, queue API, company dossier or UI is modified.

## Reviewed public evidence layers

Three additional CLI sections reuse immutable, already-published evidence. They add no company to the 8,035-CIK directory and do not change the original four sections' response objects or existing `search`/`evidence` Python APIs. New pure retrieval helpers are `layer_search` and `layer_evidence`; the CLI dispatches to them only for these sections.

```sh
python backend/company_evidence_retrieval.py search --section offerings --name 'corp'
python backend/company_evidence_retrieval.py evidence --section going_concern --cik 1513761
python backend/company_evidence_retrieval.py evidence --section assertions --cik 25743
```

- **offerings:** 223 Form D issuer-notice associations for 187 company CIKs, from the fixed Q3 prepared batch. Stable record ID combines exact CIK, accession and source issuer-row ID. Declared predecessors, amendment flags and security-type assertions remain unchanged. These are notices, not verified financing completions or reconstructed offering lifecycles. For the other 7,848 cohort CIKs, zero means only no selected notice in this fixed projection.
- **going_concern:** all 123 selected prepared contexts for 97 CIKs across 108 filings. Stable IDs are the original `notes-txt-*` identifiers. The 119 uninterpreted blocks, two uninterpreted specific strings and two false-as-reported booleans remain distinct. False is not a company-wide no-risk conclusion. Raw narratives and dimension strings are not added; verbatim context IDs and existing dimension caveats remain. For the other 7,938 cohort CIKs, zero means only no selected standard context in the fixed October projection.
- **assertions:** all 11 packages in the fixed original-document inventory, associated with 12 registrant CIKs because the Xerox package lists two separate filers. The eight unsupported-grammar packages remain inspectable and are included in search membership; they do not mean no financial results. The three supported packages retain their seven exact source-reported metric pairs, precision limitations, original dates and arithmetic abstentions. TXMD rounded display arithmetic is not upgraded to actual growth; VitaSpring negative/zero-baseline and IEH unknown-period/currency/comparability limits remain unchanged. CIKs outside this 12-registrant inventory receive **null**, `NOT_ASSESSED_IN_FIXED_ELEVEN_PACKAGE_ASSERTION_INVENTORY`, even if present in the broader company directory. This is not an exhaustive financial scan of 8,035 companies.

Every result wraps the unchanged original source object with its stable record ID, JSON pointer and canonical object hash. Whole assertion packages retain all filers; retrieval does not merge registrants or reassign facts. Source-specific clocks, status fields and unknowns are preserved. Section-filtered search returns companies with a retained record/package, not companies with qualifying activity or risk. Global name ambiguity is still evaluated against the original full directory before section/CIK/page filtering. Search labels remain the existing source-reported directory labels, not a new preferred-name registry.

The Form D (450,574 bytes / `38b21e9f921c6be5ce8db840d9f400d0dcb1ff8b9a25709cb451fbdad4db3d22`), going-concern (304,958 bytes / `4aef0578d20f4f391decf33738917ae4c7e97d36d38ea2f41b69704e666f0170`) and assertion (44,334 bytes / `1540ffdad2a5b31ee8bd024657621cd1d08c3e551903aa9b2e3275372d6eab90`) artifacts are fixed byte/hash pins. Sidecar cohort pins and exact memberships, duplicate IDs, status/qualification fields and census counts are checked. Assertion-related released findings are separately pinned and their exact CIK/accession membership is verified. The common company index still undergoes its existing full public-source rebuild.

This layer validation is explicitly **published-projection integrity and association validation**, not a new audit of private SQLite, original ZIP/filing bytes or current official websites. No private input is opened and no request or new interpretation occurs. Public source provenance is copied intact, including unknown first-public/retrieval times. Existing five-record evidence pages, twenty-company search pages, output byte cap, no-partial-stdout errors and disabled execution/training flags continue to apply. Tests exhaustively compare all company memberships and every returned source object, preserve old response-byte hashes, and reject changed pins, duplicate/misassociated records, unknown statuses and changed counts.

## Optional TXMD companion 10-Q layer

`--section companion_10q` adds one immutable reviewed companion document, not a
new scanner record or expansion of the 8,035-company cohort. Both `search` and
`evidence` accept the existing exact-CIK/name/pagination rules. For example:

```
python backend/company_evidence_retrieval.py evidence --cik 25743 --section companion_10q
python backend/company_evidence_retrieval.py search --cik 25743 --section companion_10q
```

The 4,613-byte sidecar SHA256
`72a69128b92c968f4b2777fc106decb7e4b5ef74ae1f3f740243b091f7bbb6cd`
is verified before use, together with its separate released 8-K clock sidecar.
Exact CIK/accession membership and the three finding IDs are validated. The
unchanged complete source object is returned under stable record ID
`0000025743:0001213900-26-119697:COMPANION_10Q`; its empty JSON pointer denotes the
whole document. This verifies published projections, not fresh original bytes
or source availability. No original SEC request or private file access occurs.

The calendar-2025 milestone recognized in Q3 and separate calendar-2026 milestone
amended November 10 remain distinct. Approximate amounts, future issuer
expectations and acceptance-clock limitations are unchanged. No new arithmetic,
accounting conclusion, trade or readiness change is introduced.

For an in-cohort CIK other than TXMD, evidence returns
`NOT_ASSESSED_IN_SINGLE_COMPANION_10Q_REVIEW` and a null total, not no activity.
Out-of-cohort CIKs retain `OUTSIDE_FIXED_COHORT_UNASSESSED`. Search reports zero
matching reviewed documents in those cases and the explicit
`layer_exact_cik_coverage` distinction; that zero does not assert no filings or
milestones. Existing sections, counts, snapshot pins and responses are unchanged.
