# Worthington saved-observation chronology control

## Fixed scope and evidence basis

This is a static, case-specific chronology check, not a new event classifier or an update to a frozen projection. It concerns only CIK `0000108516`, accession `0001193125-26-464853`, in saved receipt `data/sec-observations/20261118T192626511660Z.json` (6,637 bytes; SHA-256 `6ebebfb3fafa156857d5c2685352c3fb15332e564ce45f5f65bc7213df3a29d5`). It is not a claim that this remains the latest observation.

The receipt records SEC acceptance `2026-11-17T13:52:55.000Z` and collector observation `2026-11-18T19:26:42.681073+00:00`. Its event remains `METADATA_DISCOVERY_NOT_ELIGIBLE`, eligible false, first-public time null. Its metadata source SHA-256 is `f637d59d3599d816862602e2faa59aa522df269018af710389650ff5fa10502e`.

The source-content interpretation below is supplied by the coordinating primary-source review on November 19, 2026. The original chronology control performed no additional retrieval. The claim-comparison extension below was separately checked against primary-source web text on November 19. No original-page HTTP bytes, status, retrieval timestamp or page hash is asserted by this package. The receipt hash certifies the saved receipt bytes only, not the linked original document or issuer calendar. Tests bind the static explanation to the receipt and reviewed interpretation; they are not an independent refetch or proof of online availability.

## Distinct clocks and source objects

- [Original 8-K](https://www.sec.gov/Archives/edgar/data/108516/000119312526464853/wor-20261112.htm): reports that the November 12, 2026 Baird conference actually occurred. It states that the presentation deck had already been posted before the conference. The transcript is separately furnished as Exhibit 99.2. This does not establish the transcript's first-public time or that every fact was already public.
- [Earlier issuer calendar notice](https://ir.worthingtonenterprises.com/news/news-details/2026/Worthington-Enterprises-Participating-in-Baird-Global-Industrial-Conference-Following-Investor-and-Analyst-Day/default.aspx): gives a scheduled November 12 start of 1:35 p.m. ET and a distinct November 10 Investor Day. The schedule is not proof of the actual start instant; no ET-to-UTC conversion is made here. Do not merge the two events.
- SEC acceptance: November 17, not the conference start and not authenticated first-public time for the deck, transcript or all information.
- Collector observation: November 18, the saved metadata discovery clock, not the event start or first-public time.

The reproducible comparison is only calendar-day ordering: the reported November 12 occurrence date precedes the November 17 acceptance day and November 18 discovery day. It does not calculate event-to-market delay or invent an actual start time. The pre-conference deck statement is object-specific; it is not a general novelty verdict. Exhibit numbering does not authenticate earlier public availability.

## Unchanged boundaries

Precise first-public time, actual start instant, complete source coverage, information-level novelty, price joins, trading outcomes and eligibility remain unverified. This note creates no collector request, provider request, order, paper decision or price return. Existing receipt, metadata snapshots, frozen studies and paper state remain unchanged. The collector page exposes this as an expandable saved-case detail, independently of its current saved-status loader.

## Reproduce the bounded check

`python3 -m unittest discover -s backend -p 'test_worthington_saved_chronology.py'`

The test verifies exact receipt bytes and one-event membership, metadata-snapshot hash and issuer association, static displayed timestamps, distinct source references, calendar-date ordering, preserved unknown/false states and the absence of interactive actions in the detail. It deliberately cannot certify the unretained source pages or a first-public timestamp.

## Six-claim earlier-filing comparison (November 19 review)

Scope: the same Worthington CIK and Baird accession above. This is a manual, bounded comparison, not a new event, generalized novelty classifier or source-ingestion pipeline. Primary-source web text was inspected for the following locations; no original HTTP byte archive, page hash or authenticated historical availability receipt was retained. Tests verify the saved interpretation and UI correspondence, not the truth of unretained pages.

Earlier source: [Investor Day filing index](https://www.sec.gov/Archives/edgar/data/108516/000119312526454489/0001193125-26-454489-index.htm), accession `0001193125-26-454489`, filing date November 10, acceptance displayed `2026-11-10 08:16:28` (SEC index clock; coordinating review identifies ET, no UTC conversion). [Exhibit 99.1](https://www.sec.gov/Archives/edgar/data/108516/000119312526454489/wor-ex99_1.htm) has these earlier-filed statements:

| Claim ID | Earlier deck location and statement | Later Baird comparison |
|---|---|---|
| cooling-fy26 | Slide 35: about US$13 million FY26 cooling net sales | Cooling Q&A, Joe Hayek: historical FY26 amount repeated |
| cooling-q1fy27 | Slide 35: about US$13 million Q1 FY27 cooling net sales | Same Q&A: quarter amount repeated |
| adjusted-ebitda-target | Slides 60/61/65: long-term adjusted EBITDA margin target 25%; slide 61 explicitly contrasts 2023 framework 24% with updated 25% | Prepared remarks and margin Q&A repeat target and prior-target distinction |
| gross-margin-target | Slide 65: approximately 30% long-term gross margin / net sales | Margin Q&A, Colin Souza: 30% target |
| sga-target | Slide 65: approximately 20% long-term SG&A / net sales | Same Q&A: 20% target |

Later source: [Baird Exhibit 99.2](https://www.sec.gov/Archives/edgar/data/108516/000119312526464853/wor-ex99_2.htm), event November 12. Locate the prepared-remarks prior-margin-target discussion, CFO answer following the analyst's margin question, and CEO cooling answer. These are six compared claims, not six independent confirmations or new events. Preserve approximations and target-versus-achieved distinctions. Do not compute growth between the annual and quarterly cooling amounts.

Every compared claim's precise first-public time remains null. Earlier SEC filing evidence supports this bounded earlier-disclosure comparison, not exact first-public availability. Whole-document novelty remains unknown. The sequential cooling-growth expectation is compared only to the September source below; other statements remain outside the comparison, without any newly-reported or already-public classification.

A separate [Investor Day transcript](https://www.sec.gov/Archives/edgar/data/108516/000119312526460589/wor-ex99_1.htm), accession `0001193125-26-460589`, describes the November 10 event but was accepted November 13. The coordinating review identifies its slide-35 discussion as repeating the historical amounts and sequential FY27 expectation, attributed to a prior earnings call. This later-filed transcript is not evidence of SEC publication before the November 12 Baird event; its event date must not replace its acceptance date or establish exact availability. It is not included among the six strict earlier-filed comparisons.

No collector, source event, frozen receipt, price, paper decision, outcome or eligibility is altered. The comparison is static and does not fetch the linked originals when expanded. Existing first-public-null and not-eligible states remain unchanged.

### Sixth claim: earlier September forward-looking statement

[September filing index](https://www.sec.gov/Archives/edgar/data/108516/000119312526402803/0001193125-26-402803-index.htm), accession `0001193125-26-402803`, displays acceptance September 25, 2026, 16:01:39 (Eastern SEC clock, no UTC conversion). The [September 23 call transcript, Exhibit 99.1](https://www.sec.gov/Archives/edgar/data/108516/000119312526402803/wor-ex99_1.htm) CEO cooling discussion and subsequent Q&A describe expected sequential ASME tank revenue growth through the remainder of FY27. Baird repeats that expectation. Claim ID `sequential-cooling-expectation` is forward-looking, not realized growth or a prediction by this app. The September discussion additionally corroborates the two historical cooling amounts, not extra independent events.

The September cover's Q2 label conflicts with parent Item 2.02 and the call introduction identifying Q1. Preserve that source discrepancy. The event date and acceptance date are separate; neither establishes authenticated first-public time, which remains null for this sixth claim too. The later-filed November Investor Day transcript is contextual corroboration only, not the earlier SEC publication basis for this expectation. No other transcript claims are classified.
