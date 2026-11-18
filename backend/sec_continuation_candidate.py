"""Offline continuation preflight, NOT admission or a network-capable collector.

Original trial gate, workflow and reservation logic remain unchanged. Passing this
preflight never grants collection permission; separate wiring/review is required.
"""
from datetime import datetime, timedelta, timezone
from pathlib import Path
import hashlib
from collector_status import build, instant

UTC = timezone.utc
START = datetime(2026, 11, 23, 11, tzinfo=UTC)
END = datetime(2026, 11, 28, 0, tzinfo=UTC)
MAX_RUNS = 130
ISSUERS_PER_RUN = 10
POLICY_FILES = {
    '.github/workflows/sec-observations.yml': '118290b70cf5394b1631b5deb23e598f139ec8b7902f04ca018c7ef366b4d375',
}

def slots():
    return tuple(datetime(2026, 11, day, hour, minute, tzinfo=UTC)
                 for day in range(23, 28) for hour in range(11, 24)
                 for minute in (17, 47))

def inspect(root, as_of, reservations=(), complete_history_verified=False):
    """Evaluate saved evidence and caller-supplied reservation inventory only.

Caller-provided completeness is a simulation input, not independently verified
Actions history. Unknown history always blocks; output is never executable.
"""
    root = Path(root); now = instant(as_of)
    state = build(root, as_of)
    blockers = ['ACTIVATION_AND_WORKFLOW_REVIEW_REQUIRED']
    if complete_history_verified is not True:
        blockers.append('COMPLETE_ACTIONS_AND_RESERVATION_HISTORY_NOT_VERIFIED')
    for name, digest in POLICY_FILES.items():
        if hashlib.sha256((root/name).read_bytes()).hexdigest() != digest:
            blockers.append('PRODUCTION_POLICY_CHANGED_REAUDIT_REQUIRED')
    sec = state['collectors'][0]
    if sec['source_status'] != 'COMPLETE_RETAINED_METADATA':
        blockers.append('LATEST_RETAINED_SOURCE_RECEIPT_NOT_COMPLETE')
    if now < START: blockers.append('CONTINUATION_WINDOW_NOT_STARTED')
    if now >= END: blockers.append('CONTINUATION_WINDOW_EXPIRED')
    if START <= now < END and now.hour < 11: blockers.append('DAILY_WINDOW_CLOSED')
    if not isinstance(reservations, (tuple, list)) or len(reservations) > 2000:
        raise ValueError('invalid bounded reservation inventory')
    seen = set(); counts = {}; selected = []
    for item in reservations:
        if not isinstance(item, dict) or set(item) != {'run_id','reserved_at','resolved_complete'}:
            raise ValueError('invalid reservation evidence')
        run = item['run_id']; reserved = instant(item['reserved_at'])
        if not isinstance(run, str) or not run.isdecimal() or len(run)>20 or int(run)<1 or run in seen or reserved > now:
            raise ValueError('invalid reservation identity or clock')
        if type(item['resolved_complete']) is not bool: raise ValueError('invalid completion state')
        seen.add(run)
        if not item['resolved_complete']:
            blockers.append('UNRESOLVED_OR_FAILED_RESERVATION')
        if START <= reserved < END:
            day = reserved.date().isoformat(); counts[day] = counts.get(day,0)+1
            selected.append(reserved)
            if reserved.hour < 11:
                blockers.append('RESERVATION_OUTSIDE_DAILY_WINDOW')
    if len(selected) >= MAX_RUNS: blockers.append('WINDOW_RUN_CEILING_REACHED')
    if counts.get(now.date().isoformat(),0) >= 26: blockers.append('DAILY_RUN_CEILING_REACHED')
    if any(count > 26 for count in counts.values()): blockers.append('HISTORICAL_DAILY_CEILING_EXCEEDED')
    if selected and now-max(selected) < timedelta(minutes=30): blockers.append('RECENT_RESERVATION')
    return {'mode':'OFFLINE_CANDIDATE_ONLY', 'collection_enabled':False,
            'can_collect':False, 'activation_review_required':True,
            'as_of':now.isoformat(),'start_utc':START.isoformat(),'exclusive_end_utc':END.isoformat(),
            'configured_slots':len(slots()),'daily_run_ceiling':26,'window_run_ceiling':MAX_RUNS,
            'max_source_requests':MAX_RUNS*ISSUERS_PER_RUN,
            'ceiling_status':'PROPOSED_REQUIRES_NEW_RUNNER_ENFORCEMENT',
            'reserved_window_runs':len(selected),
            'next_candidate_slot':next((x.isoformat() for x in slots() if x>now),None),
            'blockers':sorted(set(blockers)),
            'history_input_status':'CALLER_ASSERTION_NOT_INDEPENDENT_VERIFICATION' if complete_history_verified else 'UNKNOWN'}
