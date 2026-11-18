# Full retained FTD CUSIP directory

This extends the existing five-CUSIP diagnostic without modifying that saved sample. It covers **all 13,097 source CUSIPs and 63,157 reported rows** in the retained October 2026 second-half SEC FTD file. It is not all historical or current securities, verified issuer identity, short interest or a trading signal.

## Source and coverage

The unchanged source-pinned audit verifies ZIP `d54748d8ecba8c56c3caf41e8d0cd9cc1886275dff7a9dbd9b1c4da87cf56178` and shared SQLite `360491837fa5a8fd45d9d7c3b6b06a19324954bc839e203f2ad6235e88b14cae` before and after read-only processing. Every field of every persisted FTD row is compared to the raw archive. Source header, duplicate/date validation, trailer integrity and database schema/quick-check remain required. No source requests or database writes are added.

The shared axis has the 12 dates actually present in the file, October 15–30, 2026. Sparse series contain only reported rows: **94,007** CUSIP/date combinations have no source row. This is a count of absent cells, not failed shares. Consumers must show an absent row distinctly from a reported zero. The [sample methodology](ftd-balance-series.md) explains the SEC zero-balance omission convention and why balances are not summed across dates or interpreted as new failures, age, resolution flows or misconduct.

## Bounded delivery

`web/settlement/ftd-directory-v1/index.json` is **766,353 bytes**. Its `entries` arrays have named columns: source CUSIP, reported observation count, distinct source symbols and distinct source descriptions. Different labels across dates are preserved, not reconciled. The directory contains no balances, prices or company CIKs.

Sixty-four hash-pinned shards each contain **291,130–469,309 bytes**, totaling **24,525,432 bytes**. A browser loads the directory and only the shard needed for a selected CUSIP, not every balance. Bucket assignment is the first SHA256 byte of ASCII CUSIP modulo 64, formatted as two lowercase hexadecimal digits. The only permitted shard filenames are `shard-00.json` through `shard-3f.json`.

Each source-reported observation preserves its exact quantity string, settlement date, symbol/description and canonical row/line evidence. No previous-day price, dollar conversion, cross-date balance total, issuer link or security-class inference is added. Context and limitations are shared at directory level. Retrieval and first-public clocks remain unknown. Settlement date is not knowledge time: SEC describes an approximately half-month-delayed release schedule, not a guaranteed publication timestamp. This 2026 file uses the post-2008 omission convention; the older reporting threshold is not applied. The original `ftd-balance-sample.json` bytes and default generator output remain unchanged.

## Search is filtering, not identity resolution

`ftd_balance_directory.search(index, query, field='cusip', limit=20, offset=0)` accepts an already verified generated directory, not arbitrary external JSON. Fields are explicit: exact source CUSIP, literal CUSIP prefix, or exact case-sensitive source symbol. It never automatically falls back between fields. Symbols may match multiple CUSIPs; all matches and their total remain visible before pagination. No preferred/current identity is chosen. A missing match is absent from this retained file, not a zero balance or proof of no security.

Queries are bounded printable ASCII; CUSIP queries have the source format, while symbol queries are literal strings, not regular expressions or executable text. Results are limited to 1–100, offsets to 0–20,000. Empty pages preserve the total match count.

Before use, browser code must pin/check directory hash, size, schema, complete CUSIP uniqueness/order, counts, fixed shard paths and source flags. Verify the selected shard's byte length/hash, bucket, unique CUSIP membership, all source-date/row counts and exact selected CUSIP before displaying inert text. Show the shared date axis with explicit no-row cells; do not zero-fill gaps or join them into a continuous trend. Separate UI review is required before claiming full lookup is live.

## Reproduce

```sh
python3 backend/ftd_balance_directory.py \
 --archive PRIVATE_RETAINED_FTD_ZIP \
 --database PRIVATE_PREPARED_SQLITE \
 --out NEW_PRIVATE_OUTPUT_DIRECTORY
```

The builder validates source inputs before producing output; the writer refuses an existing path or one inside the checkout. Output directory/files use 0700/0600. A write failure leaves `INCOMPLETE`; all persisted bytes are reread before completion hashes are written and the marker removed. Only index/shards are copied for public release. Caps are 3 MB for the directory, 1.5 MB per shard, 20,000 selected CUSIPs and the existing 100,000-source-row limit. No financial qualification, execution enablement, portfolio or frozen-report edits occur.
