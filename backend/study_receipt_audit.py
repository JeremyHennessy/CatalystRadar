"""Offline feature/source clock joins to retained receipt bytes, not authenticity.

No network, filesystem, execution registration or changes to study inputs.
Receipt hashes bind exact bytes, not a trusted clock or the truth of their issuer.
"""
import hashlib
import json
import re
from study_archive_audit import audit_archived_study
from study_split_audit import instant

MAX_RECEIPTS = 1000
MAX_RECEIPT_BYTES = 65536
MAX_TOTAL_BYTES = 8 * 1024 * 1024


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('duplicate receipt field')
        result[key] = value
    return result


def audit_receipted_study(rows, *, archives, receipts, required_features,
                          training_cutoff_utc, holdout_start_utc):
    """Each feature source names observation_receipt_sha256.

    receipts maps that hash to exact retained JSON bytes. Receipt v1 has only
    version, source_ref, sha256 (source bytes), and observed_utc. A separate
    collector/trusted-clock review is still necessary; this is a consistency
    check of caller-supplied evidence, not permission to manufacture receipts.
    """
    if not isinstance(receipts, dict) or len(receipts) > MAX_RECEIPTS:
        raise ValueError('bounded receipt mapping required')
    total = 0
    for key, raw in receipts.items():
        if not isinstance(key, str) or not re.fullmatch('[a-f0-9]{64}', key):
            raise ValueError('receipt SHA256 key required')
        if type(raw) is not bytes or len(raw) > MAX_RECEIPT_BYTES:
            raise ValueError('bounded exact receipt bytes required')
        total += len(raw)
        if total > MAX_TOTAL_BYTES:
            raise ValueError('receipt total byte limit exceeded')
    report = audit_archived_study(rows, archives=archives,
        required_features=required_features, training_cutoff_utc=training_cutoff_utc,
        holdout_start_utc=holdout_start_utc)
    checks, referenced = [], set()
    for row in rows:
        for feature in row.get('features', []):
            for source in feature['sources']:
                key = source.get('observation_receipt_sha256')
                status = 'MISSING_RECEIPT_REFERENCE'
                if key is not None:
                    if not isinstance(key, str) or not re.fullmatch('[a-f0-9]{64}', key):
                        raise ValueError('invalid observation receipt reference')
                    referenced.add(key)
                    raw = receipts.get(key)
                    status = 'MISSING_RECEIPT'
                    if raw is not None:
                        status = 'RECEIPT_HASH_MISMATCH'
                        if hashlib.sha256(raw).hexdigest() == key:
                            status = 'MALFORMED_RECEIPT'
                            try:
                                receipt = json.loads(raw, object_pairs_hook=_unique_object)
                                if (not isinstance(receipt, dict) or set(receipt) !=
                                        {'version', 'source_ref', 'sha256', 'observed_utc'} or
                                        type(receipt['version']) is not int or receipt['version'] != 1):
                                    raise ValueError('invalid receipt schema')
                                observed = instant(receipt['observed_utc'])
                                if receipt['source_ref'] != source['source_ref'] or receipt['sha256'] != source['sha256']:
                                    status = 'RECEIPT_SOURCE_MISMATCH'
                                elif observed != instant(source['observed_utc']):
                                    status = 'RECEIPT_TIME_MISMATCH'
                                else:
                                    status = 'RECEIPT_BOUND'
                            except (ValueError, TypeError, KeyError, AttributeError, UnicodeError):
                                pass
                checks.append({'event_id': row['event_id'], 'feature': feature['name'],
                               'source_ref': source['source_ref'], 'receipt_sha256': key,
                               'status': status})
    bound = bool(checks) and all(c['status'] == 'RECEIPT_BOUND' for c in checks)
    report.update(meaning='RETAINED_RECEIPT_CLOCK_BINDING_NOT_AUTHENTICATION',
                  receipt_checks=checks, receipt_bindings_verified=bound,
                  unreferenced_receipt_count=len(set(receipts) - referenced),
                  all_receipt_integrity_checks_passed=report['all_integrity_checks_passed'] and bound,
                  observation_receipts_verified=False, trusted_clock_verified=False,
                  source_authenticity_verified=False, feature_values_recomputed=False,
                  trade_eligible=False)
    return report
