"""Frozen evidence completeness and ordered blockers, not a trading decision."""
import argparse
import hashlib
import json
from pathlib import Path
import re

from research_scanner import encoded

ASSESSMENT_ID = 'documentary-coverage-and-readiness-v1'
BASE = 'web/trade-ideas/v1/'
SNAPSHOTS = (
    (BASE + 'latest.json', 420, '8c70e86caeddcb8a8b9c254f1eaa8ba8eb53175c73eace8d1a492e8f34d3d8b7'),
    (BASE + 'releases/0185e53523fb7687fc97a97aeee6e99ddebd6de7a0c3d142f23cb1311fe2ba36.json',
     486, '0185e53523fb7687fc97a97aeee6e99ddebd6de7a0c3d142f23cb1311fe2ba36'),
)
HEX = re.compile(r'[0-9a-f]{64}')
THESIS = re.compile(r'research-[0-9a-f]{24}')
CIK = re.compile(r'(?!0000000000)[0-9]{10}')
ACCESSION = re.compile(r'[0-9]{10}-[0-9]{2}-[0-9]{6}')

CHECKS = (
    ('source_identity', 'Original source identity'),
    ('event_content', 'Source-reported event content'),
    ('event_availability', 'Verified first-public availability'),
    ('instrument_identity', 'Effective-dated instrument identity'),
    ('financial_comparability', 'Qualified financial comparison'),
    ('market_data', 'Eligible current market data'),
    ('liquidity', 'Verified liquidity'),
    ('trading_status', 'Trading-session and halt validation'),
    ('corporate_actions', 'Corporate-action continuity'),
    ('outcome_evidence', 'Evaluated outcome evidence'),
)

# An issue earlier in this sequence takes precedence independently of ranking.
GATES = (
    ('event_availability', 'NEEDS_EVENT_VERIFICATION'),
    ('instrument_identity', 'NEEDS_SECURITY_IDENTITY'),
    ('market_data', 'NEEDS_MARKET_DATA'),
    ('corporate_actions', 'NEEDS_CORPORATE_ACTION_REVIEW'),
    ('liquidity', 'NEEDS_LIQUIDITY_OR_HALT_VALIDATION'),
    ('trading_status', 'NEEDS_LIQUIDITY_OR_HALT_VALIDATION'),
)

UNKNOWN_MARKET_FIELDS = (
    'first_public_verified', 'security_mapping', 'current_price',
    'corporate_action_continuity', 'expected_return', 'return_outcome',
)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def _read_pin(root, path, size, digest):
    if type(size) is not int or size < 1 or size > 5_000_000:
        raise ValueError('Invalid evidence byte count')
    file_path = root / path
    with file_path.open('rb') as f:
        raw = f.read(size + 1)
    if len(raw) != size or sha(raw) != digest:
        raise ValueError('Evidence bytes do not match the pin: ' + path)
    return json.loads(raw)


def _require_idea(idea, source_pins):
    if (not THESIS.fullmatch(idea['id'])
            or idea['execution_ready'] is not False or idea['training_ready'] is not False
            or idea['actionability'] != 'UNPRICED_NOT_ACTIONABLE'
            or idea['status'] not in ('WATCH', 'ABSTAIN')):
        raise ValueError('Research-only idea identity or boundary changed')
    if any(idea['coverage'][field] is not None for field in UNKNOWN_MARKET_FIELDS):
        raise ValueError('New evidence requires a separately reviewed assessment version')
    if not idea['source_records'] or not idea['issuer_associations']:
        raise ValueError('Missing documentary source or issuer association')
    for row in idea['source_records']:
        if (row['execution_ready'] is not False or row['training_ready'] is not False
                or row['evidence_state'] != 'SOURCE_REVIEWED_WITH_LIMITS'
                or row['first_public_utc'] is not None
                or not row['source_ref']['key'] in source_pins
                or not HEX.fullmatch(row['source_ref']['object_sha256'])
                or not row['source_accessions'] or not row['issuer_associations']
                or not all(ACCESSION.fullmatch(x) for x in row['source_accessions'])
                or not all(CIK.fullmatch(x['issuer_cik']) for x in row['issuer_associations'])):
            raise ValueError('A reviewed source-bound documentary record is required')


def _assess_idea(idea, source_pins):
    _require_idea(idea, source_pins)
    values = {
        'source_identity': ('VERIFIED', 'The ranked source records are bound to accession and registrant CIK. A filing CIK does not identify a tradable share class.'),
        'event_content': ('VERIFIED', 'The linked source content was reviewed within its stated limits. It does not independently verify the claimed economic effect.'),
        'event_availability': ('UNKNOWN', 'No verified first-public time for this source-backed event. A filing date, acceptance clock or later observation is not first-public time.'),
        'instrument_identity': ('UNKNOWN', 'No effective-dated security or share-class mapping is verified for this thesis.'),
        'financial_comparability': ('NOT_ASSESSED', 'The ranking does not qualify the financial comparison. An exact reported period is not evidence of comparability.'),
        'market_data': ('UNKNOWN', 'The snapshot has no verified current executable price or permission-qualified market data for this thesis.'),
        'liquidity': ('UNKNOWN', 'No verified liquidity evidence for the intended instrument and time.'),
        'trading_status': ('UNKNOWN', 'Session eligibility and halt status have not been verified.'),
        'corporate_actions': ('UNKNOWN', 'No verified corporate-action continuity for the intended instrument.'),
        'outcome_evidence': ('NOT_ASSESSED', 'No qualified post-decision outcome was evaluated in this snapshot.'),
    }
    evidence = [{'id': key, 'state': values[key][0], 'detail': values[key][1]} for key, _ in CHECKS]
    pending = [(key, state) for key, state in GATES if values[key][0] != 'VERIFIED']
    # v1 covers only the bounded retrospective, unpriced research artifacts.
    # This code cannot promote a thesis or produce a trading instruction.
    blockers = [{'id': key, 'detail': values[key][1]} for key, _ in pending]
    return {
        'id': idea['id'],
        'evidence': {
            'verified': sum(x['state'] == 'VERIFIED' for x in evidence),
            'total': len(CHECKS),
            'checks': evidence,
        },
        'readiness': {
            'state': pending[0][1],
            'first_blocker': blockers[0],
            'blockers': blockers,
        },
    }


def _build_snapshot(snapshot, pin):
    if (snapshot['schema_version'] != 1 or snapshot['mode'] != 'RETROSPECTIVE_RESEARCH_PRIORITY'
            or snapshot['actionability'] != 'UNPRICED_NOT_ACTIONABLE'
            or snapshot['execution_ready'] is not False or snapshot['training_ready'] is not False
            or snapshot['provider_requests_made'] is not False or snapshot['counts']['actionable_trades'] != 0
            or snapshot['counts']['paper_trades_placed'] != 0):
        raise ValueError('Not a bounded retrospective research snapshot')
    assessments = [_assess_idea(x, snapshot['source_pins']) for x in snapshot['ideas']]
    if not 1 <= len(assessments) <= 10 or len({x['id'] for x in assessments}) != len(assessments):
        raise ValueError('Invalid displayed thesis membership')
    return {
        'schema_version': 1,
        'assessment_id': ASSESSMENT_ID,
        'cutoff_utc': snapshot['cutoff_utc'],
        'snapshot': pin,
        'checks': [{'id': key, 'label': label} for key, label in CHECKS],
        'assessments': assessments,
    }


def build(root):
    root = Path(root)
    results = {}
    for path, size, digest in SNAPSHOTS:
        manifest = _read_pin(root, path, size, digest)
        pin = manifest['snapshot']
        if (set(pin) != {'path', 'bytes', 'sha256'} or not HEX.fullmatch(pin['sha256'])
                or pin['path'] != BASE + 'snapshots/' + pin['sha256'] + '.json'):
            raise ValueError('Invalid content-addressed snapshot pin')
        snapshot = _read_pin(root, pin['path'], pin['bytes'], pin['sha256'])
        raw = encoded(_build_snapshot(snapshot, pin))
        results[BASE + 'assessments/' + sha(raw) + '.json'] = raw
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', default=Path(__file__).resolve().parents[1], type=Path)
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    results = build(args.root)
    for path, raw in results.items():
        if args.write:
            target = args.root / path
            target.parent.mkdir(parents=True, exist_ok=True)
            try:
                with target.open('xb') as handle:
                    handle.write(raw)
            except FileExistsError:
                if target.read_bytes() != raw:
                    raise ValueError('Immutable assessment collision')
        print(path, len(raw), sha(raw))


if __name__ == '__main__':
    main()
