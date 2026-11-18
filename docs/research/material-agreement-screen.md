# Material-agreement source review across ten retained packages

The fixed rule checks the exact filed header label `Entry into a Material Definitive Agreement` in **all ten retained original packages**. It finds one declared Item 1.01 (Xerox) and nine packages without that header declaration. Absence is not evidence of no contract or event. Each package retains original identity, observation clock and primary/exhibit byte hashes. EX-4.n and EX-10.n documents are inventoried as review evidence, not automatically classified as new or effective instruments.

This is a retrospective, limited cohort, not a representative or prospective discovery test. The generic screen is reusable but does not infer legal obligations. Only the exact independently inspected Xerox source receives structured exchange terms.

## What the original says

The [Xerox original 8-K](https://www.sec.gov/Archives/edgar/data/108772/000119312526460692/0001193125-26-460692.txt), primary `d134827d8k.htm`, reports completion on November 13, 2026 of **previously announced** exchanges under an October 29 support agreement. The separate Exchange Agreement is dated November 13. These are not interchangeable dates or a newly discovered announcement.

- **Xerox Holdings Corporation, CIK 0001770450:** $173,679,000 principal of its 5.500% notes due 2028 was exchanged; it issued 3,872,062 common shares as one exchange component.
- **Xerox Corporation, CIK 0000108772:** newly issued $121,086,000 principal of 10.250% secured first-lien notes due 2030. The exhibit table names Holdings as parent guarantor.

The exact paragraph, equity-issuance paragraph and two exhibit-table rows are byte-span/hash bound. No obligations are propagated between registrants. The dollar unit is reported, ISO currency remains unknown. The $1 par value is deliberately not used as a share price or equity value. Subtracting the two principal amounts would not establish total net-debt change, transaction value or economic gain; none is calculated.

Completion is **issuer reported**, not independent settlement verification. The retained observation is November 14 at 23:33:43.933078 UTC; first-public time and historical availability are not authenticated. No security mapping, price adjustment, forecast, return, trading or training admission follows.

## Preservation and reproduction

Public artifact: `web/company-findings/material-agreements.json`. It contains metadata, typed terms and source-span hashes, not complete narrative, addresses, contacts or signatures. Other packages keep scoped negative/unknown states. Existing reports, ledger, old dividend API/tests and other findings remain untouched. This is a distinct new module, not a replacement for prior extractors.

```sh
python3 backend/material_agreement_screen.py \
  --archive /private/CatalystRadar-SEC-originals-2026-11-14.zip \
  --out /private/new-material-agreement-screen
python3 -m unittest discover -s backend -p test_material_agreement_screen.py
```

ZIP, manifest and individual original bytes are pinned. The builder checks every receipt's accession, URL, CIK among explicit filers, size, hash and clock, then rechecks the ZIP. Screen bounds enforce a unique primary, balanced/non-nested DOCUMENT inventory, safe filenames, exact header classification and separate amendment status. New private output must be outside the checkout under a trusted parent; 0700/0600 with INCOMPLETE until all output hashes complete. This is overwrite refusal, not immutable storage. No provider requests are made. UI integration is separate.
