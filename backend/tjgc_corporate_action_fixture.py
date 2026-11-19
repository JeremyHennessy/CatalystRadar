"""Manual historical issuer-level review warnings, never price adjustments.

Independent of production gates, SEC notes audits, collectors and paper books.
Date overlap is a review trigger, NOT a point-in-time security mapping.
"""
from copy import deepcopy
from datetime import date
import re

_CIK = '0001969928'
_SOURCES = {
    'nasdaq_split': 'https://www.nasdaqtrader.com/TraderNews.aspx?id=ECA2026-350',
    'issuer_split': 'https://www.sec.gov/Archives/edgar/data/1969928/000118518526002042/tjgcgroup6k051426.htm',
    'issuer_annual': 'https://www.sec.gov/Archives/edgar/data/1969928/000118518526003078/tjgc20f033126.htm',
    'issuer_redesignation': 'https://www.sec.gov/Archives/edgar/data/1969928/000118518526003374/tjgc6k073126.htm',
    'nasdaq_resume': 'https://ir.nasdaq.com/node/110496/pdf',
}
_EVENTS = [
    {'id': 'tjgc-ordinary-reverse-split-20260526', 'date': '2026-05-26',
     'type': 'REVERSE_SPLIT', 'date_basis': 'EXCHANGE_ANNOUNCED_ISSUER_LATER_REPORTED_EFFECTIVE',
     'share_ratio': {'old_shares': 3, 'new_shares': 1},
     'class_as_reported': 'ordinary shares', 'post_split_cusip_as_reported': 'G2588N116',
     'symbol_as_reported': 'TJGC', 'symbol_change_announced': False,
     'nominal_post_split_issued_shares': 10100000,
     'later_reported_post_rounding_issued_shares': 10100023,
     'source_ids': ['nasdaq_split', 'issuer_split', 'issuer_annual']},
    {'id': 'tjgc-share-redesignation-20260812', 'date': '2026-08-12',
     'type': 'SHARE_REDESIGNATION', 'date_basis': 'ISSUER_ANNOUNCED_MARKETPLACE_REFLECTION_DATE',
     'share_ratio': None, 'class_as_reported': 'Class A and Class B ordinary shares',
     'symbol_as_reported': 'TJGC for Class A',
     'source_ids': ['issuer_redesignation']},
]


def fixture():
    return deepcopy({'mode': 'MANUAL_HISTORICAL_CORPORATE_ACTION_REVIEW_ONLY',
                     'issuer_cik': _CIK, 'issuer_name': 'TJGC Group Limited',
                     'sources': _SOURCES, 'events': _EVENTS,
                     'financial_presentation': '20-F share and per-share financial data already retrospectively restated; do not adjust twice.',
                     'halt_context': 'May 26 falls between the separately reported May 15 halt and June 3 scheduled resumption; no trade on May 26 inferred.',
                     'source_bytes_sha256': None, 'first_public_utc': None,
                     'historical_observation_utc': None,
                     'vendor_adjustment_factor': None, 'same_share_class_verified': False,
                     'complete_corporate_action_coverage': False,
                     'training_ready': False, 'execution_ready': False})


def _date(value):
    if not isinstance(value, str) or not re.fullmatch(r'[0-9]{4}-[0-9]{2}-[0-9]{2}', value):
        raise ValueError('ASCII calendar date YYYY-MM-DD required')
    return date.fromisoformat(value)


def review_window(*, issuer_cik, start_date, end_date):
    """Inclusive calendar-date warning query; never validates vendor bar basis.

    Boundary dates trigger review because intraday effect/observations are not
    modeled. No match means unknown, not corporate-action-free. An event match
    does not identify the security/class involved in any caller's data.
    """
    if not isinstance(issuer_cik, str) or not re.fullmatch('[0-9]{10}', issuer_cik):
        raise ValueError('exact ten-digit ASCII CIK required')
    start, end = _date(start_date), _date(end_date)
    if start > end:
        raise ValueError('reversed date window')
    matches = deepcopy([e for e in _EVENTS if issuer_cik == _CIK and start <= _date(e['date']) <= end])
    return {'issuer_cik': issuer_cik, 'start_date': start_date, 'end_date': end_date,
            'status': 'ISSUER_DATE_REVIEW_REQUIRED' if matches else 'UNKNOWN',
            'matched_events': matches,
            'same_share_class_verified': False, 'known_at_window_time_verified': False,
            'vendor_adjustment_factor': None, 'adjusted_return': None,
            'complete_corporate_action_coverage': False,
            'training_ready': False, 'execution_ready': False}
