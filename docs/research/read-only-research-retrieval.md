# Read-only research retrieval interface

This deterministic Python function/CLI is a usable local retrieval surface over the released research queue. It does not call an LLM, interpret natural-language questions, connect to providers, write files, train a model or activate orders. It answers only which **saved research entries** match an exact issuer CIK, a bounded literal source-name substring and/or an explicit category.

## Use now

From the repository:

```sh
python3 backend/research_retrieval.py --cik 32604 --category ISSUER_REPORTED_FINANCING_REVIEW
python3 backend/research_retrieval.py --cik 50292
python3 backend/research_retrieval.py --name "Emerson Electric"
python3 backend/research_retrieval.py --category ACQUISITION_DISPOSAL_DISCLOSURE_REVIEW --limit 20
python3 backend/research_retrieval.py --limit 100 --offset 100
```

For a programmatic consumer: `from research_retrieval import retrieve`, then `retrieve(repository_root, cik='32604', category='ISSUER_REPORTED_FINANCING_REVIEW')`. CIK accepts one to ten ASCII digits, excludes zero, and normalizes leading zeros. It is not ticker or name-to-identity resolution. Categories are exactly the existing five research types; unsupported categories fail, rather than guess. Limit is 1–100; offset is 0–10,000. Results retain ascending CIK order, never rank by business quality, returns or significance.

The CLI returns complete JSON to stdout on success. Invalid command syntax, numeric argument syntax or category choices use standard argparse usage/error output on stderr and exit code 2, with no JSON result. Retrieval validation failures (such as invalid CIK/range or unavailable/mismatched evidence) use a fixed error on stderr and exit code 2, also with no partial result. Empty matches are a successful scoped result, not an error and not evidence that a company or event does not exist. `requested_cik_present_in_snapshot` distinguishes a known company with no selected category from a CIK outside this snapshot. An offset past the result set yields an empty page while preserving the total matched count.

## Evidence and qualification

The exact released version 3 index is pinned by SHA-256 and byte length. All nine referenced released artifacts are re-read under their pins and the existing index generator reconstructs the snapshot; the response is refused unless it is equal. Thus the interface cannot silently mix a new financial case version with old insider or disclosure references. New data requires a reviewed snapshot/interface update. This is local byte/derivation verification, not independent source authentication or fresh URL checking.

Each result includes the original research entry, its existing investigation URL, any separately linked insider detail URLs, and relevant source artifact paths/hashes/byte lengths/URLs. URLs use a fixed published-app base and narrowly allowlisted destinations. No URL is fetched. Published files can change later, so retain the hashes with any result. Original SEC link availability and review qualifications remain in the source artifact; a link is not a claim of new access.

The snapshot covers 108 company entries, including 106 financial-review issuers, IEH's separate reported comparison and Emerson's reported financing. It is not all SEC companies. The financial cohort remains 106/605 contexts; insider and disclosure source scopes remain distinct. Missing source coverage, unknown first-public timing, unqualified accounting comparability and disabled training/execution are preserved. Holdings remain unassessed, with position count null, because no verified issuer-security mapping exists in these retained sources.

The interface emits no new financial values, narrative, private owner details, source credentials, ranking, probability or trade recommendation. It retrieves research questions and evidence pointers rather than synthesize an answer or infer a combined event. A later AI-facing adapter must preserve these semantics and must not treat results as instructions or as qualified training examples. No server, external API, model integration or UI change is included in this release.

## Verification

Tests cover exact CIK/category results, scoped no-match distinctions, pagination, deterministic output, source hashes, invalid identifiers/options/links, corrupted snapshot/source refusal, and the actual CLI including no partial output on failure. Existing UI, source snapshots, reports, ledger and collector schedules remain unchanged.


## Interface version 2: bounded source-name retrieval

Optional `--name` (or `retrieve(..., name='Emerson Electric')`) searches only financial/release/financing/insider **company-name fields**. As-filed ticker fields are excluded. Input is 3–120 characters before and after normalization. Control/format characters are rejected. NFC normalization, Unicode case folding and whitespace collapse precede **literal substring** matching; punctuation is not stripped. There is no regex, fuzzy search, alias expansion, spelling correction or fallback to ticker/name inference. A short symbol that happens to be text in an actual reported company name may match that name; it is not resolved as a ticker.

Each result retains its exact issuer CIK and all matched source-name labels with their field associations. Duplicate name occurrences within the same source field do not create additional company results. The interface does not select a preferred current name or merge different CIKs. Existing source dates and identity caveats remain attached to the entries/evidence.

`name_search.matching_companies_before_other_filters` and `ambiguous_before_other_filters` describe the complete name match set **before CIK/category filtering and pagination**. Thus a one-result page or an exact CIK filter cannot hide that a name matched multiple companies. A unique saved match is still a source-label candidate, not independently verified identity. All filters combine with AND; no match causes no broadening. Unknown CIK versus category/name exclusion is reported separately by the existing CIK-presence flag. Without a name query, name counts/ambiguity are null and matched-label lists are empty.

The same exact snapshot and nine-source hash/reconstruction gate runs before every search. No provider calls, model inference or new data are introduced. Additional tests cover true as-filed name matching, ticker-field exclusion, ambiguous pagination/filtering, Unicode normalization, repeated labels, literal regex/shell/HTML/instruction-shaped inputs and rejected controls/overlong queries. Query text is data, never executed or treated as instructions. CLI and function output remain JSON/public evidence only.
