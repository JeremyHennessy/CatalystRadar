# Current Nasdaq listing-reference evidence

Research only. This package adds a bounded offline importer of one official Nasdaq Listed directory snapshot, not prices, a historical security master or trading authorization. It does not change the dashboard, collectors, held reports or paper ledger.

## Observed source

One ordinary HTTPS request on 2026-11-17 at 23:16:25.922454–23:16:29.974476 UTC returned HTTP 200 and 348,446 bytes. Source SHA-256: `6ed3bcc1a80a6c4bccfe12faaaa6594ad1cb48ba6fdf99cca846edcf26ad7624`.

- [Official symbol lookup and dataset-specific rights](https://nasdaqtrader.com/Trader.aspx?id=symbollookup)
- [Official directory schema](https://www.nasdaqtrader.com/Trader.aspx?id=SymbolDirDefs)
- [Exact Nasdaq Listed download](https://nasdaqtrader.com/dynamic/SymDir/nasdaqlisted.txt)

The lookup page's download selector and its inline handler map Nasdaq Listed to this file. Its dataset-specific Events Data notice includes Nasdaq Listed and permits unrestricted use without further licensing requirements, overriding general Nasdaq terms for the named data. This is not a grant covering Fund Network, other-listed files, prices, paid Daily List, or every Nasdaq dataset. Rights checked November 17, 2026; no subscription, key or account created.

The footer declares `1117202618:01`. Reviewed documentation does not specify its timezone. We retain the literal, leave timezone/UTC null and do not invent a precise freshness interval or historical first-public timestamp.

## Retained coverage

5,609 rows have distinct source symbols. All raw fields and original line numbers are preserved privately:

- 5,601 non-test and 8 test issues.
- 1,286 ETF-flagged and 4,323 non-ETF rows. Non-ETF does not prove common equity.
- Market categories: 2,498 G, 1,443 Q and 1,668 S.
- Financial-status codes: 5,259 N, 330 D, 13 E and 7 H. These describe listing-compliance status, not halts or executable liquidity.
- Source round lots: 5,504 at 100, 98 at 40 and 7 at 10.
- All NextShares flags N. This flag is retained as supplied, without inferring broader product eligibility.

Four of the ten pinned project watchlist symbols occur: CINF, GT, TXMD and XRX. This is exact symbol correspondence only. The source has no CIK or FIGI field, so issuer/security identity is not independently established. The other six are merely absent from this Nasdaq-only file; they are not labeled delisted or untradeable.

The dotted symbol `ZXYZ.A` is explicitly a test issue. Names with trailing spaces are retained without rewriting. Neither test records nor differing instrument classes are silently discarded.

## Reproduction and safeguards

`backend/nasdaq_listed_evidence.py` accepts retained source, receipt and watchlist paths plus their SHA-256 hashes. It makes no network requests. Each parsed input is bound to the exact bytes hashed, with strict duplicate-free JSON receipts/watchlists. Source maximum 2 MB, maximum 20,000 data rows, exact eight-column schema and footer, unique symbols, supported codes and positive round-lot strings are enforced. Unsupported symbols or future-impossible source dates fail closed rather than becoming partial successes.

The source clock remains timezone-unknown. A footer date more than one day after the UTC observation date is rejected as impossible under civil timezone offsets; this sanity bound does not authenticate the source clock or prove timeliness.

The existing private completion protocol writes INCOMPLETE first, then evidence and summary, then hashes in COMPLETE. The output directory must be a new location outside this checkout under a trusted private parent; this is not immutable storage or protection against another checkout's publication. The public JSON contains counts and ten watchlist comparisons only, not the full directory or private paths. Private `candidate-pairs.json` is the shared evidence-container filename, not a claim that these records are financial pairs.

Synthetic tests cover malformed headers/footers, unknown codes, duplicates, bounds, clocks, hash/receipt mismatches, nonstandard JSON constants and missing watchlist matches. The first local attempt rejected legitimate trailing spaces in names and remains INCOMPLETE. The corrected authoritative v2 preserves those bytes; no source request was repeated.

## What this enables and what it does not

The retained snapshot provides a source-bound current Nasdaq universe with explicit test/instrument/compliance flags for later research screening. It cannot backfill historical constituent membership, ticker changes, corporate actions, CIK links, consolidated prices, halt status or outcome labels. No qualified training examples, predictions, returns or trades are created. Execution and training admission remain false.
