"""Validate allowlisted public collection metadata, never private price bytes."""
from datetime import datetime, timezone


def timestamp(value):
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None or parsed > datetime.now(timezone.utc):
        raise ValueError('invalid collection timestamp')
    return parsed


def summarize_price_status(p):
    expected = {'status', 'verified_at', 'symbols_tested', 'rows_per_symbol',
                'first_session', 'last_session', 'execution_ready',
                'scheduled_collection_verified'}
    if set(p) not in (expected, expected | {'latest_collection'}):
        raise ValueError('unreviewed price status schema')
    if p['status'] != 'private_daily_snapshot_tested' or p['execution_ready'] is not False:
        raise ValueError('unreviewed price status schema')
    if type(p['scheduled_collection_verified']) is not bool or p['scheduled_collection_verified'] != ('latest_collection' in p):
        raise ValueError('schedule verification requires collection evidence')
    if type(p['symbols_tested']) is not int or p['symbols_tested'] != 11 or type(p['rows_per_symbol']) is not int or p['rows_per_symbol'] != 100:
        raise ValueError('unreviewed coverage change')
    timestamp(p['verified_at'])
    first = datetime.strptime(p['first_session'], '%Y-%m-%d')
    last = datetime.strptime(p['last_session'], '%Y-%m-%d')
    if first > last:
        raise ValueError('invalid session range')
    as_of = p['verified_at']
    detail = f"Previously reviewed daily-price sample covers through {p['last_session']}. "
    if 'latest_collection' in p:
        c = p['latest_collection']
        fields = {'observed_at', 'saved_snapshots', 'rows_per_symbol', 'scheduled_run_verified'}
        if set(c) not in (fields, fields | {'coverage_audit'}):
            raise ValueError('unreviewed collection schema')
        if timestamp(c['observed_at']) < timestamp(p['verified_at']):
            raise ValueError('collection predates initial verification')
        if type(c['saved_snapshots']) is not int or c['saved_snapshots'] != 11 or type(c['rows_per_symbol']) is not int or c['rows_per_symbol'] != 100 or c['scheduled_run_verified'] is not True:
            raise ValueError('unreviewed collection evidence')
        as_of = c['observed_at']
        detail += 'A historical scheduled collection was verified: 11 stored snapshots, 100 rows each. '
        if 'coverage_audit' in c:
            a = c['coverage_audit']
            if set(a) != {'verified_at', 'first_session', 'last_session', 'hashes_and_symbols_verified'} or a['hashes_and_symbols_verified'] is not True:
                raise ValueError('unreviewed coverage audit')
            if timestamp(a['verified_at']) < timestamp(c['observed_at']):
                raise ValueError('audit predates collection')
            start = datetime.strptime(a['first_session'], '%Y-%m-%d').date()
            end = datetime.strptime(a['last_session'], '%Y-%m-%d').date()
            if start > end or end > timestamp(c['observed_at']).date():
                raise ValueError('invalid audited session range')
            detail += f"Retained response hashes and symbols checked at {a['verified_at']}; all 11 cover {a['first_session']} through {a['last_session']}. Calendar completeness is not established. "
        else:
            detail += 'Latest covered session not independently verified; collection time is not market-data freshness. '

    else:
        detail += 'Scheduled collection not yet verified. '
    detail += 'These historical receipts do not establish current storage privacy or permission to redistribute prices. Further collection requires current storage and source-permission checks. Raw daily data only; not realtime, official auction or total-return data. Execution remains disabled.'
    return {'status': 'snapshot_only', 'as_of': as_of, 'detail': detail}
