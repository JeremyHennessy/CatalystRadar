# Private originals → public readiness checkpoint

The originals recovered on November14 are privately retained, not in public git.
The local verifier reopens each original, checks header identity, byte count,
SHA256, review binding and retrieval clocks, then emits a strictly whitelisted
checkpoint containing accession/CIK, hashes and timestamps only. It never emits
raw documents, storage paths, Library identifiers or credentials.

Reproduce after restoring the private archive into a local directory:

```
python3 backend/private_archive_checkpoint.py --reviews data/filing_reviews.json --archive-dir PRIVATE-DIRECTORY --output NEW-CHECKPOINT.json
```

The output must not exist already. Retain previous checkpoints. Compare matching
record fields; `verified_at` naturally differs on a fresh byte verification.
`reviews_sha256` binds exact review-file bytes, so changed review input invalidates
the checkpoint until deliberately regenerated. A valid format is not a trusted
attestation: someone could author the same JSON without possessing the originals.

`data/private_originals_checkpoint.json` is the current reviewed saved checkpoint.
The public report calls its count **private originals checked (saved checkpoint)**
and marks `RECORDED_NOT_REVERIFIED_IN_PUBLIC_BUILD`. The separately labelled
**originals rechecked in this build** remains zero because public builds cannot
access the private archive. No source-authenticity, first-public, historic
availability, factual-feature, outcome or trading gate is lifted by this count.

The current checkpoint records all ten originals matching the prior review hashes.
Full qualification still needs event/factual review, frozen decision rules and
qualified outcome data. Every missing/outside-family record is retained.
