# Full retained reporting-manager filing directory

This expands the earlier five-manager diagnostic without replacing it. The directory covers every **10,807 reporting-manager CIKs and 11,852 submissions** in the retained June–August 2026 Form 13F filing batch. It is not a current-manager universe, complete manager history, held-company mapping, portfolio reconstruction or trading signal.

## Actual source → directory path

The exact previously audited archive and SQLite are pinned, checked before and after a read-only database query and `quick_check`. Existing strict submission/cover/summary joins, dates and category validation are reused for every manager. The default diagnostic and exact-manager CLI behavior remain unchanged. The new explicit all-manager projection retains every submission, including notices, amendments and the known form/cover amendment disagreement, without reconciliation.

- Archive SHA256: `4db97d5652e262de51617971104e06313211de4d092e6bcb5d7bf34ee7efe054`
- SQLite SHA256: `5117bb2573288481d336dde11232ffb8bc64cb04a495f0fc179a64bf0e2aafda`
- Source: https://www.sec.gov/files/datastandardsinnovation/data/form-13f-data-sets/01jun2026-31aug2026_form13f.zip
- Actual exact HTTP/retrieval and first-public clocks remain unknown. File/report dates are source-reported, not observation or decision times.
- Pins establish the selected input bytes, not independently authenticated source origin. Prior full-field archive-to-database audit establishes retained-byte correspondence.

## Bounded public delivery

`web/holdings/manager-directory-v1/index.json` is 210,090 bytes. Its sorted `entries` arrays use explicitly named columns: padded manager CIK, submission count, distinct as-filed report-period count. There are 230 managers with more than one report period. These are not counts of economic positions or trades.

Sixteen `shard-[0-9a-f].json` files contain all selected filing metadata, partitioned by numeric CIK modulo 16. Each is 568,049–676,611 bytes; combined shard size is 9,693,016 bytes. The directory records each exact shard path, SHA256, byte count, manager count and filing count. A UI can fetch the directory once, then only a requested manager's shard. No millions of position records are loaded or published. Generator caps are 1 MB directory and 2 MB per shard, 20,000 source submissions, 100 filings per manager; excess fails closed.

Per-manager records preserve all source-reported periods and every filing, with accession, distinct filing/report dates, form/report type, amendment flags/type/number, source-row lineage and confidentiality flags. Blank remains blank and a missing summary remains null, not false or no positions. Shared interpretation is at directory level. No manager names, addresses, signatures, personal contacts, CUSIPs, securities, quantities, prices, holding values or underlying positions are included.

## Lookup and consumer contract

`manager_filing_directory.search(directory, query, exact=True, limit=20, offset=0)` operates on the generated, verified directory, with 1–10 ASCII nonzero CIK digits, exact normalization, or explicit literal prefix of the **unpadded numeric CIK**. Leading zero padding is ignored in both modes. Limits are 1–100 and offsets 0–20,000. No name/ticker search, fuzzy expansion, company or security resolution occurs. Missing CIK means no matching submission in this retained batch, not no manager or holdings. Empty pagination does not erase the pre-pagination match count.

The helper is not an untrusted JSON loader. Before browser lookup, pin the index version/hash/size; validate schema, unique sorted CIKs, directory/shard count coverage and fixed shard paths. Fetch only the derived fixed shard, check its listed size/hash, bucket and exact manager membership, then display inert text. Never trust a supplied URL or connect manager CIK to the company research queue. SEC links are constructed accession lookups, not fetched/verified original filings. User-facing search requires a separately tested UI integration; this release alone does not change the existing UI.

## Reproduce without source requests

```sh
python3 backend/manager_filing_directory.py \
 --database PRIVATE_HOLDINGS_SQLITE \
 --database-sha 5117bb2573288481d336dde11232ffb8bc64cb04a495f0fc179a64bf0e2aafda \
 --archive PRIVATE_RETAINED_13F_ZIP \
 --archive-sha 4db97d5652e262de51617971104e06313211de4d092e6bcb5d7bf34ee7efe054 \
 --output NEW_PRIVATE_OUTPUT_DIRECTORY
```

The output must not exist. `INCOMPLETE` remains on write/verification failure; each file is reopened and byte-compared, then `COMPLETE.json` records all hashes/lengths before the incomplete marker is removed. Private output directory/files use 0700/0600. Public release copies only index and shards, not the private completion marker or raw archive/database. Deterministic output has no invented current-data clock. Source gaps, confidentiality and amendments prevent completeness claims. Training and execution remain disabled; held reports and paper ledger are unchanged.
