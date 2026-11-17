# Bounded collection fallback, not a scheduler repair claim

GitHub's configured cron remains unchanged. An observed successful manually dispatched run proves the collector/secret/publication path works, not automatic scheduling. This alternative uses existing authenticated repository write access and a root assistant wake; no new service, credentials, spend, provider endpoint or trade capability.

## Request contract

An authorized controller checks current main, all queued/in-progress/waiting observation runs, latest receipt and prior reservations first. If fresh complete observation exists or any unresolved attempt/source refusal exists, do not request another scan. At most one fallback attempt per New York date is admitted. Failed/ambiguous requests must not be resubmitted automatically.

Create a single-parent commit changing **only** `data/sec-control/request.json` on `main`, using compare-and-swap on the previously checked main SHA. Sender/GITHUB_ACTOR must be `JeremyHennessy`. The request has exactly these fields:

```json
{
  "version": 1,
  "purpose": "PUBLIC_SEC_OBSERVATION_ONLY",
  "requested_at": "ACTUAL_CURRENT_UTC_ISO_TIMESTAMP",
  "expires_at": "UTC_TIMESTAMP_AT_MOST_15_MINUTES_LATER",
  "session": "ACTUAL_AMERICA_NEW_YORK_DATE"
}
```

The placeholders are not a valid request. No request file is created by this implementation release. Both timestamps must fall in the existing Nov16–20,2026 06:00–18:59:59 New York observation gate. Expired requests stop; there is no backdating. For pretrade observation, the root wake should be well before08:00 NY and set expiry before that cutoff; this observation path never authorizes or places orders regardless of timing.

A push to any other path does not trigger collection. A request commit that has been superseded by the time checkout occurs, is a merge commit, contains other changed paths, or has an unapproved actor fails closed. The observer bot's reservation/result commits do not change the request path and cannot create a loop. Existing shared concurrency serializes all schedule/manual/push observation runs.

## Durable reservation and denial handling

All three triggers use the same admission controller. A complete observation less than30minutes old skips collection. An incomplete latest scan (including403/429) blocks automatic collection until an explicit reviewed resolution; it is never retried through another trigger. An unresolved earlier reservation also blocks new collection. Historical failed scans before a later successful authorized scan do not poison current state.

Before any SEC request, append `data/sec-control/attempts/<github-run-id>.json`, commit and non-force push it to main. A failed push never calls the scanner. Confirm remote main equals this reservation commit, then recheck timing before calling the bounded scanner. A later complete immutable scan receipt with the same run URL/event and a start no earlier than reservation resolves the attempt. Failed tests, conflicts, cancellation or build failure can leave an unresolved reservation; investigate rather than deleting it or retrying blindly. Git history is durable evidence under existing repository controls, not immutable storage or an independently trusted clock.

The fallback quota is counted from committed reservations, including failed attempts. Successful normal scheduled scans remain available after the freshness window. Reservations and source receipts are public allowlisted operational metadata, with no email or private quotes. No raw private data, report regeneration or ledger edits are introduced.

## Verification and limitations

Verify exact request commit, run event=`push`, durable reservation, source HTTP/identity/hash checks, immutable receipt, main commit and live Pages bytes. The dashboard explicitly labels this a request-triggered fallback and continues to say scheduled execution is unverified. A green workflow may have skipped because of freshness or time window; it is not proof of a new scan.

GitHub push delivery and the root wake are still external dependencies, not a guaranteed SLA. This method must be proven by one authorized genuine request before calling it operational. Never create fake source observations, weaken gates or fabricate a historical freeze to compensate for delayed data. Source failure, unsupported execution/corporate-action/halt evidence, or a missed prospective decision cutoff still means no trade.
