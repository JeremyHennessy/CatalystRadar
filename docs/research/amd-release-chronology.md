# AMD sampled-Q2 release chronology safeguard

This annotation binds **one exact existing prepared revenue-review packet**, not all AMD filings, a ticker/security, the entire scanner or current issuer news. It does not qualify financial growth or replace the missing original XBRL evidence.

## What was observed

On November 18, 2026, manual review of two official AMD investor-relations pages observed:

- [AMD's source-dated August 4, 2026 Q2 release](https://ir.amd.com/news-events/press-releases/detail/1295/amd-reports-second-quarter-2026-financial-results), whose GAAP quarterly results table displays revenue of 11,536 and 7,685 in `$M`, labeled Q2 2026 and Q2 2025.
- [AMD's source-dated November 3, 2026 Q3 release](https://ir.amd.com/news-events/press-releases/detail/1303/amd-reports-third-quarter-2026-financial-results), which includes 11,536 as its Q2 2026 comparative in the same displayed scale.

The sampled SEC filing is accession `0000002488-26-000123`, filed August 5, 2026. Its exact prepared packet ID is `f9d8ff71357ad53a181de86ad2295164d300026976bfe2fb926ba0bdb481cd41`. The existing packet contains revenue candidate values 11,536,000,000 and 7,685,000,000, labeled USD. The source-sample bytes and both NUM row hashes plus the SUB row hash are pinned before applying this annotation.

The deterministic check scales the issuer's displayed `$M` numbers by one million and verifies numeric equality to those prepared values. It does **not** calculate growth. The issuer's `$M` label is not independently promoted to an ISO-currency assertion, and numeric equality does not establish accounting scope or exact period comparability.

The defensible wording is **“an earlier source-dated matching issuer release was observed in this review”** and **“a later-quarter release was observed.”** The sampled Q2 filing is not evidence of a new current announcement. This is not authenticated proof of prior publication, earliest announcement, economic-event duplication or complete/latest issuer news.

## Evidence status and clocks

The curated note was written from manual primary-page review through web search/open. **Original HTTP/page bytes were not retained.** Its SHA-256 `8ed2087d4a0a2608295e2e4099a13b1e8c9570e54d45594d895ef237670d6b4c` authenticates only the local reviewed-note bytes, not the website, HTTP response or historical first-public time. The public projection includes short curated facts and exact citations, not full pages or source narratives.

The date check is calendar-only: August 4 < filing August 5 < November 3 ≤ review November 18. Intraday ordering and authenticated first-public time remain unknown. Same-day ordering is rejected rather than invented. A later-release date after the observation date or a non-later fiscal label fails validation.

The prior SEC download timeout is not retried. Original XBRL retention, exact start/end contexts, independent accounting comparability, historical availability and security qualification remain unresolved. No old sample, scanner, queue, company manifest or report is altered.

## Consumer contract

Public artifact: `web/company-findings/amd-release-chronology.json` (5,061 bytes). A consumer must verify the full byte/SHA pin and bind the exact sample ID, CIK, accession, SUB hash and both NUM hashes before showing this optional warning. Do not apply it to arbitrary AMD evidence or present it as a current-news badge. Keep the original prepared-source status and missing-original blockers visible.

The statuses are `PRIOR_DATED_MATCHING_ISSUER_RELEASE_OBSERVED` and `LATER_QUARTER_RELEASE_OBSERVED`; their descriptions are calendar-date observations, not authenticated publication or novelty conclusions. All growth, comparison, execution and training upgrades remain false.

## Reproduction

```sh
python3 backend/amd_release_chronology.py --root . \
  --note /path/to/amd-timing-review18/research-note.json \
  --out /trusted/new-private-directory
python3 -m unittest discover -s backend -p test_amd_release_chronology.py
```

The generator reads only the pinned existing public sample and pinned curated note. It makes no provider requests. URL allowlisting, exact identity/source-row binding, bounded strict JSON, decimal formatting, scale checks and calendar prerequisites fail closed. Output is deterministic; private directories/files are 0700/0600, INCOMPLETE precedes work and COMPLETE hashes follow the final candidate. Failed builds retain INCOMPLETE.
