# Xerox accession: two explicit filers, not interchangeable identities

Accession **0001193125-26-460692** is a retained November 13, 2026 8-K with two separate `FILER` entries:

- **0001770450 — Xerox Holdings Corp**
- **0000108772 — XEROX CORP**

The apparent discrepancy is between an original-archive receipt associated with 108772 and retained submissions metadata associated with 1770450. Both CIKs appear explicitly in the same submission header. The cover also names both registrants. Signature context limits each company's signature to matters referring to that company and its subsidiaries. These observations justify a first-layer dual-filer annotation, **not** an automatic issuer merge, parent/subsidiary determination, security link, or assignment of every fact to both companies.

## Exact retained evidence

The original is 1,983,577 bytes, SHA256 `1e6110051c0653b7ac636de5bee60ec2feed9a91c59621470ac5fd0dafb1234e`, within the already retained and independently audited originals ZIP `0f92e2c02a597b14f08c29395ae2fc9b87f2db580016e632c8d76c3059e449c0`. Its manifest SHA is `ac6316ad597b9a931613c71e4f1442425f5f83c873d47ba17192f0c1b6a2274a`.

The original receipt records retrieval **2026-11-14 23:33:43.933078 UTC** under CIK 108772. The separate retained submissions snapshot records CIK 0001770450 and this exact accession, 8-K form, November 13 filing date and file number 001-39013. Its SHA is `7c6399e2da54dc6adc8ebc3578ba46c366611b25aa7ddec51eee4c7532c8a243`; the pinned scan records its observation **2026-11-17 19:54:39.227044 UTC**. Neither clock is first-public timing or proof of present access.

[Original receipt URL](https://www.sec.gov/Archives/edgar/data/108772/000119312526460692/0001193125-26-460692.txt) and [submissions metadata endpoint](https://data.sec.gov/submissions/CIK0001770450.json) are source references, not newly requested or newly verified links.

## Safe interpretation and preservation

`web/company-findings/xerox-filing-identity.json` is a separate public annotation. It preserves both source-associated CIKs, header-as-filed names, exact identity-field byte spans/hashes, original and metadata source hashes, and distinct observation clocks. It publishes no contact/address, signature, full paragraph or financial amount. It does not replace existing records or clear historical discrepancy flags. Frozen research reports, ledger, queue identities and source receipts remain unchanged.

The reusable header extractor supports bounded ASCII SEC headers with explicit `FILER → COMPANY DATA → FILING VALUES` structure, one name/CIK pair per filer and unique nonzero 10-digit CIKs. Duplicate fields, duplicate CIKs, unclassified CIKs, ambiguous header structure and unsupported roles fail closed. It does not interpret ownership, legal relationships or document-specific fact attribution. The actual annotation builder pins the ZIP, manifest, original, submissions snapshot and immutable scan receipt; there are no network calls.

```sh
python3 backend/filing_registrant_identity.py \
 --archive PRIVATE_RETAINED_SEC_ORIGINALS_ZIP \
 --root . \
 --out NEW_PRIVATE_OUTPUT_DIRECTORY
```

The private output must be new and outside the checkout. `INCOMPLETE` precedes work; the completed annotation hash is written last. Public app integration is separate and must preserve both CIKs and the limited meaning of co-filing. No training, financial qualification, execution or automatic fact reassignment is enabled.
