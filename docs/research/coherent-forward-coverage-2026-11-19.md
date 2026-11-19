# Coherent single-case forward coverage checkpoint: excluded

**Protocol cutoff: 2026-11-19 21:11:52 UTC.** This is an internal, unauthenticated protocol checkpoint defined before either target close, not an execution decision or authenticated public availability. It is distinct from the immutable 20:10:08 UTC ranking cutoff, which remains retrospective.

**Identity and clock boundary:** [Coherent's Item 7.01](https://ir.coherent.com/node/18481/html), accession 0001193125-26-467737, issuer CIK 0000820318, discloses a board authorization, not completed repurchases. The pinned original's cover reports COHR, common stock with no par value, on the NYSE as of the report. This does not match that class to a price-provider instrument across the required dates. The retained [OpenFIGI lookup](openfigi-watchlist.md) remains a candidate and does not validate listing continuity or a provider-specific join.

Official SEC acceptance: 11:30:06 UTC. First saved metadata observation of this exact pair: 11:41:59.642713 UTC. The 19:31:48.997515 UTC poll repeated the same accession, acceptance and metadata hash. None of the three clocks authenticates when the filing first became public. A retrospective pairing from the first saved metadata observation would yield November 19 and 20, but it is not prospectively frozen and cannot be used as a result of this protocol.

**Convention:** Use the first two regular [NYSE scheduled closes](https://www.nyse.com/trade/hours-calendars) strictly after the protocol cutoff, 16:00 ET / 21:00 UTC on Friday November 20 and Monday November 23, 2026. These are candidate observation sessions, not proposed fills, proven actual sessions, tradability, or a claim of causation.

**Exclusion:** Both dates are beyond the last retained date, November 16, in the pinned [date-only audit](price-session-audit-2026-11-17.json), which covered 100 dates for each of 11 series. This is a necessary exclusion from audited retention without any ticker join, not proof that no other data exist. No additional provider reads, actual-session/halt attestations, corporate-action chain, or legal right to publish licensed values/results were established. No return or price is calculated. Authorization to observe evidence is not authorization to trade.

**Next evidence step:** After both target sessions, verify that a permitted source actually retained both dated observations. Then independently bind the provider instrument to the effective-dated share class, validate actual sessions and corporate actions, and confirm rights for any outward sharing before computing a descriptive change. Do not swap dates after observing results, rebase the historical ranking, resume collectors, or treat missing data as zero.

Offline recheck in the exact `c623ca3` checkout plus this checker, using the already-retained issuer HTML (29,296 bytes, SHA-256 `aef701901dc28af1cdd0b0b543e01a74fccd77fa45fa274be81090383798d983`):

```
python backend/coherent_forward_coverage.py . /path/to/retained/coherent18481.html
python -m unittest discover -s backend -p 'test_coherent_forward_coverage.py'
```

Script pins both receipts, the frozen ranking, source metadata, issuer HTML, and the existing date-only audit; it does not need or read any market price values. It does not put the retained original in Git.
