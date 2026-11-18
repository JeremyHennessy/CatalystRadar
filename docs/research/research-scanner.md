# Retained-evidence Research Scanner

This is one searchable navigation and inspection contract over **905 already released evidence records associated with 117 distinct issuer CIKs**. It is not a new market scan, complete company coverage, event deduplication, opportunity ranking or admission to training/trading. It does not collect data.

## Included scope

- All 605 financial contexts, 282 insider filing references (279 financial-cohort + 3 Emerson), five disclosure filing references, and two reported findings from the existing fixed 108-company dossier snapshot.
- Six later explicitly selected source-reviewed findings: VitaSpring revenue and net loss, KeyCorp later security-class annotation, Xerox dual-filer identity and reported exchange, and H&R Block votes/conditional authorization.
- All five separately policy-selected prepared-revenue candidates. They remain outside the 108-company dossier cohort.

That yields **897 original-review-required evidence units and eight narrowly source-reviewed findings**. This distinction is not a quality score or investment recommendation. A CIK may have both kinds. The 117-CIK union is not 117 fully screened companies and not the broader issuer directory. Xerox evidence has two separate registrant associations on one evidence unit; neither entity is merged, nor is every obligation attributed to both. Existing queue, source records, dossiers, held reports and paper ledger are unchanged.

The disclosure subset is five of the existing 466-file catalog; insider records are only referenced queue filings, not the full archives. No result means no result in this included set, not no corporate activity. The scanner does not create empty issuer profiles or convert unassessed coverage to zero.

## User-facing workflow

Search exact CIK or literal source-reported company labels; filter the explicit category/evidence state; inspect the bounded source-record detail; follow an existing investigation or original source link inside that record. Names are as reported, not current identity validation. Source CIK is not security mapping. Default ordering is CIK/category/ID, never predicted return or urgency. Consumers may foreground the eight source-reviewed records while keeping the complete set available with clear counts.

`investigation_path` is **existing page or section navigation**, not a promise that the precise record is automatically selected. In particular, most of the 282 insider references are not in the separate 27-filing watchlist page. Their unchanged source objects are inspectable in scanner details, and in the exact-CIK dossier where applicable. KeyCorp navigation opens the FTD directory, where source CUSIP 493267702 must be selected. Disclosure routes use the existing `#filing-ACCESSION` convention. The new five revenue candidates are in their separately labeled section.

## Source, status and timing integrity

`PINS` freezes every input path, byte count and SHA-256. The existing v3 queue is independently rebuilt by its existing validator before projection. References must resolve to the exact source CIK, with duplicate source IDs/references rejected. No ticker/name join is used. Each result binds one source key + JSON pointer + canonical source-object SHA-256. The hash serialization is ASCII `json.dumps(sort_keys=True,separators=(',',':'))` plus newline, not original source bytes. Source artifact hashes bind those original published bytes.

Clock values are literal source strings, except `source_exact_period`, whose value is exactly an object with `start` and `end` source-date strings. Byte spans/hashes are provenance, never clock values. Dates are labeled per source. Coarse prepared financial dates are not exact accounting periods; filing date is not announcement or transaction date. Source observation is not first-public time; local verification is not download time. First-public remains null. No generic timeline silently combines the different clocks.

Original-reviewed is narrow documentary extraction review, not accounting truth, full comparability, current catalyst, independent settlement or security identity. VitaSpring retains undefined zero-base growth and both net losses. KeyCorp's November description is not June/October mapping or completed redemption. Xerox obligor/issuer/guarantor roles stay separate. H&R Block conditional authorization is not issued shares, capacity or dilution. New revenue candidates retain no change calculation and missing exact original contexts.

## Bounded delivery and consumer contract

The compact index `web/research-scanner/v1/index.json` contains search summaries, explicit unknowns and next action, source references and 64 detail-shard pins. It is about 1.45 MB. All 905 unchanged public source objects are distributed into 64 shards by `sha256(record_id)[0] % 64`, sorted by ID. The measured maximum shard is about 46 KB; the whole package is about 3.11 MB. Hard limits: 1.6 MB index, 300 KB per detail shard, 8 MB package. This avoids loading all family source files or thousands of full records to inspect one result.

Consumers must:

1. Pin exact index bytes/SHA and validate schema, counts, unique IDs, categories/states, CIK associations, allowed paths and flags before using search fields.
2. Validate all directory shard memberships once: every index ID appears exactly once in its stated bucket, with no duplicates, omissions or extra IDs.
3. Fetch only a selected detail shard; verify exact bytes/SHA, schema/bucket and full ordered ID membership.
4. For **every** record in that shard, verify its source reference against the index, canonical source-object hash and identity. Do not render a partially validated shard.
5. Render all strings inertly with text nodes, never HTML. Validate external source URLs against their specific official-source contract; this package does not newly fetch or authenticate target URLs. Keep unknowns/status/clocks alongside any source facts.
6. Fail closed on mismatch; preserve existing app features. No fallback to a different version, broad query or inferred identity.

## Reproduce without provider requests

```sh
python3 backend/research_scanner.py --root . > /tmp/scanner-index.json
python3 -m unittest discover -s backend -p test_research_scanner.py
```

The CLI builds entirely before emitting stdout, so source-validation failures emit no successful-looking JSON. It writes no files itself. For the complete static package, call `build_package(root)`; it returns the index object and a fixed-path mapping of all 65 encoded payloads. Write them only after successful complete construction. The generator reads public local artifacts only, not private databases or provider endpoints. It does not modify source data, workflows, schedules, collection gates, prices, orders or the paper book.
