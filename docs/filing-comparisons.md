# Retrospective reported comparisons

`data/filing_comparisons.json` is a saved, current-analysis research artifact, not a forecast, training label, admitted event or automatically refreshed dashboard dataset. Reproduce with `backend/filing_comparisons.py` using the privately retained original archive and the same analysis timestamp through its Python `build` function. The CLI uses the actual invocation clock and creates a new output only. Public builds cannot reopen the private originals and do not independently reverify this artifact.

The bounded parser supports only IEH CIK 50292, accession 0001174947-26-000991, EX-99.1. It reads literal bytes of the single revenue paragraph after validating the SEC header and the previously recorded source hash/retrieval receipt. It does not use SEC Frames, Company Facts, current ticker associations or any price provider. Ten reviewed cases are retained, including unsupported, missing and invalid cases. Other issuers have not become zero-revenue examples.

The issuer reports 10,700,084 versus 7,077,592 in dollar-denominated revenue for the quarters ended September 30, 2026 and September 30, 2025, respectively. The arithmetic difference is 3,622,492 and relative change is 51.182549%, consistent with its rounded 51% statement. Exact paragraph offsets and SHA256, original-document SHA256, accession, issuer CIK and actual retrieval clock accompany the pair. Quarter start dates and ISO currency are not asserted because this paragraph does not specify them. No cross-currency comparison is allowed.

This is the prior amount **as presented in the later release**, not proof of what was originally available in 2025. Prior original filings, restatement/amendment history, accounting comparability and corporate actions have not been reconciled. Amended submissions are rejected, not silently substituted. A separate reviewed path would be required for amendments. Zero/nonpositive revenue baselines, duplicate paragraphs, conflicting rounded percentages, wrong accession/issuer, other periods or unsupported exhibits fail closed.

IEH remains outside the approved exchange universe. Historical ticker identity, first-public availability, decision clock and outcomes remain null. Its reported growth is not a trade signal. TXMD remains unresolved: continuing-operations EPS has a rounded-zero comparator and the exhibit quarter description conflicts with its body. Revvity and Worthington still lack a verified same-period prior-guidance basis. Existing reviews and all strategy gates remain unchanged.

`analysis_utc` records invocation/reproduction time, not authenticated computation completion or historical availability. No source-authenticity or prospective-readiness upgrade is claimed. No original text, private archive location, Library identifier, secrets or provider data are published. There are no new network calls, schedules, private-workflow changes or orders.

## Additional signed pairs from the same paragraph

The same bounded accession now supplies three further issuer-reported pairs:

- Operating profit 1,046,496 versus operating loss 104,380 (signed prior -104,380): difference 1,150,876 reported dollar units.
- Net income 1,363,414 versus net loss 26,861 (signed prior -26,861): difference 1,390,275 reported dollar units.
- Basic earnings per share 0.55 versus basic loss per share 0.01 (signed prior -0.01): difference 0.56 reported dollar units per basic share. This is not diluted EPS.

Their fiscal labels are second quarter fiscal year 2027 and second quarter fiscal year 2026, exactly as stated. Each nested pair inherits the parent accession, source SHA256, retrieval clock and exact paragraph evidence span. No percentage growth is calculated from a negative baseline. Missing, duplicated or mismatched literal pairs retain null values rather than becoming zeros. Four reported metric pairs in one outside-universe issuer do not constitute four independently sampled events, four qualified comparisons, or a forecasting result. All currency, original-prior-filing, restatement, historical-identity and comparability caveats above still apply.
