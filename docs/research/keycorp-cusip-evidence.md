# A retained issuer disclosure provides one CUSIP review lead

This is retrospective evidence, **not a historical security master**. The retained KeyCorp 8-K (0001628280-26-073875), EX-99.1, dated November 13, 2026 explicitly associates CUSIP 493267702 with depositary shares representing 1/40th of Series E fixed-to-floating perpetual non-cumulative preferred stock. Its sole FILER is KeyCorp /NEW/, CIK 0000091576. Exact original-byte spans and hashes bind the annotation.

The same CUSIP string occurs in four retained FTD records (October 16, 19, 21 and 26) and two retained 13F records for June 30 holdings, filed in August. These are exact identifier correspondences, not ticker/name matches. The two 13F class labels are `PUBLIC` and `Common Stock`; neither is silently corrected. The later issuer description supplies a concrete class-review question, not proof of historical validity or authority to convert holdings classes. Manager CIKs are not issuer CIKs.

The November notice describes an intention to redeem on December 15. It does not prove completed redemption, present trading status or a corporate-action adjustment. Source bytes were observed November 14 at 23:33:35.714449 UTC, later than every matched FTD/holdings date. First-public time and historical effective interval remain unknown. No backdated knowledge, training admission or execution is enabled.

## Why not use the free SEC 13F security list as a master?

The [official list page](https://www.sec.gov/rules-regulations/staff-guidance/official-list-section-13f-securities) supplies quarterly CUSIP/name/class data, but no CIK. The [2026 Q2 PDF cover](https://www.sec.gov/files/investment/13flist2026q2.pdf), inspected November 18, explicitly restricts redistribution without CGS permission. Its user sheet describes June 30 quarter-end reporting applicability, not a complete effective-dated security history. No list was ingested into or redistributed by this feature. A public download is not a blanket reuse license.

The smallest remaining blocker for a historical company join is a permitted issuer/class/CUSIP assertion applicable to the earlier observation date, including relevant changes. This one later disclosure does not fill that gap. Retained OpenFIGI snapshots also do not establish issuer CIK or historical effective intervals.

## Reproduce

From the repository root, with previously retained private inputs:

```sh
python3 backend/cusip_issuer_evidence.py \
  --archive /private/CatalystRadar-SEC-originals-2026-11-14.zip \
  --ftd /private/prepared.sqlite \
  --holdings /private/holdings.sqlite \
  --out /private/new-keycorp-cusip-evidence
```

Exact ZIP, member, manifest and both database SHA256s are fixed in code. Read-only exact-CUSIP queries preserve raw filed labels/date strings and row hashes; source and database pins are checked before and after. Prior source ingestion audits established raw ZIP-to-database equality. The new output must be outside this checkout under a trusted private parent. `INCOMPLETE` persists on failure; completed output has hashes and private file permissions. This is overwrite refusal, not immutable storage.

Public projection: `web/company-findings/keycorp-cusip-evidence.json`. Only source identity/class metadata, dates, selected row references and hashes are published. No holdings value/quantity, FTD balance/price, addresses, contacts or complete narrative. Constructed original/exhibit links are not newly fetched. Prior source datasets, filing labels, UI and held reports/ledger remain unchanged. Browser integration is separate.
