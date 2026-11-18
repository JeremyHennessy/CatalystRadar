"""Reproduce a frozen diagnostic cohort; audit originals without promoting facts.

No network, selection replacement, exact-period inference, or trading action.
"""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile
from inline_context_evidence import parse

STRATA = ('cross_batch_numerically_equal', 'cross_batch_different_reported_numbers',
          'within_batch_repeated_context')

def bounded_read(path, limit):
    with Path(path).open("rb") as f:
        raw = f.read(limit + 1)
    if len(raw) > limit:
        raise ValueError("input byte bound exceeded")
    return raw

def digest(raw):
    return hashlib.sha256(raw).hexdigest()

def select(plan, groups):
    if plan['strata'] != list(STRATA) or plan['per_stratum'] != 2:
        raise ValueError('unsupported frozen selection policy')
    buckets = {s: [] for s in STRATA}
    ids = set()
    for g in groups:
        if g['context_id'] in ids:
            raise ValueError('duplicate context')
        ids.add(g['context_id'])
        if g['category'] != 'multiple_accession_context':
            continue
        if g['numeric_relation'] not in {'numerically_equal', 'different_reported_numbers'}:
            raise ValueError('unknown numeric relation')
        key = ('cross_batch_' + g['numeric_relation']) if g['cross_batch'] else STRATA[2]
        buckets[key].append(g)
    result = []
    for s in STRATA:
        if len(buckets[s]) < 2:
            raise ValueError('insufficient stratum; no substitution')
        result.extend((s, g) for g in sorted(buckets[s], key=lambda g: g['context_id'])[:2])
    return result

def build(plan_path, selection_path, groups_path, originals):
    """Originals: explicit local package receipts, never an exhaustive inventory claim."""
    plan_bytes = bounded_read(plan_path, 64_000)
    plan = json.loads(plan_bytes)
    selection_bytes = bounded_read(selection_path, 64_000)
    selected = json.loads(selection_bytes)
    raw = bounded_read(groups_path, 10_000_000)
    if digest(raw) != plan['input_groups_sha256'] or selected['plan_sha256'] != digest(plan_bytes):
        raise ValueError('frozen input hash mismatch')
    cases = select(plan, json.loads(raw))
    identities = [{'stratum': s, 'context_id': g['context_id']} for s, g in cases]
    if identities != selected['cases']:
        raise ValueError('frozen selection mismatch; no substitution')
    if not isinstance(originals, list) or len(originals) > 100:
        raise ValueError("original inventory bound exceeded")
    inventory = {}
    for entry in originals:
        receipt_raw = bounded_read(entry['receipt'], 1_000_000)
        if digest(receipt_raw) != entry['receipt_sha256']:
            raise ValueError('receipt hash mismatch')
        receipt = json.loads(receipt_raw)
        package = bounded_read(entry['package'], 50_000_000)
        if digest(package) != receipt['zip_sha256'] or len(package) != receipt['zip_byte_count']:
            raise ValueError('original package mismatch')
        accession = receipt['accession']
        if accession in inventory:
            raise ValueError('duplicate original accession')
        import io
        with zipfile.ZipFile(io.BytesIO(package)) as z:
            member = receipt['primary_member']
            if len([i for i in z.infolist() if i.filename == member]) != 1:
                raise ValueError('missing/duplicate primary member')
            if z.getinfo(member).file_size > 10_000_000:
                raise ValueError('oversize primary member')
            facts = parse(z.read(member), receipt['primary_member_sha256'])
        cik = str(receipt['issuer_cik_verified']).zfill(10)
        if any(str(f['issuer_identifier_as_filed']).zfill(10) != cik for f in facts):
            raise ValueError('original issuer conflict')
        inventory[accession] = (cik, facts, receipt)
    rows = []
    for stratum, group in cases:
        observations = []
        for o in group['observations']:
            cik = str(group['context']['issuer_cik']).zfill(10)
            original = inventory.get(o['accession'])
            if original and original[0] != cik:
                raise ValueError('cohort original issuer conflict')
            candidates = [f for f in original[1] if f['concept']['local_name'] == group['context']['tag']] if original else []
            observations.append({'accession': o['accession'],
                'source_rowid': o['source_rowid'], 'database_sha256': o['database_sha256'],
                'original_status': 'RETAINED_REQUIRES_CONTEXT_REVIEW' if original else 'NOT_IN_CHECKED_INVENTORY',
                'original_sha256': original[2]['zip_sha256'] if original else None,
                'same_issuer_concept_candidates': [{'fact_id': f['fact_id'], 'period': f['period'],
                    'unit': f['unit'], 'dimension_or_scenario_present': f['dimension_or_scenario_present'],
                    'declared_decimals': f['decimals_as_filed']} for f in candidates],
                'exact_archive_to_original_match_verified': False,
                'blockers': ['EXACT_CONTEXT_MATCH_UNVERIFIED', 'ACCOUNTING_COMPARABILITY_UNVERIFIED',
                             'HISTORICAL_AVAILABILITY_UNVERIFIED', 'SECURITY_AND_OUTCOME_UNQUALIFIED'] +
                            ([] if original else ['ORIGINAL_NOT_IN_CHECKED_INVENTORY'])})
        rows.append({'context_id': group['context_id'], 'stratum': stratum, 'issuer_cik': cik,
            'metric': group['context']['tag'], 'rounded_ddate': group['context']['ddate'],
            'rounded_qtrs': group['context']['qtrs'], 'observations': observations,
            'qualified': False, 'status': 'ABSTAIN', 'growth': None})
    return {'version': 1, 'scope': 'FROZEN_RETROSPECTIVE_DIAGNOSTIC_NOT_REPRESENTATIVE_TRAINING_SAMPLE',
        'plan_sha256': digest(plan_bytes), 'selection_sha256': digest(selection_bytes),
        'groups_sha256': digest(raw), 'checked_original_accessions': sorted(inventory),
        'cases': rows, 'qualified_cases': 0, 'execution_ready': False,
        'limitations': ['Same issuer and concept identifies candidates only, not exact period/unit matching.',
          'Absent means absent only from the supplied verified inventory, not unavailable at SEC.',
          'Selection is frozen; no replacement based on source availability or outcomes.',
          'No numerical financial values, growth rates, security joins or outcomes generated.']}

if __name__ == '__main__':
    p = argparse.ArgumentParser();p.add_argument('plan');p.add_argument('selection');p.add_argument('groups');p.add_argument('originals');p.add_argument('output');a = p.parse_args()
    result = build(a.plan, a.selection, a.groups, json.loads(bounded_read(a.originals, 64_000)))
    with Path(a.output).open('x') as f:
        json.dump(result, f, indent=2);f.write('\n')
