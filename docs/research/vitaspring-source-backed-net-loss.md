# VitaSpring: retained-source net-loss observation

The same retained SEC 10-Q used for the zero-revenue observation also reports **net losses of $110,845 for May 1–July 31, 2025 and $218,662 for May 1–July 31, 2024**. Both amounts are negative. Their exact signed arithmetic difference is **+$107,817**, a narrower reported loss, not a profit or a percentage earnings-growth finding.

This is an additional source-reported financial fact for company research. It does not establish sustainable operating improvement, its cause, full accounting comparability, a current catalyst, investment merit or predictive value. No percentage growth is presented on the negative comparison base. It is not a claim that such a mathematical ratio cannot be calculated; a ratio would not establish comparable earnings growth here.

## Exact identity and periods

- Issuer CIK: 0001697884, VITASPRING BIOMEDICAL CO. LTD. as filed. No verified current ticker/security mapping.
- Accession: 0001640334-26-001075, Form 10-Q.
- Report period: July 31, 2025. Filing date in retained prepared SUB: June 17, 2026. FY2026/FPQ2 labels remain as filed; they do not change the two source duration contexts into 2026 results.
- Source statement heading: Three Months Ended July 31, 2025/2024. Source row: Net loss.
- Concept: `us-gaap/2025:NetIncomeLoss`; simple ISO4217 USD units; exact CIK entity; no context dimensions/scenario.
- 2025 original occurrences: `fid_2251` and `fid_2284`; literal `110,845`, explicit negative sign, no scale, decimals 0. Prepared NUM row 3041479: `-110845.0000`.
- 2024 original occurrences: `fid_2252` and `fid_2315`; literal `218,662`, explicit negative sign, no scale, decimals 0. Prepared NUM row 3041470: `-218662.0000`.
- Repeated occurrences in the equity statement repeat the same source-local contexts. They are not additional independent observations. Six-month amounts and equity-component/dimensional facts are excluded.

Prepared rows have qtrs=1, USD, empty segments/coreg/footnote, exact accession/tag/version/end-date correspondence. Exact start dates come from the original inline contexts, not an inference from qtrs. SUB row 6719 supplies filing identity. Numeric correspondence is not independent verification of accounting truth or full accounting comparability.

## Source and clock evidence

[Original filing index](https://www.sec.gov/Archives/edgar/data/1697884/000164033426001075/0001640334-26-001075-index.html) and [primary document](https://www.sec.gov/Archives/edgar/data/1697884/000164033426001075/vsbc_10q.htm).

Original retained ZIP SHA256: `e68c0065e400b19e92d07c7bb9cefdba522eefa9c4c35e6a701083f8552c0ee4`.
Primary member SHA256: `ea92f6ce189e277c36b47b60a74d6d4d40098dabc1f17fea3d0d0e6b171e7510`.
Prepared Q2 archive/database and identity-manifest hashes remain in the public card's allowlisted provenance. The builder reruns the original→numeric→occurrence→prepared correspondence pipeline rather than trusting a copied number.

Local source verification time remains November 17, 2026 at 21:34:38.194086 UTC. This is not the exact download or first-public timestamp; those remain unknown. The new card generation clock is separate. Nothing establishes these retained bytes were available to a past trading decision. No prices, outcomes, historical orders or returns are joined.

Context hashes use the previously documented ElementTree serialization method, not raw byte-slice or canonical XML hashes. Raw archive/member hashes bind retained original bytes.

## Implementation and limits

`backend/company_loss_finding.py` is intentionally case-specific. It first reuses the existing source identity/receipt/filing checks, then requires all four exact loss occurrences, negative sign transformation, period/unit/entity match, prepared numeric equality and consistent repeated contexts. Missing, duplicate, changed, dimensional, wrong-period or footnoted selected evidence fails closed. Arithmetic uses integer dollars without floating-point rounding.

Private output uses INCOMPLETE-first and COMPLETE-last hash verification with 0700/0600 permissions. `web/company-findings/vitaspring-net-loss.json` is the completed public projection only. It includes no private SUB address/contact fields, owner data, raw narrative or restricted price data. The existing revenue card remains unchanged. Held research reports, paper ledger, workflow schedules, source data and disabled training/execution gates remain unchanged. User-facing UI integration is a separate reviewed change.
