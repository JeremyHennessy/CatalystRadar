# Collector operations and bounded continuation

Audit: 2026-11-18 01:08 UTC. Public checkpoint `0e1e663c4922d3e39ead81d07efe67ca21b25d13`; private checkpoint `9a9225f76201e86f83c61f1a4c7bec104f226ffa`. This change adds an offline projection only. No workflow, trial gate, credentials, budget, paper book or provider requests change.

## Operational index

`web/collector-status.json` is generated from saved public receipts and audited policy metadata by `backend/collector_status.py`. Run:

```
python backend/collector_status.py --as-of "$(date -u +%Y-%m-%dT%H:%M:%SZ)" --output web/collector-status.json
```

`as_of` is the projection clock, not a collection timestamp. Ages and next slots are computed at that clock; a UI must show this timestamp and not describe an old projection as live. Next configured slots are not guaranteed executions. Refresh means reloading this saved index, never making provider calls. This first index is manually generated; existing scheduled builds do not refresh it.

SEC `last_successful_observation` is derived only from a complete retained receipt. The last retained reservation is admission intent, not successful retrieval. `last_attempt`, missing periods, rejection counts and current workflow failure remain explicitly unknown because a complete Actions-history listing was not available in this audit. Known successful job steps were checked for public run44163556564 and private run44172913902; that does not exclude later failed/skipped attempts. Do not interpret unknown as zero. Private success metadata comes from the allowlisted public `data/price_feed_status.json`, not private raw snapshots. The index publishes no prices, returns, private source bodies or secrets.

## Current policies

- SEC: `17,47 11-23 16-20 11 *`; runtime Nov16–20 2026,06:00–18:59:59 New York. Last configured slot Nov20 23:47UTC; cutoff Nov21 00:00UTC.10 issuer metadata feeds only. Latest retained complete observation Nov17 19:54:39UTC. Durable reservation before requests, shared concurrency,30-minute suppression, failed-receipt/unresolved-reservation block, bounded daily push fallback.
- Private prices: `10 12 16-21 11 *`; runtime Nov14 through Nov21UTC, cutoff Nov22 00:00UTC. Private workflow blob `094a279366d11bfb3972b24d36535df8ff08f35c`, public collector pin `2cc42023deddf3ad275848d6631e59b21ca80680`.11 symbols ×100 compact daily rows. Latest retained receipt Nov17 20:49:18UTC.13-second pacing, no retries/redirects, privacy rechecks, shared single-consumer concurrency. Conservative11-call/run reservation across current/retired price workflows allows at most22 calls in rolling24h; external key use remains unknown.
- Historical financial/notes/insider/13F/reference data: manual/offline imports, not scheduled acquisition. Grouping these in the index does not certify each individual dataset's freshness or rights.
- Private conditional evaluation has its own Nov17–21 schedule and uses retained evidence without provider calls. It is not an ingestion collector and must not be represented as executable trading. The separate paper engine remains disabled.

## Continuation proposal, NOT activated

1. Preserve the trial evidence and gates. Use a separately reviewed bounded policy with explicit start/end, request ceiling, source scope and receipt requirements; do not simply remove dates.
2. SEC may retain existing10-feed scope and safety controls after permission/rate-policy review. Keep reserved-before-network and denial/unresolved-run stops. Test date boundaries, delayed runs, duplicate/overlapping jobs, latest failed scan, missing receipt and publication failure.
3. Private prices require verified remaining free Actions/storage allowance and source-use rights. Confirm no uncounted key consumers. Keep11 symbols and private storage; do not add public consumers or new data products.
4. Fix conservative history accounting before indefinite operation: current budget rejects at100 combined history rows. Add bounded pagination or a durable reservation ledger with tests; do not weaken fail-closed behavior. Update pinned collector only after compatibility review.
5. Add secret-safe structured failure classes: auth, entitlement, quota, rate limit, schema, validation, network, stale, partial, empty-success. Existing generic sanitization is safe but insufficient for operational diagnosis. Preserve last success separately from last attempt, and never print provider bodies/secrets.
6. Keep archive expansion manual until a concrete analytical gap selects source/window and confirms storage, rights, hashes and schema. Prioritize extraction from existing retained evidence.

No continuation has been enabled. Unknown licensing, key consumers, billing allowance or consequential protected-workflow changes stay blocked pending the appropriate review. No assertion of $0 ongoing execution can be made from workflow files alone.
