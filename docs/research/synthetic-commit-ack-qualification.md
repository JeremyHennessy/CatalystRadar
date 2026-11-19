# Synthetic commit/acknowledgment process-boundary qualification

Local-only test package based on public main `7b0965cf`. It adds no execution
module, collector, quote source, schedule, ledger adapter or UI. The existing
`synthetic_paper.py` and test-only SQLite `JournalFixture` remain unchanged.
All SQLite files are disposable temporary fixtures; all identifiers are synthetic.

## New boundary covered

Existing restart tests simulated a lost acknowledgment by ignoring a method return
and killed a process before commit. The new tests use independent spawned Python
processes to cover:

1. A partial fill commits and then its process exits abruptly with code 23 before
   delivering any result. A fresh fixture reopens the database, verifies the
   committed chain and resolves repeated retries to the same exact record.
   A subsequent cancellation releases only the remaining reservation. A late retry
   after cancellation returns the original acknowledged prefix, not the latest
   journal tip; callers must separately reread the authoritative journal. A changed
   fee on that old command is rejected, leaving the newer tip unchanged.
2. Two processes released by a shared barrier submit the identical command against
   the same acknowledged prefix. Both receive the same record; storage has exactly
   one added record, one fee charge and one partial fill.
3. Two individually valid but distinct fill commands compete for that same next
   index. Exactly one commits and the other conflicts. Winner order is deliberately
   unspecified. No automatic rebasing or second fill occurs.

Each case independently checks synthetic cash, held quantity, remaining cost,
fees and reservations. The 500-unit starting account, 4-unit fill at 9 per unit,
and 0.04 fee leave cash 463.96, position cost 36.04 and remaining reservation
60.06. Cancellation changes the reservation to zero, not cash or owned quantity.
Amounts in the tests use integer millionths of synthetic currency.

## Stop and fill ordering after restart

Three additional tests cover a committed stop racing a synthetic partial fill.
Each only uses the same disposable SQLite fixture and accounting reducer:

* **Stop commits first, acknowledgment is lost.** Restart recovers the stop.
  An identical retry acknowledges the existing record. The competing fill
  conflicts against the old prefix and still fails if submitted against the
  recovered tip. Cash stays at 500, with no fee or position.
* **Fill commits first, acknowledgment is lost.** A stop against the old prefix
  conflicts. Submitting the stop against the verified current tip latches it
  without reversing the earlier fill. A late fill retry retrieves its original
  acknowledgment without recording a second fill.
* **Two processes contend for the same next record.** Exactly one can commit.
  Neither has implicit priority. If the fill wins, the caller must verify the
  new tip and explicitly submit the stop again; a conflicting stop must never
  be reported as latched.

In either order, a latched stop survives restart, rejects subsequent fills and
does not itself cancel orders. Explicit cancellation releases the remaining
reservation without changing cash, holdings, cost or fees. This is a local
journal ordering guarantee, not an emergency-stop latency or broker guarantee.

## Limits

This qualifies the existing fixture under this local filesystem/SQLite/process
configuration only. The barrier synchronizes contenders before submission but
SQLite intentionally serializes the transaction; this is not a throughput test.
The post-commit exit occurs after the fixture's submit method returns inside the
child and before the parent receives a result. It is not an injected power loss,
hardware durability proof, network timeout, remote service acknowledgment, or
proof of multi-host correctness. A trusted retained prefix remains required;
these tests do not add external anchoring, rollback protection or authenticated
writer ownership. They do not make synthetic fills real, admit market data,
authorize orders or alter the protected paper book.

Run `python3 -m unittest discover -s backend -p test_synthetic_commit_ack.py -v`.
Children have bounded barriers/joins and are terminated on a join failure. No
provider request, permanent artifact or remote publication is made by the tests.
