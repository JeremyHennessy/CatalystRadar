"""One manually reviewed historical SEC order, not a feed or trading adapter.

No network, paper integration, historical observation clock, or negative evidence.
The order's minute-resolution boundary minutes are deliberately left unknown.
"""
from datetime import datetime, timedelta, timezone
from copy import deepcopy
import re
from zoneinfo import ZoneInfo

_FIXTURE = {
    'fixture_id': 'sec-34-106668-tjgc-historical-v1',
    'mode': 'OFFLINE_HISTORICAL_ORDER_RESEARCH',
    'issuer_cik': '0001969928',
    'issuer_name': 'TJGC Group Limited',
    'order_release': '34-106668',
    'order_date': '2026-10-14',
    'source_urls': [
        'https://www.sec.gov/files/litigation/suspensions/2026/34-106668.pdf',
        'https://www.sec.gov/files/litigation/suspensions/2026/34-106668-ts.pdf',
    ],
    'listing_as_of': {'date': '2026-10-14', 'symbol': 'TJGC',
                      'market': 'Nasdaq Capital Market'},
    'initial_listing_date': None,
    'start_local_minute': '2026-10-15T04:00',
    'end_local_minute': '2026-10-28T23:59',
    'timezone': 'America/New_York',
    'source_time_precision': 'minute',
    'boundary_policy': 'BOTH_BOUNDARY_MINUTES_UNKNOWN',
    'first_public_utc': None,
    'historical_observation_utc': None,
    'source_pdf_sha256': None,
    'provenance': 'MANUAL_PRIMARY_DOCUMENT_REVIEW_NOT_BYTE_ARCHIVE',
    'reason_scope': 'SEC cited potential manipulation; not an adjudicated finding.',
    'resumption_utc': None,
    'current_trading_status': None,
    'complete_halt_coverage': False,
    'execution_eligible': False,
}


def fixture():
    """Independent copy; caller edits cannot alter the fixed historical case."""
    return deepcopy(_FIXTURE)


def _instant(value):
    if not isinstance(value, str) or not re.fullmatch(
            r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?(?:Z|[+-]\d{2}:\d{2})', value):
        raise ValueError('explicit timezone and second precision required')
    return datetime.fromisoformat(value.replace('Z', '+00:00')).astimezone(timezone.utc)


def historical_order_match(*, issuer_cik, instant):
    """Positive/unknown only, against the order's retrospective legal interval.

    This is NOT what the system knew at instant. It provides no retrospective
    trading eligibility, current status, market-session calendar or resume proof.
    Matching is issuer-level and does not identify a particular share class.
    """
    if not isinstance(issuer_cik, str) or not re.fullmatch(r'\d{10}', issuer_cik):
        raise ValueError('exact ten-digit CIK required; ticker matching unsupported')
    at = _instant(instant)
    result = {'fixture_id': _FIXTURE['fixture_id'], 'issuer_cik': issuer_cik,
              'query_utc': at.isoformat().replace('+00:00', 'Z'),
              'status': 'UNKNOWN', 'positive_order_match': None,
              'complete_halt_coverage': False, 'resumption_utc': None,
              'current_trading_status': None, 'execution_eligible': False,
              'historical_knowledge_verified': False}
    if issuer_cik != _FIXTURE['issuer_cik']:
        result['reason'] = 'ISSUER_OUTSIDE_SINGLE_ORDER_FIXTURE'
        return result
    zone = ZoneInfo(_FIXTURE['timezone'])
    start = datetime.fromisoformat(_FIXTURE['start_local_minute']).replace(tzinfo=zone).astimezone(timezone.utc)
    end = datetime.fromisoformat(_FIXTURE['end_local_minute']).replace(tzinfo=zone).astimezone(timezone.utc)
    if start + timedelta(minutes=1) <= at < end:
        result.update(status='HISTORICAL_SEC_ORDER_INTERIOR',
                      positive_order_match=True, reason='STRICT_INTERIOR_OF_ORDER_WINDOW')
    elif start <= at < start + timedelta(minutes=1) or end <= at < end + timedelta(minutes=1):
        result['reason'] = 'MINUTE_PRECISION_BOUNDARY_UNKNOWN'
    else:
        result['reason'] = 'OUTSIDE_ORDER_WINDOW_NOT_CLEARANCE_OR_RESUMPTION'
    return result
