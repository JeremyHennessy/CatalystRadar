# Observed OpenFIGI watchlist candidates

One keyless public mapping request on November 17, 2026 returned one US-equity candidate for each of the ten configured research tickers: COHR, HRB, CINF, TXMD, RVTY, EMR, GT, KEY, WOR and XRX. The exact response was 2,704 bytes, HTTP 200. All 30 identifier fields (FIGI, composite FIGI and share-class FIGI) passed structural/check-digit checks. These are ten observed candidate mappings, not ten verified historical security links or training examples.

## Scope and rights

[Official API documentation](https://www.openfigi.com/api/documentation) permits unauthenticated mapping with up to ten jobs per request and 25 requests per minute. One request was made, without credentials, redirects or retries; the returned rate-limit header indicated 24 requests remaining. This uses no Alpha Vantage quota. The request explicitly included unlisted equities, so no match proves an actively traded listing. Only the existing ten research tickers were queried; the benchmark SPY and the wider market were not queried.

[OpenFIGI terms](https://www.openfigi.com/docs/terms-of-service) dedicate FIGI identifiers to the public domain and allow their reuse. [The FAQ](https://www.openfigi.com/about/faq) explains identifier checksums and limits returning proprietary third-party identifiers. Public output is limited to our query tickers, FIGI identifiers, request scope, status, hashes and local clocks. Provider issuer names and other descriptive response metadata are retained privately rather than treating the identifier grant as unlimited rights to every response field. No endorsement, accuracy guarantee or third-party identifier license is implied. These official pages were reviewed November 17, 2026.

## Validation and boundaries

`backend/openfigi_evidence.py` is offline only. It reads bounded request, response and receipt bytes once under supplied SHA256 pins, rejects duplicate JSON fields/nonstandard constants, validates scope and order alignment, and checks all identifier fields. All candidates remain retained when a job is ambiguous. Provider errors/warnings and absent mappings remain distinct states, not a guessed match. Mismatched tickers, exchanges, sectors, duplicate identifiers, unsupported schemas and invalid checksums fail closed. Cross-query shared identifiers are counted rather than silently treated as independent securities.

A US composite, a venue FIGI and a share-class FIGI have different scopes. This query does not establish historical ticker ownership, effective dates, issuer CIK, corporate actions or active listing status. Names were not used to manufacture a CIK link. The recorded observation interval is a current collection clock, not a historical effective/publication timestamp. None of these mappings enables execution or admits price/event training examples.

## Reproduction

Run the CLI with request, response and receipt paths and their expected hashes plus a new output directory under a trusted private parent outside this checkout. The shared INCOMPLETE/COMPLETE hash protocol retains raw evidence privately; only the dated allowlisted mapping summary is public. Overwrite refusal is not immutable storage, and the path guard only excludes this checkout. The raw collector is a separately retained one-off artifact, not a new schedule or active integration.

`python3 -m unittest discover -s backend -q` runs synthetic identifier/checksum, ambiguity, malformed response, clock, bounds and pinned-input tests. Synthetic examples use documented identifiers and do not claim actual requests or financial outcomes. No approved UI, held reports, ledger or existing collectors change.
