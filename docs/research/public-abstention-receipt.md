# Public timestamp check for a research abstention

This research-only verifier can establish that the exact bytes of an ABSTAIN
record existed by the creation of a GitHub Actions run. It does not prove the
instant an analyst first decided, the time a filing first became public, a
broker or audit timestamp, or the existence of a market price or fill.

## Review protocol

1. Freeze the eligibility policy and future cutoff independently of the
   candidate. Create a canonical, standalone ABSTAIN record from the
   reviewed ranking snapshot and exact source bytes. Record the actual
   writing clock; never substitute the ranking cutoff or a filing clock.
2. Place the record under `research/abstention-freezes/<full SHA-256>.json`
   on an isolated `work/research-freeze-*` branch. Ordinary repository CI
   may run. No workflow, collectors, execution gates or ledger are changed.
3. An independent reader checks the first-attempt **push** run against the
   exact repository, workflow and commit. Read the immutable Git tree and
   regular file for that commit using the authenticated GitHub API. Use the
   independently preserved cutoff and full-record hash, not values acquired
   solely from the record being verified.
4. Check that GitHub's run creation is strictly before the cutoff. Store
   this receipt separately; never inject it into the archived decision
   that the receipt binds. If a valid event is missing, late or ambiguous,
   do not promote any timing or performance claim.

The verifier consumes a trusted read-only API adapter; it makes no
network request itself, and it cannot authenticate offline JSON supplied
by an untrusted decision author. A successful CI run is reported
separately from the byte-and-time binding. There is no trading, market
data, score change, outcome calculation or automatic promotion in this
protocol. The earlier retrospective ranking and separate Coherent
close-to-close coverage checkpoint are unchanged.
