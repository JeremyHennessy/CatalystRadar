# Second retrospective ranking snapshot

Cutoff: November 19, 2026, 20:10:08 UTC. This is the timestamp on a
retrospective documentary build, not an as-of-trading information set.
The fixed review set is the first release's 905 scanner records plus three
bounded follow-ups selected by exact issuer CIK and accession. No collector,
paper book, market-price join, expected return, directional model or provider
request was introduced. The first manifest, rubric, and snapshot remain at
their exact release bytes.

| Follow-up | Narrow fact and policy disposition |
| --- | --- |
| Coherent, CIK 0000820318, accession 0001193125-26-467737 | Include the issuer-reported November 18 board authorization for up to US$2.0 billion of common-stock repurchases, excluding related fees. No expiry or minimum share amount is stated. This does not establish spending, completed purchases, or a newly public event. |
| TherapeuticsMD, CIK 0000025743, accession 0001213900-26-119697 | Include a documentary comparison of the two *different* IMVEXXY milestone years and the associated MD&A caveat. Do not combine the CAD 500,000 calendar-2025 recognition with the November 10 amendment to calendar-2026 payments. Neither cash receipt nor a future run rate is inferred. The 8-K is a separate accession. |
| Worthington, CIK 0000108516, accession 0001193125-26-464853 | Exclude as the bounded earlier-disclosure control. Six specific claims were compared; this is not a verdict on all statements or an event-wide novelty finding. |

The Coherent and Worthington records in the morning push receipt and later
scheduled receipt match in accession, CIK, form, items, acceptance clock and
published metadata hash. A later observation is not another filing, does not
change filing-age scoring, and is not an authenticated first-public time.

The four original weights and tie-breaks are retained. The two added records
earn 40 for original source review, 20 for accession, unknown for an exact
period (not zero), and 20 for filing age. Both are **80/100 research priority**;
nothing in the rubric scores expected return or forecasts market direction.
Seven ideas survive the policy, zero qualify to trade, and zero are added just
to fill the ten slots.

## Reproduction

- `python backend/research_priority_successor.py` verifies the fixed source
  receipts and public review objects, reconstructs the original scanner and
  ranking, and emits expected successor pins without writing.
- The focused test checks exact released artifact bytes, unchanged original
  files, every new input pin, source-object references, exclusion accounting,
  disabled trading states, and rejection of a conflicting repeated
  observation: `python -m unittest discover -s backend -p 'test_research_priority_successor.py'`.
- Optional local source-byte recheck, with `lxml` only for the original HTML
  cross-check: add `--verify-originals <retained-issuer-html> <retained-sec-complete-submission>`.
  This checked the Coherent issuer page at 29,296 bytes, SHA-256
  `aef701901dc28af1cdd0b0b543e01a74fccd77fa45fa274be81090383798d983`,
  exact CIK/accession and authorization terms, and the complete TXMD SEC
  submission at 4,487,035 bytes, SHA-256
  `b1d9611d086251771ab12b16a836d94aee216ba25c24f1131e70731194c2469a`,
  exact header, primary HTML hash and all three normalized Note 8, Note 14
  and MD&A spans. Neither original is included in this release; CI validates
  the published evidence objects, not original response bodies or availability.
- `--write` emits only content-addressed artifacts; it does not advance or
  overwrite the original pointer. Selecting a release in the app is a
  separately reviewed hard-pin change, not an automatic daily write.

For boundaries see [Coherent authorization review](coherent-saved-repurchase-authorization.md),
[TXMD original verification](txmd-companion-local-verification.md) and
[Worthington chronology control](worthington-saved-observation-chronology.md).
