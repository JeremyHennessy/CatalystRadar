# TJGC historical corporate-action review fixture

Offline, manually reviewed primary-source case for CIK `0001969928`. No feed,
production gate, ledger, price correction, execution or model admission changes.

## Evidence and separate claims

- [Nasdaq ECA2026-350](https://www.nasdaqtrader.com/TraderNews.aspx?id=ECA2026-350), May 21 announcement: a 1-for-3 reverse split of ordinary shares effective May 26, 2026, with post-split CUSIP G2588N116.
- [Issuer May 21 Form 6-K](https://www.sec.gov/Archives/edgar/data/1969928/000118518526002042/tjgcgroup6k051426.htm): the ticker remains TJGC; the announced nominal issued-share count falls from 30,300,000 to 10,100,000, with fractional entitlements rounded up. The filename is not the report date.
- [Issuer 20-F, Share Consolidation and Note 17](https://www.sec.gov/Archives/edgar/data/1969928/000118518526003078/tjgc20f033126.htm): later reports the May 26 effective action and final issued count of 10,100,023 after rounding. Its financial-statement share/per-share data are retrospectively restated for the consolidation. Do not apply the ratio again to those already-restated financial amounts. This financial presentation does not establish vendor-bar adjustment methodology.
- [Nasdaq June 3 announcement](https://ir.nasdaq.com/node/110496/pdf): reports the separate May 15 halt and schedules June 3 resumption. May 26 falls inside that historical interval. Neither an announced opening nor effective split date proves an actual trade or fill.
- [Issuer August 11 Form 6-K](https://www.sec.gov/Archives/edgar/data/1969928/000118518526003374/tjgc6k073126.htm): describes the distinct Class A/Class B ordinary-share redesignations to be reflected in the marketplace August 12; Class A retains ticker TJGC. This is not another 1-for-3 split and does not establish timeless share-class continuity.

## Guard semantics

`review_window` takes an exact ten-digit ASCII CIK and inclusive calendar dates.
An overlapping disclosed event date triggers an issuer-level review warning.
Same-day boundaries are deliberately included: no precise intraday mapping is
claimed. No match means unknown, never corporate-action-free or safe to trade.

The ratio is old/new share-count information, not a price-adjustment factor.
Same CIK or ticker is not proof that a particular vendor bar belongs to the same
security/class. CUSIP is retained as reported for this action, not as a permanent
mapping. No historical first-public or observation clock, byte archive/hash,
complete action coverage, actual resumption, prices or returns are established.

The existing `split_basis_evidence` utility is a different private SEC-notes
standard-tag audit. This fixture follows its issuer-warning-only semantics but
does not rewrite its corpus, counts, unverified mappings or admission decisions.
No production caller imports this fixture.

## Tests

`python3 -m unittest discover -s backend -p 'test_tjgc_corporate_action_fixture.py'`

Seven tests cover inclusive boundaries, separate redesignation, unknowns,
forbidden adjustment/admission implications, rounding versus nominal counts,
copy isolation and invalid identity/date inputs. No external requests are made.
