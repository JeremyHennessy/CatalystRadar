# Coherent saved repurchase-authorization case

## Exact saved observation

CIK `0000820318`, accession `0001193125-26-467737`, Item 7.01, form 8-K, as-filed ticker COHR. Receipt `data/sec-observations/20261119T114159492631Z.json` SHA-256 `10b3c74b4949b1d23d850a9c822f052343dac979fa1112f3723c37fda81100bc` includes this event and a separate Worthington event. Do not treat Coherent as the only event or merge them. `github_event_name=push`: this saved run is the request-triggered fallback, not proof of a scheduled collection success.

Coherent's retained metadata source is `data/sec-snapshots/c0f3a419d2d23b0966097f86fc70ae90bdceeb911620a4674c07e60937591d52.json`, SHA-256 equal to its basename, 159,944 bytes. SEC acceptance is `2026-11-19T11:30:06.000Z`; this observation is `2026-11-19T11:41:59.642713+00:00`. Their difference is exactly 713.642713 seconds, not an availability lag or first-public time. `first_public_utc=null`, eligible false, `METADATA_DISCOVERY_NOT_ELIGIBLE`, orders_created=0 and eligible_count=0 remain unchanged.

## Independently inspected primary source

[Issuer-hosted 8-K, Item 7.01](https://ir.coherent.com/node/18481/html) was successfully fetched November 19, 2026: HTTP 200, 29,296 bytes, SHA-256 `aef701901dc28af1cdd0b0b543e01a74fccd77fa45fa274be81090383798d983`. It embeds the exact accession in its filing download links and CIK in its XBRL. This hash describes the issuer HTML as fetched, not EDGAR bytes, earlier availability, a historical dissemination clock, or authenticated first-public time. The source was inspected locally; the raw issuer page is not added to the public repository. Tests bind this reviewed interpretation and saved metadata, not a fresh online fetch.

The board authorized up to US$2.0 billion of common-stock repurchases on November 18, excluding fees, commissions and other related expenses. The cap is neither spending nor a disclosed purchase amount. The program has no expiration date, does not require any particular share quantity, and may be suspended or discontinued. The filing does not disclose completed purchases; absence of that disclosure is not proof of zero purchases. This is not an executive transaction or strategic-investment finding. No unrelated transaction detail is imported.

## Boundaries and regression

No first-public, whole-document novelty, price effect, eligible catalyst, return or trade conclusion follows. No source event, receipt, collector settings, policy, frozen projection, price or paper state is changed. The collector page adds only a static expandable saved-case note; it cannot run a collector or fetch an original.

Run `python3 -m unittest discover -s backend -p 'test_coherent_saved_case.py'`, both existing collector JavaScript suites and `python3 backend/verify_public_state.py`. The focused test checks the exact receipt and metadata association, two-event membership, push trigger, clocks and exact interval, source links, authorization-versus-purchases wording, null/false states and unchanged existing control IDs. It is not independent historical source availability evidence.
