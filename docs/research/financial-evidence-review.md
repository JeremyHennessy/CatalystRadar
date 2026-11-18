# Financial evidence review workspace

This additive projection makes **605 retained repeated financial contexts** inspectable, including 90 with different reported numbers and 515 numerically equal. These are review cases, not qualified growth facts, confirmed restatements, events or securities. There are zero qualified return outcomes here.

The workspace searches exact retained issuer CIKs and accessions, filters four financial metrics and numeric relation, and paginates 20 cases at a time. It links each case to its original SEC filing index. Company names are now attached only through exact accession and CIK joins to retained SEC submission rows; tickers are not inferred. The sole reviewed original-source company finding remains separate and unchanged.

## Source and private/public boundary

Input is the completed retained four-quarter SEC prepared-financial overlap audit. Candidate SHA256: `19327178d9dbe5e8a2d5956bd51a717d4f7ce458ae7e7ee89b8fa77b52915ba1`. The original public checkpoint `four-quarter-context-checkpoint-2026-11-18.json` binds each database and archive. Source data consists of public SEC financial statement archives, not licensed market prices. No new provider calls, credentials or collection changes are introduced.

The previous audit remains immutable and private at row level. Under the new explicit company-intelligence instruction, this separate allowlisted projection publishes only issuer CIK, exact source-associated company names, metric, taxonomy, end date, comparison relation, filing identifiers/dates, source hashes and row IDs. The base index never republishes numerical amounts, narratives, owners, addresses, contacts, accepted timestamps, private provider data or held reports. Separately audited archive-reported values are now available on demand; see financial-archive-facts.md for their stricter raw-row correspondence and remaining limitations. Source rows remain retained for independent reproduction. The publication is a new artifact, not a reclassification of earlier private archives.

The existing extractor chooses standard taxonomy, supported form, single-quarter, empty dimension/co-registrant candidate contexts. Its exclusions mean this is not all financial data or all companies. qtrs=1 is not proof of exact duration; empty dimensions do not prove consolidated scope. EPS is a separate metric, never summed with dollars of profit. All selected cases keep comparability false and outcome INSUFFICIENT EVIDENCE. Numeric differences are rechecked from retained values but amounts are stripped before public output.

## Reproduce the original version 1 baseline

`python3 backend/financial_review_catalog.py PRIVATE/candidate-pairs.json NEW_OUTPUT.json`

The input must match the exact reviewed source hash and fit the bound. Output is exclusively created; no existing evidence is overwritten. The projection rejects duplicate contexts, inconsistent issuer associations, invalid dates/identifiers, nonfinite numeric inputs, incorrect relation flags and unexpected qualification. The catalog is bounded to 1,000 contexts, 30 observations each; the reviewed version 1 output with source-unit labels was 605 contexts and 807,404 bytes, fetched only on demand, not millions of rows.

## Limitations and verification

Filing-index URLs are deterministically constructed from validated public SEC CIK/accession pairs. They have not been individually fetched in this change and must not be described as fetch-verified original documents. Source clocks are not publication or historical decision clocks. First observed remains unknown, not substituted with audit processing time. No price rights, corporate actions, security mapping, outcome or causal interpretation is claimed.

Python tests check real published counts, allowlist privacy, relation/identity failures and duplicate rejection. JavaScript checks real saved schema, search, filters and invalid states. Public-state verifier protects the disabled paper engine. Independent browser review checked actual desktop and 375px mobile rendering, filtering 90 differing-number cases, empty results, pagination and absence of mobile overflow. The final pagination scroll/focus patch is covered by JavaScript contracts; its final browser recheck was interrupted by transport disconnection. No deployment is claimed.

The initial local-only candidate e4daa5f was lost when temporary storage reset. The reviewed web/data/docs survived in the workspace. The two Python files were reconstructed from their authored source, the generator reproduced the surviving catalog byte-for-byte, and checks were rerun on current main 7c91cc0 before release.

## As-filed company-name search extension

The current version 2 catalog is 930,170 bytes. Its 605 review contexts cover 106 issuer CIKs and 318 unique accessions. The retained exact submission joins provide 108 distinct as-filed labels. Name variants remain visible: for example, CIK 0001156041 has both HOUSTON AMERICAN ENERGY CORP and ABUNDIA GLOBAL IMPACT GROUP, INC. These names come from the respective linked submissions; this does not establish a current name, effective rename date, current listing or security mapping. Name similarity is never used for issuer identity.

`backend/financial_review_names.py` builds on the unchanged pinned candidate projection. It requires the exact four-database map, checks each database SHA256 against source-observation identities before and after read-only queries, and joins exactly one SUB row by accession. CIK and filed date must also match. Missing/duplicate or conflicting joins fail rather than invent names. Only the name and SUB row ID are projected; addresses, contacts and other SUB columns are excluded. Source hashes and filing URLs remain unchanged.

Reproduce into a new file with `python3 backend/financial_review_names.py PRIVATE/candidate-pairs.json PRIVATE/database-map.json NEW_OUTPUT.json`. Schema version 2 and a new script cache version prevent old clients from silently accepting a name-less or mismatched catalog. Numeric searches remain exact CIK matches; text searches match recorded name variants or partial accession, not inferred ticker identities. No additional data download, price call, financial calculation or qualification has occurred.
