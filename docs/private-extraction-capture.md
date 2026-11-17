# Private local extraction capture

`backend/record_feature_extraction.py` consumes the existing reviewed filing
collector's `manifest.jsonl` and exact source files. It performs **no network
requests** and has no provider credentials or trading integration.

```sh
python backend/record_feature_extraction.py \
  --reviews /private/input/reviews.json \
  --archive /private/input/originals \
  --private-destination /private/extraction-runs
```

Use an absolute private destination outside the public code checkout. The
recorder refuses a public-checkout destination, symlink destination, non-private
existing destination permissions, changed source bytes, duplicate source files,
future observations, oversized inputs and overwrite attempts. Run directories
are 0700 and files 0600. Protect their parent location and any backup separately.
This local directory is not immutable or remote storage, a retention guarantee,
or an access-control substitute for a shared machine. Overwrite protection applies
to this utility, not other processes. Checkout exclusion covers this code checkout
only; it cannot detect another publishing checkout. The destination and its parent
directories must be private and trusted, with no concurrent untrusted writers.

Each run retains exact input reviews, original manifest bytes and source bytes.
Structural header features are computed using the existing parser. New
`computed_utc` values use the actual runtime clock after calculation finishes;
source retrieval times remain unchanged. No CLI option can supply a historical
computation time. A completion record binds the source manifest, reviews,
feature bytes and implementation hashes, and is written last. A failed or
interrupted run without `complete.json` is incomplete and must not be consumed;
it is left for inspection, not automatically retried or deleted. Consumers must
verify retained hashes and all required files rather than trusting a filename.

## What this does not establish

The runtime clock is recorded, not independently authenticated. A later
computation on an old filing is not earlier knowledge. Historical availability,
trusted-clock verification and trade eligibility remain false; decision times
and first-public times remain unknown. Header markers are not comparable
financial facts. Invalid or missing eligibility remains blocked and no order,
fill or public research report is created.

## Prospective use

After source access is separately authorized, retain each actual collector run
without overwriting older vintages. Capture extraction on those bytes, preserve
independent receipt/storage timing, and review semantic financial extraction.
Only a later separately reviewed integration may use complete evidence in a
new decision frozen before its cutoff. This utility does not alter schedules,
collector code pins, publication holds or the disabled paper book.
