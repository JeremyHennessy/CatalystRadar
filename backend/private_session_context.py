"""Offline NYSE core-session reference, not provider availability or admission.
Bounded November 2026 calendar only. No network, quotes, files or production imports.
A ticker does not establish that a security follows this exchange calendar.
"""
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

SOURCE = 'https://www.nyse.com/trade/hours-calendars'
PIN = '2cc42023deddf3ad275848d6631e59b21ca80680'
FIRST, LAST = date(2026,11,13), date(2026,11,30)
HOLIDAY = date(2026,11,26)
EARLY = date(2026,11,27)
ET = ZoneInfo('America/New_York')

def session_close(day):
    if not isinstance(day,date) or isinstance(day,datetime) or not FIRST <= day <= LAST:
        raise ValueError('Outside reviewed calendar')
    if day.weekday()>4 or day==HOLIDAY: return None
    return datetime.combine(day,time(13 if day==EARLY else 16),ET)

def inspect(observed, reported_last_session=None):
    if not isinstance(observed,datetime) or observed.tzinfo is None or observed.utcoffset() is None:
        raise ValueError('Aware observation clock required')
    local=observed.astimezone(ET)
    # Nov14 lower bound guarantees a previous reviewed session exists.
    if not date(2026,11,14) <= local.date() <= LAST:
        raise ValueError('Outside reviewed observation interval')
    latest=None
    day=FIRST
    while day<=local.date():
        close=session_close(day)
        if close is not None and close<=local: latest=day
        day+=timedelta(days=1)
    # Reproduce the old weekday-only calendar expression for comparison only.
    legacy=local.date()
    if local.hour<16: legacy-=timedelta(days=1)
    while legacy.weekday()>4: legacy-=timedelta(days=1)
    relation='NO_REPORTED_SESSION'
    if reported_last_session is not None:
        if not isinstance(reported_last_session,str): raise ValueError('ISO session date required')
        reported=date.fromisoformat(reported_last_session)
        if reported.isoformat()!=reported_last_session: raise ValueError('Canonical session date required')
        if not FIRST<=reported<=LAST: relation='OUTSIDE_REVIEWED_CALENDAR'
        elif session_close(reported) is None: relation='NON_SESSION_IN_REFERENCE_CALENDAR'
        elif reported>latest: relation='CORE_SESSION_NOT_CLOSED_AT_OBSERVATION'
        elif reported==latest: relation='MATCHES_LATEST_CLOSED_CORE_SESSION_ONLY'
        else: relation='EARLIER_THAN_LATEST_CLOSED_CORE_SESSION'
    return {'version':1,'scope':'OFFLINE_NYSE_CORE_SESSION_REFERENCE_ONLY',
        'observed_utc':observed.astimezone(timezone.utc).isoformat(),
        'latest_closed_core_session':latest.isoformat(),
        'latest_core_close_utc':session_close(latest).astimezone(timezone.utc).isoformat(),
        'legacy_weekday_expectation':legacy.isoformat(),
        'legacy_calendar_differs':legacy!=latest,'reported_session_relation':relation,
        'source_url':SOURCE,'production_collector_pin':PIN,
        'collection_enabled':False,'receipt_qualified':False,'trade_eligible':False,
        'provider_availability':'UNVERIFIED','security_calendar_association':'UNVERIFIED',
        'blockers':['PROVIDER_DAILY_SERIES_SESSION_SEMANTICS_UNVERIFIED',
                    'PROVIDER_PUBLICATION_DELAY_UNVERIFIED','SECURITY_CALENDAR_ASSOCIATION_UNVERIFIED',
                    'GLOBAL_KEY_CONSUMERS_AND_QUOTAS_UNVERIFIED','PRIVATE_ACTIONS_COST_UNVERIFIED',
                    'CONTINUATION_NOT_ACTIVATED'],
        'limitations':['Core close is not evidence of provider publication, an auction fill or a complete daily bar.',
                      'Late trading and eligible option sessions differ; this reference is equity core-session only.',
                      'Earlier reported date is not automatically a source failure. Unknown availability remains unknown.',
                      'Scheduled reference does not establish absence of unplanned closures or individual security halts.',
                      'Historical receipt/source bytes and trial controls are not modified.']}
