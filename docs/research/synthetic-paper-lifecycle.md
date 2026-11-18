# Isolated synthetic lifecycle foundation

This offline library is **SYNTHETIC_TEST_ONLY_NOT_EXECUTION_QUALIFIED**. It is not
connected to the existing `paper.py`, protected $500 ledger, UI, market providers,
collectors, broker APIs or schedules. Importing it does not perform I/O. It has no
CLI, file writer, execution adapter or activation switch. All instrument,
candidate, order, session and event identifiers require the `SYNTH_` namespace;
that is a misuse guard, not proof that caller-supplied facts are synthetic.

## Implemented and tested

`backend/synthetic_paper.py` exposes `append(tuple_of_records, event)`,
`replay(tuple_of_records)` and `reconcile(tuple_of_records, cached_snapshot)`.
Start with INIT and a positive synthetic cash balance. Every record contains an
explicit UTC-second timestamp, unique event ID, sequence and previous-record hash.
INTENT freezes a candidate reference, decision time, synthetic session, side,
quantity, limit and total-order fee cap. This candidate reference is not an
eligibility check or source-backed research decision. No automatic sizing or
strategy selection is implemented.

BUY reserves remaining quantity times limit plus remaining fee allowance. SELL
reserves owned, unreserved quantity; short selling is not supported. FILL accepts
only a positive whole quantity, positive price, remaining fee allowance, matching
synthetic session, and price respecting the limit. Partial fills retain the
remaining reservation. Completion releases unused fee allowance. CANCEL releases
only the unfilled remainder; already filled inventory remains. REJECT is allowed
only before any fill. Orders retain their history and cannot reuse IDs after a
terminal state. Repeated events fail closed rather than being silently replayed
as new commands. Lost acknowledgments must be resolved by inspecting the retained
journal, not blindly issuing a new ID.

KILL is a one-way latch for this synthetic account. It stops new intents and all
synthetic fills. It does not imply an external cancellation, release reservations,
liquidate inventory or invent exit prices. Explicit cancellation remains allowed.
Real asynchronous broker fill reconciliation after a kill is NOT implemented;
this module must not be used as a broker adapter.

## Accounting and replay

Amounts are integer millionths of a synthetic currency unit. Inputs are bounded
integers, never floats; quantities are whole units. Fees enter buy cost basis and
reduce sale proceeds. Average cost is allocated proportionally on each sale,
floored to one millionth; the final disposal takes the residual. This is a declared
synthetic accounting convention, not a tax-lot engine. Every applied event checks:

- Cash is at least total cash reservations.
- Owned inventory covers all sell reservations.
- Cash plus remaining inventory cost equals initial cash plus realized P&L.

Replaying canonical JSON records rebuilds state and verifies sequence, hashes,
nondecreasing event time and unique IDs. Same-second events use sequence order.
The returned snapshot is a fresh copy. A mismatch in `reconcile` means the cache
must not be trusted; the library does not repair or overwrite any file.

The immutable tuple and hash chain detect accidental corruption against the
provided chain. They are NOT signed, externally anchored, durable persistence,
protection against an attacker rewriting the whole chain, or rollback/truncation
detection. A valid prefix remains a valid journal. Production recovery would need
durable atomic append, exclusive writer ownership and an external committed-tip
checkpoint before any activation decision. Maximum replay size is 10,000 records;
append validates by full replay, deliberately favoring a small offline test model
rather than claiming production throughput.

## Admission remains blocked

Synthetic fixtures prove only software accounting/state behavior. They are not
realistic market fills or returns and must not be included in research cohorts,
model training, published performance, the protected main ledger or app totals.
No production marks or prices are read or published.

Before any execution-qualified extension: independently verify data rights,
stable historical security identity, actual eligible observations, spreads and
liquidity, trade/quote conditions, market calendars/holidays/early closes, halts,
corporate actions, timing and fill assumptions, durable persistence/reconciliation,
concurrency controls, independent tests and explicit activation authorization.
Session matching here compares synthetic labels only; it does not validate an
exchange calendar or trading hours. Corporate actions, mark-to-market,
unrealized P&L, drawdown, daily reporting and real execution evidence remain
unimplemented. Never infer those from this package.

Run: `python3 -m unittest discover -s backend -p 'test_synthetic_paper.py'`.
The suite covers full round trip, partials, competing cash/inventory reservations,
overfills, fee/limit violations, cancel/reject/kill behavior, replay, tampering,
clock regression, exact cost residuals and deterministic randomized partitions.
