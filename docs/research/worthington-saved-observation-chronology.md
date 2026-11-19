# Worthington saved-observation chronology control

## Fixed scope and evidence basis

This is a static, case-specific chronology check, not a new event classifier or an update to a frozen projection. It concerns only CIK `0000108516`, accession `0001193125-26-464853`, in saved receipt `data/sec-observations/20261118T192626511660Z.json` (6,637 bytes; SHA-256 `6ebebfb3fafa156857d5c2685352c3fb15332e564ce45f5f65bc7213df3a29d5`). It is not a claim that this remains the latest observation.

The receipt records SEC acceptance `2026-11-17T13:52:55.000Z` and collector observation `2026-11-18T19:26:42.681073+00:00`. Its event remains `METADATA_DISCOVERY_NOT_ELIGIBLE`, eligible false, first-public time null. Its metadata source SHA-256 is `f637d59d3599d816862602e2faa59aa522df269018af710389650ff5fa10502e`.

The source-content interpretation below is supplied by the coordinating primary-source review on November 19, 2026. This package performs no additional retrieval. No original-page HTTP bytes, status, retrieval timestamp or page hash is asserted by this package. The receipt hash certifies the saved receipt bytes only, not the linked original document or issuer calendar. Tests bind the static explanation to the receipt and reviewed interpretation; they are not an independent refetch or proof of online availability.

## Distinct clocks and source objects

- [Original 8-K](https://www.sec.gov/Archives/edgar/data/108516/000119312526464853/wor-20261112.htm): reports that the November 12, 2026 Baird conference actually occurred. It states that the presentation deck had already been posted before the conference. The transcript is separately furnished as Exhibit 99.2. This does not establish the transcript's first-public time or that every fact was already public.
- [Earlier issuer calendar notice](https://ir.worthingtonenterprises.com/news/news-details/2026/Worthington-Enterprises-Participating-in-Baird-Global-Industrial-Conference-Following-Investor-and-Analyst-Day/default.aspx): gives a scheduled November 12 start of 1:35 ET and a distinct November 10 Investor Day. The schedule is not proof of the actual start instant; no ET-to-UTC conversion is made here. Do not merge the two events.
- SEC acceptance: November 17, not the conference start and not authenticated first-public time for the deck, transcript or all information.
- Collector observation: November 18, the saved metadata discovery clock, not the event start or first-public time.

The reproducible comparison is only calendar-day ordering: the reported November 12 occurrence date precedes the November 17 acceptance day and November 18 discovery day. It does not calculate event-to-market delay or invent an actual start time. The pre-conference deck statement is object-specific; it is not a general novelty verdict. Exhibit numbering does not authenticate earlier public availability.

## Unchanged boundaries

Precise first-public time, actual start instant, complete source coverage, information-level novelty, price joins, trading outcomes and eligibility remain unverified. This note creates no collector request, provider request, order, paper decision or price return. Existing receipt, metadata snapshots, frozen studies and paper state remain unchanged. The collector page exposes this as an expandable saved-case detail, independently of its current saved-status loader.

## Reproduce the bounded check

`python3 -m unittest discover -s backend -p 'test_worthington_saved_chronology.py'`

The test verifies exact receipt bytes and one-event membership, metadata-snapshot hash and issuer association, static displayed timestamps, distinct source references, calendar-date ordering, preserved unknown/false states and the absence of interactive actions in the detail. It deliberately cannot certify the unretained source pages or a first-public timestamp.
