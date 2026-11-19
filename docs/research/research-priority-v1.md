# Research priority v1: unpriced, not actionable

This is a retrospective documentary review queue, not a top-trades prediction. The fixed cutoff is 2026-11-19 18:57:49 UTC, declared before output construction. This local ordering is not independently authenticated preregistration. No prices, private market data, outcomes or learned weights are used.

## Fixed universe and selection

Rebuild and byte-compare the already released scanner index and all 64 detail shards from their pinned public source objects. Evaluate all 905 records. Exclude 897 needing original review and two identity/security-context records. Six financial/event records remain; consolidate only VitaSpring's same-CIK/same-accession revenue/loss pair into one financial review thesis. Five entries are returned, not padded to ten. This is neither market-wide nor the ten-stock watchlist. TXMD companion, newer COHR/WOR filings and later supplemental findings are outside this version's selected input, not declared absent.

Multi-filer Xerox remains one source thesis with two explicit registrant associations, never one merged company/security. Source records remain unchanged, including VitaSpring's undefined zero-baseline growth and both-loss semantics, and IEH's issuer-reported comparison with unverified ISO currency/start dates/accounting comparability. No new arithmetic on financial values is performed.

## Rubric and unknowns

Weights sum to 100: narrow original-source review 40; exact accession citation 20; explicit exact period context 20; explicit declared filing-date age 20 (0–30 days=20,31–90=10,older=0). Unknown factors and points are null, not zero. Score is the sum of known points, not renormalized; known-factor weight appears separately. This measures documentary review inputs, NOT attractiveness, confidence, economic magnitude, expected return or validated comparison. A well-documented old finding can outrank a more recent incomplete one.

Ties: newest explicit filing date, then sorted exact registrant CIK set, then stable thesis ID. Observation/verification times do not substitute for filing age. A future planned date remains a plan, not evidence available in advance. The cutoff checks source clock claims, but does not authenticate first-public availability or imply this assembled snapshot existed historically.

Every entry is WATCH / UNPRICED_NOT_ACTIONABLE. Current price, security mapping, corporate-action continuity, first-public timing, expected return and outcome remain null. Qualified trades=0. Nothing changes the protected paper book, collector workflow, source rights or readiness.

## Reproduce

From repository root:

```
python backend/research_priority.py
python -m unittest discover -s backend -p test_research_priority.py -v
```

`--write` creates only `web/trade-ideas/v1/` outputs and rejects differing existing files. Snapshot filename is its SHA-256. `latest.json` pins snapshot and versioned rubric byte lengths/hashes; consumers must check both before rendering, validate invariants, and show source-specific clocks/limitations. Candidate decisions conserve all 905 source IDs; the source input pins bind full provenance without copying raw filing bodies, owners or private prices. Nothing is fetched.
