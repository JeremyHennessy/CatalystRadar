# New-issuer revenue evidence review sample

Five inspectable review packets extend beyond the existing 108-company queue: Abbott Laboratories, Acme United, Advanced Micro Devices, Air Products & Chemicals, and CECO Environmental. These are historical SEC prepared-data candidates, **not qualified comparable revenue results or growth signals**. The existing queue and its dossier pages are unchanged. App integration is separate from publishing this evidence file.

## Selection fixed before inspecting selected values

Local retrospective policy v2 SHA256 `d8d6fc6fb315c42762a6421e04ba37302454423b2c7f5a677d2e426f71624782` was frozen before the selected identities and values were inspected. This is reproducible local ordering, not independently authenticated preregistration, unbiased sampling or prospective availability.

Starting with four completed 2025 Q4–2026 Q3 **filing-batch** pair artifacts:

1. Restrict to standard `Revenues` or `RevenueFromContractWithCustomerExcludingAssessedTax` candidates admitted by the earlier narrow context matcher.
2. Exclude normalized exact CIKs present in the pinned v3 108-company queue. Do not match names or tickers.
3. Choose the five smallest numeric remaining CIKs.
4. For each, choose the most recent filing date **among these retained candidate batches only**. Break ties lexically by accession, tag, taxonomy, batch, submission period, both reported context dates, quarters, units, segments, co-registrants, and finally numeric row IDs. Reject duplicate complete identities. Never select on amount, sign, numerical difference or performance.
5. Do not replace a chosen issuer if original/context review is blocked.

The 40,628 input candidate pairs split into 29,158 other-metric exclusions, 336 pairs associated with the existing queue, and 11,134 eligible revenue pairs across 3,841 CIKs. Five pairs are selected; 11,129 eligible pairs and 3,836 eligible CIKs are not selected. These are different counting units. They are not a full SEC company universe. Original upstream NUM-row exclusions and group dispositions for every batch remain in the public packet summary and pinned completed inputs. Earlier rejected or unsupported contexts were never in the candidate universe.

## What was actually verified

For each selected pair, the retained Q3 financial database and original SEC prepared ZIP were hash-checked before and after read-only processing. The two NUM records, unique SUB record, unique standard monetary TAG record and every associated PRE record were compared field-for-field against the original TSV rows. The original context classifier was rerun against all matching same-filing numeric contexts, rejecting duplicate, dimensional, unit, footnote, taxonomy or submission inconsistencies. Raw decimal strings are preserved, not rounded, rescaled or converted.

Public packets include the two reported USD values, standard taxonomy, exact accession and CIK, source filing/report/fiscal fields, prepared presentation context, row identifiers and full-source-row hashes. Full SUB addresses and other unnecessary fields, taxonomy narrative text, owner information and source contacts are excluded. A row hash can bind omitted source fields without publishing them. Row hashes use the full parsed TSV field dictionary serialized as sorted-key, ASCII-escaped compact JSON plus one newline; they are not hashes of original TSV byte spans. Archive and member hashes bind the original bytes separately.

All five selected candidates happen to be in the retained Q3 filing batch. Their `ddate` context keys are June 30, 2026 and June 30, 2025. **These are prepared reported/rounded context dates, not independently verified exact period ends.** `qtrs=1` does not establish exact start dates, duration, fiscal calendar or comparable accounting scope. The filing batch is not a label for the fiscal quarter represented by a value. Empty segment/co-registrant strings do not prove consolidated scope. A taxonomy label does not prove that two revenue concepts are interchangeable.

## Concrete blocker and next action

Each selected accession was checked against the explicit retained original inventory: ten archived 8-K submissions and one original inline-XBRL package. None matched. This is narrowly **no exact accession in that checked inventory**, not proof that no original exists elsewhere or that an SEC URL is unavailable. The source accession index URLs are constructed from validated identifiers and were not fetched during this task.

The next action for each packet is to inspect that exact original filing's statements and XBRL contexts, establishing actual start/end dates, unit, entity/consolidation scope and comparative presentation. Until then, original-text review, consolidated scope and comparability remain false; exact period start, first-public/first-observed availability, absolute change and percentage change remain null. No growth or current-catalyst claim is made.

The most-recent retained candidate is not declared the correct/reconciled version. Other candidate pairs for each selected issuer remain counted and preserved in pinned inputs, including any competing filings or revisions. They are not collapsed, overwritten, declared equivalent, or exhaustively reconciled by this sample. Counts of those pairs are not counts of unique filings or independent events.

## Reproduce and consume

`backend/revenue_review_sample.py` takes the pinned private policy, four completed candidate directories, explicit database/archive path mappings and the two scoped original-package inputs. Example invocation with locally authorized retained paths:

```
python3 backend/revenue_review_sample.py \
  --root . --workspace /trusted/retained \
  --plan-path /trusted/retained/policy-v2.json --plan-sha d8d6fc6fb315c42762a6421e04ba37302454423b2c7f5a677d2e426f71624782 \
  --databases /trusted/retained/database-paths.json --archives /trusted/retained/archive-paths.json \
  --original-zip /trusted/retained/ten-originals.zip \
  --original-receipt /trusted/retained/xbrl-receipt.json --original-package /trusted/retained/original-xbrl.zip \
  --output-directory /trusted/retained/new-revenue-review
```

The output must be new and outside the checkout under a trusted existing parent. It is private by default (directory 0700/files 0600), with `INCOMPLETE` before processing and `COMPLETE.json` only after successful persistence. Do not publish incomplete output. The reviewed public projection is `web/company-findings/revenue-review-sample.json`; policy and source hashes make its scope explicit. It contains no live provider retrieval or refresh promise. A consuming UI must pin bytes/hash, validate exact CIK/accession associations, render labels inertly and retain all candidate/unknown qualifiers. This publication does not admit training samples or enable simulation/trading.
