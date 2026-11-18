# Exact instance references for revenue-context review

The five new revenue review candidates still lack inspected original accounting contexts. This small sidecar gives a reviewer a more specific retrieval reference than a filing index, using the **literal XBRL instance filename reported in the retained SEC SUB table**. It does not retrieve that document or qualify any financial comparison.

## Evidence and limits

The original Q3 prepared archive's bundled `readme.htm` defines `instance` as the submitted XBRL Instance Document name. Its SHA256 is `b3913445c6b971c4c42d44d17358a577e64a6ccbbcc4c8f7fa8e3bba5809508a`. The generator binds all five filenames to the exact SUB row, accession, normalized issuer CIK, database/archive hashes and canonical full-SUB-row hashes already audited for the revenue packets. It compares those rows directly with the original ZIP's `sub.txt` again.

The constructed references are:

| Source-reported issuer | Instance filename as reported |
|---|---|
| Abbott Laboratories | `abt-20260630_htm.xml` |
| Acme United | `acu-20260630_htm.xml` |
| Advanced Micro Devices | `amd-20260627_htm.xml` |
| Air Products & Chemicals | `apd-20260630_htm.xml` |
| CECO Environmental | `ceco-20260630_htm.xml` |

The exact CIK and accession directory are combined with the reported safe filename. Slash, traversal, percent encoding, query/fragment characters and unsupported file types are rejected. **The URLs were not fetched. Their accessibility, HTTP status and actual document contents remain unknown.** A reported XBRL instance may be an extracted XML document; it is not asserted to be the primary inline HTML filing or a human-readable statement.

Filename strings are not authoritative dates, ticker mappings or security identities. In particular, AMD's filename contains a different date-like string from the prepared June30 context key. This is a reason to inspect the actual context, not proof of an exact June27 period end. No dates are parsed from any filename.

## Why collection was not attempted

At the inspected repository checkpoint `023719ef`, the active trial workflow remains the fixed ten-issuer submissions-metadata collection. It is not a five-issuer original-XBRL collection route. Offline continuation/send checks explicitly retain external authorization/ownership/history blockers and do not authorize a send. This work did not dispatch or modify that workflow, inspect credentials, change gates, make an SEC request, or retry a stopped source.

The explicit eleven-original inventory checked for PR123 contains no exact selected accession. A filename search of the current retained workspace and inspection of the retained cohort bundle found no additional exact named instances. These are scoped local checks, not proof that documents do not exist in Library, elsewhere, or on EDGAR. The retained October notes batch is not a substitute for these July/August filing accessions.

## Reproduce and use

```
python3 backend/revenue_instance_references.py \
  --root . --database /trusted/retained/prepared.sqlite \
  --archive /trusted/retained/2026q3.zip \
  --output-directory /trusted/retained/new-instance-references
```

The source packet is pinned to PR123's immutable bytes. The new external destination requires a trusted existing parent and uses 0700/0600, `INCOMPLETE` before processing and a final `COMPLETE.json` hash receipt after persistence. The reviewed public file is `web/company-findings/revenue-instance-references.json`. It contains only five issuer/accession/reference records and their provenance; no original document, address, owner, prices or new financial values.

Consumers must pin this sidecar, match each record to the exact CIK and accession in the pinned revenue packet, render the filename inertly, and label navigation **reported XBRL instance lookup, not fetched/verified**. Do not automatically fetch a provider document during rendering. Preserve all original-candidate blockers and null change fields. The existing revenue packet, 108-company queue and dossier files are unchanged. App integration is a separate reviewed change.
