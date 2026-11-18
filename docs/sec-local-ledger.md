# Local-only durable SEC accounting adapter

`backend/sec_local_ledger.py` adds offline persistence for the reviewed accounting state machine. It makes **no HTTP requests**, imports no collector, changes no schedule/gate and always reports `collection_enabled=false`. This is not the remote GitHub ledger or production runner needed for scheduled continuation.

## Narrow guarantee

For cooperating processes using the same trusted owner-only **local POSIX filesystem**, `append` obtains an exclusive `flock`, rereads and validates the complete bounded ledger, compares the expected tip, validates exactly one appended event, and persists a new full snapshot. It fsyncs a private temporary file, atomically replaces `ledger.json`, fsyncs the directory and verifies readback before acknowledging local persistence. Two competing processes with the same expected tip cannot both append successfully. Existing event prefixes are never changed by the API.

The only persistence acknowledgment is `persisted_locally=true`; `remote_persistence_verified` and `collection_enabled` remain false. Atomic rename, working locks and honest fsync/storage behavior are prerequisites, not properties independently certified by this code. Network filesystems, cross-host locks, Windows, malicious owners, administrator edits, snapshot rollback and external source consumers are outside this guarantee. A lost ephemeral workspace is still lost evidence; local fsync is not a durable remote archive.

## Crash and failure handling

- Crash before replacement: old snapshot remains; an owner-only `.pending-*` temporary may remain. It contains no committed intent and is never read as the ledger. Cleanup is not automatic and no provider call was authorized.
- Crash after replacement or a failed/lost acknowledgment: the new snapshot may already exist. Reread and reconcile; never blindly replay a request. A persisted unresolved intent remains blocked by the accounting state machine.
- Process crash tests verify actual `os._exit` behavior at file-sync, replacement and directory-sync boundaries. They do **not** simulate power loss or certify hardware write caches.
- A directory-sync failure never returns a success acknowledgment, even if readback later sees the new intent. Such an observation is not proof of crash durability; production recovery needs separate review.
- The initialization API only creates a new directory and refuses overwrite. Incomplete initialization, missing ledger, symlinks, nonprivate permissions, linked files, corrupted JSON, invalid hashes, stale tips and invalid events fail closed. Parent directories must be trusted and stable; this does not defend against a privileged actor replacing ancestors or the lock inode.

## Interface

`initialize(new_root)` creates the owner-only store. `inspect(root, as_of)` returns the supplied local history and replay state under the lock. `append(root, expected_tip, event, as_of)` accepts a candidate from the offline accounting layer and acknowledges only local persistence. Caller time and source hashes remain assertions; no source result is independently authenticated by storage. No implicit lease expiry, ledger-reset recovery or quota refund exists.

Tests cover real competing processes, killed workers at three boundaries, directory-sync failure, stale expected tips, mutation rejection, incomplete stores, duplicate JSON, permissions and ledger/lock symlinks, hardlinks and FIFOs. File opens are nonblocking before the regular-file check so an unexpected FIFO cannot stall the operation while holding the lock. They use synthetic events only.

## Still required before any collector activation

A separately reviewed remote durable CAS implementation with a trusted checkpoint/history, complete managed-consumer scope, actual-send time/cutoff/spacing checks, source identity/receipt verification, shared runner concurrency and safe lost-acknowledgment recovery remains necessary. The original trial continues unchanged; this local adapter cannot extend it or claim global SEC request enforcement. Never wire an existing source request directly to a successful local append without that independent end-to-end review.
