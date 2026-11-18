# Acquisition and disposal disclosures: a source-bound review queue

## Purpose and verified scope

This package organizes **546 retained prepared-disclosure records across 466 filings and 454 issuer CIKs** for acquisition/divestiture research. These are **not 546 deals, new announcements, or verified catalysts**. The underlying October 2026 SEC statements-and-notes archive was already downloaded and independently compared field-for-field to the private database. No new source requests were made.

Starting HEAD: `c0e7ec544c375eea2b5abd343f69b04906804241`. Code and aggregate documentation only. Existing dashboard, historical issuer metadata, held research reports, collectors, and disabled paper ledger are unchanged.

The fixed selection uses exact standard taxonomy concepts, versions `us-gaap/2025` and `us-gaap/2026`, datatype `textBlock`, and both custom/abstract flags equal to `0`:

| Concept | Source records |
|---|---:|
| BusinessCombinationDisclosureTextBlock | 295 |
| MergersAcquisitionsAndDispositionsDisclosuresTextBlock | 83 |
| DisposalGroupsIncludingDiscontinuedOperationsDisclosureTextBlock | 130 |
| AssetAcquisitionTextBlock | 38 |

The retained source taxonomy definitions identify entire business-combination, combined M&A/disposition, disposal-group, and asset-acquisition disclosures respectively. A disposal group can be held for sale, discontinued, or disposed of other than by sale; an asset acquisition is not automatically a business combination. No concept alone establishes a completed transaction, novelty, materiality, buyer/target identity, or price effect.

There are 508 records under taxonomy 2026 and 38 under taxonomy 2025. Eight retain dimensional context. The 2,703,647 bytes of text remain **private**, along with every selected TXT field and joined submission, taxonomy and dimension context. Records overlap across concepts, periods, filings and dimensions; their count is not an event count. Forms include periodic filings, registration statements and amendments, not just current reports.

## Evidence model

`backend/deal_disclosure_evidence.py` creates a deterministic source-row ordered review queue. Each private record contains:

- Original TXT row ID and every original field, including language, escaping, duration, dates, footnote, context and dimensions.
- SHA-256 of canonical JSON for the full TXT field dictionary, excluding the SQLite row ID. This is not an original-filing byte hash.
- SHA-256 of the exact UTF-8 retained value, with no unescaping or normalization.
- Unique same-accession SUB, exact tag/version TAG, and exact dimension-hash DIM joins, including source row IDs.
- `UNADJUDICATED_DISCLOSURE_NOT_EVENT` status. Event type/date, announcement time, first-public time, novelty and materiality remain null; training eligibility remains false.

The prepared source's mixed escaping flags are preserved, not interpreted. Text may include markup, claims, denials, and quoted material; it is untrusted evidence, never instructions or executable HTML. The generic private filename `candidate-pairs.json` is inherited from the existing completion writer; its contents here are disclosure review records, not paired financial facts.

## Temporal and interpretation limits

The batch describes filings made in October 2026, not transactions occurring then. Reporting periods, acceptance strings, filing dates, and context dates are retained but are not event-announcement or effective dates. Earlier deals and later accounting updates can appear repeatedly. This retrospective collection cannot become a feature supposedly available at an earlier decision time.

Before a record can support a catalyst example, an analyst must verify the actual filing and relevant original announcement; resolve negation, prior-period repetition and transaction stage; identify the issuer/security and counterparty; assess materiality; establish an appropriate information cutoff; and independently obtain licensed outcome evidence. No such adjudication is performed by this selection utility.

The exact four-tag scope deliberately excludes custom concepts, other taxonomy versions, generic accounting-policy blocks, insurance policy acquisition costs, and untagged narratives. Absence from this queue is not proof of no acquisition or divestiture. It is not an exhaustive legal/M&A feed and does not change source rights or grant training permission.

## Integrity and reproduction

[Official SEC statements-and-notes dataset](https://www.sec.gov/data-research/sec-markets-data/financial-statement-notes-data-sets) and the exact source archive URL/hashes appear in the public aggregate `deal-disclosure-coverage-2026-11-18.json`.

The utility pins the source ZIP and read-only SQLite database before and after reading, checks SQLite integrity, validates exact schemas and selected taxonomy metadata, rejects missing/ambiguous joins and invalid identities/batch dates, and bounds rows, per-field and total retained text. Raw duplicate disclosure occurrences remain distinct; matching text is not deduplicated into a supposed single event.

```sh
python3 backend/deal_disclosure_evidence.py \
  --database PRIVATE_NOTES_DB --database-sha REVIEWED_DB_SHA256 \
  --archive PRIVATE_NOTES_ZIP --archive-sha REVIEWED_ZIP_SHA256 \
  --output-directory NEW_PRIVATE_DIRECTORY
python3 -m unittest discover -s backend -p 'test_deal_disclosure_evidence.py'
```

The existing private completion writer creates 0600 files in a newly created 0700 directory, writes evidence before summary, flushes each file, and writes `COMPLETE.json` with both hashes last. Failures retain `INCOMPLETE`; existing outputs are not overwritten. These controls are not immutable storage or independently authenticated clocks. Input hashes identify retained evidence; prior independent ingestion audits establish database-to-archive derivation.

Synthetic tests cover denials and old-period wording without event inference, raw escaping/markup preservation, repeated occurrences, empty text, dimensions, missing/duplicate joins, nonstandard taxonomy, malformed identity/date/schema, public form-label allowlisting, hash binding, completion and failed writes. Synthetic success is not market evidence.

Only aggregate counts, selection and input hashes are public. Raw narratives, issuer identities for selected cases and financial/transaction values remain private. Verified event count is zero, training/execution remain false, and no orders or fills are created.
