# All-observed metadata rehearsal and strict fact admission

This offline adapter reads retained public scan reports and their hash-bound SEC
submission snapshots. It enumerates every 8-K/8-K/A row in those snapshots,
without the live scanner's trailing 96-hour acceptance filter. It makes no
network requests, changes no scanner or workflow, and does not activate the
prospective protocol or frozen private mechanical experiment.

The distinction is deliberate: complete recent-response contents are not all
SEC history, the entire market, or necessarily newly public events. Old rows
remain marked as older than 96 hours at observation. A first retained observation
is not the scanner's first-ever knowledge or first-public availability. Current
ticker context is not a verified historical security mapping.

Source failures, missing snapshots and malformed evidence remain visible.
Hashes, lengths (when recorded), source CIK and URL, explicit observation times
inside the run, bounded snapshot sizes and row counts are checked. All candidate
observations remain present across reports; accession identities group repeated
metadata, not independently established underlying events. Conflicting revisions
are held with both versions. A disappearance is not recorded as deletion.
Unknown first-public, underlying-event groups, family facts and outcomes stay
null/UNKNOWN; no trading eligibility is inferred from metadata.

## Reproduce the actual manual pre-trial rehearsal

```sh
python3 backend/normalize_candidates.py --root . \
  --report data/sec-observations/20261115T021704113580Z.json \
  --output /tmp/catalyst-all-observed.json
```

The exclusive output command refuses to overwrite an existing file. The exact
retained public inputs produce 1,591 accession candidates across ten validated
metadata sources, including 1,580 older than 96 hours at observation. The live
scanner emitted the eleven recent rows; this adapter retains the older metadata
as well, without relabeling it fresh. This is NOT 1,591 independent, qualified
training examples. All family facts/outcomes remain unknown; qualification is
zero. Full filing bytes are not established by submission metadata.

The generated complete rehearsal JSON is about 5 MB and is not duplicated in
the repository; the public source snapshots, report and code reproduce it. No
private document, price, path or credential enters the output. A missing/failed
poll is not reconstructed. The draft prospective inclusion rule is not claimed
satisfied until this adapter and complete-source capture are independently
bound into a future activated pipeline.

## Strict selected-family contract

`fact_admission.admit_facts` requires every existing rule operand and boolean.
Missing/null/mistyped/nonfinite values yield UNKNOWN, not a default zero or a
negative signal. Explicit False, zero and negative finite values count as
present, not necessarily comparable or rule-positive. COMPLETE_FACT_TYPES_ONLY
means type/presence checks only, never factual truth or source authenticity.

`classify_family` is an explicit, currently unconnected wrapper. It calls the
existing classifier only after the selected family contract is complete and
the declared event type matches. Common evidence, time, security, market,
calendar, halt and action gates still apply. Missing facts never reach the
classifier. The result cannot borrow another family's positive flag. Guidance
currently maps to EARNINGS in `radar.py`; this code does not add a new standalone
GUIDANCE branch. No caller or frozen rule code was changed, and no real-data
classifications were performed. Future source-grounded extraction must still
supply and independently verify those operands, exact periods/bases, and actual
completion clocks before any prospective use.
