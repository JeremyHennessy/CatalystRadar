# Read-only company evidence dossier

The existing search interface returns research queue entries and navigation links. `backend/research_dossier.py` adds **bounded source-record retrieval for one exact CIK**. It returns the actual already-public financial cases, insider filing summaries, disclosure catalog records or reviewed issuer-reported finding referenced by that company entry. No model, network, private database, provider credential or file-writing action is used.

```sh
python3 backend/research_dossier.py --cik 1130310 --section financial --limit 2
python3 backend/research_dossier.py --cik 1130310 --section financial --limit 2 --offset 2
python3 backend/research_dossier.py --cik 1130310 --section disclosure
python3 backend/research_dossier.py --cik 32604 --section reported
```

## Useful examples and boundaries

- CenterPoint CIK 1130310 has six financial review contexts, one selected insider filing and one selected disclosure filing in this snapshot. Sections remain independent; their relationship is exact reporting CIK, not common event, aligned time, security identity or causality.
- Emerson CIK 32604 returns its source-reported financing finding and three separately scoped watchlist insider filings. It is **not evaluated in the financial 106-company cohort**; financial and disclosure totals remain null, not zero.
- IEH CIK 50292 returns the existing issuer-reported revenue finding, without forcing it into financial/insider/disclosure coverage.
- A CIK outside this **fixed 108-company v3 snapshot**, including H&R Block, returns an explicit out-of-snapshot result. Later cards and the wider issuer directory are not automatically incorporated. No-match does not mean the company or activity does not exist.

`section_overview` distinguishes total selected source records from unassessed/null coverage. `selected_section` contains the page, original source objects, total, returned count and next offset. An empty page beyond a known total is not no evidence. A scoped zero means no selected records within that source's stated selection, not absence of activity. Source labels, dates, flags and unknowns are preserved verbatim in each returned record.

## Integrity and limits

The interface reuses the existing v3 snapshot SHA/byte pin and nine-source derivation rebuild. Every source loaded for hydration is read again from its fixed path, verified against the snapshot's exact SHA and size, and bounded to 2 MB. References must be unique, present and associated with the same CIK; duplicate source IDs are rejected before pagination. Insider identity includes both filing batch and accession. EMR's watchlist source is distinct from the financial-cohort insider source. Reported findings must match ID, CIK and accession.

Queries accept a required one-to-ten digit nonzero ASCII CIK, section `financial`, `insider`, `disclosure` or `reported`, limit 1–25 and offset 0–10000. Output is capped at 500,000 bytes in its actual indented JSON encoding. Records beyond a page are not emitted. The CLI writes JSON only to stdout; it does not create saved artifacts. Argument syntax/choice errors use standard argparse messages; retrieval failures return exit 2 with a fixed error and no JSON result.

Financial prepared dates remain coarse source context keys, not verified exact accounting durations. Numerical equality or difference is not accounting comparability or restatement. Insider P/S includes open-market **or private** transactions; a filing quarter is not a transaction-time window. Disclosure tags are review candidates, not confirmed deals. All original source limitations remain, holdings company mapping stays unassessed, and training/execution remain disabled.

This is a deterministic retrieval layer for the current research interface, not a public endpoint, chat model or new dataset. Existing CLI behavior, queue files, UI, workflows, held reports and ledger are unchanged. Browser integration, if useful, is a separate reviewed step.
