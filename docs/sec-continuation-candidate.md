# Non-operational bounded SEC continuation candidate

Reviewed 2026-11-18. This is an offline preflight and test package, not a collection runner. It does not call providers, reserve attempts, change either repository's workflow, change the original trial gate, or enable collection. Even caller-supplied complete-history assertions cannot make `can_collect` true.

## Exact next window

Proposed: November 23–27, 2026, 06:00–18:59:59 America/New_York, exclusive UTC cutoff November 28 00:00. Original trial ends November 21 00:00 UTC. November 21–22 are Saturday/Sunday; the original weekday-only policy excludes them. November 23 is the next eligible weekday. Candidate slots start November 23 11:17 UTC and end November 27 23:47 UTC.

Production uses `17,47 11-23 16-20 11 *`: thirteen UTC hours times two minutes = 26 slots/day. Candidate preserves those hours/minutes across five weekdays: 130 slots, at most 130 admitted runs and 1,300 source requests for the unchanged ten-issuer universe. These are proposed aggregate ceilings requiring enforcement by a separately reviewed new runner, not limits enforced by existing production code and not promised run counts. Manual and fallback runs must consume the same ceilings, never add to them. Thursday November 26 is a US market holiday; SEC metadata collection is not stock-market session collection and no trading-session outcomes are inferred.

## Verified evidence and policy

- Current public latest receipt blob `88fc0440ce0bf2eff938965f5a19e88c3faccab8`: November 17 19:54:39 UTC, 10/10 source metadata feeds complete. Latest attempted run remains unverified without complete Actions history.
- Current private workflow blob `094a279366d11bfb3972b24d36535df8ff08f35c`: final configured collection November 21 12:10 UTC; pinned public collector `2cc42023deddf3ad275848d6631e59b21ca80680`; hard cutoff November 22 00:00 UTC.
- Current private receipt blob `51daf3312f9bc79d12eb2e370590d0b379fdfe32`: November 17 20:49:18 UTC, 11 saved snapshots, 100 rows each. No raw quotes are included here.
- [SEC fair-access policy](https://www.sec.gov/about/privacy-information) permits rate controls at more than ten requests/second. Current collector spaces source requests by two seconds, identifies approved contact, and stops after denials. That local pacing is not proof of aggregate shared-IP traffic; any denial stays a stop, not a request to switch origin.
- [GitHub Actions billing](https://docs.github.com/en/actions/concepts/billing-and-usage) says standard public GitHub-hosted runners are free. This candidate retains the existing public standard Ubuntu runner; it does not create paid services. Private runner allowance remains account-specific.
- [Alpha Vantage free service](https://www.alphavantage.co/support/api-key/) documents 25 daily calls for most datasets. [Terms](https://www.alphavantage.co/terms_of_service/) limit ordinary use to personal/noncommercial use absent another agreement. Neither establishes this key's external usage or public redistribution permission.

## Before any activation

1. Independently review this candidate and pin the then-current production scanner, gate, admission controller, watchlist and workflow. Reconcile full Actions history with every durable reservation and source receipt. The offline preflight's `complete_history_verified` is an explicit simulation assertion, not a substitute for this audit.
2. Implement a separate bounded continuation runner/policy without removing or rewriting the historical trial gate. It must reuse or extract the existing tested admission rules, not bypass them: owner/main/first-attempt context, approved contact, durable reservation before requests, successful reservation push verification, clean checkout, shared concurrency, no overlapping jobs, 30-minute freshness suppression, one push fallback/day, and unresolved/failed latest receipt stop.
3. Enforce the exact ten-issuer scope and aggregate ceilings before reserving; include schedule, manual and fallback consumers. Preserve 2-second request spacing, no redirect/retry bypass, 403/429 stop, raw hashes, append-only source evidence and separate publication verification. Recheck the cutoff after reservation persistence.
4. Test delayed runs, cutoff races, amended/invalid receipts, scope changes, incomplete history, ceiling exhaustion, source denial, quota/budget uncertainty and failed publication. Independently inspect the new workflow diff before enabling any cron. A continuation beyond this one bounded week needs another review.
5. Status index must show the new reviewed policy and actual receipts without treating projected slots as executions. Preserve the original trial evidence.

## Private-price continuation: blocked

Do not change its pin or dates yet. Remaining prerequisites:

- Account-specific free Actions/storage availability and spending-stop protection are unverified; successful past jobs do not prove future $0 operation.
- Other consumers of the same API key remain unknown. Current budget conservatively reserves eleven calls per run across two known workflows, maximum 22/rolling-24h; that is not a global-key ledger.
- Collector history rejects any individual workflow page of 100 and the combined list of 100; bounded pagination or a durable global reservation ledger needs testing without weakening fail-closed behavior.
- **Additional blocker:** pinned `private_prices.metadata` explicitly assumes the original trial has no exchange holidays and checks the latest session using weekdays only. Extending it across Thanksgiving would misclassify valid data. A verified exchange calendar, holiday/early-close coverage and regression tests are required before updating the pinned collector.
- Structured, secret-safe failure receipts are absent. Preserve stop-on-failure and do not confuse latest successful snapshot with latest attempted collection.
- Keep owner-only repository/privacy rechecks, 13-second spacing, first-attempt-only and no retries/redirects. No public prices or derived returns. Verify continued source entitlement and private-use rights before extension.

Highest-value next step: implement and independently test the separate SEC continuation runner with the above unchanged controls. Private-price activation remains blocked, not silently extended.
