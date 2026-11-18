# Reusable frozen financial cohort audit

`backend/frozen_financial_cohort.py` turns the existing November 17 six-case diagnostic into a repeatable offline interface. It does not select a new cohort or replace unsuccessful cases. This is a bounded diagnostic, **not a statistically representative universe or training sample**.

The original policy chooses the first two context IDs sorted within each of three strata: equal cross-batch, differing cross-batch, and within-batch repeated contexts. Selection is reproduced before reading original-source availability. The exact plan, selection and input hashes must match. Missing strata, duplicate IDs and changed selection fail closed.

The tool accepts an explicit local original-package inventory. It verifies receipt and ZIP hashes/length, primary-member uniqueness/size/hash and parsed issuer identity using the existing inline context parser. Same-issuer/concept facts are review candidates only. It does not match exact periods from rounded `ddate`/`qtrs`, convert values, infer consolidation, treat duplicate presentations as independent evidence, or calculate growth. All cases abstain until exact context, accounting, timing, security and outcome requirements are independently met.

## Real retained-source run

Using the existing frozen plan `842a5e2078604aef3bd42cc88eb228ba643ff734a300bf660e1539d466e2ca55`, selection `a90b97118bcfffe62af47ed8423fbf3927cbcc30e3a6de3ebd132678925a9996`, and overlap input `12859e0159dd8f6a5c71f04c52141712d89bda3f4bd46e2bb674341efa75c62f`:

- Six fixed cases, twelve observations.
- Explicit inventory: one retained VitaSpring original package, SHA256 `e68c0065e400b19e92d07c7bb9cefdba522eefa9c4c35e6a701083f8552c0ee4`.
- One of twelve observations has a retained original in this inventory. Four same-issuer/concept context candidates are exposed for review, not admitted as exact archive matches.
- Eleven observations are absent from **this inventory only**. This does not mean SEC originals do not exist.
- Zero qualified cases, numerical changes, outcomes or trades.

Unlike the earlier historical audit, this run does not claim the older eleven-original inventory was rechecked. The supplied inventory scope is recorded explicitly. Original availability is not a historical-publication clock.

## Local CLI

```
python3 backend/frozen_financial_cohort.py PLAN.json SELECTION.json GROUPS.json ORIGINALS.json NEW_OUTPUT.json
```

ORIGINALS is an array of `{receipt, receipt_sha256, package}` local paths/pins. Receipts follow the retained source-package manifest with accession, issuer, ZIP hash/length and primary member/hash. Output creation is exclusive. Output is a local research artifact; no app integration or automatic publication occurs. No network requests, collectors, provider quotas, paper-book states or public payloads are changed.

Next useful step: source review of the preserved selected accessions, not substitution with easier or better-looking cases. Original availability alone cannot admit a comparable financial fact.

Accession association is the explicitly trusted pinned receipt binding, not an accession independently parsed from inline facts. Inline issuer identity is checked separately. Reads are bounded before decoding: plan/selection/config64KB, groups10MB, receipt1MB, original ZIP50MB; at most100original entries and primary member10MB.
