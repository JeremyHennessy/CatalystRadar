import ast
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import random
import unittest
import synthetic_paper as s


class SyntheticLifecycleTests(unittest.TestCase):
    def setUp(self):
        self.n = 0
        self.j = s.append((), self.event('INIT', cash_units=1_000_000_000))

    def event(self, kind, **fields):
        self.n += 1
        return {'event_id': f'SYNTH_E{self.n}', 'at': '2030-01-02T12:00:00Z', 'kind': kind, **fields}

    def intent(self, order='SYNTH_B1', side='BUY', quantity=10, **fields):
        return self.event('INTENT', order_id=order, candidate_id='SYNTH_C1',
            instrument_id='SYNTH_ASSET', side=side, quantity=quantity,
            limit_units=10_000_000, fee_cap_units=100_000,
            decision_at='2030-01-02T12:00:00Z', session_id='SYNTH_SESSION', **fields)

    def fill(self, order='SYNTH_B1', quantity=4, price=9_000_000, fee=40_000):
        return self.event('FILL', order_id=order, quantity=quantity,
            price_units=price, fee_units=fee, session_id='SYNTH_SESSION')

    def add(self, event):
        self.j = s.append(self.j, event)
        return s.replay(self.j)

    def bought(self):
        self.add(self.intent())
        return self.add(self.fill(quantity=10, fee=100_000))

    def denied(self, event):
        prior = self.j
        state = s.replay(self.j)
        with self.assertRaises(ValueError):
            s.append(self.j, event)
        self.assertEqual(prior, self.j)
        self.assertEqual(state, s.replay(self.j))

    def test_full_lifecycle_partial_cancel_sell_replay(self):
        self.add(self.intent())
        r = self.add(self.fill())
        self.assertEqual(r['cash_units'], 963_960_000)
        self.assertEqual(s.reservations(r), 60_060_000)
        self.assertEqual(r['orders']['SYNTH_B1']['status'], 'PARTIAL')
        r = self.add(self.event('CANCEL', order_id='SYNTH_B1'))
        self.assertEqual(s.reservations(r), 0)
        self.add(self.intent('SYNTH_S1', 'SELL', 4))
        r = self.add(self.fill('SYNTH_S1', 2, 11_000_000, 20_000))
        self.assertEqual(r['positions']['SYNTH_ASSET'], {'quantity': 2, 'cost_units': 18_020_000})
        self.assertEqual(r['realized_pnl_units'], 3_960_000)
        r = self.add(self.fill('SYNTH_S1', 2, 11_000_000, 20_000))
        self.assertEqual(r['cash_units'], 1_007_920_000)
        self.assertEqual(r['positions']['SYNTH_ASSET']['cost_units'], 0)
        self.assertEqual(r['fees_units'], 80_000)
        self.assertTrue(s.reconcile(tuple(json.loads(json.dumps(self.j))), r))
        r['cash_units'] += 1
        self.assertFalse(s.reconcile(self.j, r))

    def test_buy_reservations_compete_and_release(self):
        self.add(self.intent(quantity=90))
        self.denied(self.intent('SYNTH_B2', quantity=10))
        self.add(self.event('REJECT', order_id='SYNTH_B1'))
        self.add(self.intent('SYNTH_B2', quantity=10))

    def test_overselling_and_simultaneous_sell_reservations(self):
        self.denied(self.intent('SYNTH_S1', 'SELL', 1))
        self.bought()
        self.add(self.intent('SYNTH_S1', 'SELL', 6))
        self.denied(self.intent('SYNTH_S2', 'SELL', 5))
        self.add(self.intent('SYNTH_S2', 'SELL', 4))
        self.add(self.fill('SYNTH_S1', 3, 11_000_000))
        self.denied(self.intent('SYNTH_S3', 'SELL', 1))
        self.add(self.event('CANCEL', order_id='SYNTH_S1'))
        self.add(self.intent('SYNTH_S3', 'SELL', 3))

    def test_kill_preserves_positions_and_reservations_until_cancel(self):
        self.add(self.intent())
        before = self.add(self.fill())
        after = self.add(self.event('KILL'))
        self.assertEqual(before['positions'], after['positions'])
        self.assertEqual(before['cash_units'], after['cash_units'])
        self.assertEqual(s.reservations(before), s.reservations(after))
        self.denied(self.intent('SYNTH_B2'))
        self.denied(self.fill())
        self.denied(self.event('KILL'))
        self.assertEqual(s.reservations(self.add(self.event('CANCEL', order_id='SYNTH_B1'))), 0)

    def test_duplicate_ids_rejected_even_after_terminal(self):
        intent = self.intent()
        self.add(intent)
        self.denied(intent)
        self.add(self.event('CANCEL', order_id='SYNTH_B1'))
        self.denied(self.intent())
        self.denied(self.fill())
        self.denied(self.event('CANCEL', order_id='SYNTH_B1'))

    def test_bad_fills(self):
        self.add(self.intent())
        for field, value in [('quantity', 11), ('quantity', 0), ('quantity', True),
                             ('price_units', 10_000_001), ('price_units', -1),
                             ('fee_units', 100_001), ('fee_units', -1),
                             ('session_id', 'SYNTH_OTHER')]:
            with self.subTest(field=field, value=value):
                e = self.fill(); e[field] = value; self.denied(e)
        self.add(self.fill())
        self.denied(self.event('REJECT', order_id='SYNTH_B1'))
        self.denied(self.fill(quantity=6, fee=60_001))
        self.add(self.fill(quantity=6, fee=60_000))
        self.denied(self.fill())

    def test_sell_limit_and_fee_gates(self):
        self.bought()
        self.add(self.intent('SYNTH_S1', 'SELL'))
        self.denied(self.fill('SYNTH_S1', price=9_000_000))
        self.denied(self.fill('SYNTH_S1', price=11_000_000, fee=100_001))

    def test_bad_intents(self):
        for field, value in [('quantity', -1), ('quantity', 1.0), ('quantity', 10**16),
                             ('limit_units', 0), ('fee_cap_units', -1), ('side', 'SHORT'),
                             ('instrument_id', 'AAPL'), ('candidate_id', 'real'),
                             ('session_id', '2026-11-18'), ('decision_at', '2030-01-02T11:00:00Z')]:
            with self.subTest(field=field):
                e = self.intent(); e[field] = value; self.denied(e)

    def test_bad_schema_and_initialization(self):
        self.denied(self.event('INIT', cash_units=10))
        self.denied(self.event('UNKNOWN'))
        e = self.intent(); e['real_market_qualified'] = True; self.denied(e)
        for amount in [True, 1.0, '100', 0, -1]:
            with self.assertRaises(ValueError):
                s.append((), self.event('INIT', cash_units=amount))
        with self.assertRaises(ValueError): s.append((), self.intent())
        with self.assertRaises(ValueError): s.replay(())
        with self.assertRaises(ValueError): s.replay(list(self.j))

    def test_timestamp_regression_and_invalid_clock(self):
        for at in ['2030-01-01T12:00:00Z', '2030-01-02T12:00:00', '2030-02-30T12:00:00Z']:
            e = self.event('KILL'); e['at'] = at; self.denied(e)

    def test_tamper_reorder_and_canonical_validation(self):
        self.add(self.intent())
        record = json.loads(self.j[0]); record['event']['cash_units'] += 1
        with self.assertRaises(ValueError): s.replay((s.canonical(record),) + self.j[1:])
        with self.assertRaises(ValueError): s.replay(tuple(reversed(self.j)))
        with self.assertRaises(ValueError): s.replay((self.j[0] + ' ',) + self.j[1:])
        with self.assertRaises(ValueError): s.replay((self.j[0], self.j[0]))

    def test_mutable_inputs_and_snapshots_cannot_modify_history(self):
        e = self.intent(); self.add(e); e['quantity'] = 999
        snapshot = s.replay(self.j); snapshot['orders']['SYNTH_B1']['quantity'] = 999
        self.assertEqual(s.replay(self.j)['orders']['SYNTH_B1']['quantity'], 10)

    def test_fractional_cost_residual_conserves_exactly(self):
        e = self.intent(quantity=3); e['fee_cap_units'] = 1; self.add(e)
        self.add(self.fill(quantity=3, fee=1))
        self.add(self.intent('SYNTH_S1', 'SELL', 3))
        for _ in range(3):
            r = self.add(self.fill('SYNTH_S1', 1, 10_000_000, 0))
        self.assertEqual(r['positions']['SYNTH_ASSET'], {'quantity': 0, 'cost_units': 0})
        self.assertEqual(r['realized_pnl_units'], 2_999_999)

    def test_deterministic_many_partial_fill_partitions(self):
        rng = random.Random(4321)
        for run in range(20):
            self.setUp()
            self.add(self.intent(quantity=50))
            remaining = 50
            while remaining:
                quantity = rng.randint(1, remaining)
                self.add(self.fill(quantity=quantity, price=rng.randint(1, 10_000_000), fee=0))
                remaining -= quantity
            self.add(self.intent('SYNTH_S1', 'SELL', 50))
            remaining = 50
            while remaining:
                quantity = rng.randint(1, remaining)
                r = self.add(self.fill('SYNTH_S1', quantity, rng.randint(10_000_000, 20_000_000), 0))
                remaining -= quantity
                s.invariant(r)
            self.assertEqual(r['positions']['SYNTH_ASSET']['cost_units'], 0)
            self.assertEqual(r['cash_units'], r['initial_cash_units'] + r['realized_pnl_units'])

    def test_interleaved_buy_with_two_reserved_sells(self):
        self.bought()
        self.add(self.intent('SYNTH_S1', 'SELL', 6))
        self.add(self.intent('SYNTH_S2', 'SELL', 4))
        self.add(self.intent('SYNTH_B2', quantity=3))
        self.add(self.fill('SYNTH_B2', 3, 8_000_000, 1))
        r = self.add(self.fill('SYNTH_S1', 3, 11_000_000, 7))
        self.assertEqual(s.held(r, 'SYNTH_ASSET'), 7)
        self.assertEqual(r['positions']['SYNTH_ASSET']['quantity'], 10)
        self.add(self.fill('SYNTH_S2', 4, 12_000_000, 11))
        self.add(self.fill('SYNTH_S1', 3, 13_000_000, 13))
        self.add(self.intent('SYNTH_S3', 'SELL', 3))
        r = self.add(self.fill('SYNTH_S3', 3, 10_000_000, 0))
        self.assertEqual(r['positions']['SYNTH_ASSET'], {'quantity': 0, 'cost_units': 0})
        self.assertEqual(r['fees_units'], 100_032)
        self.assertEqual(r['cash_units'], 1_035_899_968)
        self.assertEqual(r['realized_pnl_units'], 35_899_968)
        self.assertEqual(s.reservations(r), 0)

    def test_protected_production_state_and_no_adapter(self):
        root = Path(__file__).resolve().parent.parent
        ledger_path = root / 'data/paper_ledger.json'
        before = hashlib.sha256(ledger_path.read_bytes()).hexdigest()
        self.bought()
        ledger = json.loads(ledger_path.read_text())
        self.assertFalse(ledger['simulation_enabled'])
        self.assertEqual(ledger['initial_cash'], 500)
        self.assertEqual(ledger['fills'], [])
        self.assertEqual(before, hashlib.sha256(ledger_path.read_bytes()).hexdigest())
        import paper
        self.assertEqual(paper.APPROVED_PROVIDERS, {})
        imports = {n.names[0].name for n in ast.walk(ast.parse(Path(s.__file__).read_text())) if isinstance(n, ast.Import)}
        self.assertEqual(imports, {'hashlib', 'json', 're'})
        self.assertEqual(s.replay(self.j)['mode'], s.MODE)


if __name__ == '__main__':
    unittest.main()
