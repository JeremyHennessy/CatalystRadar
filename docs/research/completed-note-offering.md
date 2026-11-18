# Completed-note offering research extraction

Policy: run one bounded, explicit completed-note narrative grammar over **all ten** manifest-pinned retained 8-K originals, accession ascending. No selection by issuer, return, ticker coverage or favorable outcome; all unsupported cases remain visible. The initial source investigation examined the first three accession-sorted originals, not a claimed prospective sample. Grammar development is retrospective and not a general financial-language model.

## Original-source result

One of ten matches: Emerson Electric, CIK0000032604, accession0001140361-26-043782. The primary8-K reports completion on November13,2026 of previously announced €750,000,000 aggregate-principal4.000%notes due2032. It explicitly references pricing announced in an8-K filed November12. Nine originals have no supported paragraph and remain abstentions; this does not imply absence of financing.

The extraction preserves exact primary paragraph byte span/hash and original hash, reported dates and amounts. It labels debt, previously announced status and issuer-reported completion. Coupon is not yield; aggregate principal is not net proceeds, equity issuance, current debt balance or confirmed settlement. Full maturity date is unknown in this narrow paragraph; do not infer January1 or December31 from the year. No return/price/trade interpretation is generated.

[Original SEC filing](https://www.sec.gov/Archives/edgar/data/32604/000114036126043782/0001140361-26-043782.txt)

## Reproduction and limits

```
python3 backend/completed_note_offering.py RETAINED_ORIGINALS.zip NEW_OUTPUT.json
```

Archive/manifest/all original hashes and byte limits are checked before extraction; original header issuer/accession identity checked. No requests, credentials, quotas, collectors or paper controls. Amendments abstain; multiple matches are ambiguous and no facts admitted. Whole paragraph match rejects prefixed negation. Comment/script/style contexts excluded. Only explicit euro-denominated notes with this grammar are supported; unsupported currency, structure or dates require separate review.

Raw originals remain local; output includes only bounded fact metadata and evidence references, not raw document text or contacts. Existing SEC public-filing reuse policy applies to source facts, not third-party market-price rights. Original dates and observation time remain separate from unknown first-public time. The original is previously retained; source link was not refetched in this package.

Independent original-source review must precede public application projection. This extractor alone does not publish a new app view or promote comparability/outcome eligibility.

Invalid calendar dates in an otherwise matching paragraph reject the entire run with an error; they are not quietly omitted or treated as an empty valid dataset. Invalid source archive pin/oversize likewise fail before ZIP parsing. These fail-closed cases have regression coverage.

## Public company projection

`company_note_projection.py` rebuilds the archive audit and checks the exact independently reviewed canonical audit hash before projecting `web/company-findings/emerson-note-offering.json`. The public file contains one reviewed issuer-reported finding, original SEC provenance, nine accession/status abstentions, unknown proceeds/dilution/full maturity/first-public fields and disabled training/execution state. It contains no raw paragraphs, contacts or price data. A changed source/audit requires independent review, not silent projection. Display integration is separate from this projection.
