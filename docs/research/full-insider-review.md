# Full retained insider filing review

A research workflow over every reported P/S nonderivative transaction row in the retained 2026 Q2 and Q3 SEC filing batches. It is not a trading signal, recent-activity alert, complete company history, owner-level analysis or economic trade count.

## Actual scope

| Batch | Reported P/S rows | Filing accessions | Issuer CIKs |
|---|---:|---:|---:|
| 2026 Q2 | 32,927 | 13,866 | 2,975 |
| 2026 Q3 | 30,625 | 12,961 | 2,847 |
| Combined | 63,552 | 26,827 | 3,809 distinct |

54,502 rows have footnote references, 147 have reported P/S versus acquisition/disposition contradictions, and 833 appear in amended filings. These diagnostics overlap. No selected filing is quarantined in these retained inputs. Each selected filing has at most 30 selected rows. This does not prove correctness or completeness of original reporting.

P/S means open-market **or private** purchase/sale. The filing and transaction dates are date-only values, not first-public times or executable prices. Amendments remain separate and unreconciled. Submission-level plan flags do not identify every row's plan status. No flow, intent, compliance conclusion, forecast, ranking or investment recommendation is produced.

## Navigation and bounded output

`web/insider-full/v1/index.json` supports exact CIK and literal as-filed issuer/ticker search. Labels retain all reported variants and are not security-master mappings. No match means no selected records in this bounded retained scope, not no insider activity.

The index has 256 detail-shard pins with exact paths, byte lengths, hashes and issuer membership. The selected issuer's shard supplies filing cards, P/S row counts, original dates and reason-coded diagnostics. Cards link to a constructed SEC accession search, **not a fetched/verified original filing**. The original review, amendment reconciliation, first-public clock and qualification flags remain unknown/false. Consumers must render strings inertly, keep limitations visible, verify the whole selected shard before display and never silently load an alternate version.

Hard limits are 3 MB index, 1 MB per detail shard and 64 MB package. The observed package is about 31.18 MB; the largest shard is 389,156 bytes. A consumer need not download the whole package to inspect an issuer. Search/filtering is evidence review, not bullish/bearish ranking.

## Source integrity and quarantine

The offline builder runs the existing source audit on hash-pinned retained databases and source ZIPs before projection; it rechecks both hashes afterwards. This preserves the existing independently validated import boundary. It is not a fresh provider retrieval or a claim that a database hash alone validates source accounting truth.

Every P/S row belongs to one filing. Existing `insider_review_cards.project` validates identity, submission correspondence, dates, forms and labels. A projection validation failure quarantines the **whole filing**, preserving selected-row count and source-reference-bundle hash without echoing malformed content. Quarantine is explicit in the index and not silently excluded from selected totals. Structural source corruption, ambiguous transaction identity or source hash mismatch aborts the build; it never becomes a successful empty dataset. Missing transaction dates remain explicit on otherwise valid filing cards. The existing source audit flags the missing date; it is not repaired.

All selected rows reconcile to admitted review rows plus quarantined rows. Cross-batch accession overlap and duplicated selected identities fail closed. Public cards use a fixed allowlist: issuer/filing labels, source date fields, reported code counts, diagnostic counts, source row bindings and explicit unknowns. No owners, addresses, quantities, prices, transaction values, footnote text or secret contacts are emitted. Filing source hashes bind full private rows without publishing them.

The transaction bundle hash is SHA256 of sorted `{rowid, sha256, transaction_key}` references serialized with sorted keys, compact separators, ASCII escaping and one trailing newline. The underlying full parsed TSV row hashes use sorted-key compact JSON with UTF-8 encoding, ensure_ascii=False and no trailing newline. Neither serialization is an original TSV byte-span hash. Source ZIP and database hashes separately bind retained bytes. Exact retrieval clocks remain null rather than invented from file creation or this processing run.

## Reproduction

```
python3 backend/insider_full_review.py --config /trusted/private/two-batch-config.json --output /trusted/private/new-output
python3 -m unittest discover -s backend -p test_insider_full_review.py
```

Config names each batch, database, database SHA256, original archive and archive SHA256. The output must be new and outside the checkout. Processing completes before files are written, then `INCOMPLETE` marks persistence until every payload is reread and hashed. `COMPLETE.json` records all 257 payloads. Publish only reviewed public payloads, not config/private raw inputs.

No collector, quota, schedule, source receipt, frozen report, existing 27-filing watchlist, scanner, dossier, price data or paper account is modified. UI integration is separate.
