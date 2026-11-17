# Two archived payroll-release vintages

This is a small, manually reviewed documentary check, not an automated financial parser, unbiased sample, consensus study or training example.

The official October 2, 2026 Employment Situation archive (September reference month) and November 6, 2026 archive (October reference month) support **two exact previous-value correspondences**. The earlier document's September headline and revised August observation equal the previous values stated in the later document's revision paragraph. The later revised values do not overwrite those earlier observations.

The earlier release also contains a downward revision crossing zero for July. That negative revision and the August downward revision remain intact in the retained excerpt and PDF; they are not dropped because the existing narrow parser accepts only the other layout. The parser was deliberately not broadened for this hand-reviewed case. No numbers are normalized into an economic exposure or combined with equity returns.

## Evidence and reconstruction

The machine-readable aggregate pins both PDFs, original successful HTTP receipts, and exact UTF-8 `pdftotext -layout` outputs. Private evidence retains the selected headline/revision paragraphs with exact character offsets and extracted-text span hashes, the two source values and their revision relationships, units and seasonal-adjustment context. Establishment payroll changes count unscaled payroll jobs, not unique people; household unemployment statistics use a different survey/population. Its hash is in the public aggregate. Full PDF contents are retained, not just the selected excerpts.

To reproduce this diagnostic, retrieve the already retained source packages, check the manifest hashes, rerun the existing local `pdftotext -layout` version, and verify each private span against its text range. Compare the September headline and revised August value in the earlier document with the later document's corresponding previous-value text. Independently check each reported revised-minus-previous integer difference against its stated revision. No arithmetic context rounding or float conversion is needed. Source vintage ordering uses the printed declarations; actual retrieval order is different and is retained explicitly.

The earlier declaration is October 2 at 08:30 Eastern (12:30 UTC, daylight time); the later is November 6 at 08:30 Eastern (13:30 UTC, standard time). Both copies were retrieved November 17. **This does not establish that the system held identical bytes in October/early November, or independently authenticate historical first-public availability.** Selection and review are retrospective, not prospectively registered.

## Scope and rights

- [BLS Employment Situation archive](https://www.bls.gov/bls/news-release/empsit.htm) warns that archived values may be revised later.
- [October 2 original PDF](https://www.bls.gov/news.release/archives/empsit_10022026.pdf).
- [November 6 original PDF](https://www.bls.gov/news.release/archives/empsit_11062026.pdf).
- [BLS copyright guidance](https://www.bls.gov/bls/linksite.htm) permits agency public-domain facts; no image/emblem permission is inferred.

Public output is lineage, clocks and counts only. Private raw evidence is not committed. There are no new dependencies, collector changes, automatic semantic admission rules, UI changes, held-report changes or orders. Existing tests and public-state checks are rerun; independent review checks the actual private source correspondence separately. Model training and execution remain unqualified/disabled.
