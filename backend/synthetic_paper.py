"""Offline synthetic-only lifecycle. Not imported by production paper execution.

Amounts are integer millionths of a synthetic currency unit, never binary floats.
History is an append-only hash chain, not a signed or durable audit service.
"""
from copy import deepcopy
from datetime import datetime
import hashlib
import json
import re

MODE = 'SYNTHETIC_TEST_ONLY_NOT_EXECUTION_QUALIFIED'
ACTIVE = {'OPEN', 'PARTIAL'}
MAX_EVENTS = 10000
ZERO_HASH = '0' * 64
COMMON = {'event_id', 'at', 'kind'}
FIELDS = {
    'INIT': {'cash_units'},
    'INTENT': {'order_id', 'candidate_id', 'instrument_id', 'side', 'quantity',
               'limit_units', 'fee_cap_units', 'decision_at', 'session_id'},
    'FILL': {'order_id', 'quantity', 'price_units', 'fee_units', 'session_id'},
    'CANCEL': {'order_id'}, 'REJECT': {'order_id'}, 'KILL': set(),
}


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True,
                      allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode('ascii')).hexdigest()


def identifier(value):
    if not isinstance(value, str) or not re.fullmatch(r'SYNTH_[A-Z0-9_]{1,64}', value):
        raise ValueError('explicit synthetic identifier required')


def integer(value, minimum=0):
    if type(value) is not int or not minimum <= value <= 10**15:
        raise ValueError('bounded integer units required')
    return value


def instant(value):
    if not isinstance(value, str) or not re.fullmatch(r'\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ', value, re.ASCII):
        raise ValueError('UTC second timestamp required')
    return datetime.strptime(value, '%Y-%m-%dT%H:%M:%SZ')


def reservations(state):
    return sum(o['reserved_cash_units'] for o in state['orders'].values())


def held(state, instrument):
    return sum(o['remaining'] for o in state['orders'].values()
               if o['side'] == 'SELL' and o['instrument_id'] == instrument
               and o['status'] in ACTIVE)


def invariant(state):
    if state['cash_units'] < reservations(state) or reservations(state) < 0:
        raise ValueError('cash reservation invariant')
    for instrument, position in state['positions'].items():
        if position['quantity'] < held(state, instrument) or position['cost_units'] < 0:
            raise ValueError('inventory reservation invariant')
    # Exact accounting identity; no marks, prices or fabricated return series.
    if state['cash_units'] + sum(p['cost_units'] for p in state['positions'].values()) != state['initial_cash_units'] + state['realized_pnl_units']:
        raise ValueError('cash/cost/realized reconciliation invariant')


def _apply(state, event):
    """Private reducer: callers use append/replay, never inject arbitrary state."""
    kind = event.get('kind')
    if not isinstance(kind, str) or kind not in FIELDS or set(event) != COMMON | FIELDS[kind]:
        raise ValueError('unknown event kind or fields')
    identifier(event['event_id'])
    instant(event['at'])
    if kind == 'INIT':
        if state is not None:
            raise ValueError('duplicate initialization')
        cash = integer(event['cash_units'], 1)
        return {'mode': MODE, 'initial_cash_units': cash, 'cash_units': cash,
                'realized_pnl_units': 0, 'fees_units': 0, 'killed': False,
                'orders': {}, 'positions': {}}
    if state is None:
        raise ValueError('initialization required')
    if kind == 'KILL':
        if state['killed']:
            raise ValueError('kill switch already latched')
        state['killed'] = True
        return state
    identifier(event['order_id'])
    if kind == 'INTENT':
        if state['killed']:
            raise ValueError('kill switch blocks new intent')
        for key in ('candidate_id', 'instrument_id', 'session_id'):
            identifier(event[key])
        if event['decision_at'] != event['at']:
            raise ValueError('decision must freeze at intent time')
        if event['order_id'] in state['orders']:
            raise ValueError('duplicate order id')
        if not isinstance(event['side'], str) or event['side'] not in {'BUY', 'SELL'}:
            raise ValueError('unsupported side')
        quantity = integer(event['quantity'], 1)
        limit = integer(event['limit_units'], 1)
        fee = integer(event['fee_cap_units'])
        cash = quantity * limit + fee if event['side'] == 'BUY' else 0
        if cash > state['cash_units'] - reservations(state):
            raise ValueError('insufficient unreserved cash')
        position = state['positions'].get(event['instrument_id'], {'quantity': 0})
        if event['side'] == 'SELL' and quantity > position['quantity'] - held(state, event['instrument_id']):
            raise ValueError('insufficient unreserved inventory')
        state['orders'][event['order_id']] = {**event, 'remaining': quantity,
            'filled': 0, 'fees_used_units': 0, 'reserved_cash_units': cash, 'status': 'OPEN'}
    else:
        if event['order_id'] not in state['orders']:
            raise ValueError('unknown order')
        order = state['orders'][event['order_id']]
        if order['status'] not in ACTIVE:
            raise ValueError('terminal order')
        if kind in {'CANCEL', 'REJECT'}:
            if kind == 'REJECT' and order['filled']:
                raise ValueError('partially filled order must cancel remainder')
            order['status'] = 'CANCELLED' if kind == 'CANCEL' else 'REJECTED'
            order['reserved_cash_units'] = 0
        else:
            if state['killed']:
                raise ValueError('kill switch blocks synthetic fill')
            if event['session_id'] != order['session_id']:
                raise ValueError('synthetic session mismatch')
            quantity = integer(event['quantity'], 1)
            price = integer(event['price_units'], 1)
            fee = integer(event['fee_units'])
            if quantity > order['remaining'] or fee + order['fees_used_units'] > order['fee_cap_units']:
                raise ValueError('overfill or fee cap exceeded')
            buy = order['side'] == 'BUY'
            if (buy and price > order['limit_units']) or (not buy and price < order['limit_units']):
                raise ValueError('limit violated')
            gross = quantity * price
            position = state['positions'].setdefault(order['instrument_id'], {'quantity': 0, 'cost_units': 0})
            if buy:
                state['cash_units'] -= gross + fee
                position['quantity'] += quantity
                position['cost_units'] += gross + fee
            else:
                if fee > gross:
                    raise ValueError('negative synthetic sale proceeds')
                # Proportional average cost, floor to millionth; final disposal takes residual.
                cost = position['cost_units'] * quantity // position['quantity']
                position['quantity'] -= quantity
                position['cost_units'] -= cost
                state['cash_units'] += gross - fee
                state['realized_pnl_units'] += gross - fee - cost
            state['fees_units'] += fee
            order['filled'] += quantity
            order['remaining'] -= quantity
            order['fees_used_units'] += fee
            order['status'] = 'PARTIAL' if order['remaining'] else 'FILLED'
            order['reserved_cash_units'] = (order['remaining'] * order['limit_units'] +
                order['fee_cap_units'] - order['fees_used_units']) if buy and order['remaining'] else 0
    invariant(state)
    return state


def replay(journal):
    """Rebuild and verify canonical records. No I/O; no production state accepted."""
    if type(journal) is not tuple or not 1 <= len(journal) <= MAX_EVENTS:
        raise ValueError('bounded nonempty immutable journal tuple required')
    state, previous, last_time, seen = None, ZERO_HASH, None, set()
    for sequence, raw in enumerate(journal):
        if not isinstance(raw, str) or len(raw) > 4096:
            raise ValueError('invalid journal record')
        record = json.loads(raw)
        if not isinstance(record, dict) or set(record) != {'sequence', 'previous', 'event', 'sha256'}:
            raise ValueError('invalid journal schema')
        if canonical(record) != raw or type(record['sequence']) is not int or record['sequence'] != sequence or record['previous'] != previous:
            raise ValueError('noncanonical or reordered journal')
        body = {k: record[k] for k in ('sequence', 'previous', 'event')}
        if record['sha256'] != digest(body):
            raise ValueError('journal hash mismatch')
        event = record['event']
        if not isinstance(event, dict):
            raise ValueError('invalid event')
        at = instant(event.get('at'))
        identifier(event.get('event_id'))
        if event['event_id'] in seen or (last_time is not None and at < last_time):
            raise ValueError('duplicate event or time regression')
        state = _apply(state, event)
        seen.add(event['event_id'])
        previous, last_time = record['sha256'], at
    return deepcopy(state)


def append(journal, event):
    """Return a new validated tuple; rejected commands cannot mutate input/history."""
    if type(journal) is not tuple or len(journal) >= MAX_EVENTS:
        raise ValueError('bounded immutable journal tuple required')
    if journal:
        replay(journal)
    body = {'sequence': len(journal), 'previous': json.loads(journal[-1])['sha256'] if journal else ZERO_HASH,
            'event': deepcopy(event)}
    candidate = journal + (canonical({**body, 'sha256': digest(body)}),)
    replay(candidate)
    return candidate


def reconcile(journal, snapshot):
    """A cached snapshot is advisory, never trusted as execution state."""
    return canonical(replay(journal)) == canonical(snapshot)
