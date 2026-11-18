"""Local SQLite restart fixture, not a collector, broker or production ledger."""
from contextlib import closing
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest

import synthetic_paper as s


class JournalFixture:
    """Store a bounded synthetic chain with an atomic compare-and-append."""

    def __init__(self, path):
        self.path = path
        with closing(self.connect()) as db:
            db.execute('CREATE TABLE IF NOT EXISTS journal (seq INTEGER PRIMARY KEY, record TEXT NOT NULL)')

    def connect(self):
        db = sqlite3.connect(self.path, isolation_level=None)
        db.execute('PRAGMA synchronous=FULL')
        return db

    @staticmethod
    def read(db):
        rows = db.execute('SELECT seq, record FROM journal ORDER BY seq LIMIT ?', (s.MAX_EVENTS + 1,)).fetchall()
        if any(i != seq for i, (seq, _) in enumerate(rows)):
            raise ValueError('invalid stored sequence')
        chain = tuple(record for _, record in rows)
        if chain:
            s.replay(chain)
        return chain

    def restart(self):
        with closing(self.connect()) as db:
            return self.read(db)

    def submit(self, prior, event):
        # The caller retains its last acknowledged full prefix independently.
        # An exact match at the next index resolves a lost acknowledgement.
        with closing(self.connect()) as db:
            db.execute('BEGIN IMMEDIATE')
            chain = self.read(db)
            if chain[:len(prior)] != prior:
                raise ValueError('acknowledged prefix is missing or differs')
            candidate = s.append(prior, event)
            if len(chain) > len(prior):
                if chain[len(prior)] != candidate[-1]:
                    raise ValueError('competing event at expected index')
            else:
                db.execute('INSERT INTO journal VALUES (?, ?)', (len(prior), candidate[-1]))
            db.commit()
            return candidate


class SyntheticRestartTests(unittest.TestCase):
    def setUp(self):
        folder = TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.path = Path(folder.name) / 'synthetic.sqlite'
        self.store = JournalFixture(self.path)
        self.init = {'event_id': 'SYNTH_INIT', 'kind': 'INIT',
                     'at': '2030-01-02T12:00:00Z', 'cash_units': 500_000_000}
        self.kill = {'event_id': 'SYNTH_KILL', 'kind': 'KILL',
                     'at': '2030-01-02T12:00:01Z'}

    def test_restart_replays_committed_chain(self):
        prior = self.store.submit((), self.init)
        expected = self.store.submit(prior, self.kill)
        self.assertEqual(expected, JournalFixture(self.path).restart())
        self.assertEqual(s.replay(expected), s.replay(self.store.restart()))

    def test_lost_ack_then_retry_does_not_append_again(self):
        prior = self.store.submit((), self.init)
        self.store.submit(prior, self.kill)  # caller did not receive ACK
        recovered = JournalFixture(self.path).submit(prior, self.kill)
        self.assertEqual(len(recovered), 2)
        self.assertEqual(recovered, self.store.restart())
        with self.assertRaises(ValueError):
            self.store.submit(prior, {**self.kill, 'event_id': 'SYNTH_OTHER'})

    def test_uncommitted_write_disappears_on_close(self):
        prior = self.store.submit((), self.init)
        candidate = s.append(prior, self.kill)
        with closing(self.store.connect()) as db:
            db.execute('BEGIN IMMEDIATE')
            db.execute('INSERT INTO journal VALUES (?, ?)', (1, candidate[-1]))
        reopened = JournalFixture(self.path)
        self.assertEqual(reopened.restart(), prior)
        self.assertEqual(reopened.submit(prior, self.kill), candidate)

    def test_abrupt_process_exit_before_commit_preserves_prefix(self):
        prior = self.store.submit((), self.init)
        candidate = s.append(prior, self.kill)
        child = subprocess.run([sys.executable, '-c', """
import os, sqlite3, sys
db = sqlite3.connect(sys.argv[1], isolation_level=None)
db.execute('BEGIN IMMEDIATE')
db.execute('INSERT INTO journal VALUES (?, ?)', (1, sys.argv[2]))
os._exit(23)
""", str(self.path), candidate[-1]], capture_output=True, timeout=10)
        self.assertEqual(child.returncode, 23, child.stderr)
        self.assertEqual(JournalFixture(self.path).restart(), prior)

    def test_tampered_record_and_rolled_back_prefix_fail_closed(self):
        prior = self.store.submit((), self.init)
        expected = self.store.submit(prior, self.kill)
        with closing(self.store.connect()) as db:
            original = json.loads(expected[-1])
            db.execute('UPDATE journal SET record = ? WHERE seq = 1',
                       (s.canonical({**original, 'sha256': s.ZERO_HASH}),))
        with self.assertRaises(ValueError):
            self.store.restart()
        with closing(self.store.connect()) as db:
            db.execute('DELETE FROM journal WHERE seq = 1')
        with self.assertRaises(ValueError):
            self.store.submit(expected, {**self.kill, 'event_id': 'SYNTH_RETRY'})
        self.assertEqual(prior, self.store.restart())
