# Static company dossier delivery

This is a bounded delivery projection of the existing exact-CIK dossier, not new research or wider company coverage. It enables an app to fetch five selected public evidence records at a time rather than transferring the full source cohorts. No provider, model, private database, price, or trading access is introduced.

## Reproduce

From this repository:

```
python3 backend/research_dossier_static.py --destination /tmp/dossier-static-new
```

The destination must not exist. The generator verifies the reviewed v3 queue and all nine source pins through its existing deterministic rebuild, calls `research_dossier.dossier` for each CIK and section with a fixed page size of five, and checks the source snapshot again at completion. Its output is deterministic, without a new clock or claim of source freshness. Existing queue versions, CLI behavior, and public records are unchanged.

A failed write leaves `INCOMPLETE`; successful persistence checks every written byte and writes `COMPLETE.json` last. Only the generated `web/company-dossiers/v1/` tree belongs in the public repository. The completion file is a local build receipt, not a source clock or immutable storage claim. Use trusted output parent directories.

## Scope and payload

The fixed 108-company cohort contains 605 financial contexts, 282 insider filing records, five disclosure filings, and two issuer-reported findings. These are distinct source record units, not a sum of independent events or qualified training examples. The 282 insider records comprise 279 in the financial cohort plus three separately scoped Emerson filings.

The manifest lists every CIK and all four sections, including explicit coverage, source key, and total. A null total means not evaluated in the snapshot. An assessed zero means no selected records in that particular source scope, not no activity. Neither creates a page. An unknown CIK is outside the fixed snapshot. Later reviewed findings and the wider issuer directory are not silently included.

Each page carries its exact CIK, section, pinned queue snapshot, and unchanged `selected_section` object. Source dates, uncertainty, as-filed labels, original-link qualifications, and source-specific limitations remain inside the records. Shared interpretation, source pins, and unassessed holdings linkage live in the manifest. Financial context dates are coarse source keys, not independently established accounting durations. Cross-source CIK grouping is not event alignment, causality, security identity, or verified current activity.

## Required consumer validation

Pin the manifest byte length and SHA256 in the consuming app. Before use, validate its schema, exact snapshot, 108 distinct normalized CIKs, four known sections, unique fixed-relative page paths, totals, coverage, and contiguous five-record pagination. Never accept an arbitrary source URL or guessed page path. The manifest includes the exact byte length and SHA256 for each page.

Fetch only the selected page. Enforce the advertised byte length and 500,000-byte absolute cap; verify SHA256 before parsing, then validate the page's CIK, section, snapshot, coverage, source key, total, offset, limit, returned count and next offset against the manifest. Reject a mismatch without silently loading broader or unverified evidence. A caller must not use a page from one company as another company's evidence. Render all source strings as inert text and retain the source link safety checks. No user query causes a source-provider request.

The entire generated package is capped at eight million bytes and 1,000 files; the manifest is capped at 500,000 bytes. This is static saved research, not a live endpoint or promise of current URL availability. UI integration is a separate reviewed release; publishing these files alone does not make a new app interaction live.
