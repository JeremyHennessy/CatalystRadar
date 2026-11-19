# Research evidence completeness and trade readiness v1

This separately versioned, retrospective overlay reads the original and the
second published documentary rankings via their immutable SHA-256-bound
release manifests. It adds no information about what was known at either
cutoff. It neither rewrites those snapshots nor changes their score,
ordering, WATCH labels, qualifications or underlying assumptions.

Three distinct assessments:

1. **Research priority** remains the existing documentary ranking, not a
   return model or a trade recommendation.
2. **Evidence completeness** counts how many of ten named checks are
   verified in the pinned snapshot. This is a coverage count with equal check
   weights, not a score for the strength or quality of the thesis. Each
   current idea has two verified checks: accession/registrant identity and
   source-reported content reviewed within limits. That neither identifies a
   tradable share class nor establishes an economic effect. **Unknown** means
   the reviewed package does not establish the requirement, not that it is
   unavailable in general or that a check failed. **Not assessed** means this
   ranking did not qualify a financial comparison or evaluate an outcome.
   No verified absence, source denial, or failed market-data check is inferred
   from null or missing evidence. Those states require separately reviewed
   evidence and a new policy version.
3. **Trade readiness** uses a fixed gate order: first-public availability,
   effective-dated security identity, eligible market data, corporate action
   continuity, liquidity, and trading session/halt validation. These are
   necessary conditions, not a complete execution model. The first blocker is
   the first unresolved requirement in that order, not necessarily the
   hardest blocker to clear. All current ideas **need event verification**
   because no linked evidence establishes first-public timing. The display
   should retain later blockers and the original scoped research caveats.

The rule fails closed on record states outside the bounded retrospective
contract; it cannot upgrade a thesis or emit a trade. The JSON overlay includes
the snapshot path, SHA-256, byte count, and cutoff solely as integrity bindings.
The output is also content-addressed. A new policy or permitted evidence
requires a new reviewed version and new asset pins, not a mutable overlay.

From the repository root:

```sh
python backend/research_readiness.py
python -m unittest discover -s backend -p 'test_research_readiness.py'
```

Add `--write` to create the immutable overlays. There are no provider calls or
changes to ingestion, the protected paper ledger, ranking snapshots, or the
reviewed source evidence.
