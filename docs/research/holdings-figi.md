# Historical holdings and current identifier correspondence

This is a source-quality and exact-identifier correspondence audit, not verified historical security mapping, exposure reconstruction or a trading signal. No network requests were made for this study. The approved dashboard, held reports and disabled ledger are unchanged.

## Actual evidence

The independently ingested June–August 2026 SEC 13F filing batch has 3,830,274 holding rows. A census of its source `FIGI` field found:

- 3,382,495 blank rows.
- 446,353 rows with a structurally valid identifier/checksum, representing 21,214 distinct strings.
- 1,426 rows with invalid structure/checksum, representing 1,305 distinct strings. These are not repaired, inferred or silently removed from the coverage denominator.

Revalidating the retained November 17 keyless OpenFIGI observation and matching exact valid strings found **1,507 holding rows across 423 accessions and 19 identifiers**, covering all ten queried tickers. The match is against today's observed mapping, not proof that a ticker belonged to that security on the reported date.

561 rows match `figi` and `compositeFIGI` (the returned values coincide); 946 match `shareClassFIGI`. A row matching two fields is counted once in total. These scopes remain explicitly distinct. No identifiers are shared across separate queried tickers in this observation.

The matched source rows include 34 `Call`, 32 `Put`, and 1,441 blank option flags. Blank does not independently prove common-stock ownership. Report periods range from December 2022 through June 2026; 1,461 rows report June 30, 2026. There are 31 rows in amended filings, not 31 independent new purchases. No values, shares, option exposures or manager portfolios are added together. Reporting-manager CIKs are not held-issuer CIKs.

## Reproduction and privacy

`backend/holdings_figi_evidence.py` pins the retained ZIP and SQLite hashes, reopens the database read-only, checks database integrity and verifies both hashes again after the audit. It independently revalidates the original mapping request/response/receipt using `openfigi_evidence.py`. Those pins identify the inputs; the prior full-field SEC ingestion audit, rather than this utility, establishes ZIP-to-database derivation.

For each selected row, private evidence retains exact database rowid/full holding fields, submission record, selected amendment/confidentiality cover context and every corresponding query/scope. CUSIPs, names, holding values and manager identifiers remain private. Raw source values are not republished. Output uses the existing INCOMPLETE-first and COMPLETE-with-hashes protocol, owner-only permissions, and refuses overwrite. This is trusted local storage, not immutable or independently timestamped storage.

CLI arguments are `--database`, `--database-sha`, `--archive`, `--archive-sha`, `--request`, `--request-sha`, `--response`, `--response-sha`, `--receipt`, `--receipt-sha`, and `--output-directory` (a new private directory outside the checkout). The accompanying aggregate JSON pins all five inputs and records the mapping observation time. Historical disclosure/first-public clocks remain unverified.

The scan is bounded to five million holding rows and 50,000 exact matches. It rejects nontext identifiers, malformed selected accession identity, missing/ambiguous filing joins, conflicting report periods, and unsupported public date/category values. A source identifier passing checksum is not independently authenticated or verified as correctly assigned by the filer. Amendment conflicts are preserved and counted, never reconciled automatically. No ticker-name fallback exists.

## Sources and remaining qualification

- [SEC Form 13F datasets](https://www.sec.gov/data-research/sec-markets-data/form-13f-data-sets): original prepared filing evidence; as-filed and delayed, not current positions.
- [OpenFIGI API documentation](https://www.openfigi.com/api/documentation): current mapping scope and response semantics.
- [OpenFIGI identifier FAQ](https://www.openfigi.com/about/faq): identifier structure and checksum.
- [OpenFIGI terms](https://www.openfigi.com/docs/terms-of-service): FIGI identifier rights; no blanket rights claim for third-party identifiers or other provider metadata.

No CIK-to-held-security issuer link, historical ticker interval, comparative security identity, current ownership, action-corrected outcome or qualified training pair is established by this study. Execution remains disabled. The original archives and mapping evidence were already independently retained; no additional provider quota or paid service was used.
