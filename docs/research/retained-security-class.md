# Retained TXMD cover-class assertion

This package narrows one market-data identity prerequisite for the unchanged frozen TXMD outcome case. It does not create another company explorer, join a ticker to prices or qualify an outcome.

The reviewed original archive SHA256 is `0f92e2c02a597b14f08c29395ae2fc9b87f2db580016e632c8d76c3059e449c0`; filing `0001213900-26-119681` has 233,722 bytes and SHA256 `e69ffeb2329ad596f652619d63e6c9195ad2b411258315b259fee04a2f131c47`. The existing frozen source-review builder verifies the exact archive, manifest, accession, issuer and original SEC receipt before this adapter operates. No new source request is made.

The primary 8-K cover has a single row associating its reported common-stock class, TXMD and exchange wording. The three inline facts share an entity context for CIK0000025743. That context contains equal **start/end dates**, November13, not an instant. We preserve this form and do not turn it into a historical effective-date interval. The inline exchange text is Nasdaq; its declared transformation is recorded but not evaluated. The visible cell says The Nasdaq Stock Market LLC.

The narrow public sidecar contains only issuer-disclosed factual identity labels, source hashes/spans and qualification caveats, not full filing content, addresses, contacts, private quotes or licensed identifiers. Its source is the already retained public SEC filing under the existing authorized SEC research route, not Alpha Vantage or a market-data entitlement. No general license grant, price redistribution rights or independent historical security mapping is inferred. Source and observation provenance are carried unchanged from the existing frozen review.

## Verification and abstention

The bounded parser requires a unique primary 8-K, unique reviewed context, single FILER, same-row three-fact association and matching cover headers/cells. It rejects duplicate contexts/facts/documents, hidden/commented facts, altered taxonomy/context identity, dimensions, continuations, changed values, unsupported exchange transforms, malformed markup and DTD/entity declarations. Bytes are separately hash-bound in the production builder; parser fixtures are synthetic and do not certify source truth.

```
python3 backend/retained_security_class.py CHECKOUT RETAINED_ORIGINALS.zip NEW_OUTPUT.json
python3 -m unittest discover -s backend -p test_retained_security_class.py
```

Output refuses overwrite. Historical mapping, effective interval, action continuity, actual trading/session evidence, price endpoint coverage, source timing and outcome qualification remain independently unresolved. No order, collector, workflow, frozen study or original fact is changed.
