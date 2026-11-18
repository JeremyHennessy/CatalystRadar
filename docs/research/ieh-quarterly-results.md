# IEH: reported operating, net and basic-per-share results

This supplement deepens the existing IEH company investigation. It is not a new event, independent corroboration, a current profitability conclusion or a trading signal. The existing revenue artifact and all scanner/queue pins remain unchanged. A consumer can load this separately after verifying its pin and exact cross-reference to the existing IEH evidence.

## What the retained issuer paragraph reports

The same EX-99.1 paragraph compares the quarter ended **September 30, 2026**, labeled **2nd quarter fiscal year 2027**, with the quarter ended **September 30, 2025**, labeled **2nd quarter fiscal year 2026**:

| Metric | Current reported value | Prior reported value | Calculated signed difference |
|---|---:|---:|---:|
| Operating profit / loss | 1,046,496 | −104,380 | 1,150,876 |
| Net income / loss | 1,363,414 | −26,861 | 1,390,275 |
| Basic gain / loss per share | 0.55 | −0.01 | 0.56 |

Dollar symbols are source-reported; **ISO currency is unknown**. The first two metrics have units “dollars as reported”; basic EPS has units “dollars per basic share as reported.” No diluted EPS, share count, margin, implied currency or growth percentage is computed. Exact quarter start dates remain unknown. The differences are **calculated signed differences from reported amounts**, not independently reported facts or evidence of accounting comparability. Negative prior baselines do not become percentage-growth denominators.

Profit, income and gain wording supplies the positive sign; loss wording supplies the negative sign. The source uses positive literal magnitudes with those terms. Decimal parsing and 80-digit subtraction preserve the exact reported values; no float arithmetic or model is used.

## Original source and relation to revenue

The original archive, receipt, accession, single issuer CIK, header/form/dates, source member and original revenue paragraph are checked by the existing `issuer_revenue_comparison.load_source` and `build` APIs without modifying them. The old public revenue artifact is independently pinned. The new projection requires exact equality of issuer, filing, comparison and provenance, then explicitly requires the same original paragraph span and exhibit hash.

- Accession: `0001174947-26-000991`
- Issuer CIK: `0000050292`
- Retained source: `https://www.sec.gov/Archives/edgar/data/50292/000117494726000991/0001174947-26-000991.txt`
- Exhibit: `EX-99.1`, `ex99-1.htm`
- Original paragraph bytes: 29,667–30,325, with SHA-256 in the artifact.
- Filing date: November 13, 2026; reported release/report date: November 12, 2026.
- Recorded retrieval: November 14, 2026 at 23:33:31.646886 UTC. This is retrospective observation, not first-public or decision time.

The prior release's “only revenue extracted” statement remains accurate for that version. This new supplemental artifact extracts three additional metrics from the same paragraph; it does not rewrite the original card, imply independent confirmation or qualify underlying financial statements. No matching prepared-data or security join is added.

## Narrow reusable extraction and failure behavior

`issuer_quarterly_results.extract` accepts only the existing full-paragraph grammatical form, with all three current profit/income/gain and prior loss clauses, dollars and **basic** per-share wording. All fiscal labels must agree across metrics, with the same ordinal quarter and consecutive fiscal years; the actual reviewed case additionally pins FY2027/FY2026 and IEH identity. Unsupported wording, negation/extra qualifiers, quoted context, duplicated paragraphs, malformed inventory, changed units or signs and inconsistent labels fail closed. Other issuer formats are not asserted absent or interpreted opportunistically.

Private evidence retains the normalized paragraph; public output contains only metrics, source spans/hashes, identity, clocks and explicit limits. Per-literal character spans bind the normalized text produced by `financial_admission_rehearsal.plain`, with UTF-8 substring hashes. They are **not raw byte spans**. The separate original paragraph span/hash and exhibit/member/archive hashes bind original bytes.

No original quarterly 10-Q, accounting policies, consolidation, amendments or full comparative basis has been reviewed by this supplement. The values remain issuer-reported. First-public time, historical security mapping, training and execution remain unqualified; outcome estimates are null.

## Reproduce privately

```sh
python3 backend/issuer_quarterly_results.py \
  --root . \
  --archive /path/to/CatalystRadar-SEC-originals-2026-11-14.zip \
  --out /trusted/new-private-directory
python3 -m unittest discover -s backend -p test_issuer_quarterly_results.py
```

Output directories are new, outside the checkout and mode 0700; files are 0600. `INCOMPLETE` is written first. Private evidence and the public finding are written before final completion hashes; failed work retains `INCOMPLETE` and never gets a completion marker. No provider call, source collection, workflow, ledger or trade action occurs.

Public file: `web/company-findings/ieh-reported-quarterly-results.json`. UI integration belongs inside the existing IEH company/scanner detail, with old revenue facts still usable if this optional supplement is unavailable. A consumer must validate its exact bytes/hash, CIK/accession, revenue cross-reference pin and paragraph/exhibit hashes before displaying it, preserving reported units, negative signs, separate dates, null currency/starts and all qualification limits.
