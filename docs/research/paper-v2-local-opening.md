# PAPER_V2 owner-local opening

The new version-2 account has US$500 in virtual opening cash and no real
capital. Account opening is separate from paper-order processing. The new
module cannot admit or process an order, connect to a broker, retrieve market
data, or modify the original November trial. No runtime imports it.

The opener requires a dedicated, freshly provisioned 0700 directory outside
the repository and Pages, with local POSIX file and directory sync and
atomic no-clobber hard links. Verify the environment supports those primitives.
Use read-only status after opening and verify the sealed genesis and opening time
from a new process. The recorded clock is local and not externally authenticated.
Keep an independently retained full genesis digest. A restart or interrupted
initial opening must not initialize a second account.

No automatic reopening after unexplained missing state: stop and reconcile.
The opener can finish sealing a known interrupted first opening at the original
timestamp, but does not establish authenticity, remote durability, or protection
from loss or rollback of the entire local directory. The policy annex is separate
and bound to the exact genesis bytes. Limits describe the prospective policy,
not an active order engine or proof of enforcement by one.

The owner-local read-only portfolio generator accepts the local account directory
and emits a self-contained, no-network HTML snapshot to standard output. Create
the output with owner-only permissions, outside the repository. It is not a
web server or authenticated remote dashboard; regenerate it to refresh. No
account-specific state, reports, or market prices belong in Pages or Git.

Enabled order processing will require an independently reviewed prospective
decision contract, rights and effective-dated security/session evidence, a
declared conservative fill model, and a separately verified durable order
ledger. Existing WATCH and ABSTAIN research records do not create trades. A
cash-only opening balance is not a qualified equity series or performance history.
