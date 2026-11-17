# Continuing-operations narrative evidence

The offline financial rehearsal now recognizes one exact EX-99.1 paragraph
grammar: continuing-operations income paired with an explicitly combined basic
and diluted common-share amount and a stated prior-quarter comparison.

It preserves separately reported amounts, units and EPS strings, including a
rounded `0.00`. Scaling uses each operand's own stated thousand/million unit. The grammar allows
at most 15 integer and 8 fractional digits; longer values remain unsupported.
A local 64-digit decimal context prevents caller-context rounding during scaling.
Exact original paragraph byte offsets/hash and containing document hash bind
the extraction to source bytes. The caller first validates filing identity and
source digest. Comments, scripts, styles, unrelated document types and paragraphs
outside the supported grammar are not used. Multiple matches are ambiguous,
not additional independent samples.

This is **not** total-company GAAP EPS or comparable-period verification. The
supported paragraph does not identify its current period, so that field remains
null even when a prior year makes a likely interpretation tempting. ISO currency,
same-share basis and total-company comparability remain unknown. No growth ratio
is calculated from rounded EPS, and the extracted fields are not mapped into
the classifier's GAAP facts. All qualification, signal and order outputs remain
blocked. Surrounding accounting context still needs separate review.

Read-only validation on the ten recovered filings found one supported paragraph
in accession 0001213900-26-119681. This is a retrospective parser check, not an
eligible event or a new forecast. Neither the held financial research output nor
public dashboard data was regenerated for this change. The public change contains
only parser code, synthetic tests and this methodological description; original
source bytes and derived result files are not published.
