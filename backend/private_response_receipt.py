"""Offline, secret-safe response classification. Not imported by any collector."""
import json
import math
from datetime import datetime, timezone

MAX_BYTES = 2_000_000
ENVELOPE_KEYS = {'Information', 'Note', 'Error Message'}
TRANSPORT = {'RESPONSE_RECEIVED', 'NETWORK_FAILURE', 'NOT_ATTEMPTED', 'UNKNOWN'}

def _unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('ambiguous JSON')
        result[key] = value
    return result

def _constant(_):
    raise ValueError('non-finite JSON')

def _float(value):
    number = float(value)
    if not math.isfinite(number):
        raise ValueError('non-finite JSON')
    return number

def classify(*, transport, http_status=None, body=None):
    """Classify caller-supplied evidence; never infer credentials/quota from prose.

    No body, headers, exception, URL, symbol, price, secret or derived value is
    returned. RESPONSE_CANDIDATE is schema-shape only, not successful ingestion.
    """
    if type(transport) is not str or transport not in TRANSPORT:
        raise ValueError('unsupported transport state')
    if transport != 'RESPONSE_RECEIVED':
        if http_status is not None or body is not None:
            raise ValueError('conflicting transport evidence')
        return {'NETWORK_FAILURE': 'NETWORK_FAILURE_REPORTED', 'NOT_ATTEMPTED': 'NOT_ATTEMPTED_REPORTED', 'UNKNOWN': 'REQUEST_STATE_UNKNOWN'}[transport]
    if type(http_status) is not int or not 100 <= http_status <= 599 or type(body) is not bytes:
        raise ValueError('invalid response evidence shape')
    # HTTP class is grounded only in the supplied status, never response prose.
    if http_status == 401: return 'HTTP_AUTHENTICATION_FAILURE'
    if http_status == 403: return 'HTTP_ACCESS_DENIED'
    if http_status == 429: return 'HTTP_RATE_LIMITED'
    if 300 <= http_status < 400: return 'HTTP_REDIRECT_RESPONSE'
    if http_status != 200: return 'HTTP_OTHER_NON200'
    if not body: return 'EMPTY_RESPONSE_UNQUALIFIED'
    if len(body) >= MAX_BYTES: return 'RESPONSE_BOUND_REACHED_UNQUALIFIED'
    try:
        data = json.loads(body.decode('utf-8'), object_pairs_hook=_unique, parse_constant=_constant, parse_float=_float)
    except (UnicodeError, ValueError, RecursionError):
        return 'INVALID_OR_AMBIGUOUS_JSON'
    if type(data) is not dict: return 'UNEXPECTED_SCHEMA'
    envelopes = ENVELOPE_KEYS.intersection(data)
    if envelopes:
        if 'Meta Data' in data or 'Time Series (Daily)' in data:
            return 'CONFLICTING_PROVIDER_ENVELOPE'
        # Provider messages conflate quota, premium entitlement, invalid input and
        # other reasons. Presence alone cannot distinguish them reliably.
        return 'PROVIDER_MESSAGE_REASON_UNRESOLVED'
    if set(data) != {'Meta Data', 'Time Series (Daily)'}:
        return 'UNEXPECTED_SCHEMA'
    meta, series = data['Meta Data'], data['Time Series (Daily)']
    if type(meta) is not dict or type(series) is not dict:
        return 'UNEXPECTED_SCHEMA'
    if not series: return 'EMPTY_SERIES_UNQUALIFIED'
    if len(series) > 100: return 'UNEXPECTED_COMPACT_COVERAGE'
    if not {'2. Symbol', '3. Last Refreshed', '5. Time Zone'}.issubset(meta):
        return 'UNEXPECTED_SCHEMA'
    if any(type(meta[k]) is not str or not meta[k] for k in ('2. Symbol', '3. Last Refreshed', '5. Time Zone')):
        return 'UNEXPECTED_SCHEMA'
    expected = {'1. open', '2. high', '3. low', '4. close', '5. volume'}
    if any(type(row) is not dict or set(row) != expected for row in series.values()):
        return 'UNEXPECTED_SCHEMA'
    return 'DAILY_RESPONSE_CANDIDATE_NOT_VALIDATED'

def receipt(*, observed_utc, transport, http_status=None, body=None):
    """Generate a projection only. No persistence or execution authorization."""
    if type(observed_utc) is not str or len(observed_utc)>64:
        raise ValueError('aware observation clock required')
    try:
        clock = datetime.fromisoformat(observed_utc.replace('Z', '+00:00'))
    except ValueError:
        raise ValueError('aware observation clock required') from None
    if clock.tzinfo is None: raise ValueError('aware observation clock required')
    classification = classify(transport=transport, http_status=http_status, body=body)
    return {'schema_version': 1, 'scope': 'OFFLINE_CALLER_SUPPLIED_RESPONSE_CLASSIFICATION',
            'observed_utc_as_supplied': clock.astimezone(timezone.utc).isoformat(),
            'clock_independently_verified': False, 'classification': classification,
            'http_status_as_supplied': http_status, 'quota_reason_verified': False,
            'collection_success_verified': False, 'source_validation_verified': False,
            'persistence_verified': False, 'publication_verified': False,
            'retry_authorized': False, 'collection_enabled': False,
            'execution_ready': False, 'training_ready': False}
