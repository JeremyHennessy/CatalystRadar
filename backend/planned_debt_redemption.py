"""Offline, exact-original review of reported future redemption terms, not settlement."""
import argparse
import json
import re
import zipfile
from pathlib import Path
from financial_admission_rehearsal import plain
from filing_registrant_identity import digest, span, extract as identity
from material_agreement_screen import build as validate_archive, screen
from financial_pair_candidates import sha

ACCESSION = '0001628280-26-073584'
CIK = '0000042582'
SOURCE_SHA = '238617de38af3365b142edf1572e4123870a674196f4ef369a2f81df883e65a1'
TERMS = 'On November 13, 2026, The Goodyear Tire & Rubber Company (the “Company”) called for redemption $700 million in aggregate principal amount of its outstanding 4.875% Senior Notes Due 2027 (the “Notes”) on December 15, 2026 (the “Redemption Date”). The redemption price will be equal to 100% of the principal amount of the Notes being redeemed plus accrued and unpaid interest thereon to the Redemption Date.'
CAVEAT = 'This Current Report on Form 8-K is not a notice of redemption of the Notes. The redemption is being made solely pursuant to the Notice of Redemption, dated November 13, 2026, relating to the Notes.'

def inspect_context(raw):
    """Testable context checks; only build() admits the pinned original for publication."""
    filers = identity(raw, ACCESSION)['filers']
    if [(f['cik'], f['name_as_filed']) for f in filers] != [(CIK, 'GOODYEAR TIRE & RUBBER CO /OH/')]:
        raise ValueError('issuer identity')
    primary = screen(raw)['primary']
    if (primary['type_as_filed'], primary['filename']) != ('8-K', 'gt-20261113.htm'):
        raise ValueError('primary identity/amendment')
    s = primary['source_span']; doc = raw[s['byte_start']:s['byte_end']]
    # Whole reviewed contexts, not permissive keyword extraction. No hidden,
    # quoted, negated or extra qualifying text may be silently discarded.
    terms = raw[19300:19875]; caveat = raw[19904:20231]
    for part, expected in ((terms, TERMS), (caveat, CAVEAT)):
        if not re.fullmatch(rb'<div><span style="[^"]+">[^<>]*</span></div>', part):
            raise ValueError('reviewed context structure')
        if plain(part) != expected or doc.count(part) != 1:
            raise ValueError('whole context/ambiguity')
        if any(x in part.lower() for x in (b'display:none', b'visibility:', b'opacity:', b'font-size:0')):
            raise ValueError('hidden context')
    if not s['byte_start'] < 19300 < 20231 < s['byte_end']:
        raise ValueError('context outside primary')
    header = raw[:raw.index(b'</SEC-HEADER>')]
    if re.findall(rb'^ITEM INFORMATION:[ \t]*([^\r\n]+)', header, re.M) != [b'Regulation FD Disclosure']:
        raise ValueError('item context')
    return {'reported_terms': span(raw, 19300, 19875), 'notice_limitation': span(raw, 19904, 20231)}

def build(archive):
    audited = validate_archive(archive)  # Whole ten-member archive, receipts, identities and clocks.
    rows = [r for r in audited['packages'] if r['accession'] == ACCESSION]
    if len(rows) != 1 or rows[0]['source_sha256'] != SOURCE_SHA:
        raise ValueError('retained source binding')
    row = rows[0]
    with zipfile.ZipFile(archive) as z:
        raw = z.read(SOURCE_SHA + '.txt')
    if digest(raw) != SOURCE_SHA or sha(archive) != audited['provenance']['archive_sha256']:
        raise ValueError('source/archive changed')
    spans = inspect_context(raw)
    return {'schema_version': 1, 'provider_requests_made': False, 'category': 'REPORTED_PLANNED_DEBT_REDEMPTION',
        'finding_id': 'planned-redemption:' + CIK + ':' + ACCESSION,
        'issuer_cik': CIK, 'company_name_as_filed': 'GOODYEAR TIRE & RUBBER CO /OH/',
        'accession': ACCESSION, 'primary_filename': 'gt-20261113.htm',
        'status': 'ISSUER_REPORTED_REDEMPTION_CALL_NOT_COMPLETION',
        'source_url': row['source_url'], 'source_sha256': SOURCE_SHA,
        'source_bytes': len(raw), 'source_spans': spans, 'provenance': audited['provenance'],
        'source_observed_utc_as_recorded': row['source_observed_utc_as_recorded'],
        'reported_call_date': '2026-11-13', 'planned_redemption_date': '2026-12-15',
        'principal_as_reported': '700 million', 'principal_scaled_value': '700000000',
        'unit_as_reported': '$', 'currency_iso': None,
        'instrument_description_as_reported': '4.875% Senior Notes Due 2027',
        'coupon_percent_as_reported': '4.875', 'maturity_year_as_reported': '2027',
        'exact_maturity_date': None, 'redemption_percent_of_principal_as_reported': '100',
        'accrued_unpaid_interest_additional_as_reported': True, 'interest_amount': None,
        'filing_is_redemption_notice': False, 'referenced_notice_date': '2026-11-13',
        'referenced_notice_independently_reviewed': False,
        'redemption_completion_verified': False, 'actual_completion_date': None,
        'cash_change': None, 'net_debt_change': None, 'total_outstanding_principal': None,
        'security_id': None, 'first_public_utc': None, 'historical_availability_verified': False,
        'market_outcome_qualified': False, 'training_ready': False, 'execution_ready': False,
        'limitations': ['One retrospectively selected retained original, not market-wide discovery.',
            'Issuer-reported future redemption terms, not proof of payment, retirement or completion.',
            'The 8-K explicitly is not a redemption notice; the referenced notice is not independently reviewed.',
            'Dollar symbol does not independently establish ISO currency; interest and cash/debt changes are unknown.',
            'Coupon and redemption percentage are reported instrument terms, not market yields or executable prices.',
            'Observation clock is archive retrieval, not first-public availability. No verified security mapping or qualified outcome.']}

if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('--archive', required=True); p.add_argument('--out', required=True)
    a = p.parse_args(); result = build(a.archive)
    with Path(a.out).open('x', encoding='utf-8') as f:
        json.dump(result, f, indent=2, sort_keys=True); f.write('\n')
