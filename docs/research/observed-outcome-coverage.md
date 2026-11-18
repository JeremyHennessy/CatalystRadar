# Conservative post-observation daily coverage

This is a separate retrospective specification from the first-public study. It asks a narrower descriptive question: are two consecutive scheduled closes after actual retained observation available at all? First observation is not first publication, novelty or event occurrence. It is not backdated to SEC acceptance or a historical filing date. No fill, prediction, return or causal claim is made.

## Fixed selection and actual source check

Select every 8-K/8-K/A record in the seven pinned public collector receipts and all ten retained original-filing receipts, without selecting for prices, financial direction or content. The seven runs contain 53 metadata observations; one failed run has zero events and ten errors, not a valid empty source. Original retrieval receipts add ten observations. Group only by exact issuer CIK plus accession, choosing earliest retained clock per pair. All observations remain within this frozen checkpoint, not a claim of earliest observation anywhere.

There are 14 issuer/accession pairs and 13 distinct accessions. Accession `0001193125-26-460692` appears with two CIKs; the audit flags and retains both associations rather than resolving the conflict or merging issuers. Metadata observation proves only metadata discovery, while original retrieval is labeled separately. No source-content novelty or earnings classification is assumed.

The eleven retained private Alpha Vantage snapshots are revalidated through the existing offline price-session auditor: pinned snapshot/response bytes, source function, symbol, actual observation clocks and schema-quality fields. All 1,100 daily dates run June 26–November 16, 2026. The calculation reads dates only into its output; no quote values, quantities or returns are published.

## Result: zero coverage passes, zero qualified outcomes

Convention: first scheduled US-equity close strictly after the retained observation clock, then the next scheduled close. Existing reviewed 2026 calendar rules and America/New_York timezone account for weekends, listed closures and early closes. These are candidate scheduled dates, not proof of actual operations, security listing/trading or auction prices.

Thirteen pairs have earliest candidate dates November 16 and 17; one has November 17 and 18. November 17/18 are absent even from the union of **all** eleven retained series. Thus no series could supply both dates, independently of any ticker mapping. The audit deliberately makes no issuer/security join. This is a necessary coverage exclusion, not qualified endpoint selection. Even a synthetic case with both dates remains unqualified until independent requirements pass.

Private individual research permission recorded in [private retention](../private-retention.md) does not establish public quote/derived-data redistribution rights. Missing historical security/share-class association, effective corporate-action treatment, actual-session qualification and source-specific event interpretation remain separate. No new provider requests or rights refresh occurred. The raw collector is unadjusted daily data, not total returns or an executable closing auction. A future permitted November 17 snapshot alone would remove only the first date-coverage blocker for some cases, not qualify a return study.

## Reproduce offline

```
python3 backend/observed_outcome_coverage.py CHECKOUT ORIGINAL_ARCHIVE.zip PRIVATE_SNAPSHOT_DIRECTORY NEW_OUTPUT.json
```

The private directory must contain the previously audited eleven snapshots and `audit-summary.json`; exact manifest and receipt hashes are pinned. Changed receipt inventory fails review, not silent extension. Output is created only after all validation. The existing first-public audit and all paper/collection controls remain unchanged. Tests cover exact close boundaries, weekends/holidays/early closes, timezone rejection, issuer conflict, no acceptance backdating, insufficient/sufficient date bounds without admission, and changed inventory/pins.
