# Goodyear reported redemption call: retained-source review

A single, retrospectively selected original, accession `0001628280-26-073584`, reports a November 13, 2026 call for redemption of $700 million aggregate principal of 4.875% Senior Notes Due 2027, planned for December 15, 2026 at 100% of principal plus accrued unpaid interest. This is not proof of redemption completion, cash spending, debt reduction, an investment opportunity, or independent security identification. The 8-K explicitly is not the redemption notice. The referenced notice was not independently reviewed.

## Reproduction

```
python3 backend/planned_debt_redemption.py --archive /path/to/CatalystRadar-SEC-originals-2026-11-14.zip --out /new/path/finding.json
python3 backend/company_evidence_retrieval.py evidence --cik 42582 --section redemption_calls
```

No source requests are made. The builder reuses the existing complete ten-member archive validation, including ZIP and manifest pins, individual source hashes, issuer identity, receipt URLs and observation-clock ordering. The Goodyear original SHA-256 is `238617de38af3365b142edf1572e4123870a674196f4ef369a2f81df883e65a1`. The reviewed primary is `gt-20261113.htm`. Exact byte intervals `[19300,19875)` and `[19904,20231)` retain hashes for terms and the notice limitation. Whole-context checks reject extra qualifiers, negation, ambiguous duplicate contexts, wrong issuer, primary/amendment and item context. Only the exact original pin can be published; the context inspector is a testable review check, not a general-purpose event classifier.

The public projection exposes typed terms and source references, not the original narrative, signatures or contact information. $700 million is scaled arithmetically to 700000000 reported dollars. ISO currency remains unknown. The due year is not an exact maturity date. The 100% redemption term is not a market price. Accrued interest, total outstanding debt, cash change and actual completion are unknown. Archive retrieval (`2026-11-14T23:33:27.622944+00:00`) is not first-public time. No return, prediction or trading qualification is inferred.

The additive `redemption_calls` retrieval layer joins only verified CIK 0000042582. Other companies are **not assessed**, not reported to have no redemption events. Existing frozen assertions and company corpus are unchanged. The existing financial assertion audit's unsupported grammar is not an absence-of-event finding.

## Verification scope

Focused tests exercise original-context shapes and public semantics, source-pin failure, identity, negation, extra/duplicate content, amendment and item mismatches. Retrieval tests retain all prior source output hashes and check every company association plus unknown states. The retained real archive was rebuilt locally and compared with published bytes; CI cannot independently retrieve the original archive. Deployment and browser verification are separate release steps, not claimed by these source tests.
