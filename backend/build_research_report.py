"""Reproducible readiness report from real saved SEC evidence, no network/prices.

Does not invent decisions, features or outcome windows to make audit APIs pass.
The source byte checker is shared with the historical study audit. Temporal and
split audits remain NOT_RUN until a frozen protocol supplies their real inputs.
"""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from study_archive_audit import verify_archive_bytes
from study_split_audit import instant

ROOT = Path(__file__).resolve().parent.parent


def build(root=ROOT, generated_at=None):
    root = Path(root)
    generated_at = generated_at or datetime.now(timezone.utc).isoformat()
    instant(generated_at)
    inputs = {}
    def load(name):
        payload = (root / name).read_bytes()
        inputs[name] = hashlib.sha256(payload).hexdigest()
        return json.loads(payload)
    reviews = load('data/filing_reviews.json')['records']
    provenance = load('data/provenance.json')['sources']
    scan = load('data/latest_scan.json')
    if len(reviews) > 1000 or len(scan['sources']) > 1000:
        raise ValueError('bounded input required')
    sources = {}
    archive_root = (root / 'data/sec-snapshots').resolve()
    for src in scan['sources']:
        if src.get('status') != 200 or not src.get('archive_path'):
            continue
        path = (root / src['archive_path']).resolve()
        if archive_root not in path.parents:
            raise ValueError('archive path outside public snapshot directory')
        payload = path.read_bytes() if path.exists() else None
        check = verify_archive_bytes(payload, src['sha256'])
        inputs[src['archive_path']] = check['actual_sha256']
        if check['status'] != 'HASH_MATCH':
            continue
        try:
            observed = instant(src['retrieved_utc'])
            doc = json.loads(payload)
            cik = str(int(doc['cik']))
            recent = doc['filings']['recent']
            if len(recent['accessionNumber']) != len(recent['form']):
                continue
            forms = {}
            for accession, form in zip(recent['accessionNumber'], recent['form']):
                if accession in forms and forms[accession] != form:
                    raise ValueError('conflicting accession forms')
                forms[accession] = form
        except (KeyError, ValueError, TypeError):
            continue
        sources.setdefault(cik, []).append((src, observed, forms))
    records, seen = [], set()
    for r in reviews:
        event_id = r['accession']
        if event_id in seen:
            raise ValueError('duplicate reviewed accession')
        seen.add(event_id)
        cik = str(int(r['issuer_cik']))
        matches = [(s, t, f[event_id]) for s, t, f in sources.get(cik, []) if event_id in f]
        full = [s for s in provenance if s.get('sha256') == r['source_sha256'] and s.get('status') == 200]
        reasons = ['FULL_FILING_BYTES_NOT_IN_REPOSITORY', 'NO_FROZEN_DECISION_OR_OUTCOME_WINDOW',
                   'NO_VERIFIED_PRICE_OUTCOME', 'CORPORATE_ACTION_AND_HALT_COVERAGE_UNRESOLVED']
        if not matches:
            reasons.append('METADATA_IDENTITY_NOT_VERIFIED')
        elif len({m[2] for m in matches}) != 1:
            reasons.append('METADATA_FORM_CONFLICT')
        if not full:
            reasons.append('FULL_FILING_PROVENANCE_MISSING')
        if any(t > instant(generated_at) for _, t, _ in matches):
            reasons.append('METADATA_OBSERVED_AFTER_REPORT')
        # Manual triage is retained, never interpreted as a numeric predictor.
        records.append({'event_id': event_id, 'issuer_id': cik, 'issuer': r['issuer'],
            'review_status': r['status'], 'reviewed_utc': r['reviewed_utc'],
            'metadata_bytes_verified': bool(matches),
            'metadata_identity_matched': bool(matches) and len({m[2] for m in matches}) == 1,
            'metadata_observations': [{'source_url': s['url'], 'sha256': s['sha256'],
                'observed_utc': s['retrieved_utc'], 'form': form} for s, _, form in matches],
            'full_filing_recorded_sha256': r['source_sha256'],
            'full_filing_bytes_verified': False, 'outcome': None, 'qualified': False,
            'blockers': sorted(reasons)})
    counts = {'reviewed_records': len(records),
        'metadata_bytes_verified': sum(x['metadata_bytes_verified'] for x in records),
        'metadata_identity_matched': sum(x['metadata_identity_matched'] for x in records),
        'full_filing_bytes_verified': 0, 'qualified_observations': 0, 'outcomes_available': 0}
    blockers = Counter(reason for row in records for reason in row['blockers'])
    report = {'schema_version': 1, 'mode': 'REAL_ARCHIVE_READINESS_NOT_FORECAST',
        'generated_at': generated_at, 'counts': counts,
        'blocker_counts': [{'reason': k, 'count': v} for k, v in sorted(blockers.items())],
        'input_sha256': inputs, 'records': sorted(records, key=lambda x: x['event_id']),
        'temporal_and_split_audits': 'NOT_RUN_MISSING_FROZEN_DECISIONS_AND_WINDOWS',
        'original_filing_archive_scope': 'METADATA_ONLY_ORIGINAL_BYTES_NOT_PUBLISHED',
        'source_authenticity_verified': False, 'forecast_probability': None,
        'expected_return': None, 'trade_eligible': False,
        'limitations': ['Manual ten-record sample, not an unbiased training cohort.',
            'A current source hash or retrieval timestamp does not establish first-public availability.',
            'No prices, outcome labels, historical decisions, or numeric catalyst features inferred.']}
    return report

if __name__ == '__main__':
    report = build()
    (ROOT / 'data/research_report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report['counts'], sort_keys=True))
