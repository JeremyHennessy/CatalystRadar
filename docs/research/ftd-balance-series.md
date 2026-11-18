# Retained FTD settlement-balance diagnostic

This is a source-reported security-identifier view, not an issuer or short-interest dataset. It uses the already retained October 2026 second-half SEC file. No new dataset request or account is needed.

## Interpretation

[SEC guidance](https://www.sec.gov/data/foiadocsfailsdatahtm), checked November 18, explains that these are net outstanding fails-to-deliver balances for each settlement date, not daily new fails. Zero balances after September 2008 have no row. Missing cells therefore preserve source-row absence and null rather than inventing explicit reported zeros. Balances must not be summed across dates; they do not establish fail age, the same participants, short interest or abusive activity. The previous-day price field is not published or used here.

## Fixed diagnostic selection

The five lexicographically smallest CUSIPs in the entire retained file are selected before projecting their date series: `00032Q104`, `000360206`, `000375204`, `00039J103`, `00039J202`. This is a deterministic diagnostic after batch coverage inspection, not a preregistered, unbiased or ranked sample.

There are 63,157 source records, 13,097 source CUSIPs and 12 settlement dates, October 15–30, 2026. All 12 source dates are shown for each selected CUSIP. The five series have respectively 1, 2, 3, 4 and 12 reported observations: **22 source rows and 38 no-row cells**. These counts are not quantities of failed shares. The descriptions include ADS and ETF labels; no independent common-stock or current-security classification is asserted.

Every present cell retains its exact integer quantity as source text, source-specific symbol/description, SQLite row ID, source line number and canonical full-six-field SHA256. Labels may differ across dates and are never used to merge identities. Missing cells have no synthetic source identity or price. CUSIP-to-issuer, current ticker, corporate-action continuity, participants, market prices, returns, prediction and trading eligibility remain unverified or disabled.

## Source integrity and reproducibility

- Retained ZIP: `d54748d8ecba8c56c3caf41e8d0cd9cc1886275dff7a9dbd9b1c4da87cf56178`, 1,435,614 bytes.
- Shared prepared SQLite: `360491837fa5a8fd45d9d7c3b6b06a19324954bc839e203f2ad6235e88b14cae`.
- [Exact source URL](https://www.sec.gov/files/data/fails-deliver-data/cnsfails202610b.zip).

The generator bounds the ZIP and member, verifies both source pins before and after read-only processing, reuses the strict FTD header/date/duplicate/trailer parser, checks SQLite schema and integrity, and compares **every field of every one of the 63,157 persisted rows** to the archive. Trailer quantity is used solely for source-integrity checking, never as an analytical total. Exact retrieval/first-public timestamps remain null. A currently accessible guidance page does not establish historical data availability.

```sh
python3 backend/ftd_balance_series.py \
 --archive PRIVATE_RETAINED_FTD_ZIP \
 --database PRIVATE_PREPARED_SQLITE \
 --out NEW_PRIVATE_OUTPUT_DIRECTORY
```

The output must be new and outside the checkout. Failure leaves `INCOMPLETE`; successful output records its final hash. Public `web/settlement/ftd-balance-sample.json` contains only this bounded projection, no price field or raw archive. UI integration is separate: display null as no source row, distinguish as-reported labels from verified identity, and never render a cross-date balance sum or a zero-filled/continuous trend across absent rows. Existing reports, portfolio and execution gates are unchanged.
