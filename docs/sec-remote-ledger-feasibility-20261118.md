# Remote SEC ledger: feasible primitive, unverified production contract

No remote ledger, provider call, schedule, credential or production workflow was created or changed. The deliverable is six local bare-Git contract experiments, not a remote adapter. Existing continuation remains disabled.

## What the existing setup establishes

The connected repository permits ordinary reviewed branch/commit/PR work. On November 18 the public repository rulesets endpoint returned an empty list; querying main branch protection returned HTTP403 `Resource not accessible by integration`. This does not prove protection is absent. It means this connection cannot verify the relevant branch protection. No permission escalation or alternate credential was attempted.

The official [GitHub reference API](https://docs.github.com/en/rest/git/refs#update-a-reference), read during this audit, supports `sha` and `force`; false requests a fast-forward update. It does not document an expected-old-head request field. The connector advertises an additional expected-SHA safeguard, but its server-side atomic implementation is not established by the REST contract. Do not assume a client read/check followed by force update is atomic.

The [contents API](https://docs.github.com/en/rest/repos/contents#create-or-update-file-contents) requires the old blob SHA when replacing a file. That is not, by itself, proof of authenticated complete ledger history, protection against deletion/reset, or ownership of source sending.

## Smallest candidate design, not implemented remotely

A dedicated append-only branch could hold a bounded canonical ledger. Each contender reads a validated head, constructs one child commit with exactly that parent and one appended validated event, then requests a non-force update. Sibling proposals cannot both fast-forward the same branch. After an uncertain acknowledgment, read the authoritative branch and locate the exact candidate and request identity; never create another source request to resolve uncertainty. Persisted unresolved intents remain blocking, without timeout reclamation. Uploaded objects alone are not a reservation.

This needs a controlled writer set, enforced no-force/no-delete policy, authenticated complete history, verified read-after-write semantics and fail-closed outage handling. Those guarantees have not been established for a dedicated remote branch here. Ordinary successful PR publication does not establish them.

## Executed local proof and counterexample

`backend/test_sec_git_append_contract.py` creates only temporary local bare Git repositories. It demonstrates sequential sibling append rejection, local object construction without push not counted as reservation, simulated lost-ack reconciliation, idempotent same-commit retry and unresolved intent surviving a later clock. These are simulated boundary experiments: no process crash is injected, no simultaneous push race is tested, and the unpushed object is never uploaded to the bare remote. A discarded successful push response simulates acknowledgment loss; it does not test a transport timeout. The existing accounting module always returns collection disabled. A sixth test deliberately force-resets the disposable local branch: the ledger disappears. This counterexample shows why cooperative fast-forward writes do not provide protection against privileged resets.

These tests establish local Git behavior and supplied-ledger state-machine behavior only. They do not prove GitHub atomicity, remote durability, credential scope, clock authenticity or a global request budget. They do not issue HTTP calls. No runtime persistence adapter is added.

## Exact blockers and next verification

1. Verify dedicated ledger branch no-force/no-delete enforcement and all permitted/bypass writers through an appropriately authorized administration inspection. Current integration cannot read branch protection; do not work around that denial.
2. Define the authenticated writer/read protocol and validate remote contention, lost acknowledgment and outage behavior on an explicitly approved isolated branch with no collector invocation.
3. Verify all managed consumers use it, inventory unmanaged consumers, and bind persisted reservation to actual-send fencing. Never claim project-wide enforcement for consumers outside that inventory.
4. Confirm ongoing GitHub API/Actions quotas and zero incremental cost for the bounded runner, not merely this local test.
5. Only then independently review any runtime wiring, keeping original trial evidence and controls unchanged.

Given these unresolved guarantees, adding a live remote adapter now would overstate readiness. The next step is verification of the remote writer/protection contract, not more speculative collector code.
