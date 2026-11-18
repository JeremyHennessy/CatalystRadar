# SEC prepared financial field semantics

The retained `readme.htm` in each of the four pinned source ZIPs defines NUM `ddate` as the end date rounded to nearest month-end; `qtrs` is a rounded whole-quarter count, not an exact duration. NUM values are unscaled but limited to four decimal places. This is not a guarantee of original precision.

Legacy JSON field names `reported_end_date` and `period_end` in the financial-review and financial-archive-facts artifacts carry this rounded `ddate`, **not exact XBRL context end dates**. They remain unchanged for compatibility; rendered labels explicitly identify the rounding. No derived exact date, fiscal-quarter identity or comparability is established. Original-filing company cards have independently retained context or issuer-release evidence and do not inherit this prepared-data semantics.

NUM `uom` is the reported unit; TAG `datatype` describes the concept type. In retained EPS candidates, TAG is `perShare`, NUM is `USD`. The SEC XBRL API compound-unit naming convention must not be imposed on this distinct archive format. USD alone does not establish a source defect, and neither column resolves the full original XBRL unit context. EPS values remain withheld pending original-context qualification. Empty segments/coreg fields do not independently establish consolidated scope.

| Retained batch | SHA256 of original ZIP readme.htm bytes |
|---|---|
| q1_2026_filing_batch | `b3913445c6b971c4c42d44d17358a577e64a6ccbbcc4c8f7fa8e3bba5809508a` |
| q2_2026_filing_batch | `b3913445c6b971c4c42d44d17358a577e64a6ccbbcc4c8f7fa8e3bba5809508a` |
| q3_2026_filing_batch | `b3913445c6b971c4c42d44d17358a577e64a6ccbbcc4c8f7fa8e3bba5809508a` |
| q4_2025_filing_batch | `25e0a9e16de0b6cabdb3a07b85ab2dbf2263c9f3e4800d62ad9430728322eb5d` |

Documentation: https://www.sec.gov/files/financial-statement-data-sets.pdf . No new archive or provider requests were made for this correction. No stored observations, numbers, source hashes, protected controls or eligibility states changed.
