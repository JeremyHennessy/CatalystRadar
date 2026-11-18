# Source to company finding: VitaSpring historical revenue

This is the first narrow numerical company-research card in the expanded app: an actual retained SEC source, a checked extraction, a matching prepared-data record, an issuer association, and an explicit **abstention**, rather than an invented trading signal.

Starting HEAD: `0e1e663c4922d3e39ead81d07efe67ca21b25d13`. The separate company finding does not regenerate the held research reports or enable the paper account. Publication of this limited source-derived fact card is covered by the user's new company-intelligence directive; raw private addresses, contacts, narratives and provider-restricted prices remain excluded.

## What the retained filing reports

Issuer: **VITASPRING BIOMEDICAL CO. LTD.**, CIK `0001697884`.

| Exact inline revenue context | Source-reported value |
|---|---:|
| May 1–July 31, 2025 | USD 0 |
| May 1–July 31, 2024 | USD 0 |

The source literals are dashes, not missing values. Both facts explicitly declare the supported Inline XBRL `zerodash` transform, USD unit, undimensioned issuer contexts and declared decimals of zero. Checked extraction gives numerical zero for each.

**Finding:** a percentage revenue-growth calculation with a zero comparison denominator is undefined. It is not zero-percent growth and does not establish a revenue-growth research lead. Revenue is not earnings; this card does not determine earnings growth. No probability, price target, expected return or buy/sell recommendation is supplied.

These are **2025 and 2024 reporting periods**, not current financial results. The prepared submission reports a June 17, 2026 filing date and July 31, 2025 report period. Fiscal year `2026` and fiscal period `Q2` are retained as filed; they must not be relabeled calendar Q2 2026 or fiscal Q2 2025.

## Reproducible evidence chain

1. The original SEC XBRL ZIP for accession `0001640334-26-001075` was retained through the ordinary public browser download control, locally verified November 17, 2026. Exact HTTP/download and first-public clocks were not exposed and remain unknown.
2. The archive SHA-256 is `e68c0065e400b19e92d07c7bb9cefdba522eefa9c4c35e6a701083f8552c0ee4`; primary member `vsbc_10q.htm` SHA-256 is `ea92f6ce189e277c36b47b60a74d6d4d40098dabc1f17fea3d0d0e6b171e7510`.
3. Original fact IDs `fid_2230` and `fid_2231` supply exact context start/end dates, issuer CIK, resolved unit, transformation and value. Context hashes refer to ElementTree serialization, **not** raw context byte slices or canonical XML.
4. The reviewed Q2 2026 prepared-financial database has matching same-accession `Revenues`, `us-gaap/2025`, USD zero-valued records at NUM row IDs `3041506` and `3041504`; SUB row ID `6719` links the issuer and filing metadata. Matching end date and `qtrs=1` provide candidate correspondence, not proof of exact prepared start dates or full accounting comparability.
5. `backend/company_revenue_finding.py` reruns the existing original-source/prepared-database audit, validates this fixed case, and projects only explicitly allowed public fields into `web/company-findings/vitaspring-revenue.json`.

[Original filing index](https://www.sec.gov/Archives/edgar/data/1697884/000164033426001075/0001640334-26-001075-index.html) · [Primary statement](https://www.sec.gov/Archives/edgar/data/1697884/000164033426001075/vsbc_10q.htm)

The retained source and original prepared archive were independently verified previously. This card's selected facts, issuer linkage and output require their own independent review. Numerical extraction and source-byte integrity are not an independent audit of the company's accounting truth or source-clock authenticity.

## What remains unqualified

- The second diagnostic filing was not retained after a timeout; it is not silently substituted or re-requested. Cross-filing comparison and novelty are unverified.
- This retrospective observation was not established as available at a historical decision time.
- No current ticker, tradable share class, price/outcome evidence, corporate-action-adjusted returns or execution inputs are joined.
- Full accounting comparability is not certified by the absence of dimensions or by prepared-data agreement.

The appropriate action is to **abstain from a percentage-growth inference**, inspect the original statement/accounting context, and establish independent security/timing/outcome prerequisites before predictive evaluation. If researching another case, use a predeclared selection and a genuinely comparable baseline rather than choosing convenient results. The app must show the historical periods and all unknowns prominently.

## Tests and reproduction

Synthetic tests reject nonzero/unequal, missing/duplicate, wrong-concept/unit/duration/dimension, identity/date/source-path and admitted-state inputs. They confirm zero-denominator abstention, date distinctions, private-field exclusion and fail-closed completion. The utility is deliberately case-specific, not a general financial qualifier or a replacement for the original research gate.

Use the existing reviewed hashes and private paths in an input configuration matching `source_prepared_correspondence.audit` arguments, then:

```sh
python3 backend/company_revenue_finding.py --config PRIVATE_CONFIG.json --out NEW_PRIVATE_DIRECTORY
python3 -m unittest discover -s backend -p 'test_company_revenue_finding.py'
```

Private output uses a new trusted 0700 directory, 0600 files and a final hash-bearing completion marker. Prior files are not overwritten. Only the reviewed finding JSON is copied into the public repository. Source retrieval did not recur; no new accounts, credentials, spend, model training, orders or fills were introduced.
