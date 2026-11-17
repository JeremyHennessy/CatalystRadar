# Bounded inline numerical evidence

This offline research utility interprets two declared lexical formats from the previously retained, hash-pinned filing package. It does not collect new data, qualify financial facts, infer growth, join prepared facts or enable execution. The approved UI and held reports remain untouched.

## Supported subset and primary specifications

The [XBRL Transformation Registry 3](https://www.xbrl.org/Specification/inlineXBRL-transformationRegistry/REC-2015-02-26/inlineXBRL-transformationRegistry-REC-2015-02-26.html) binds the 2015-02-26 namespace to `numdotdecimal` and `zerodash`. This implementation intentionally supports a narrower subset: ASCII digits with optional correctly grouped commas and decimal point, or an ASCII hyphen for zerodash. Space/NBSP separators, other dash characters, other namespaces and transforms remain unsupported, not guessed.

The [Inline XBRL 1.1 primer](https://www.xbrl.org/specification/inlinexbrl-part0/rec-2013-11-18/inlinexbrl-part0-rec-2013-11-18.html) describes the separate sign and scaling declarations. Only absent scale is supported here, because all retained target facts have absent scale. Sign is absent or minus. Nil, continued or excluded text is unavailable. XML whitespace is collapsed; arbitrary Unicode whitespace is not silently removed. Text is bounded to 256 characters and decimals to 100 digits. Decimal construction is exact even with a low caller precision; declared decimals are retained but never used for rounding. These restrictions do not constitute a complete XBRL validator.

## Actual evidence and limits

The dated aggregate records 29 lexical conversions from one retained source: 17 numdotdecimal and 12 zerodash. Twelve facts have dimensional/scenario context, retained separately. This is not 29 independent financial observations or qualified training examples. Raw text, signed decimal strings, namespace bindings, unit definitions, duration dates and serialized context evidence remain private. Existing byte hashes bind the source; neither those hashes nor the transformation establish historical first-public availability or economic truth. No ratio, growth, restatement, comparability, security mapping, outcome or performance claim is produced.

## Reproduction and storage

Run `backend/inline_numeric_evidence.py` with `--archive`, `--archive-sha256`, `--member`, `--member-sha256`, and a new `--output-directory` under a trusted private parent outside this checkout. The archive is re-extracted using the previously reviewed bounded parser rather than trusting editable derived JSON. The shared completion protocol creates INCOMPLETE first, writes private candidate records and summary, and writes their COMPLETE hashes last. Consumers must reject an INCOMPLETE directory. The utility refuses overwrite; this is not immutable storage. Exclusion only detects its own checkout, not every possible publication directory. No raw facts are published by this package.

Run `python3 -m unittest discover -s backend -q`. Synthetic tests cover unsupported representations, missing versus zero, sign, precision and unchanged inputs. Source specifications were checked November 17, 2026. The actual source package was independently audited earlier; this conversion requires its own independent review before release.
