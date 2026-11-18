# Bounded as-filed reporting-key comparison

This is a deterministic investigative lead, not evidence of trades or economic position changes. The fixed policy chooses the numerically first reporting-manager CIK with multiple HR/HR-A periods, then its earliest two reporting periods. It never substitutes another manager to obtain a desired result. Ambiguous same-period filings, an explicit amendment or confidential omission/release, notice/combination scope, mismatched declared row counts, missing key fields or oversized filings fail rather than silently reconcile.

## Source-backed example

CIK `0000051762`, RNC Capital Management LLC, is the first selected manager. Its March 31 and June 30, 2026 disclosures were filed August 6 and 7, respectively. The retained filing batch contains 172 and 181 holding rows. These are delayed as-filed disclosures, not contemporaneous observations of portfolio activity.

The six-field literal key is reported CUSIP, class title, put/call, shares/principal type, investment discretion and other-manager reference. Exact matching finds **168 common keys, 4 earlier-only keys and 13 later-only keys**, with no repeated-key groups in this pair. Common keys do not prove unchanged holdings or identical securities; source labels may change or mask corporate actions. Earlier/later-only means absence from the other selected filing's literal keys, not a new/discontinued economic position. No security or issuer mapping is performed.

Each difference preserves all corresponding allowlisted source rows, labels and original row IDs. Repeated keys would preserve multiple rows, not aggregate quantity/value. Names are evidence labels rather than matching identity. Original source SUBMISSION, COVERPAGE, SUMMARYPAGE and INFOTABLE rows are compared field-for-field against the pinned SEC archive for all 359 selected records (353 holding rows plus six context rows). The ZIP/database are pinned before and after processing.

Both forms are HR and confidential omission is N. Amendment and denied/expired flags are blank, explicitly unknown rather than proof of no amendments or confidential releases. The study does **not** reconstruct the full amendment/confidential chronology or claim complete portfolios. The actual retained periods are not used as proof of first-public availability.

## Public boundary and next review

The same source-only SEC filing reuse boundary as the [holdings sample](manager-holdings-sample.md) applies. Only source identifiers/class/options/discretion/labels and source metadata are projected; no values, quantities, prices, addresses, signatures or contact fields. Source links are constructed, not fetched. No new provider request, mapping service, collector or paper-engine change occurs.

The next research question is why these 17 literal keys differ: inspect originals, amendment history and class/option/discretion changes before any economic interpretation. This metadata lead cannot establish security identity, ownership magnitude, intent or actual transactions. App display is a separately reviewed integration requiring byte/hash checks and explicit caveats; this data package alone adds no UI.

```
python3 backend/manager_reported_difference.py HOLDINGS.sqlite ORIGINAL_SEC.zip NEW_OUTPUT.json
```

The result is generated only after complete source validation, then written exclusively to a new file. Tests exercise every key field, preserved duplicates, omission of values, actual original-ZIP/database matching and mismatch, wrong pins, period ambiguity, explicit confidentiality and declared-row-count blockers. This is a retrospective diagnostic, not a representative or preregistered performance cohort.
