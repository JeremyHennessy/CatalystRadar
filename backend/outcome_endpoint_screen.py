"""Conservative date-only rejection screen, never a price join or trading gate."""
from datetime import date
import json
from pathlib import Path

from cohr_listing_anchors import compare
from coherent_forward_coverage import AUDIT_SHA, CUTOFF_UTC
from observed_outcome_coverage import candidate_dates, read
from price_session_audit import scheduled

COHERENT_ENDPOINTS = ('2026-11-20', '2026-11-23')


def _date(value):
    if type(value) is not str or date.fromisoformat(value).isoformat() != value:
        raise ValueError('canonical date required')
    return value


def screen(first, second, date_sets):
    """Use two (date, symbol, venue) observations and bounded anonymous date sets.

    Same-series date coverage alone cannot establish instrument identity,
    corporate actions, prices, actual session, halt status or data rights.
    """
    if any(type(key) is not tuple or len(key) != 3 for key in (first, second)):
        raise ValueError('endpoint must be a date-symbol-venue tuple')
    start, end = _date(first[0]), _date(second[0])
    if start >= end:
        raise ValueError('strictly ordered endpoint dates required')
    if type(date_sets) is not tuple or len(date_sets) > 32:
        raise ValueError('bounded anonymous series tuple required')
    endpoints, found, pairs = {start, end}, set(), 0
    for series in date_sets:
        if type(series) is not frozenset or len(series) > 366:
            raise ValueError('bounded immutable date set required')
        for day in series:
            _date(day)
        found.update(endpoints & series)
        pairs += endpoints <= series
    identity = compare(first, second)['status']
    missing = sorted(endpoints - found)
    reasons = []
    if identity in ('DIFFERENT_ISSUER', 'DIFFERENT_SHARE_CLASS'):
        reasons.append(identity)
    elif identity == 'UNVERIFIED_ANCHOR':
        reasons.append('UNVERIFIED_LISTING_ANCHOR')
    if missing:
        reasons.append('ENDPOINT_MISSING_FROM_AUDITED_SERIES')
    elif not pairs:
        reasons.append('ENDPOINTS_NEVER_COOCCUR_IN_ONE_AUDITED_SERIES')
    return dict(endpoint_dates=[start, end], identity_status=identity,
                audited_series=len(date_sets), missing_from_all_series=missing,
                date_pair_series_count=pairs, screen_rejections=reasons,
                provider_instrument_verified=False, listing_continuity_verified=False,
                actual_session_verified=False, halt_status_verified=False,
                corporate_actions_verified=False, price_rights_verified=False,
                return_value=None, qualified=False, execution_ready=False)


def coherent_pinned(root):
    """Recheck the fixed research dates against the existing pinned date audit."""
    path = Path(root) / 'docs/research/price-session-audit-2026-11-17.json'
    audit = json.loads(read(path, AUDIT_SHA, 100_000))
    dates = frozenset(scheduled(audit['window_start'], audit['window_end']))
    rows = audit['results']
    if (audit['status'] != 'SCHEDULED_SESSION_DATE_COMPARISON_ONLY'
            or len(rows) != 11 or audit['symbols_checked'] != 11
            or audit['symbols_matching_date_set'] != 11 or not dates):
        raise ValueError('pinned audit inventory')
    # This frozen receipt says each individual date set matches the exact
    # schedule. No reconstruction is allowed for partially described series.
    for row in rows:
        if (row['matches_scheduled_date_set'] is not True or row['missing_scheduled_dates']
                or row['unexpected_dates'] or row['observed_dates'] != len(dates)
                or row['expected_scheduled_sessions'] != len(dates)):
            raise ValueError('pinned date set not fully described')
    if tuple(candidate_dates(CUTOFF_UTC)) != COHERENT_ENDPOINTS:
        raise ValueError('frozen calendar dates changed')
    start, end = COHERENT_ENDPOINTS
    result = screen((start, 'COHR', 'NYSE'), (end, 'COHR', 'NYSE'), (dates,) * len(rows))
    return {**result, 'audit_sha256': AUDIT_SHA, 'audit_window_end': audit['window_end'],
            'protocol_cutoff_utc': CUTOFF_UTC}
