# Shareholder votes and conditional authorization

All ten retained original packages are screened for the exact Item 5.07 header label. One package declares that item, nine do not. No header declaration means no such item in this retained filing, **not no vote**. A bounded, reusable parser recognizes four-column vote tables with exact headings: Votes For, Votes Against, Abstentions, Broker Non-Votes. It preserves integer strings, zero counts and distinct tables; no majority calculation, percentage or cross-proposal total is produced.

## H&R Block: original-source result

The [retained original](https://www.sec.gov/Archives/edgar/data/12659/000001265926000042/0000012659-26-000042.txt), primary `hrb-20261110.htm`, reports an annual meeting on **November 10, 2026**. Exact reviewed proposal context says these three proposals were approved:

| Proposal | For | Against | Abstentions | Broker non-votes |
|---|---:|---:|---:|---:|
| Auditor ratification | 104,299,723 | 667,812 | 200,021 | 0 |
| Advisory executive compensation | 90,281,162 | 1,747,915 | 1,584,642 | 11,553,837 |
| 2026 incentive plan | 90,578,373 | 1,501,832 | 1,533,514 | 11,553,837 |

The separate director-election table is recognized as unsupported by this narrow four-column rule, not treated as absent or zero. Individual director identities are not published. Legal voting thresholds and denominator rules are not inferred from these counts. Advisory compensation approval is not an equity grant.

The 2026 Long Term Incentive Plan summary states **6,500,000 common shares available for awards subject to adjustment, less one share for every share subject to an award granted under the 2018 plan after September 11, 2026**. The deduction quantity is unknown. Therefore net remaining capacity, shares actually issued and dilution percentage all remain null. Effectiveness is stated as one business day following shareholder approval; no calendar date is calculated. The issuer expressly qualifies its summary by the full plan/proxy. This research does not comprehensively assess their terms, eligibility or adjustment provisions.

The source was observed November 14 at 23:33:03.633657 UTC, after the meeting. First-public time and historical availability are not authenticated. This is historical governance research, not a current catalyst, prediction or trading instruction.

## Implementation and reproduction

`backend/shareholder_vote_research.py` reuses the existing retained-cohort archive/receipt/hash/identity/clock validation, but not its material-agreement findings. It separately screens the voting header and primary document. Only complete bounded table text matching the four headings plus four unsigned integers is supported. Nested tables, script/style/comments and malformed number formats are not parsed. Generic table rows carry no proposal identity or approval inference; only the exact independently reviewed H&R source receives source-bound context and conditional plan terms.

```sh
python3 backend/shareholder_vote_research.py \
  --archive /private/CatalystRadar-SEC-originals-2026-11-14.zip \
  --out /private/new-vote-research
python3 -m unittest discover -s backend -p test_shareholder_vote_research.py
```

Public artifact: `web/company-findings/shareholder-votes.json`. Raw source bytes stay private; only issuer/proposal metadata, reported counts, conditions and exact source-span hashes are published. The ten-package cohort is retrospective and not representative. No source requests, prices, owners, signatures, contact details or full narrative are included. Output uses a trusted private parent outside checkout, 0700/0600 files and INCOMPLETE until hash-bearing completion; not immutable storage. Existing APIs, reports, ledger and UI remain unchanged. App integration is a separate reviewed step.
