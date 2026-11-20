"""Disposable local process tests; no real journal, dates or publication."""
from contextlib import contextmanager
from functools import partial
import json
import os
from pathlib import Path
import selectors
import stat
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

import research_abstention_journal as journal
import research_abstention_store as store

ROOT = Path(__file__).resolve().parents[1]
RANK = "28e8b1d7b80a34de480ad03e9bdf7a5d18b65fdf5816239968f2f2fd52e6196a"
def inputs(root):
    raw = (root / ("web/trade-ideas/v1/snapshots/" + RANK + ".json")).read_bytes()
    scan = json.loads(raw)
    source = (root / scan["source_pins"]["coherent"]["path"]).read_bytes()
    return dict(command_id="synthetic-durable-store-test", snapshot_raw=raw,
                snapshot_sha256=RANK, thesis_id="research-88f4fe3fecb3853d4c6596aa",
                issuer_cik="0000820318", accession="0001193125-26-467737",
                deadline_utc="2026-11-20T21:00:00Z", reasons=["MISSING_MARKET_DATA"],
                source_bytes={"coherent": source})


class AbstentionStoreTests(unittest.TestCase):
    def setUp(self):
        folder = TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.directory = Path(folder.name)
        self.state = self.directory / "abstentions.ndjson"
        self.args = inputs(ROOT)
        # Only the test harness introduces a synthetic clock.
        self.append_patch = patch.object(
            journal, "append", partial(journal.append, clock=lambda: "2026-11-20T12:00:00Z"))
        self.append_patch.start()
        self.addCleanup(self.append_patch.stop)
        store.initialize(self.directory)

    def append(self, tip=journal.ZERO, **changes):
        return store.append(self.directory, expected_tip=tip, **(self.args | changes))

    @contextmanager
    def child(self, script):
        preamble = ("import json, os, sys\nfrom functools import partial\n"
                    "from pathlib import Path\nimport research_abstention_store as store\n"
                    "import research_abstention_journal as journal\n"
                    "from test_research_abstention_store import inputs, ROOT\n"
                    f"directory = Path({str(self.directory)!r})\n"
                    "journal.append = partial(journal.append, clock=lambda: '2026-11-20T12:00:00Z')\n")
        with subprocess.Popen([sys.executable, "-c", preamble + script],
                              cwd=ROOT / "backend", stdin=subprocess.PIPE,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True) as p:
            try:
                yield p
            finally:
                if p.poll() is None:
                    p.kill()
                    p.wait(timeout=5)

    def test_reopen_restart_duplicate_cas_conflict_and_exact_bytes(self):
        self.assertEqual(store.read(self.directory)["tip_sha256"], journal.ZERO)
        with self.child("print(json.dumps(store.append(directory, expected_tip=journal.ZERO,"
                        " **inputs(ROOT))))\n") as process:
            stdout, stderr = process.communicate(timeout=8)
            self.assertEqual(process.returncode, 0, stderr)
        record = json.loads(stdout)
        old = self.state.read_bytes()
        self.assertEqual(old, journal.encoded(record))
        self.assertEqual(stat.S_IMODE(self.state.stat().st_mode), 0o600)
        self.assertFalse(record["prospective_eligible"])
        self.assertFalse(record["training_ready"])
        self.assertFalse(record["execution_ready"])
        self.assertEqual(store.read(self.directory)["records"], {self.args["command_id"]: record})
        self.assertEqual(self.append(), record)
        self.assertEqual(self.state.read_bytes(), old)
        with self.assertRaisesRegex(ValueError, "idempotency conflict"):
            self.append(reasons=["UNVERIFIED_SECURITY_IDENTITY"])
        with self.assertRaisesRegex(ValueError, "stale tip"):
            self.append(command_id="synthetic-other")
        second = self.append(record["sha256"], command_id="synthetic-other")
        self.assertEqual(self.state.read_bytes(), old + journal.encoded(second))
        self.assertEqual(self.append(), record)  # Lost acknowledgment even after later appends.
        with self.assertRaises(FileExistsError):
            store.initialize(self.directory)
        self.assertEqual(store.read(self.directory)["tip_sha256"], second["sha256"])

    def test_other_process_lock_then_restart(self):
        script = """
with store._locked(directory):
    print("locked", flush=True)
    sys.stdin.readline()
"""
        with self.child(script) as holder:
            try:
                with selectors.DefaultSelector() as sel:
                    sel.register(holder.stdout, selectors.EVENT_READ)
                    self.assertTrue(sel.select(timeout=8), "holder handshake timed out")
                    self.assertEqual(holder.stdout.readline().strip(), "locked")
                with self.assertRaises(store.JournalBusy):
                    self.append()
                with self.assertRaises(store.JournalBusy):
                    store.read(self.directory)
                self.assertEqual(self.state.read_bytes(), b"")
            finally:
                if holder.poll() is None:
                    holder.stdin.close()
                    try:
                        holder.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        holder.kill()
                        holder.wait(timeout=5)
        self.assertEqual(self.append()["sequence"], 1)

    def test_crash_before_rename_leaves_prior_transcript(self):
        prior = self.append()
        old = self.state.read_bytes()
        script = f"""
os.replace = lambda *args, **kwargs: os._exit(23)
store.append(directory, expected_tip={prior["sha256"]!r},
             **(inputs(ROOT) | {{"command_id": "synthetic-crash-before-rename"}}))
"""
        with self.child(script) as process:
            _, stderr = process.communicate(timeout=8)
            self.assertEqual(process.returncode, 23, stderr)
        self.assertEqual(self.state.read_bytes(), old)
        self.assertEqual(store.read(self.directory)["tip_sha256"], prior["sha256"])
        self.assertEqual(len(list(self.directory.glob(".abstentions-*.tmp"))), 1)
        result = self.append(prior["sha256"], command_id="synthetic-crash-before-rename")
        self.assertEqual(self.state.read_bytes(), old + journal.encoded(result))

    def test_lost_ack_after_replace_actual_process_exit(self):
        script = """
store._sync_visible = lambda dfd: os._exit(24)
store.append(directory, expected_tip=journal.ZERO, **inputs(ROOT))
"""
        with self.child(script) as process:
            _, stderr = process.communicate(timeout=8)
            self.assertEqual(process.returncode, 24, stderr)
        visible = self.state.read_bytes()
        record = self.append()
        self.assertEqual(self.state.read_bytes(), visible)
        self.assertEqual(store.read(self.directory)["records"], {self.args["command_id"]: record})

    def test_temp_sync_failure_preserves_prior(self):
        with patch.object(os, "fsync", side_effect=OSError("synthetic temp sync error")):
            with self.assertRaisesRegex(OSError, "temp sync"):
                self.append()
        self.assertEqual(self.state.read_bytes(), b"")
        self.assertEqual(list(self.directory.glob(".abstentions-*.tmp")), [])
        self.assertEqual(self.append()["sequence"], 1)

    def test_uncertain_after_replace_requires_resync_on_duplicate_retry(self):
        real_fsync = os.fsync

        def fail_directory(fd):
            if stat.S_ISDIR(os.fstat(fd).st_mode):
                raise OSError("synthetic directory sync error")
            real_fsync(fd)

        with patch.object(os, "fsync", side_effect=fail_directory):
            with self.assertRaises(store.CommitUncertain):
                self.append()
            visible = store.read(self.directory)
            self.assertEqual(len(visible["records"]), 1)
            old = self.state.read_bytes()
            with self.assertRaises(store.CommitUncertain):
                self.append()  # Seeing the old record is not enough to acknowledge.
            self.assertEqual(self.state.read_bytes(), old)
        with patch.object(os, "replace", side_effect=AssertionError("retry must not rewrite")):
            result = self.append()
        self.assertEqual(result, visible["records"][self.args["command_id"]])
        self.assertEqual(self.state.read_bytes(), old)

    def test_dangling_symlink_fifo_and_nonprivate_files_fail_closed(self):
        self.state.unlink()
        self.state.symlink_to(self.directory / "missing")
        with self.assertRaises(OSError):
            store.read(self.directory)
        with self.assertRaises(FileExistsError):
            store.initialize(self.directory)
        self.state.unlink()
        os.mkfifo(self.state, 0o600)
        with self.assertRaisesRegex(ValueError, "regular"):
            store.read(self.directory)
        self.state.unlink()
        self.state.touch(mode=0o644)
        self.state.chmod(0o644)
        with self.assertRaisesRegex(ValueError, "owner-only"):
            store.read(self.directory)
        self.state.chmod(0o600)
        (self.directory / "second-name").hardlink_to(self.state)
        with self.assertRaisesRegex(ValueError, "unlinked"):
            store.read(self.directory)

    def test_corrupt_oversized_and_deleted_transcript_not_reinitialized(self):
        self.append()
        old = self.state.read_bytes()
        for raw in (old[:-1], b"\n", b"\n" * 257, b"x" * 2_000_001):
            self.state.write_bytes(raw)
            with self.assertRaises((ValueError, TypeError)):
                self.append()
            self.assertEqual(self.state.read_bytes(), raw)
        self.state.unlink()
        with self.assertRaises(FileNotFoundError):
            self.append()
        with self.assertRaises(FileExistsError):
            store.initialize(self.directory)
        self.assertFalse(self.state.exists())
        self.assertTrue((self.directory / "writer.lock").is_file())

    def test_missing_stable_lock_never_recreated_over_existing_transcript(self):
        self.append()
        original = self.state.read_bytes()
        lock = self.directory / "writer.lock"
        lock.unlink()
        with self.assertRaises(FileNotFoundError):
            self.append()
        with self.assertRaises(FileExistsError):
            store.initialize(self.directory)
        self.assertFalse(lock.exists())
        self.assertEqual(self.state.read_bytes(), original)

    def test_no_clock_override_and_reject_bad_tips(self):
        with self.assertRaisesRegex(ValueError, "caller clock"):
            self.append(clock=lambda: "2026-11-20T12:00:00Z")
        for malformed in (None, 0, "", "A" * 64, "0" * 63):
            with self.assertRaisesRegex(ValueError, "expected tip"):
                self.append(malformed)
        self.assertEqual(self.state.read_bytes(), b"")
