# Original-agency macro release evidence

Two official archived BLS PDFs were retrieved without keys, private contact information, paid services or retries on November 17, 2026. The archived employment release declares an embargo ending November 6 at 08:30 Eastern; the CPI release declares November 10 at 08:30 Eastern. Both concern October 2026. These declarations convert to 13:30 UTC, separately from actual current retrieval receipts.

**A printed embargo declaration is not independent authentication of first-public availability.** Today's copy is not evidence that CatalystRadar possessed identical bytes at an earlier decision. No past decision, consensus forecast, surprise, price outcome or training qualification is created.

## Evidence retained

The employment document contains a current payroll/unemployment statement and an explicit prior-month revision statement. The CPI document contains headline and core monthly statements and a missing year-earlier-comparator warning. Independent review of the original rendered pages confirmed the release declarations and context. The payroll revisions must not be overwritten by current numbers; missing CPI annual comparisons must not become zero or be inferred from another series. CPI seasonally adjusted history is itself subject to later annual revision, while chained CPI has separate revision rules.

The public JSON is an aggregate manifest: source URLs, raw/extracted hashes, observation and declared timestamps, reference periods and statement counts. Extracted values, exact text spans and source PDFs remain in private evidence storage. No BLS emblem or illustrations are displayed or redistributed by this release.

## Implementation and limits

`backend/bls_release_evidence.py` is offline only. It reads a bounded PDF once, verifies its exact SHA256 and matching successful keyless receipt, passes those same bytes to locally installed Poppler `pdftotext -layout`, with a child-process 2 MB output-file limit and 30-second timeout, then checks bounded extracted text. UTC-aware retrieval clocks and date/filename/weekday identity are checked. A narrowly supported header and two known layouts produce literal statement evidence with offsets and SHA256 **of UTF-8 extracted text**, not PDF byte positions or canonical PDF structure.

Literal matches are not automatic semantic assertions: every matched span has `semantic_context_verified: false`. Quotation, negation or surrounding qualifications require manual review, even if a text pattern matches. The two actual snapshots were separately reviewed; that does not make this a general-purpose semantic extractor. Other release wording, negative changes, unsupported layouts, ambiguous matching statements or missing required evidence fail matching. No full table extraction or economic arithmetic occurs.

CLI arguments: `--pdf`, `--pdf-sha`, `--receipt`, `--receipt-sha`, `--kind` (`empsit` or `cpi`), `--output-directory`. Requires the existing local Poppler executable and POSIX process resource limits; no installation or network occurs in this utility. New private output directories must be outside its checkout. INCOMPLETE is written before work; source evidence and aggregate summary precede COMPLETE hashes. Existing directories are never overwritten. This is trusted local evidence retention, not tamperproof storage or an authenticated clock.

## Rights and provenance

- [BLS copyright and linking](https://www.bls.gov/bls/linksite.htm) permits reuse of BLS public-domain material with attribution; previously copyrighted images and the BLS emblem are excluded. This work uses agency facts, not image/logo rights.
- [Employment release archive](https://www.bls.gov/bls/news-release/empsit.htm).
- [Employment October 2026 PDF](https://www.bls.gov/news.release/archives/empsit_11062026.pdf).
- [CPI October 2026 PDF](https://www.bls.gov/news.release/archives/cpi_11102026.pdf).

The direct official source avoids assuming FRED access grants archival or model rights. No claim of complete BLS coverage, historical vintages, consensus data or predictive performance. Approved UI, held reports and disabled trading ledger remain unchanged.
