# Revvity: cited prior guidance recovered, no verified raise

The November 13 Investor Day exhibit explicitly refers to November 3 guidance. The cited original was located on SEC EDGAR in accession **0000031791-26-000031**, EX-99.1 `q32026pressrelease.htm`. A single request using the existing bounded SEC transport recovered the full 871,713-byte submission on **November 15 at 01:06 UTC**. Its header CIK/accession and exact-byte SHA256 were checked. This is a newly observed source, not proof of November 3 machine availability. No prior-byte hash existed and none was invented.

The reproducible two-source checkpoint finds:

- November 3: FY2026 pro-forma revenue approximately 2.86 billion reported dollar units, approximately 5% organic growth, adjusted EPS 5.40–5.45. The basis excludes China immunodiagnostics (China IDX).
- November 13 presentation: FY2026 estimated revenue approximately 2.9 billion. **2.86 rounded to one decimal is 2.9.** These values are compatible with rounding, not evidence establishing a guidance increase. This does not prove every guidance item was unchanged.
- Its approximately 6% organic growth belongs to **2027 considerations**, and the text says formal 2027 guidance will come with the Q4 call. Comparing this with FY2026's approximately 5% as a same-period increase would be wrong.
- No same-period EPS revision is established. Currency ISO remains unresolved, exact presentation graphics have not been fully reviewed, and no qualified signal results.

The two original accessions retain separate retrieval clocks, source hashes and exact exhibit byte spans in `data/revvity_basis_review.json`. The later presentation was already privately retained; the newly recovered original and receipt are kept out of the public repository. Public artifacts contain derived facts and source references only. Public builds cannot reopen those private originals. Local retention does not itself establish durable remote storage.

Run `backend/revvity_basis_review.py` with authorized original-source directories. Its Python `build` accepts the saved analysis clock for exact reproduction. It requires the exact reviewed source hashes, matching CIK/accessions, receipt byte counts/URLs and ordered observation clocks, and rejects amended headers. The extraction is explicitly accession-specific, not a general financial model. It does not resolve full amendment history or prior-period accounting comparability.

All first-public, decision, outcome and historical-ticker fields remain null. The analysis timestamp is invocation/reproduction time, not authenticated completion. Existing strategy, forecasts, private workflows and schedules remain unchanged; zero orders.
