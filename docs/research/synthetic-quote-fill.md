# Synthetic quote-to-fill regression

This is a pure simulation test adapter, not the PAPER_V2 order engine, a source
connector, or an input-rights assessment. It accepts only the existing
`SYNTH_` lifecycle identifiers and does not write anything.

One illustrative model uses a fresh, same-instrument/same-session snapshot
from strictly after the last journal event. Quote timestamp, observation,
tradability observation and preview time must be ordered; the quote may be
at most two seconds old. Missing, stale or future evidence, unknown or halted
tradability, invalid/crossed book, a noncrossing limit, or unavailable displayed
size causes refusal. The quantity is the smaller of active order remainder
and opposite-side displayed size. Buy at ask, sell at bid, with illustrative
integer-unit one-cent-per-whole-share fee and the previously reserved fee cap.
This does not model priority, cancellations after observation, full-depth or
multi-venue liquidity, actual market status, or venue execution.

The crossing output is an existing synthetic lifecycle event, not an order
placement, reservation mutation, commission schedule or actual fill. A preview
must be produced with the latest acknowledged synthetic prefix for new
activity. Tests combine bad evidence refusal, a size-limited partial fill,
an actual child-process exit after a disposable SQLite test commit, and an
exact retry from the original frozen input and prefix. Assert that position,
cash, fees and reserves are unchanged by duplicate retry. An event from a new
prefix cannot recycle the old quote clock under this model. This does not
reserve displayed size across independent simulations.

The journal commits the resulting FILL fields, not source quote bytes or a
verified quote receipt. Matching output values do not prove that two inputs
were identical. External source identity, time, entitlement and retained input
binding require separate proof before any non-synthetic use. The $500 V2 and
historic trial remain outside these tests.
