# Scheduled-session coverage of retained daily snapshots

This offline diagnostic tests date coverage, not tradability, market performance or permission to train. No new Alpha Vantage requests, credential access, workflow changes or price redistribution occur.

## Official calendar basis

Reviewed November 17, 2026:

- [Nasdaq U.S. holiday and trading hours](https://www.nasdaq.com/holiday-trading-hours)
- [NYSE holiday and trading hours](https://www.nyse.com/trade/hours-calendars)
- [NYSE's published 2026–2028 announcement](https://ir.theice.com/press/news-details/2025/NYSE-Group-Announces-2026-2027-and-2028-Holiday-and-Early-Closings-Calendar/)

The published 2026 full closures are January 1/19, February 16, April 3, May 25, June 19, July 3, September 7, November 26 and December 25. November 27 and December 24 are early-close **sessions**, not excluded dates. July 2 is not a scheduled early-close day in this calendar. This package records calendar facts with attribution, not a market-data licensing grant.

Only **2026** is supported. These are scheduled US equity dates, not an exhaustive record of unplanned exchange closures, security-specific halts, foreign calendars, options/late-session hours, settlement dates or the SEC filing calendar. The diagnostic does not establish each symbol's actual historical listing venue.

## Fixed-window result

The requested window was explicitly fixed to **June 26–November 16, 2026**, rather than inferred from each file's first and last available row. It contains 102 weekdays minus two scheduled closures (July 3 and September 7), yielding **100 scheduled sessions**.

All eleven already-retained compact daily snapshots contain exactly that date set: **1,100 retained date entries, zero missing scheduled dates and zero unexpected dates**. This verifies date-set coverage inside this specific window only. It does not supply additional price history or establish any coverage before June 26, after November 16 or within each day.

The eleven symbols are COHR, HRB, CINF, TXMD, RVTY, EMR, GT, KEY, WOR, XRX and SPY. Snapshot observations remain the original November 17 pre-close clocks, approximately 20:47–20:49 UTC, not the audit clock. No November 17 completed session is present or implied. The two scheduled early closes occur outside the observed window; their correct inclusion is tested synthetically, not verified with actual early-close bars.

## Source integrity and scope

`backend/price_session_audit.py` takes the private snapshot directory, previously retained audit-manifest hash, and independently specified start/end dates. The manifest pins each snapshot SHA-256 and decoded provider-response SHA-256. Exact symbol, observation, endpoint/function, compact output scope and prior quality metadata are checked. Duplicate JSON fields, nonstandard constants, altered bytes and unexpected/missing snapshot files fail closed. Each original OHLCV response is revalidated privately with the existing raw-schema validator; this is not independent verification of the provider's reported prices.

The only public artifact is an allowlisted diagnostic containing hashes, symbols, counts and dates. It contains no OHLCV values, raw response body, credentials or private file paths. The source snapshots were previously audited and compared to private repository blobs; this utility uses the retained bytes, not a fresh remote fetch. Audit completion UTC is separate from original snapshot observation UTC.

A successful comparison **does not** verify historical security identity, split/dividend adjustments, intraday completeness, consolidated volume, closing auction prices, executable liquidity, source correctness or outcome labels. It does not establish model-training or redistribution entitlement. It leaves the existing collector's `calendar_complete`, `eligible` and execution flags unchanged. Nothing is written back to source snapshots, the ledger, held reports, UI or workflows.

## Reproduction and tests

Run the offline CLI with `--directory`, `--manifest-path`, `--manifest-sha`, `--start 2026-06-26`, `--end 2026-11-16` and a new private `--output-directory`. Input files and response bodies are bounded; only the reviewed calendar year is accepted. The existing raw-price validator is reused without extending its fixed trial freshness assumptions.

The private output protocol uses INCOMPLETE until evidence and summary are written and COMPLETE hashes persist. The directory must be outside this checkout under a trusted private parent; this is not immutable storage or protection from other publication checkouts. The shared private evidence filename `candidate-pairs.json` contains dates and prior validation metadata, not newly qualified financial pairs.

Synthetic tests exercise first/last/interior missing sessions, weekend/holiday/out-of-window extras, early-close retention, duplicates, malformed dates, unsupported years, tampered snapshots, missing files and an end-to-end pinned fixture. Missing sessions are reported, never filled or silently dropped. This audit is a small, explicit coverage check, not a replacement for price, corporate-action, identity, rights or execution qualification.
