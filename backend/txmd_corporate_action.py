"""Manually verified TXMD common-stock action, not a vendor-price join."""
from datetime import date
import re

CIK = '0000025743'
SEC_8K = 'https://www.sec.gov/Archives/edgar/data/25743/000156459022018687/txmd-8k_20220503.htm'
CERTIFICATE = 'https://www.sec.gov/Archives/edgar/data/25743/000156459022018687/txmd-ex31_8.htm'
NASDAQ = 'https://www.nasdaqtrader.com/TraderNews.aspx?id=ECA2022-89'
LEGAL_DATE = date(2022, 5, 6)
EXCHANGE_DATE = date(2022, 5, 9)


def _iso(value):
    if type(value) is not str or not re.fullmatch(r'[0-9]{4}-[0-9]{2}-[0-9]{2}', value):
        raise ValueError('exact YYYY-MM-DD calendar date required')
    return date.fromisoformat(value)


def review_window(*, issuer_cik, share_class, start_date, end_date):
    """Conservatively flag overlap with either action clock or the gap between."""
    if type(issuer_cik) is not str or not re.fullmatch(r'[0-9]{10}', issuer_cik):
        raise ValueError('exact issuer CIK required')
    if type(share_class) is not str or not share_class:
        raise ValueError('explicit share class required')
    start, end = _iso(start_date), _iso(end_date)
    if start > end:
        raise ValueError('reversed date window')
    matched = issuer_cik == CIK and share_class == 'common' and start <= EXCHANGE_DATE and end >= LEGAL_DATE
    action = None if not matched else {
        'old_shares': 50, 'new_shares': 1,
        'issuer_reported_legal_effective_utc': '2022-05-06T21:01:00Z',
        'exchange_effective_date': EXCHANGE_DATE.isoformat(),
        'exchange_post_split_cusip': '88338N206',
        'symbol_as_reported': 'TXMD',
        'fractional_rule': 'AGGREGATE_BY_HOLDER_THEN_ROUND_UP',
        'sources': (SEC_8K, CERTIFICATE, NASDAQ),
    }
    return {
        'status': 'DOCUMENTED_ACTION_REVIEW_REQUIRED' if matched else 'UNKNOWN',
        'action': action, 'first_public_utc': None,
        'provider_security_mapping_verified': False, 'provider_adjustment_factor': None,
        'outcome_qualified': False, 'adjusted_return': None, 'execution_ready': False,
    }


def illustrative_whole_shares(aggregate_old_shares):
    """Apply the issuer's arithmetic once to an assumed per-holder total."""
    if type(aggregate_old_shares) is not int or aggregate_old_shares < 0:
        raise ValueError('nonnegative whole aggregate old shares required')
    return (aggregate_old_shares + 49) // 50
