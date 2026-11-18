# Fixed-original financial assertion inspector

This workbench reviews reported financial assertions and the arithmetic that can safely be checked from them. It does **not** qualify financial growth, accounting comparability, a current catalyst, a prediction or an outcome.

## Fixed retrospective inventory and conservation

The locally frozen policy selects **all ten identity-validated 8-K members of one exact retained original archive plus one exact retained VitaSpring XBRL ZIP**. This is exhaustive only within those explicitly pinned packages. It is not all retained originals, the entire Library, a representative market sample or independently authenticated preregistration. The prior known cases informed supported adapters; no statistical no-peeking claim is made.

Policy SHA-256: `69b856309123380dd824dd2537d62e6596ffab56edc05812aedb370ad3eab7eb`. The policy records the existing adapter module versions before this build. There is no amount, direction, return or replacement filter.

The actual audit accounts for **11 packages: three supported issuer packages, eight unsupported packages, seven metric pairs**:

| Source | Pairs | What the check establishes |
|---|---:|---|
| IEH | 4 | Reported revenue arithmetic is consistent with 51% at a whole-percent check; operating/net/basic-EPS signed differences are calculated, while negative baselines abstain from percentage growth. |
| VitaSpring | 2 | The declared inline revenue values are both zero, so percentage growth is undefined. Both net-income values are losses; their signed difference is calculated without a growth percentage. |
| TherapeuticsMD | 1 | Displayed mixed-scale license-revenue values do not exactly reconcile the separately reported increase/percentage. Precision and context require review; no hidden values or accounting error are inferred. |

Eight `NOT_SUPPORTED_GRAMMAR` outcomes mean no supported whole-context assertion under these adapters, **not no financial results or no event**. Each retains its accession, form/amendment status, explicit filer associations, filing/report dates, original source hash and separately recorded request/observation clocks. Multiple registrants remain separate. No old report, parser, card, scanner or queue is overwritten.

## TherapeuticsMD: two different arithmetic checks

The complete EX-99.1 table-cell paragraph displays license revenue of **$1.3 million** for third quarter 2026 versus **$784 thousand** for third quarter 2025. It separately reports an increase of **$475 thousand**, or **60.6%**.

The inspector preserves the literal values and scales, then clearly separates:

1. **Display-literal endpoint arithmetic:** 1.3 × 1,000,000 − 784 × 1,000 = 516,000. The display-literal ratio is approximately 65.8% at one decimal.
2. **Reported-increase internal consistency:** 475,000 ÷ 784,000 × 100 is approximately 60.6% at one decimal.

The first does not reproduce the reported increase/percentage; the second is internally consistent at that check precision. **Neither calculation establishes the actual unrounded change.** The result is `DISPLAYED_ROUNDED_VALUES_NOT_EXACT_RECONCILIATION`, not an earnings-growth finding or proof of source error. No nearest-rounding interval, hidden amount, actual rounding policy or exact source precision is inferred. The check's explicit `ROUND_HALF_UP` rule is an arithmetic presentation convention, not a claim about the issuer's rounding policy.

The full paragraph also attributes the increase primarily to an IMVEXXY sales-based milestone by Knight, tied to sales for the year ended **December 31, 2025**, with a displayed **$365 thousand** milestone payment recognized and confirmed in **third quarter 2026**. This remains issuer-reported attribution, not causal verification. The grammar must match this entire tail; it cannot extract only the convenient first sentence.

License revenue is not promoted to total GAAP revenue, earnings, cash receipts or margins. Dollar symbols do not establish an ISO currency code. The body declares third-quarter results while the exhibit description says second-quarter. The separately released source annotation is revalidated and the conflict retained without silent correction. The current body period ends September 30, 2026; no prior exact end or either exact start date is invented from quarter labels.

## Common deterministic arithmetic engine

The same bounded Decimal/Fraction engine handles all seven pairs. It preserves signed reported or display-normalized values and units. Subtraction uses a high-precision local Decimal context; percentage ratios use exact rational fractions, not floats or an LLM.

- **Positive prior value:** an explicitly labeled endpoint arithmetic check is possible. It is not accounting comparability or true unrounded growth. Reported-increase consistency is a separate optional check.
- **Zero prior value:** percentage result is null, with `ZERO_COMPARISON_BASE_UNDEFINED`; this is not 0% growth.
- **Negative prior value:** percentage result is null, with `NEGATIVE_BASE_NOT_PRESENTED_AS_GROWTH`. A signed difference may still be shown without claiming turnaround, profitability or earnings-growth percentage.
- Invalid/nonfinite/oversized decimals, unknown scales or unsupported precision basis fail closed.

IEH's operating, net and basic-per-share values retain their explicit profit/income/gain versus loss signs. Basic EPS is not diluted EPS. VitaSpring retains exact inline context dates and USD units, while underlying full accounting comparability remains unverified. Repeated inline occurrences are not new independent facts. No margins, implied share counts, denominator repairs, GAAP substitutions or forecasts are computed.

## Original-source reconstruction

The ten-member archive is validated through the existing whole-inventory loader: archive/member/manifest hashes, exact receipt identity, declared filer CIKs, source URLs and clocks. IEH's existing revenue and supplemental-results APIs are reused unchanged and reproduced against their pinned released artifacts. VitaSpring is re-extracted from the original inline XBRL through the existing numeric/context/occurrence and source-to-prepared correspondence pipeline; both old public findings must reproduce, apart from their processing timestamp.

TXMD gets a **new** bounded whole-P/TD-context grammar. It does not use the old license parser's unsafe substring `finditer` as a positive assertion rule. Negation/extra qualifiers/quoted context, a missing or changed attribution tail, partial contexts, duplicate supported paragraphs, malformed inventory, invalid encodings or unsupported period relationships cannot silently become a supported unique assertion. Identity, exhibit context and the released description/body conflict are separately revalidated before publication.

The public artifact contains values, units, source identity, explicit unknowns and original paragraph/exhibit hashes. Original full paragraphs and source-to-prepared rows remain private. Normalized literal spans are **character offsets with UTF-8 substring hashes**, not raw byte offsets. The separate raw paragraph span/hash binds original bytes. Inline context serialization hashes retain their existing non-raw-XML meaning.

Filing/report/recognition/sales-year/observation/local-verification dates have different meanings and are not collapsed. VitaSpring's precise download time remains unknown; its local verification clock is not substituted. First-public and decision times remain null throughout.

## Reproduce privately

```sh
python3 backend/financial_assertion_audit.py \
  --root . \
  --archive /path/to/CatalystRadar-SEC-originals-2026-11-14.zip \
  --vita-config /path/to/existing-source-correspondence-config.json \
  --policy /path/to/frozen-policy.json \
  --out /trusted/new-private-directory
python3 -m unittest discover -s backend -p test_financial_assertion_audit.py
```

The output directory must be new and outside the checkout (0700); files are 0600. `INCOMPLETE` is created before source work. Private evidence and the public finding precede final completion hashes; failure leaves the marker and no completion claim. No source requests, scheduler changes, orders or activation occur.

Public artifact: `web/company-findings/financial-assertion-audit.json`. This supports an inspector within the existing company/scanner workflow, not a new market scan. UI integration must independently verify the exact artifact pin and keep unsupported packages, source conflicts, display-only arithmetic and percentage abstentions visible. The inspector's numeric checks do not relax any existing training, outcome or trading gate.

Pair fields `current_value_for_arithmetic` and `prior_value_for_arithmetic` are normalized decimal inputs, not a claim about displayed precision. TXMD original literals and scales remain separately in `display_precision`. The CLI reads at most 20,001 configuration bytes and rejects inputs over 20,000 bytes.
