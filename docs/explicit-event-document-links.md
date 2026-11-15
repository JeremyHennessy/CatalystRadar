# Explicit same-event exhibit links

The financial admission rehearsal now verifies one bounded relationship grammar in a primary, non-amended 8-K: its explicit statement that a press release and presentation were issued in connection with the same named Investor Day and furnished as Exhibits 99.1 and 99.2, respectively. Both unique embedded exhibits and distinct filenames must be present. Missing/duplicate/amended/ambiguous cases remain unresolved. Matching issuer, date or filing alone never establishes a relationship.

The actual archived Revvity November 13, 2026 filing supports exactly one such bundle: its Investor Day press release and presentation. The report binds the primary paragraph, primary document and both exhibit bytes by offsets and hashes. Comments/scripts/styles cannot supply the linking statement. No raw private originals are published.

This helps prevent treating those two exhibits as two unrelated event candidates. It does **not** establish an exhaustive economic-event cluster or an independent sample. The label is issuer-reported; event timing/completion are not inferred. November 3 earnings and November 13 Investor Day are not merged. Cross-filing dedup, amendment histories, prior-publication search and temporal eligibility remain unresolved, and their counts stay unknown/zero-qualified rather than being silently certified.

Run the existing `financial_admission_rehearsal.py` CLI with the authorized originals to reproduce. Public CI uses synthetic cases, while the saved report is a current-analysis checkpoint independently reproduced against the actual private original bytes. No scanning, private experiment, order, provider quota or scheduling changes.
