"""Offline review of caller-retained halt observations; never execution evidence."""
from hashlib import sha256
import re
from xml.etree.ElementTree import ParseError

from halts_observation import MAX_BYTES, _utc, parse_halts

MAX_RECEIPTS = 24
MAX_TOTAL_BYTES = 4_000_000
FIELDS = {'raw', 'sha256', 'retrieved_utc', 'query_kind', 'query_date'}
DATE_FIELDS = {'haltdate': 'HaltDate', 'resumedate': 'ResumptionDate'}


def review_window(receipts, *, symbol, start_utc, end_utc, as_of_utc):
    """Review a completed [start,end) UTC window for a literal reported symbol.

    No transport, data rights, listing identity, source clock or complete
    coverage is implied by passing a hash check. Callers own custody of bytes.
    """
    if not isinstance(symbol, str) or not re.fullmatch(r'[A-Za-z0-9.$/^_-]{1,32}', symbol):
        raise ValueError('exact reported symbol required')
    start, end, cutoff = map(_utc, (start_utc, end_utc, as_of_utc))
    if not start < end <= cutoff:
        raise ValueError('completed nonempty window required')
    if type(receipts) is not tuple or len(receipts) > MAX_RECEIPTS:
        raise ValueError('bounded receipt tuple required')
    if sum(len(r['raw']) for r in receipts if type(r) is dict
           and type(r.get('raw')) is bytes) > MAX_TOTAL_BYTES:
        raise ValueError('total receipt byte cap exceeded')
    entries, matches, seen = [], [], set()
    emitted_rows = set()
    for index, receipt in enumerate(receipts):
        entry = {'index': index}
        entries.append(entry)
        try:
            if type(receipt) is not dict or set(receipt) != FIELDS:
                raise ValueError('schema')
            observed = _utc(receipt['retrieved_utc'])
            if observed > cutoff:
                entry['status'] = 'AFTER_CUTOFF'
                continue
            raw = receipt['raw']
            expected = receipt['sha256']
            if (type(raw) is not bytes or len(raw) > MAX_BYTES or type(expected) is not str
                    or sha256(raw).hexdigest() != expected):
                raise ValueError('hash or bytes')
            kind, day = receipt['query_kind'], receipt['query_date']
            result = parse_halts(raw, retrieved_utc=receipt['retrieved_utc'],
                                 now_utc=as_of_utc, query_kind=kind, query_date=day)
        except (ValueError, TypeError, OverflowError, ParseError):
            entry['status'] = 'INVALID_RECEIPT_OR_RESPONSE'
            continue
        key = (result['sha256'], kind, day, observed)
        if key in seen:
            entry['status'] = 'DUPLICATE_RECEIPT'
            continue
        seen.add(key)
        error_count = len(result['parse_errors'])
        valid_rows = 0
        for event in result['events']:
            field = DATE_FIELDS.get(kind)
            if field and (event['source_fields'].get(field) or '').replace('/', '') != day:
                error_count += 1
                continue
            valid_rows += 1
            event_start = _utc(event['halt_start_utc'])
            if event['symbol'] != symbol or event_start >= end:
                continue
            evidence = {k: event[k] for k in ('halt_start_utc', 'market', 'reason_code',
                        'scheduled_quote_resume_utc', 'scheduled_trade_resume_utc')}
            # Duplicate rows in one response must not inflate evidence.
            # Different receipts and changed fields remain independently visible.
            row_key = (key, *evidence.values())
            if row_key not in emitted_rows:
                emitted_rows.add(row_key)
                matches.append({**evidence, 'receipt_index': index, 'kind':
                                'REPORTED_START_IN_WINDOW' if event_start >= start else
                                'POSSIBLE_CARRY_IN_NOT_VERIFIED'})
        entry.update(sha256=result['sha256'], retrieved_utc=receipt['retrieved_utc'],
                     query_kind=kind, query_date=day, invalid_rows=error_count,
                     valid_rows=valid_rows, status='PARTIAL_OR_INVALID_ROWS' if error_count else
                     ('PARSED_ROWS' if valid_rows else 'PARSED_EMPTY_NOT_CLEAR'))
    kinds = {m['kind'] for m in matches}
    return {'reported_symbol': symbol, 'start_utc': start_utc, 'end_utc': end_utc,
            'as_of_utc': as_of_utc, 'receipts': entries, 'matches': matches,
            'status': ('REPORTED_START_IN_WINDOW' if 'REPORTED_START_IN_WINDOW' in kinds else
                       'POSSIBLE_CARRY_IN_NOT_VERIFIED' if kinds else 'NO_MATCH_COVERAGE_UNKNOWN'),
            'carry_in_baseline_verified': False, 'source_authenticated': False,
            'effective_dated_identity_verified': False, 'complete': False,
            'ordinary_close': None, 'actual_trade_resumption_verified': False,
            'execution_authorized': False}
