# Pure synthetic marked-equity reconciliation

`synthetic_valuation.report(journal, valuation_session, valuation_at, marks)` is a pure, in-memory test function. It has no CLI, file/network I/O, quote source, execution adapter, production integration or event append. The existing synthetic lifecycle and public paper ledger are unchanged. It values only an authoritative replay of the supplied synthetic journal, never a cached state.

## Predeclared arithmetic and clock contract

- Amounts and per-quantity marks are integer millionths of the journal's hypothetical currency. Marks are integers from zero through `10**15`; booleans, floats, negative values and strings are rejected. Zero is an explicitly supplied hypothetical zero valuation, not missing data.
- `marks` is a tuple of at most 1,000 exact dictionaries: `instrument_id`, `valuation_session`, `at`, `price_units`. Its instrument set must exactly equal positive-quantity held positions. Duplicates, missing marks, unknown instruments, surplus marks for flat positions and extra fields fail closed. All instrument and scenario identifiers must use the existing `SYNTH_` grammar.
- `valuation_session` is a caller-selected synthetic scenario label that binds all marks. It is **not inferred from an order**, not a global journal session and not a verified exchange session. Historical journal orders can have their own synthetic session labels.
- Every mark's timestamp must exactly equal `valuation_at`, a UTC-second timestamp. This zero-age policy rejects older and later marks rather than implicitly reusing one. Valuation time must be no earlier than the final validated journal event. A later hypothetical valuation time is allowed with explicitly contemporaneous marks, but this does not authenticate actual freshness, clock truth or future knowledge. Empty marks in a flat portfolio still require valid scenario/time and journal ordering.
- Individual and aggregate reported quantities/amounts, products, signed differences and reconciliation results must have absolute value at most `10**30`; an otherwise valid replay can be rejected for valuation overflow. Python integer arithmetic is exact. This explicit result bound is separate from the lifecycle's input-unit cap.
- No new rounding occurs. Replay's proportional average-cost disposal floors allocated cost to an integer unit; final disposal takes its residual. The valuation uses that remaining cost unchanged. Buy fees are already in cost and sale fees are already in realized P&L; neither is deducted again.

## Identities and reservations

For each held instrument:

```
hypothetical value = full held quantity × supplied synthetic mark
unrealized P&L = hypothetical value − remaining replay cost
```

Across the portfolio:

```
hypothetical equity = cash + sum(hypothetical holdings value)
hypothetical equity = initial cash + realized P&L + unrealized P&L
available cash = cash − buy-order reserved cash
```

Both equity expressions are checked exactly. Cash already includes reserved buy cash, so reservations must not be subtracted from equity again. All held quantity is valued, including sell-reserved quantity; unreserved quantity is displayed separately. Cancellation releases reservations but does not itself change equity. Realized and unrealized components remain distinct. This is accounting reconciliation, not a forecast or proof of liquidation proceeds.

The report includes journal tip hash/count/time, explicit scenario/as-of, marks through position rows, remaining cost, paid fees, reservations, full hypothetical equity and signed P&L. Hash chaining verifies internal replay consistency, not external journal authenticity. A killed journal stays killed; valuation never authorizes fills, clears a kill switch, places orders or changes lifecycle state. Execution authorization is always false.

No return, drawdown, annualization, tax, spread, liquidation fee, financing or slippage is inferred. A single snapshot cannot establish those histories. Marks are hypothetical inputs, not actual market data or executable prices.

## Tests and isolated scope

Eleven tests independently exercise partial purchases, partial/final sales with cost residuals and fees, buy/sell reservations, cancellation, flat states, killed states, zero marks, immutable inputs, cross-scenario/stale/future timestamps, malformed and duplicate identifiers, missing/extra coverage, boolean/noninteger prices, tampered journals, a genuinely replay-valid large journal exceeding valuation bounds, 80 deterministic accounting paths, multiple-instrument conservation and order independence, and an AST restriction on I/O/execution imports. Only the new module, tests and this document are added. No static scenario is presented as observed performance.
