"""Research-only verification of a public GitHub Actions creation receipt.

The caller must obtain responses directly from GitHub over authenticated
transport, not from the decision author, an uploaded transcript, or a browser
clock. Run creation bounds existence of exact bytes; it is not push time, event
time, an independent timestamp authority, or a proof of trading readiness.
Nothing here writes, dispatches, evaluates outcomes, or promotes ledger state.
"""
import base64
import binascii
import hashlib
import re
from urllib.parse import urlencode

import research_abstention_journal as journal

REPO = "JeremyHennessy/CatalystRadar"
REPO_ID = 1457970410
OWNER_ID = 23260892
WORKFLOW_ID = 418487000
WORKFLOW_PATH = ".github/workflows/ci.yml"
WORKFLOW_BLOB = "ac1a2cc40736be5dc16f313f2d643f5159110632"
_NAMESPACE = "/repos/" + REPO
_SHA1 = re.compile(r"[a-f0-9]{40}")
_SHA256 = re.compile(r"[a-f0-9]{64}")
_BRANCH = re.compile(r"work/research-freeze-[a-z0-9-]{1,48}")


def _digest(pattern, value):
    return type(value) is str and pattern.fullmatch(value) is not None


def _exact_id(value, expected):
    return type(value) is int and value == expected


def _repository(record):
    return (type(record) is dict and record.get("full_name") == REPO
            and _exact_id(record.get("id"), REPO_ID) and record.get("private") is False)


def _git_path(fetch, tree_sha, path, cache):
    parts = path.split("/")
    for index, part in enumerate(parts):
        if tree_sha not in cache:
            tree = fetch(_NAMESPACE + "/git/trees/" + tree_sha)
            if (type(tree) is not dict or tree.get("sha") != tree_sha
                    or tree.get("truncated") is not False or type(tree.get("tree")) is not list
                    or len(tree["tree"]) > 10000 or any(type(x) is not dict for x in tree["tree"])):
                raise ValueError("unverified Git tree")
            cache[tree_sha] = tree["tree"]
        matches = [entry for entry in cache[tree_sha] if entry.get("path") == part]
        if len(matches) != 1 or not _digest(_SHA1, matches[0].get("sha")):
            raise ValueError("unverified Git tree path")
        item = matches[0]
        if index < len(parts) - 1:
            if (item.get("type"), item.get("mode")) != ("tree", "040000"):
                raise ValueError("non-directory Git tree path")
            tree_sha = item["sha"]
        elif (item.get("type"), item.get("mode")) == ("blob", "100644"):
            return item["sha"]
        else:
            raise ValueError("not an ordinary Git file")
    raise ValueError("empty Git path")


def _file(fetch, path, ref, expected_blob, max_bytes):
    # Every path is either a constant or composed of a previously checked digest.
    data = fetch(_NAMESPACE + "/contents/" + path + "?" + urlencode({"ref": ref}))
    if (type(data) is not dict or data.get("type") != "file"
            or data.get("path") != path or data.get("encoding") != "base64"
            or data.get("sha") != expected_blob
            or type(data.get("size")) is not int or not 0 < data["size"] <= max_bytes):
        raise ValueError("unverified GitHub file response")
    encoded = data.get("content")
    if type(encoded) is not str or len(encoded) > 2 * max_bytes:
        raise ValueError("invalid receipt blob encoding")
    try:
        raw = base64.b64decode(encoded.replace("\n", ""), validate=True)
    except (ValueError, binascii.Error):
        raise ValueError("invalid receipt blob encoding") from None
    git_hash = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
    if len(raw) != data["size"] or git_hash != data["sha"]:
        raise ValueError("Git receipt blob mismatch")
    return raw, git_hash


def verify(*, fetch, run_id, head_sha, branch, record_sha256, expected_deadline,
           checked_at, snapshot_raw, source_bytes):
    """Verify one stand-alone ABSTAIN record against separately reviewed pins.

    `fetch` is a trusted GET adapter for exact GitHub REST endpoints and must
    reject redirects and stale/offline substitutions. Pass reviewed deadline,
    expected full record hash, exact head/ref and independently observed UTC
    verification time, not values chosen by untrusted receipt data.
    """
    if (type(run_id) is not int or not 0 < run_id < 10**20
            or not _digest(_SHA1, head_sha) or not _digest(_SHA256, record_sha256)
            or not _digest(_BRANCH, branch)):
        raise ValueError("invalid receipt identity")
    deadline = journal.instant(expected_deadline)
    checked = journal.instant(checked_at)
    run = fetch(_NAMESPACE + "/actions/runs/" + str(run_id))
    if (type(run) is not dict or not _exact_id(run.get("id"), run_id)
            or not _repository(run.get("repository"))
            or not _repository(run.get("head_repository"))
            or run.get("event") != "push" or not _exact_id(run.get("run_attempt"), 1)
            or not _exact_id(run.get("workflow_id"), WORKFLOW_ID)
            or run.get("path") != WORKFLOW_PATH
            or run.get("head_sha") != head_sha or run.get("head_branch") != branch
            or type(run.get("actor")) is not dict
            or not _exact_id(run["actor"].get("id"), OWNER_ID)):
        raise ValueError("unverified GitHub run identity")
    created = journal.instant(run.get("created_at"))
    if not created < deadline or created > checked:
        raise ValueError("late or future GitHub run creation")
    commit = fetch(_NAMESPACE + "/git/commits/" + head_sha)
    if (type(commit) is not dict or commit.get("sha") != head_sha
            or not isinstance(commit.get("tree"), dict)
            or not _digest(_SHA1, commit["tree"].get("sha"))):
        raise ValueError("unverified GitHub commit identity")
    root = commit["tree"]["sha"]
    trees = {}
    wf_sha = _git_path(fetch, root, WORKFLOW_PATH, trees)
    if wf_sha != WORKFLOW_BLOB:
        raise ValueError("unreviewed GitHub workflow")
    path = "research/abstention-freezes/" + record_sha256 + ".json"
    blob_sha = _git_path(fetch, root, path, trees)
    raw, _ = _file(fetch, path, head_sha, blob_sha, 16384)
    if journal.sha(raw) != record_sha256:
        raise ValueError("full decision hash mismatch")
    state = journal.replay([raw])
    record = next(iter(state["records"].values()))
    command = record["command"]
    logged = journal.instant(record["recorded_utc"])
    if (command["receipt_pin"] is not None or command["deadline_utc"] != expected_deadline
            or record["timing_status"] != "LOCAL_CLOCK_BEFORE_DEADLINE_UNAUTHENTICATED"
            or logged > created):
        raise ValueError("unqualified research decision clock or circular receipt")
    rebuilt = journal.command(
        command_id=command["command_id"], snapshot_raw=snapshot_raw,
        snapshot_sha256=command["snapshot_sha256"], thesis_id=command["thesis_id"],
        issuer_cik=command["issuer_cik"], accession=command["accession"],
        source_bytes=source_bytes, deadline_utc=expected_deadline, reasons=command["reasons"],
    )
    if rebuilt != command:
        raise ValueError("decision does not match pinned research evidence")
    return {
        "status": "EXACT_ABSTENTION_BYTES_EXISTED_BY_GITHUB_RUN_CREATION",
        "decision": "ABSTAIN",
        "run_id": run_id,
        "head_sha": head_sha,
        "record_path": path,
        "record_sha256": record_sha256,
        "record_git_blob_sha": blob_sha,
        "workflow_git_blob_sha": wf_sha,
        "server_created_at": run["created_at"],
        "verified_at": checked_at,
        "deadline_utc": expected_deadline,
        "ci_success_observed": run.get("status") == "completed" and run.get("conclusion") == "success",
        "trading_ready": False,
        "outcome_qualified": False,
    }
