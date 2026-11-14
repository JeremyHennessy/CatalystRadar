"""Byte integrity for declared feature evidence, not source/time authenticity.

No filesystem or network access. Callers retain private bytes; reports contain
identities, hashes and status only. This does not parse or recompute features.
"""
import hashlib
import re
from study_split_audit import audit_study

MAX_ARCHIVES = 1000
MAX_ARCHIVE_BYTES = 8 * 1024 * 1024
MAX_TOTAL_BYTES = 64 * 1024 * 1024


def verify_archive_bytes(payload, declared_sha256):
    """Shared byte check; a match does not authenticate source or timestamps."""
    if not isinstance(declared_sha256, str) or not re.fullmatch('[a-f0-9]{64}', declared_sha256):
        raise ValueError('SHA256 required')
    if payload is None:
        return {'status': 'MISSING_ARCHIVE', 'actual_sha256': None}
    if type(payload) is not bytes or len(payload) > MAX_ARCHIVE_BYTES:
        raise ValueError('bounded exact bytes required')
    actual = hashlib.sha256(payload).hexdigest()
    return {'status': 'HASH_MATCH' if actual == declared_sha256 else 'HASH_MISMATCH',
            'actual_sha256': actual}


def audit_archived_study(rows, *, archives, required_features,
                         training_cutoff_utc, holdout_start_utc):
    """archives maps (source_ref, declared_sha256) to exact bytes, not paths.

    Multiple vintages of one source are distinct keys. Caller must select and
    authenticate the observation receipts independently; current bytes cannot
    establish a historical observation time.
    """
    if not isinstance(archives, dict) or len(archives) > MAX_ARCHIVES:
        raise ValueError('bounded archive mapping required')
    total = 0
    for identity, payload in archives.items():
        if (not isinstance(identity, tuple) or len(identity) != 2 or
                not isinstance(identity[0], str) or not identity[0].strip() or
                not isinstance(identity[1], str) or
                not re.fullmatch('[a-f0-9]{64}', identity[1])):
            raise ValueError('archive identity must be (source_ref, sha256)')
        if type(payload) is not bytes or len(payload) > MAX_ARCHIVE_BYTES:
            raise ValueError('bounded exact bytes required, not paths or text')
        total += len(payload)
        if total > MAX_TOTAL_BYTES:
            raise ValueError('archive total byte limit exceeded')
    report = audit_study(rows, required_features=required_features,
                         training_cutoff_utc=training_cutoff_utc,
                         holdout_start_utc=holdout_start_utc)
    referenced, checks, digest_cache = set(), [], {}
    complete = bool(rows)
    for row in rows:
        names = {f['name'] for f in row.get('features', [])}
        if names != set(required_features):
            complete = False
        for feature in row.get('features', []):
            for source in feature['sources']:
                identity = (source['source_ref'], source['sha256'])
                referenced.add(identity)
                if identity not in archives:
                    status = 'MISSING_ARCHIVE'
                    actual = None
                else:
                    if identity not in digest_cache:
                        digest_cache[identity] = hashlib.sha256(archives[identity]).hexdigest()
                    actual = digest_cache[identity]
                    status = 'HASH_MATCH' if actual == identity[1] else 'HASH_MISMATCH'
                complete = complete and status == 'HASH_MATCH'
                checks.append(dict(event_id=row['event_id'], feature=feature['name'],
                    source_ref=identity[0], declared_sha256=identity[1],
                    actual_sha256=actual, status=status))
    report.update(meaning='DECLARED_TIMING_SPLIT_AND_BYTE_AUDIT_NOT_FORECAST_VALIDATION',
        archive_checks=sorted(checks, key=lambda x: (x['event_id'], x['feature'], x['source_ref'], x['declared_sha256'])),
        feature_source_bytes_verified=bool(checks) and complete,
        unreferenced_archive_count=len(set(archives) - referenced),
        source_authenticity_verified=False, observation_receipts_verified=False,
        feature_values_recomputed=False)
    report['all_integrity_checks_passed'] = (report['all_declared_checks_passed'] and
                                            report['feature_source_bytes_verified'])
    return report
