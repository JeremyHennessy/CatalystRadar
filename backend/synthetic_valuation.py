"""Pure hypothetical valuation of a verified synthetic journal; never execution."""
from copy import deepcopy
import json
import synthetic_paper as paper

MODE = 'SYNTHETIC_VALUATION_ONLY_NOT_EXECUTION_OR_MARKET_DATA'
MAX_MARKS = 1000
MAX_AGGREGATE = 10**30
MARK_FIELDS = {'instrument_id', 'valuation_session', 'at', 'price_units'}


def bounded(value):
    if type(value) is not int or abs(value) > MAX_AGGREGATE:
        raise ValueError('synthetic valuation aggregate bound')
    return value


def report(journal, valuation_session, valuation_at, marks):
    """Return fresh data only. Caller session binds marks, not a market session.

    Integer units are millionths of the same hypothetical currency used by the
    journal. Every mark is exactly contemporaneous with valuation_at; the latter
    cannot precede the last journal event. Neither clock is authenticated.
    """
    state = paper.replay(journal)
    paper.identifier(valuation_session)
    at = paper.instant(valuation_at)
    last = json.loads(journal[-1])
    if at < paper.instant(last['event']['at']):
        raise ValueError('valuation precedes journal state')
    if type(marks) is not tuple or len(marks) > MAX_MARKS:
        raise ValueError('bounded immutable mark tuple required')
    held = {k: v for k, v in state['positions'].items() if v['quantity'] > 0}
    mark_map = {}
    for mark in marks:
        if type(mark) is not dict or set(mark) != MARK_FIELDS:
            raise ValueError('exact synthetic mark schema required')
        instrument = mark['instrument_id']
        paper.identifier(instrument)
        paper.identifier(mark['valuation_session'])
        paper.instant(mark['at'])
        if instrument in mark_map or instrument not in held:
            raise ValueError('duplicate or unheld instrument mark')
        if mark['valuation_session'] != valuation_session or mark['at'] != valuation_at:
            raise ValueError('mark must match explicit synthetic session and exact as-of')
        mark_map[instrument] = paper.integer(mark['price_units'])
    if set(mark_map) != set(held):
        raise ValueError('complete held-instrument marks required')
    positions = []
    for instrument, position in sorted(held.items()):
        quantity = bounded(position['quantity'])
        cost = bounded(position['cost_units'])
        value = bounded(quantity * mark_map[instrument])
        reserved = bounded(paper.held(state, instrument))
        positions.append({'instrument_id': instrument, 'quantity': quantity,
                          'sell_reserved_quantity': reserved,
                          'unreserved_quantity': bounded(quantity-reserved),
                          'remaining_cost_units': cost, 'mark_units_per_quantity': mark_map[instrument],
                          'hypothetical_value_units': value,
                          'unrealized_pnl_units': bounded(value-cost)})
    value = bounded(sum(p['hypothetical_value_units'] for p in positions))
    cost = bounded(sum(p['remaining_cost_units'] for p in positions))
    unrealized = bounded(value-cost)
    cash = bounded(state['cash_units'])
    initial = bounded(state['initial_cash_units'])
    realized = bounded(state['realized_pnl_units'])
    reserved_cash = bounded(paper.reservations(state))
    equity = bounded(cash+value)
    reconciled = bounded(initial+realized+unrealized)
    if equity != reconciled or unrealized != sum(p['unrealized_pnl_units'] for p in positions):
        raise ValueError('synthetic valuation reconciliation failed')
    result = {'mode': MODE, 'valuation_session': valuation_session, 'valuation_at': valuation_at,
              'journal_last_at': last['event']['at'], 'journal_tip_sha256': last['sha256'],
              'journal_records': len(journal), 'mark_count': len(marks),
              'initial_cash_units': initial, 'cash_units': cash, 'reserved_cash_units': reserved_cash,
              'available_cash_units': bounded(cash-reserved_cash), 'remaining_cost_units': cost,
              'hypothetical_holdings_value_units': value, 'hypothetical_equity_units': equity,
              'realized_pnl_units': realized, 'unrealized_pnl_units': unrealized,
              'fees_paid_units': bounded(state['fees_units']), 'positions': positions,
              'accounting_identity_verified': True, 'journal_killed': state['killed'],
              'unit_scale': 1000000, 'max_absolute_aggregate_units': MAX_AGGREGATE,
              'mark_age_seconds': 0, 'valuation_session_is_caller_scenario_only': True,
              'actual_market_session_verified': False, 'marks_are_market_data': False,
              'marks_are_executable': False, 'execution_authorized': False,
              'drawdown_calculated': False, 'returns_calculated': False,
              'limitations': [
                  'All values and marks are hypothetical synthetic scenario inputs, not quotes, executable fills or liquidation proceeds.',
                  'Valuation-session and timestamp equality are caller scenario consistency only, not authenticated observation, market-session validity or actual freshness.',
                  'Cash includes buy-reserved cash; holdings value includes sell-reserved quantity. Available cash is separate and is not equity.',
                  'Remaining cost and realized results inherit replay average-cost flooring on partial sales and residual allocation on final disposal. Buy fees remain in cost and sell fees in realized results; fees are not subtracted twice.',
                  'Exact integer products and sums introduce no new rounding. No tax, spread, future fee, financing, slippage, return or drawdown is estimated.',
                  'This report does not append events, change reservations, clear kill state, authorize execution or verify source journal authenticity beyond its internal replay chain.']}
    return deepcopy(result)
