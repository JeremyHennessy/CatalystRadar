"""Structural leakage audit only. No historical dataset, source attestation or model.
Caller must supply stable issuer/event-group identity and independently verified
window clocks. A clean report does not admit prices, establish PIT truth or trade.
"""
from datetime import datetime, timezone
import math
import re


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


def audit_study(rows, *, required_features, training_cutoff_utc, holdout_start_utc):
    """Audit declared pre-decision feature clocks as well as split/label clocks.

    This checks caller-supplied metadata, not the archived bytes themselves.
    Never treat a filing/acceptance date as a source observation timestamp.
    """
    if (not isinstance(required_features, (list, tuple)) or
            not 1 <= len(required_features) <= 100 or
            any(not isinstance(x, str) or not x.strip() for x in required_features) or
            len(set(required_features)) != len(required_features)):
        raise ValueError('bounded unique predeclared feature names required')
    report = audit_partition(rows, training_cutoff_utc=training_cutoff_utc,
                             holdout_start_utc=holdout_start_utc)
    checks = []
    for row in rows:
        decision = instant(row['decision_utc'])
        features = row.get('features', [])
        if not isinstance(features, list) or len(features) > 100:
            raise ValueError('bounded feature evidence list required')
        names, reasons = set(), []
        for feature in features:
            if not isinstance(feature, dict):
                raise ValueError('feature evidence object required')
            name = feature.get('name')
            if not isinstance(name, str) or name not in required_features or name in names:
                raise ValueError('duplicate or undeclared feature')
            names.add(name)
            value = feature.get('value')
            if type(value) not in (int, float) or not math.isfinite(value):
                raise ValueError('finite numeric feature value required')
            # Every supplied feature, including rejected/holdout rows, is checked.
            computed = instant(feature['computed_utc'])
            sources = feature.get('sources')
            if not isinstance(sources, list) or not 1 <= len(sources) <= 100:
                raise ValueError('bounded nonempty feature source list required')
            identities = set()
            for source in sources:
                if not isinstance(source, dict):
                    raise ValueError('source evidence object required')
                sha, ref = source.get('sha256'), source.get('source_ref')
                if (not isinstance(sha, str) or not re.fullmatch('[a-f0-9]{64}', sha) or
                        not isinstance(ref, str) or not ref.strip()):
                    raise ValueError('source identity and hash required')
                identity = (ref, sha)
                if identity in identities:
                    raise ValueError('duplicate feature source')
                identities.add(identity)
                observed = instant(source['observed_utc'])
                if observed > computed:
                    raise ValueError('feature computed before source observation')
                if observed > decision:
                    reasons.append({'feature': name, 'reason': 'SOURCE_OBSERVED_AFTER_DECISION'})
            if computed > decision:
                reasons.append({'feature': name, 'reason': 'FEATURE_COMPUTED_AFTER_DECISION'})
        reasons.extend({'feature': name, 'reason': 'REQUIRED_FEATURE_MISSING'}
                       for name in sorted(set(required_features) - names))
        # Preserve failures in every partition instead of silently dropping cases.
        checks.append({'event_id': row['event_id'], 'declared_feature_clocks_passed': not reasons,
                       'reasons': sorted(reasons, key=lambda x: (x['feature'], x['reason']))})
    report['meaning'] = 'DECLARED_TIMING_AND_SPLIT_AUDIT_NOT_FORECAST_VALIDATION'
    report['feature_checks'] = sorted(checks, key=lambda x: x['event_id'])
    report['required_features'] = sorted(required_features)
    report['declared_timing_checks_passed'] = bool(rows) and all(x['declared_feature_clocks_passed'] for x in checks)
    report['all_declared_checks_passed'] = report['structural_checks_passed'] and report['declared_timing_checks_passed']
    report['feature_source_bytes_verified'] = False
    return report

