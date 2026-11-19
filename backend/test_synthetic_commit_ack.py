"""Process-boundary qualification of the existing disposable synthetic fixture."""
import json
import multiprocessing as mp
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

import synthetic_paper as s
from test_synthetic_restart import JournalFixture


def crash_after_commit(path, prior, event):
    JournalFixture(path).submit(prior, event)
    os._exit(23)  # commit returned, but no result/acknowledgment is delivered


def contend(path, prior, event, barrier, results):
    try:
        store = JournalFixture(path)
        barrier.wait(timeout=10)
        result = store.submit(prior, event)
        results.put(('accepted', result[-1]))
    except ValueError:
        results.put(('conflict', None))


class SyntheticCommitAckTests(unittest.TestCase):
    def setUp(self):
        folder = TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.path = str(Path(folder.name) / 'synthetic.sqlite')
        self.store = JournalFixture(self.path)
        self.ctx = mp.get_context('spawn')
        self.clock = '2030-01-02T12:00:00Z'
        self.prior = self.store.submit((), self.event('INIT', 'INIT', cash_units=500_000_000))
        self.prior = self.store.submit(self.prior, self.event('ORDER', 'INTENT',
            order_id='SYNTH_BUY', candidate_id='SYNTH_CASE', instrument_id='SYNTH_ASSET',
            side='BUY', quantity=10, limit_units=10_000_000, fee_cap_units=100_000,
            decision_at=self.clock, session_id='SYNTH_SESSION'))
        self.fill = self.event('FILL', 'FILL', order_id='SYNTH_BUY', quantity=4,
            price_units=9_000_000, fee_units=40_000, session_id='SYNTH_SESSION')

    def event(self, identity, kind, **fields):
        return dict(event_id='SYNTH_'+identity, kind=kind, at=self.clock, **fields)

    def join(self, processes):
        try:
            for p in processes:
                p.join(15)
                self.assertFalse(p.is_alive(), 'bounded child did not finish')
        finally:
            for p in processes:
                if p.is_alive():
                    p.terminate(); p.join(5)

    def assert_single_fill(self, chain):
        state = s.replay(chain)
        self.assertEqual(len(chain), 3)
        self.assertEqual(state['positions']['SYNTH_ASSET'], {'quantity': 4, 'cost_units': 36_040_000})
        self.assertEqual(state['cash_units'], 463_960_000)
        self.assertEqual(state['fees_units'], 40_000)
        self.assertEqual(s.reservations(state), 60_060_000)
        return state

    def test_abrupt_exit_after_committed_partial_fill_then_retry_and_cancel(self):
        p = self.ctx.Process(target=crash_after_commit, args=(self.path, self.prior, self.fill))
        p.start(); self.join([p]); self.assertEqual(p.exitcode, 23)
        reopened = JournalFixture(self.path)
        committed = reopened.restart()
        self.assert_single_fill(committed)
        for _ in range(3):
            self.assertEqual(reopened.submit(self.prior, self.fill), committed)
        cancel = self.event('CANCEL', 'CANCEL', order_id='SYNTH_BUY')
        latest = reopened.submit(committed, cancel)
        # Late retry acknowledges the original prefix, not a new fill or latest tip.
        self.assertEqual(reopened.submit(self.prior, self.fill), committed)
        self.assertEqual(reopened.restart(), latest)
        state = s.replay(latest)
        self.assertEqual(state['positions']['SYNTH_ASSET']['quantity'], 4)
        self.assertEqual(state['cash_units'], 463_960_000)
        self.assertEqual(state['fees_units'], 40_000)
        self.assertEqual(s.reservations(state), 0)
        with self.assertRaises(ValueError):
            reopened.submit(self.prior, {**self.fill, 'fee_units': 41_000})
        self.assertEqual(reopened.restart(), latest)

    def race(self, events):
        barrier = self.ctx.Barrier(2)
        results = self.ctx.Queue()
        processes = [self.ctx.Process(target=contend, args=(self.path, self.prior, e, barrier, results)) for e in events]
        try:
            for p in processes: p.start()
            self.join(processes)
            self.assertEqual([p.exitcode for p in processes], [0, 0])
            return [results.get(timeout=3) for _ in processes]
        finally:
            results.close(); results.join_thread()

    def test_two_process_same_command_retries_commit_only_once(self):
        results = self.race([self.fill, dict(self.fill)])
        self.assertEqual([r[0] for r in results], ['accepted', 'accepted'])
        self.assertEqual(results[0][1], results[1][1])
        self.assert_single_fill(self.store.restart())

    def test_two_valid_competing_commands_only_one_can_extend_prefix(self):
        other = {**self.fill, 'event_id': 'SYNTH_OTHER_FILL'}
        results = self.race([self.fill, other])
        self.assertCountEqual([r[0] for r in results], ['accepted', 'conflict'])
        chain = self.store.restart()
        self.assert_single_fill(chain)
        accepted = next(r[1] for r in results if r[0] == 'accepted')
        self.assertEqual(chain[-1], accepted)
        self.assertIn(json.loads(chain[-1])['event']['event_id'], ['SYNTH_FILL', 'SYNTH_OTHER_FILL'])

    def crash_and_reopen(self, command):
        child = self.ctx.Process(target=crash_after_commit, args=(self.path, self.prior, command))
        child.start()
        self.join([child])
        self.assertEqual(child.exitcode, 23)
        return JournalFixture(self.path)

    def assert_latched_and_cancellable(self, reopened, chain, had_fill):
        state = s.replay(chain)
        self.assertTrue(state['killed'])
        self.assertEqual(len(chain), 4 if had_fill else 3)
        self.assertEqual(state['cash_units'], 463_960_000 if had_fill else 500_000_000)
        self.assertEqual(state['fees_units'], 40_000 if had_fill else 0)
        self.assertEqual(state['positions'], (
            {'SYNTH_ASSET': {'quantity': 4, 'cost_units': 36_040_000}} if had_fill else {}))
        self.assertEqual(s.reservations(state), 60_060_000 if had_fill else 100_100_000)
        with self.assertRaisesRegex(ValueError, 'kill switch blocks synthetic fill'):
            reopened.submit(chain, {**self.fill, 'event_id': 'SYNTH_POST_KILL_FILL'})
        self.assertEqual(reopened.restart(), chain)
        cancel = self.event('CANCEL', 'CANCEL', order_id='SYNTH_BUY')
        cancelled = reopened.submit(chain, cancel)
        self.assertEqual(JournalFixture(self.path).restart(), cancelled)
        recovered = s.replay(cancelled)
        self.assertTrue(recovered['killed'])
        self.assertEqual(recovered['orders']['SYNTH_BUY']['status'], 'CANCELLED')
        self.assertEqual(s.reservations(recovered), 0)
        for field in ('cash_units', 'fees_units', 'positions', 'realized_pnl_units'):
            self.assertEqual(recovered[field], state[field])
        return cancelled

    def test_kill_committed_before_lost_ack_blocks_fill_after_restart(self):
        kill = self.event('KILL', 'KILL')
        reopened = self.crash_and_reopen(kill)
        killed = reopened.restart()
        self.assertEqual(reopened.submit(self.prior, kill), killed)
        with self.assertRaisesRegex(ValueError, 'competing event'):
            reopened.submit(self.prior, self.fill)
        self.assert_latched_and_cancellable(reopened, killed, had_fill=False)

    def test_fill_committed_before_lost_ack_survives_later_kill(self):
        kill = self.event('KILL', 'KILL')
        reopened = self.crash_and_reopen(self.fill)
        filled = reopened.restart()
        self.assert_single_fill(filled)
        with self.assertRaisesRegex(ValueError, 'competing event'):
            reopened.submit(self.prior, kill)
        killed = reopened.submit(filled, kill)
        cancelled = self.assert_latched_and_cancellable(reopened, killed, had_fill=True)
        self.assertEqual(reopened.submit(self.prior, self.fill), filled)
        self.assertEqual(reopened.restart(), cancelled)

    def test_contending_kill_and_fill_commit_at_most_one_from_same_prefix(self):
        kill = self.event('KILL', 'KILL')
        results = self.race([kill, self.fill])
        self.assertCountEqual([r[0] for r in results], ['accepted', 'conflict'])
        reopened = JournalFixture(self.path)
        chain = reopened.restart()
        self.assertEqual(len(chain), 3)
        self.assertEqual(chain[-1], next(r[1] for r in results if r[0] == 'accepted'))
        had_fill = json.loads(chain[-1])['event']['kind'] == 'FILL'
        self.assertEqual(chain, s.append(self.prior, self.fill if had_fill else kill))
        if had_fill:
            self.assert_single_fill(chain)
            # Safety action must be explicitly resubmitted against the fresh tip.
            chain = reopened.submit(chain, kill)
        self.assert_latched_and_cancellable(reopened, chain, had_fill)
