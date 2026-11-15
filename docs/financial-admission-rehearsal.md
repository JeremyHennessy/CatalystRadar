# Private-original financial admission rehearsal

Run `backend/financial_admission_rehearsal.py --reviews data/filing_reviews.json --archive-dir <authorized-originals-directory> --output <new-file>` offline. It validates the same ten archived original identities, hashes and request/retrieval clocks as the header-feature workflow before extracting. Originals are not published; the saved public report contains numeric reported values, hashes, timestamps and evidence offsets only. Public CI tests synthetic fixtures, not private original bytes.

The supported grammar is deliberately narrow: an explicit license-revenue current/prior quarter narrative, with stated units, reported increase and percentage. This is a layout grammar, not a claimed general earnings extractor or an issuer/accession whitelist. Other layouts remain unknown. Evidence binds the entire containing paragraph/table cell and original document bytes. Multiple matches remain ambiguous. Amendments require separate review and are not silently substituted.

Actual archived results: ten validated filings; one supported pair, TherapeuticsMD's third-quarter license revenue of **$1.3 million versus $784 thousand**, issuer-reported **60.6%** increase. These rounded operands do not justify independently reproducing that percentage; the program intentionally leaves calculated growth null. License revenue is not automatically total GAAP revenue, and continuing-operations/basic EPS is not silently substituted for total GAAP diluted EPS. The existing review also retains the exhibit-description second-quarter/body third-quarter discrepancy and milestone-revenue context.

The actual strict `EARNINGS_GROWTH` admission contract runs with no unsupported facts supplied. All four signal families remain UNKNOWN, with explicit missing operands; zero qualified signals or orders. This demonstrates the source-to-admission boundary, not a successful signal.

Grouping is strictly by filing identity and document evidence scope. Document offsets distinguish duplicate occurrences. No economic-event group is asserted across amendments or filings, and a document is not counted as an independent economic sample. The report preserves unsupported and invalid rows rather than discarding them.

Current analysis and retrieval clocks are not first-public receipts. The manually selected sample remains retrospective. No scanner, workflow, frozen strategy, prospective activation or private paid-provider collection changes. The next blocker is broader verified financial extraction and explicit economic-event linkage with a pre-observation protocol binding, not relaxing missing facts into zeros.

## Positive dividend declarations (bounded offline evidence)

The rehearsal also runs a narrow narrative grammar for a regular quarterly cash
dividend stated in cents per share, with explicit payment and record dates in a
single EX-99.1. It preserves the entire paragraph's exact byte span/hash. Hidden
HTML comments/scripts/styles, duplicate exhibits, malformed document inventories,
amendments and multiple matching declarations are not admitted as a unique fact.
This is not a general corporate-action feed or a complete parser of dividends.

The recovered CINF submission `0000020286-26-000064` provides one positive
reported declaration: 94 cents per share, payable January 15, 2027, to holders of
record December 23, 2026. These are separate dates. Neither is substituted for an
ex-dividend date. Currency ISO, share class, ex-date, security mapping, actual
payment and investor entitlement remain unverified. No hypothetical account is
credited, price adjusted or return label admitted from this evidence.

Source: https://www.sec.gov/Archives/edgar/data/20286/0000020286-26-000064.txt

The current artifact retains all ten reviewed cases; unmatched cases mean no
supported grammar, not no dividend. All action-coverage/total-return readiness
flags remain false. The private originals are rechecked only when this offline
rehearsal runs; public CI cannot independently reopen them. Computation records an
invocation/reproduction clock, not historical availability or a completion receipt.
This patch does not change the frozen mechanical comparison, scanner or schedules.
