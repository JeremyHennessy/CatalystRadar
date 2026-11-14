"""Structural leakage audit only. No historical dataset, source attestation or model.
Caller must supply stable issuer/event-group identity and independently verified
window clocks. A clean report does not admit prices, establish PIT truth or trade.
"""
from datetime import datetime, timezone
import math


def instant(value):
    d = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if d.tzinfo is None:
        raise ValueError('timezone required')
    return d.astimezone(timezone.utc)


def audit_partition(rows, *, training_cutoff_utc, holdout_start_utc):
    cutoff, holdout_start = map(instant, (training_cutoff_utc, holdout_start_utc))
    if cutoff >= holdout_start:
        raise ValueError('training cutoff must precede holdout')
    if not isinstance(rows, (list, tuple)) or len(rows) > 10000:
        raise ValueError('bounded explicit cohort required')
    seen, parsed, issues, assignments = set(), [], [], []
    for row in rows:
        event = row['event_id']
        for key in ('event_id', 'issuer_id', 'event_group_id'):
            if not isinstance(row.get(key), str) or not row[key].strip():
                raise ValueError('stable identity fields required')
        if event in seen:
            raise ValueError('duplicate event or revision row')
        seen.add(event)
        decision = instant(row['decision_utc'])
        start, end = map(instant, (row['window_start_utc'], row['window_end_utc']))
        if not decision <= start < end:
            raise ValueError('invalid decision/outcome window')
        outcome = row.get('outcome')
        label_known = None
        if outcome is not None:
            label_known = instant(outcome['observed_utc'])
            value = outcome['excess_total_return']
            if label_known < end or type(value) not in (int, float) or not math.isfinite(value):
                raise ValueError('invalid outcome timing/value, including holdout')
        if decision >= holdout_start:
            partition = 'holdout'
        elif decision > cutoff:
            partition = 'gap'
        elif label_known is None:
            partition = 'unresolved'
        elif end > cutoff or label_known > cutoff:
            partition = 'purged'
        else:
            partition = 'train'
        assignments.append({'event_id': event, 'partition': partition, 'label_status': 'MISSING' if label_known is None else 'OBSERVED'})
        parsed.append((row, partition, start, end))
    # Check related-event leakage even where windows do not overlap. Group IDs
    # are scoped to issuer; amendment clustering itself is NOT inferred here.
    for a, pa, sa, ea in parsed:
        if pa != 'train':
            continue
        for b, pb, sb, eb in parsed:
            if pb != 'holdout' or a['issuer_id'] != b['issuer_id']:
                continue
            if a['event_group_id'] == b['event_group_id']:
                issues.append({'reason': 'RELATED_EVENT_GROUP_CROSSES_SPLIT', 'train_event': a['event_id'], 'holdout_event': b['event_id']})
            if max(sa, sb) <= min(ea, eb):
                issues.append({'reason': 'ISSUER_WINDOWS_OVERLAP', 'train_event': a['event_id'], 'holdout_event': b['event_id']})
    return {'meaning': 'STRUCTURAL_SPLIT_AUDIT_NOT_FORECAST_VALIDATION',
            'assignments': sorted(assignments, key=lambda x: x['event_id']),
            'issues': sorted(issues, key=lambda x: (x['reason'], x['train_event'], x['holdout_event'])),
            'structural_checks_passed': not issues, 'source_truth_verified': False,
            'forecast_probability': None, 'expected_return': None, 'trade_eligible': False}
