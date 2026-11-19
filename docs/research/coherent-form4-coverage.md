# Coherent: Form 4 metadata retained, Form 4 not scanned

The [November 19 receipt](../../data/sec-observations/20261119T114159492631Z.json)
(run `20261119T114159492631Z`) records complete metadata observations for ten
configured issuers, not complete filing discovery across forms. Its Coherent
CIK `0000820318` source receipt identifies the [retained issuer metadata](../../data/sec-snapshots/c0f3a419d2d23b0966097f86fc70ae90bdceeb911620a4674c07e60937591d52.json)
(SHA-256 `c0f3a419d2d23b0966097f86fc70ae90bdceeb911620a4674c07e60937591d52`).
The metadata retrieval completed at `2026-11-19T11:41:59.642713+00:00`.

| Accession and source | As filed role | Reported transaction date | SEC acceptance (UTC) | Reported common shares × price |
| --- | --- | --- | --- | --- |
| [0000899140-26-001275](https://www.sec.gov/Archives/edgar/data/820318/000089914026001275/xslF345X06/form4.xml) | Enrico Digirolomo, director; officer not checked | 2026-11-10 | 2026-11-12 11:01:02 | 1,000 × US$222.885 = US$222,885 |
| [0000899140-26-001276](https://www.sec.gov/Archives/edgar/data/820318/000089914026001276/xslF345X06/form4.xml) | James Robert Anderson, CEO and director | 2026-11-09 | 2026-11-12 11:02:52 | 5,000 × US$199.48 = US$997,400 |

The filing date for both is November 12. The values are nominal arithmetic
from Table I of the two SEC-rendered forms, not market quotes, costs including
fees or aggregate exposure. Both mark an acquisition (A) and direct ownership
(D) on code P lines. The [SEC's Form 4 instructions](https://www.sec.gov/files/form4.pdf)
allow an open-market or private purchase for code P; the venue is unknown.
No coordinated intent or independent confirmation of later issuer repurchase
activity follows. A director not marked as an officer is not another
officer-reported transaction for an officer-only research definition.

Both accessions appear in the upstream metadata but are absent from the
scanner event list. They are outside the actual 96-hour window; separately,
the production scanner allows only 8-K and 8-K/A. The test replays the pinned
bytes with an earlier clock that puts both acceptances inside the window,
mocking the provider access completely, to isolate the form filter. The saved
8-K Item 7.01 concerns the board's later authorization, a distinct event
and actor. This review neither backdates discovery nor establishes a
first-public timestamp, signal, return, order or execution eligibility.

Run from repository root:
`PYTHONPATH=backend python -m unittest discover -s backend -p test_coherent_form4_coverage.py`.
