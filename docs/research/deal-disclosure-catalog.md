# Historical filing-evidence catalog

This is a public **metadata-only** companion to the private acquisition/disposal disclosure queue. It makes the already verified **466 filings across 454 issuer CIKs** discoverable without publishing the underlying narratives, transaction amounts or counterparties. The 546 selected disclosure records are grouped by filing accession, preserving exact concept/taxonomy-version counts and the number of records with dimensions.

Starting HEAD: `998fb836576a58ac41bfd08786fd14971ebbb8c7`. Previous protected reports and paper ledger remain unchanged. There is no new collection, model training, event qualification or execution activation.

## Files and consumer contract

- `web/disclosure-catalog/summary.json`: version/status, counts, source/input hashes, selection, generation timestamp, metadata hash/byte count and limitations.
- `web/disclosure-catalog/filings.json`: one entry per accession, sorted lexicographically.
- `backend/deal_disclosure_catalog.py`: reproducible metadata projection from the existing pinned notes audit.

Each filing contains exactly:

`accession`, `issuer_cik`, `issuer_name_as_filed`, `form_as_filed`, `filing_date`, `concepts`, `disclosure_records`, `records_with_dimensions`, `sec_filing_index_url`.

Each concept entry contains `tag`, `taxonomy_version`, and `records`. There is no event type, target, purchase price, deal date, first-public timestamp, sentiment, materiality, prediction or recommendation field. Issuer names and form types are as filed, not current identity claims. No reporting-owner data, addresses, signatures, footnotes or narrative text appears.

Consumers should verify manifest status and metadata hash/counts before rendering; reject malformed identifiers, duplicate accessions, contradictory counts or unsupported source associations. Render source strings with inert text APIs, not HTML. Search can use source issuer name, CIK and accession; filters can use reported form and exact source concept. Keep the file lazy-loaded on the evidence explorer rather than adding it to every dashboard visit.

## Source links and time

Links are constructed from the retained issuer CIK and filing accession using the standard SEC filing-index path. They were **not fetched or individually verified**. The manifest explicitly says `CONSTRUCTED_FROM_FILED_IDENTIFIERS_NOT_FETCH_VERIFIED`. A user can open the original filing to investigate; if a constructed link is unavailable, SEC issuer search is an alternative. Link construction is not proof that the original filing bytes have been retained or authenticated.

Filing dates are date-only as reported in the prepared source, within October 2026. They are not transaction dates, announcement times, or earliest public availability. Disclosure text may concern historical activity, proposed transactions, accounting updates, repeated transactions or negations. Multiple concepts can describe one activity. A filing's presence here does **not** confirm a new or completed deal; absence does not establish no deal.

The source is the previously verified October 2026 SEC statements-and-notes dataset. Selection remains the four exact standard acquisition/disposal concepts under `us-gaap/2025` and `us-gaap/2026`; custom concepts and other disclosure forms of expression are outside the stated coverage. See [the disclosure queue methodology](deal-disclosure-evidence.md).

## Verification and reproduction

The generator re-runs the pinned private notes audit, then checks record count, unadjudicated state, source-row identity and hash, accession/issuer consistency, known taxonomy concepts/versions, filing dates and form allowlist. Conflicting submission identities and duplicate source row IDs fail closed; distinct source occurrences remain counted separately. Public output has an exact field allowlist and a 5 MB size bound.

A new trusted private output directory is created with 0700 permissions; 0600 output files are flushed before the final hash-bearing completion marker. Failure leaves `INCOMPLETE`, and existing outputs are not overwritten. This is completion bookkeeping, not immutable storage or independent timestamping. Only the reviewed public metadata and manifest are copied into the repository.

```sh
python3 backend/deal_disclosure_catalog.py \
  --database PRIVATE_NOTES_DB --database-sha REVIEWED_DB_SHA256 \
  --archive PRIVATE_NOTES_ZIP --archive-sha REVIEWED_ZIP_SHA256 \
  --out NEW_PRIVATE_DIRECTORY
python3 -m unittest discover -s backend -p 'test_deal_disclosure_catalog.py'
```

Synthetic tests exercise exact output fields/URL formation, repeated contexts without fabricated filings, inconsistent identities and hashes, unsupported adjudication, count mismatches, inert-label handling, form rejection, completion and failure markers. Actual source associations require independent review before release.

Training and execution remain disabled. The catalog is a route to inspect evidence, not a set of confirmed financial events or usable labeled examples.
