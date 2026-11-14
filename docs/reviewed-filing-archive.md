# Bounded original SEC filing recovery

`python3 backend/archive_reviewed_filings.py --reviews data/filing_reviews.json --destination .data/filing-recovery/UNIQUE-RUN`

This manual read-only path takes at most ten distinct reviewed records, derives
SEC URLs from validated CIK/accession values, rejects redirects, waits two seconds
between requests, and performs no retries. HTTP403/429 stops remaining requests.
Limits: 25MB per response and75MB cumulative accepted response bytes per run.
Responses exceeding a bound are not archived and stop the remaining requests. The cumulative threshold can be
exceeded by the final bounded response before the run stops.

Only matching original SEC submission headers are saved as inert content-addressed
text. Each request/result has a receipt; successful bytes retain a new actual
retrieval timestamp and comparison with the earlier recorded source fingerprint.
A changed fingerprint is preserved as a new vintage, not relabelled old evidence.
There are no scores, decision dates, trades or first-public availability claims.

The raw files and journal are local workspace artifacts, **not verified durable
remote storage**. This command does not publish them, alter any schedule, update
the dashboard's public archive counts, or rewrite the previous review/provenance.
Retain the exact directory before using it as evidence; an absent directory must
remain missing. The public readiness report will continue reporting originals
absent until a reviewed durable archive and report integration are provided.

Keep raw recovery directories outside the repository when practical; never stage
`.data` or the recovery ZIP. Only code, tests and this documentation are published.

`accounted_response_bytes_lower_bound` excludes bytes read by an oversized
response rejected inside the transport; it is not an exact network byte total.
