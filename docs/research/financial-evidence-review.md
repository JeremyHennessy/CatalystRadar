# Financial evidence review workspace

This additive projection makes **605 retained repeated financial contexts** inspectable, including 90 with different reported numbers and 515 numerically equal. These are review cases, not qualified growth facts, confirmed restatements, events or securities. There are zero qualified return outcomes here.

The workspace searches exact retained issuer CIKs and accessions, filters four financial metrics and numeric relation, and paginates 20 cases at a time. It links each case to its original SEC filing index. Company names and tickers are deliberately not inferred. The sole reviewed original-source company finding remains separate and unchanged.

## Source and private/public boundary

Input is the completed retained four-quarter SEC prepared-financial overlap audit. Candidate SHA256: `19327178d9dbe5e8a2d5956bd51a717d4f7ce458ae7e7ee89b8fa77b52915ba1`. The original public checkpoint `four-quarter-context-checkpoint-2026-11-18.json` binds each database and archive. Source data consists of public SEC financial statement archives, not licensed market prices. No new provider calls, credentials or collection changes are introduced.

The previous audit remains immutable and private at row level. Under the new explicit company-intelligence instruction, this separate allowlisted projection publishes only issuer CIK, metric, taxonomy, end date, comparison relation, filing identifiers/dates, source hashes and row IDs. It never republishes numerical amounts, narratives, owners, addresses, contacts, accepted timestamps, private provider data or held reports. Source rows remain retained for independent reproduction. The publication is a new artifact, not a reclassification of earlier private archives.

The existing extractor chooses standard taxonomy, supported form, single-quarter, empty dimension/co-registrant candidate contexts. Its exclusions mean this is not all financial data or all companies. qtrs=1 is not proof of exact duration; empty dimensions do not prove consolidated scope. EPS is a separate metric, never summed with dollars of profit. All selected cases keep comparability false and outcome INSUFFICIENT EVIDENCE. Numeric differences are rechecked from retained values but amounts are stripped before public output.

## Reproduce

`python3 backend/financial_review_catalog.py PRIVATE/candidate-pairs.json NEW_OUTPUT.json`

The input must match the exact reviewed source hash and fit the bound. Output is exclusively created; no existing evidence is overwritten. The projection rejects duplicate contexts, inconsistent issuer associations, invalid dates/identifiers, nonfinite numeric inputs, incorrect relation flags and unexpected qualification. The catalog is bounded to 1,000 contexts, 30 observations each; actual output is 605 contexts and 762,179 bytes, fetched only on demand, not millions of rows.

## Limitations and verification

Filing-index URLs are deterministically constructed from validated public SEC CIK/accession pairs. They have not been individually fetched in this change and must not be described as fetch-verified original documents. Source clocks are not publication or historical decision clocks. First observed remains unknown, not substituted with audit processing time. No price rights, corporate actions, security mapping, outcome or causal interpretation is claimed.

Python tests check real published counts, allowlist privacy, relation/identity failures and duplicate rejection. JavaScript checks real saved schema, search, filters and invalid states. Public-state verifier protects the disabled paper engine. Independent browser review checked actual desktop and 375px mobile rendering, filtering 90 differing-number cases, empty results, pagination and absence of mobile overflow. The final pagination scroll/focus patch is covered by JavaScript contracts; its final browser recheck was interrupted by transport disconnection. No deployment is claimed.

The initial local-only candidate e4daa5f was lost when temporary storage reset. The reviewed web/data/docs survived in the workspace. The two Python files were reconstructed from their authored source, the generator reproduced the surviving catalog byte-for-byte, and checks were rerun on current main 7c91cc0 before release.
