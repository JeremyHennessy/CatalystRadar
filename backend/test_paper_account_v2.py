"""Disposable local tests only. No provisioned account or market evidence."""
from contextlib import contextmanager
from datetime import datetime, timezone
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

import paper_account_v2 as account


class PaperAccountV2Tests(unittest.TestCase):
    def setUp(self):
        folder = TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.directory = Path(folder.name)
        self.path = self.directory / "genesis-v2.json"
        self.seal = self.directory / "opening-v2.seal"

    @contextmanager
    def child(self, script):
        pre = ("from pathlib import Path\nimport json, os, sys\n"
               "import paper_account_v2 as account\n"
               f"directory=Path({str(self.directory)!r})\n")
        with subprocess.Popen([sys.executable, "-c", pre + script],
                              cwd=Path(__file__).parent, stdin=subprocess.PIPE,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True) as p:
            try:
                yield p
            finally:
                if p.poll() is None:
                    p.kill()
                    p.wait(timeout=5)

    def test_read_never_creates_and_open_uses_actual_clock(self):
        with self.assertRaises(FileNotFoundError):
            account.read_status(self.directory)
        self.assertEqual(list(self.directory.iterdir()), [])
        before = datetime.now(timezone.utc)
        status = account.open_account(self.directory)
        after = datetime.now(timezone.utc)
        opened = datetime.fromisoformat(status["opened_utc"].replace("Z", "+00:00"))
        self.assertLessEqual(before, opened)
        self.assertLessEqual(opened, after)
        self.assertEqual(status, {
            "version": 2, "account": "PAPER_V2", "account_state": "OPEN",
            "readiness": "AWAITING_MARKET_DATA", "opening_cash_cents": 50000,
            "cash_cents": 50000, "currency": "USD", "opened_utc": status["opened_utc"],
            "clock_basis": "LOCAL_SYSTEM_CLOCK_NOT_AUTHENTICATED", "order_count": 0,
            "fill_count": 0, "position_count": 0, "realized_pnl_cents": None,
            "execution_enabled": False, "brokerage_connected": False,
        })
        self.assertEqual(stat.S_IMODE(self.path.stat().st_mode), 0o600)
        before_bytes = self.path.read_bytes()
        with self.child("print(json.dumps(account.read_status(directory)))\n") as process:
            stdout, stderr = process.communicate(timeout=8)
            self.assertEqual(process.returncode, 0, stderr)
        self.assertEqual(json.loads(stdout), status)
        self.assertEqual(account.open_account(self.directory), status)
        self.assertEqual(self.path.read_bytes(), before_bytes)

    def test_simultaneous_publications_converge_without_overwrite(self):
        script = """real_link = os.link
def contested(*args, **kwargs):
    if args[1] == 'genesis-v2.json':
        print('ready', flush=True)
        sys.stdin.readline()
    return real_link(*args, **kwargs)
os.link = contested
print(json.dumps(account.open_account(directory)), flush=True)
"""
        with self.child(script) as first, self.child(script) as second:
            for child in (first, second):
                with selectors.DefaultSelector() as sel:
                    sel.register(child.stdout, selectors.EVENT_READ)
                    self.assertTrue(sel.select(timeout=8), "contender handshake timed out")
                    self.assertEqual(child.stdout.readline().strip(), "ready")
            results = []
            for child in (first, second):
                out, err = child.communicate(input="go\n", timeout=8)
                self.assertEqual(child.returncode, 0, err)
                results.append(json.loads(out))
        self.assertEqual(results[0], results[1])
        self.assertEqual(account.read_status(self.directory), results[0])
        self.assertEqual(set(self.directory.iterdir()), {self.path, self.seal})
        self.assertEqual(self.path.stat().st_ino, self.seal.stat().st_ino)

    def test_crash_before_link_is_not_an_opening(self):
        with self.child("""os.link = lambda *args, **kwargs: os._exit(23)
account.open_account(directory)
""") as p:
            _, stderr = p.communicate(timeout=8)
            self.assertEqual(p.returncode, 23, stderr)
        with self.assertRaises(FileNotFoundError):
            account.read_status(self.directory)
        self.assertEqual(len(list(self.directory.glob("*.tmp"))), 1)
        self.assertEqual(account.open_account(self.directory)["account_state"], "OPEN")

    def test_lost_ack_after_link_preserves_exact_genesis(self):
        with self.child("""real_link = os.link
def crash(*args, **kwargs):
    real_link(*args, **kwargs)
    os._exit(24)
os.link = crash
account.open_account(directory)
""") as p:
            _, stderr = p.communicate(timeout=8)
            self.assertEqual(p.returncode, 24, stderr)
        exact = self.path.read_bytes()
        with self.assertRaisesRegex(ValueError, "seal is missing"):
            account.read_status(self.directory)
        winner = account.open_account(self.directory)
        with patch.object(os, "link", side_effect=AssertionError("must not republish")):
            self.assertEqual(account.open_account(self.directory), winner)
        self.assertEqual(self.path.read_bytes(), exact)

    def test_failed_directory_fsync_is_not_acknowledged(self):
        real = os.fsync

        def fail(fd):
            if stat.S_ISDIR(os.fstat(fd).st_mode) and self.seal.exists():
                raise OSError("synthetic loss of final directory sync")
            real(fd)

        with patch.object(os, "fsync", side_effect=fail):
            with self.assertRaises(account.OpeningUncertain):
                account.open_account(self.directory)
            winner = account.read_status(self.directory)
            with self.assertRaises(account.OpeningUncertain):
                account.open_account(self.directory)
        self.assertEqual(account.open_account(self.directory), winner)

    def test_corrupt_or_changed_policy_state_is_not_repaired(self):
        original = account.open_account(self.directory)
        raw = self.path.read_bytes()
        for damaged in (raw[:-1], raw.replace(b'"status":', b'"status":null,"status":', 1),
                        raw.replace(b"50000", b"50001", 1),
                        account._envelope(original | {"cash_cents": 0}),
                        account._envelope(original | {"order_count": False}),
                        account._envelope(original | {"execution_enabled": True}),
                        b"x" * 2049):
            self.path.write_bytes(damaged)
            with self.assertRaises(ValueError):
                account.read_status(self.directory)
            with self.assertRaises(ValueError):
                account.open_account(self.directory)
            self.assertEqual(self.path.read_bytes(), damaged)
        self.path.unlink()
        with self.assertRaisesRegex(ValueError, "genesis is missing"):
            account.read_status(self.directory)
        with self.assertRaisesRegex(ValueError, "genesis is missing"):
            account.open_account(self.directory)
        self.assertFalse(self.path.exists())
        self.assertTrue(self.seal.exists())

    def test_unrelated_seal_never_accepted(self):
        account.open_account(self.directory)
        exact = self.path.read_bytes()
        self.seal.unlink()
        self.seal.write_bytes(exact)
        self.seal.chmod(0o600)
        with self.assertRaisesRegex(ValueError, "seal does not match"):
            account.read_status(self.directory)
        with self.assertRaisesRegex(ValueError, "seal does not match"):
            account.open_account(self.directory)

    def test_bad_directory_or_state_type_fails_closed(self):
        self.directory.chmod(0o755)
        with self.assertRaises(ValueError):
            account.open_account(self.directory)
        self.directory.chmod(0o700)
        self.path.symlink_to(self.directory / "not-a-state")
        with self.assertRaises(OSError):
            account.open_account(self.directory)
        self.path.unlink()
        os.mkfifo(self.path, 0o600)
        with self.assertRaises(ValueError):
            account.read_status(self.directory)
        self.path.unlink()
        account.open_account(self.directory)
        self.path.chmod(0o644)
        with self.assertRaises(ValueError):
            account.read_status(self.directory)
