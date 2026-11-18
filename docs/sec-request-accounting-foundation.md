# Offline managed SEC request-accounting foundation

`backend/sec_request_accounting.py` is a pure state machine for the proposed November 23–27, 2026 metadata continuation. It cannot access the network, write files, reserve a durable request, schedule jobs or grant collection permission. No existing trial gate, workflow, scanner, private-price pin, source evidence or app state changes.

## Implemented and tested

- Exact ten-issuer SEC submissions URL scope, one explicitly named managed consumer, fixed UTC daily/window boundaries.
- Hash-linked, sequential, exact-schema request intent and outcome events; future/reversed clocks, modified hashes, duplicate IDs and unmatched outcomes fail closed.
- `propose` checks the expected ledger tip and returns an **unpersisted** candidate event. It is not an atomic writer or proof of persistence. `collection_enabled` is always false.
- One unresolved request globally within the supplied ledger, with no automatic lease expiry. The same managed run cannot reopen or cross dates; all ten distinct issuers must complete before the next run.
- Minimum two seconds between reservation timestamps, thirty minutes between run starts, maximum 26 runs/day, 130 runs/window and 1,300 request intents. Failed and unresolved intents are counted, never refunded.
- Every categorized denial or failure permanently stops new reservations in this ledger. Recovery requires a future separate reviewed mechanism, not editing old entries or resetting a boolean.
- Success requires an allowed label, source hash and bounded byte count. **Those fields are caller assertions:** this accounting layer does not authenticate source bytes, identity validation or retrieval clocks. Production integration must independently validate them. Failure events accept no provider bodies, URLs with credentials or arbitrary diagnostic narratives.
- Outcomes arriving after the window still account for already reserved work; no new requests can start after cutoff.

## Why it is not project-wide control

The currently identified request paths are the scheduled watchlist scanner, manual discovery, batch full-text ingestion, daily-index reconciliation, separate reviewed-filing archive client, and manual browser ZIP downloads. The new state machine intercepts **none** of them. It cannot account for external processes or other users on shared infrastructure. A supplied empty or truncated-but-valid ledger is not evidence that no previous requests occurred. Hash chaining is integrity structure, not authentication or immutable storage.

## Required integration before any activation

1. Obtain complete managed-consumer inventory and ledger checkpoint/history; keep unknown consumers explicitly outside any enforcement claim. Route all intended consumers through a single serialized service, or leave them unapproved for this mode. The current foundation permits metadata only, not archive jobs.
2. A separately reviewed durable writer must compare-and-swap against a trusted remote head, persist intent before network, verify its exact committed hash, and reject stale workers/conflicts. Git append-only conventions are not malicious-owner-proof. A local returned event must never be treated as persisted.
3. Preserve the original trial unchanged. A separate runner must verify approved owner/main/first-attempt execution context, contact identity, exact pinned scanner/scope, source permissions, standard public runner $0 limits and shared non-cancelling concurrency. Existing safety checks are not replaced by this library.
4. Test crash-before/after-request, lost receipts, denied persistence, stale heads, cross-job timing, delayed runners and failed publication. HTTP cannot enforce a fencing token: never automatically recycle an unresolved lease until the old worker is independently confirmed terminated and its request outcome reconciled. At-most-once budgeting is not exactly-once retrieval.
5. Verify full source metadata and receipt identity/hashes separately; no label in this ledger grants source completeness. Add secret-safe failure recording and stop on every unsupported condition. Unknown outcomes are not empty successes.
6. Only after independent review of that complete wiring can a bounded schedule be considered. This package does not activate it. Private-price continuation retains its separate quota, rights, holiday-calendar and private Actions cost blockers.
