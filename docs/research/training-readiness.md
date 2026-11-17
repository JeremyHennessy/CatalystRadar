# Training evidence readiness: research stage, no model claim

## Acceptance and scope

Starting commit: `a57acfdf151a5f6a0baa0c6dca059fb349b0a4ae`. Goal: reproducibly distinguish observed metadata, recorded features, historical prepared rows and genuinely usable decision/outcome examples without regenerating the held report, changing the approved UI, enabling paper execution, contacting providers or spending money.

`backend/training_evidence_inventory.py` is a read-only inventory. Run `python3 backend/training_evidence_inventory.py --root . --output NEW_REPORT.json`. Output refuses overwrite. It records exact hashes for each input, checks the latest scan has an identical retained receipt, strictly decodes duplicate-free JSON, uses existing hash/metadata normalization, and rechecks input hashes before emitting results. The report names the checkout HEAD but identifies its actual basis as hashed working-tree inputs, not an attestation that every input is committed at that HEAD. Results are deterministic for unchanged inputs/HEAD. Prepared manifest counts are reported as saved summaries; private databases are not reverified by this tool.

## Verified inventory at the checkpoint

The dated JSON alongside this document binds exact input hashes:

- Seven retained scan receipts, 1,592 distinct metadata candidates and 9,550 repeated metadata observations. These are not independent training examples.
- 60 validated source observations and 10 unavailable source observations. Repeated hashes may appear across receipts; these counts are source observations, not unique files or issuers.
- The deliberately frozen November 15 report records 1,591 metadata candidates and ten reviewed records, zero qualified observations and zero outcomes. It is not rewritten to match the newer scan.
- Ten retained header-feature rows contain 50 feature values. None has a decision, first-public timestamp or outcome; none declares verified financial extraction or eligibility. These are selected retrospective header features, not an unbiased cohort or financial catalyst labels.
- Therefore there are **zero usable decision/outcome examples within these retained feature rows**. This is a scoped deficiency statement, not a census or rejection of every possible private/historical dataset.
- The paper ledger remains disabled with zero orders, fills and positions. This inventory does not modify it.

The new prepared datasets contain valuable raw research context, but their millions of rows are not interchangeable with qualified examples. Their local download/verification times do not prove availability before a historical decision. Empty values, fiscal periods, amendments, repeated statements, units, segments and taxonomy must remain distinct. Counts for managers, private issuers and filing quarters must not be added to listed-company coverage.

## Fail-closed meaning

Missing/invalid feature or ledger arrays raise an error rather than yielding zero. A supplied decision/outcome is counted only as present, not valid. If any such pair is present, the inventory's qualified-example count becomes **unknown**, not positive. Declared eligibility, finite values, source hashes and structural split success cannot authorize training or execution. Rights, security identity, source-clock authenticity and corporate-action/outcome qualification remain `NOT_ASSESSED` here. No predictions or performance metrics are produced.

## Smallest next research prerequisites

1. Select a predeclared research question and horizon supported by permitted inputs; record source-specific collection, storage, model-use and publication rights independently. Free/public access is not training permission.
2. Bind each event to a stable security and explicit event group, with retained source evidence and an independently justified availability clock. Do not use SEC acceptance dates, today's restored archive or revised historical data as proof of earlier availability.
3. Recompute required numerical features from exact retained evidence before a frozen research decision. Retain neutral, rejected, negative and missing cases; do not cherry-pick the ten manual records.
4. Acquire permitted, identified price/benchmark observations and corporate-action-consistent labels for the intended windows. Intraday horizons require actual intraday coverage. Do not invent prices, returns, fills, halts or market-wide volume from exchange-only data.
5. Run existing split, archive and receipt audits, then separately establish source truth, rights, sampling quality and label validity. Related-event leakage, overlapping outcomes, delisted/survivorship coverage and chronological embargoes require explicit review.
6. Only then consider an interpretable baseline with a held-out evaluation, uncertainty, calibration, cost sensitivity and failure analysis. No defensible real-data model evaluation can be reported from the current zero-pair feature inventory.

The existing structural audits already distinguish integrity from authentication and preserve missing labels. This package does not introduce a redundant trainer or weaken them. Next work is the source-rights/capability registry and a concrete permitted outcome-data route, not another unqualified model or indiscriminate download batch.
