# Exact retained inline-XBRL contexts, without numeric admission

Starting commit: `d06f56f72ec4a71ed73e60d75bb800901f4b838c`.

## Concrete improvement

Prepared financial rows retain `qtrs`, date, unit and dimension context, but do not themselves provide the full inline document's exact duration dates or unit structure. The one newly retained primary filing package supplies that evidence directly. The offline extractor found **29 target facts across three standard concepts**, all with declared duration periods; **12 retain segment/scenario context** rather than being silently treated as total-company facts.

The four predefined target concepts are the same narrow revenue/net-income/diluted-EPS set used by the financial-pair feasibility study. Three appear in this document. These counts include repeated and dimensional facts; they are not independent examples, growth signals or new eligible observations.

For example, the source's revenue declarations contain explicit May 1–July 31 current/prior durations, not merely `qtrs=1`. Units are resolved from actual unit elements, including numerator/denominator measures when supplied, rather than inferred from a unit ID or flattened prepared `uom`. This improves source-context evidence while leaving comparability and numerical interpretation unverified.

## Partial acquisition, not a complete cohort

The retrospective diagnostic selected six contexts covering twelve filing accessions. Only **one** primary package was saved and independently checked. The ordinary SEC viewer's “Save XBRL Zip File” supplied an eight-member, 78,182-byte ZIP containing the primary HTML and related files. It is not the complete submission text file. The second ZIP action timed out without a local artifact; collection stopped, with no retry or remaining-ten requests. The second filing was visibly readable, but its raw bytes were not archived.

The first ZIP and exact provenance are saved privately in Library. HTTP status and exact download clock were not exposed; local verification is not historical public availability. The six-case selection was locally frozen before case inspection, not independently authenticated preregistration or a prospective/unbiased sample. No additional source requests were made by this extraction package.

## Evidence retained

`backend/inline_context_evidence.py` accepts an exact hash-pinned ZIP/member. It retains:

- Raw archive and primary-member SHA-256 hashes.
- Resolved concept and transformation QNames using each element's own namespace scope, including nested prefix changes.
- Entity identifier/scheme, duration or instant dates, and referenced unit measures or divided units.
- Serialized context XML, original namespace bindings and descendant binding scopes. Segment/scenario contents remain present; they are not discarded to force a match.
- Untransformed text, declared format, scale, sign, decimals, nil, footnote/continuation references and exclusion presence. A continuation makes the retained local text explicitly incomplete.

**No numeric transformation is implemented.** A dash with a declared zero-dash format is preserved as that text and format, not converted by guessing. `numeric_value` stays null and `numeric_conversion_verified` stays false. Dates and namespaces are source declarations, not authenticity, availability, economic scope or securities-identity proofs.

Context hashes explicitly identify `ElementTree.tostring` serialization, not raw byte slices or canonical XML. Serialized namespace prefixes can differ from the source; original member hashes bind original bytes. Retained namespace maps are required when interpreting QName-valued content. No cross-runtime canonical hash claim is made.

## Fail-closed and privacy boundaries

The implementation bounds compressed ZIP size, member count/uncompressed sizes, primary bytes, XML elements/namespace expansion and context-output volume. It accepts only UTF-8-compatible bytes with supported UTF-8/ASCII declarations, rejecting UTF-16/32 and other encodings before parsing. It rejects duplicate/unsafe or aliased member names, DTD/entity declarations, duplicate evidence IDs, dangling references, unknown QName prefixes, unsupported inline namespaces/fractions, ambiguous periods and unsupported unit structures. It never extracts archive paths to the filesystem or executes document content.

Output is private, outside this checkout under an existing trusted parent, using the shared INCOMPLETE/COMPLETE protocol and 0700/0600 modes. The protocol's private `candidate-pairs.json` filename holds source-context records here, not paired financial observations. Consumers must check completion hashes and absence of INCOMPLETE. The path exclusion covers this checkout only, not every other publishing directory or an untrusted parent.

The dated public JSON contains counts/hashes only, not fact values, context XML or financial narrative. Existing UI, held research reports and disabled ledger remain unchanged. Tests cover scope rebinding, units versus IDs, dimensions, DTDs/entities across UTF-16/32 endiannesses, duplicate IDs/ZIP names, malformed/dangling references, period failures, nil/continuations/exclusions and unsupported formats of representation.

## Remaining gap

This establishes exact context evidence in one retained source. It does not finish the two-source comparison, prove historical first-public timing, implement all iXBRL transformations, validate reporting-basis comparability, identify tradable securities or supply price outcomes. Training readiness and execution remain false, with no increase in qualified examples.
