# Complete-submission exhibit coverage checkpoint

Ten recovered submissions contain **224 embedded documents**, including **seven EX-99 exhibits across six submissions**. This saved retrospective inventory reads actual content-addressed originals, verifies recorded source bytes and identity through the existing header builder, and validates closed DOCUMENT framing plus unique sequence/type/filename metadata. Each EX-99 document has original byte offsets and SHA256. Aggregate counts include XML, graphics and ZIP payloads; none are executed or rendered. Public builds cannot re-open the private originals.

This is coverage, not evidence that all 224 documents have been semantically reviewed. The public artifact explicitly marks image/text completeness unreviewed and preserves all ten cases, including missing/invalid sources. No original document bodies or private storage references are published.

## Concrete unresolved work found in the actual exhibits

- **TherapeuticsMD:** EX-99.1 description calls it second-quarter results, while the body calls it third-quarter results. Continuing-operations EPS is not verified total diluted EPS; the prior rounded 0.00 cannot support percentage growth. License revenue's rounded 1.3 million and the stated 475-thousand increase/60.6% should not be treated as exact interchangeable amounts. A 365-thousand milestone further limits interpretation as recurring growth.
- **Revvity:** EX-99.2 contains **91 HTML image references**. Its Financial Disclosures text identifies **November 3, 2026 pro forma guidance** as a basis and describes exclusions. That original guidance and identical period/basis must be recovered and reconciled before a guidance-raise claim. Image-reference count does not establish unique images, successful image resolution or visual review. EX-99.1 alone does not complete this presentation review.
- **Worthington:** EX-99.1 is an Investor Day transcript. The economic event is November 10, not refreshed to the November 13 filing date. A comparable prior guidance basis remains missing.
- **IEH:** EX-99.1 contains the previously verified revenue pair, but the issuer remains outside the approved universe and the original prior-period disclosure/amendment history remains unreconciled.

These follow-ups are explicitly manual, accession-specific review context, not classifier findings. Other cases retain their prior outside-family reviews. One header Results of Operations marker is not a complete earnings universe: an earnings-like narrative can occur in another furnished exhibit. Do not silently change eligibility based on an Item 2.02 header or an EX-99 attachment alone.

No external amendment fixture was needed for this bounded inventory. Existing tests reject amended comparison substitution; this inventory records 8-K/A as a distinct document type rather than merging it with 8-K. No later filing is treated as earlier knowledge. Historical availability, signals, outcomes, strategies, schedules and the dashboard remain unchanged.

Run `backend/exhibit_coverage.py` with the reviews and authorized local originals to generate a new artifact. To reproduce the saved checkpoint, use its Python `build` with the saved `analysis_utc`. That clock denotes invocation/reproduction, not authenticated completion or first-public time. Tests cover framing, duplicate sequences, missing metadata, body/type separation, exact span hashes and no-exhibit submissions.
