"""Replay the second retrospective documentary ranking from exact reviewed public inputs."""
import argparse
from copy import deepcopy
import json
from pathlib import Path
import re

import research_priority as v1
from openfigi_evidence import read_pinned
from research_scanner import assoc, build_package, clock, digest, encoded

CUTOFF = '2026-11-19T20:10:08Z'
COHR = ('0000820318', '0001193125-26-467737')
WOR = ('0000108516', '0001193125-26-464853')
TXMD = ('0000025743', '0001213900-26-119697')
PINS = {
    'coherent': ('data/sec-observations/20261119T114159492631Z.json', 7373, '10b3c74b4949b1d23d850a9c822f052343dac979fa1112f3723c37fda81100bc'),
    'sec_repeat': ('data/sec-observations/20261119T193148867794Z.json', 7377, 'be97f6b0e9ee936072bab704619bdebd2b2d962f0929590422153ed6969bfadc'),
    'coherent_review': ('docs/research/coherent-saved-repurchase-authorization.md', 3100, '75597457d23626ee7d8bc38d46075e3e44bf283a5a62757311dcbbd8ac06e727'),
    'coherent_metadata': ('data/sec-snapshots/c0f3a419d2d23b0966097f86fc70ae90bdceeb911620a4674c07e60937591d52.json', 159944, 'c0f3a419d2d23b0966097f86fc70ae90bdceeb911620a4674c07e60937591d52'),
    'worthington_review': ('docs/research/worthington-saved-observation-chronology.md', 9007, '806eab291a9d967394916a17619e408198f2844264913dce9cd04a1b02b5077d'),
    'txmd_companion': ('web/company-findings/txmd-companion-10q.json', 4613, '72a69128b92c968f4b2777fc106decb7e4b5ef74ae1f3f740243b091f7bbb6cd'),
    'txmd_release_clock': ('web/company-findings/txmd-declared-publication-clocks.json', 1976, '265f775ba3a9a693fa63fef78310b6bc6a5300ec59e727e086c7c16a2d8e5139'),
}
ORIGINAL_COHR_SHA = 'aef701901dc28af1cdd0b0b543e01a74fccd77fa45fa274be81090383798d983'

RUBRIC = deepcopy(v1.RUBRIC)
RUBRIC.update(
    id='documentary-research-priority-v2', declared_cutoff_utc=CUTOFF,
    selection=(
        'The same 905 records of the pinned released scanner plus a fixed three-record '
        'source-reviewed extension. Coherent Item 7.01 authorization and the TherapeuticsMD '
        'companion 10-Q license context are eligible as documentary research only. '
        'The Worthington earlier-disclosure comparison is a negative control, not a novelty verdict.'
    ),
    not_evaluated_extensions=[
        'Unreviewed filings outside the pinned scanner and three bounded follow-up records',
        'Whole-document novelty, market reaction and the separate TherapeuticsMD 8-K quarter-description conflict',
    ],
)
RUBRIC['rules']['extension_policy'] = (
    'Only the exact reviewed issuer/accession pairs in the fixed extension qualify under the two '
    'new categories. Repeated collection does not create another event or change the filing-age input. '
    'License milestone year-end labels are not an exact source period.'
)


def _input(root, key):
    path, size, expected = PINS[key]
    location = root / path
    if path.endswith('.json'):
        result, length = read_pinned(location, expected, size)
        if length != size:
            raise ValueError('source byte count changed')
        return result
    with location.open('rb') as handle:
        data = handle.read(size + 1)
    if len(data) != size or v1.sha(data) != expected:
        raise ValueError('reviewed source bytes changed')
    return data


def _record(key, pointer, source, identity, category, name, title, summary, clocks,
            path, unknowns, next_action, reviewed=True):
    cik, accession = identity
    return {
        'id': key+':'+v1.sha((pointer+'|'+cik+'|'+accession).encode())[:24],
        'category': category, 'evidence_state': 'SOURCE_REVIEWED_WITH_LIMITS' if reviewed else 'ORIGINAL_REVIEW_REQUIRED',
        'issuer_associations': [assoc(cik, [name])], 'source_accessions': [accession],
        'title': title, 'summary': summary, 'clocks': clocks, 'first_public_utc': None,
        'source_ref': {'key':key, 'json_pointer':pointer, 'object_sha256':digest(source)},
        'investigation_path': path, 'navigation_status':'EXISTING_PAGE_OR_SECTION_NOT_AUTOMATIC_RECORD_SELECTION',
        'unknowns':unknowns, 'next_action':next_action, 'dossier_ciks':[],
        'training_ready':False, 'execution_ready':False,
    }


def _receipt(value, trigger):
    if (value['github_event_name'] != trigger or value['configured_issuers'] != 10
            or value['successful_issuers'] != 10 or value['metadata_window_complete'] is not True
            or value['eligible_count'] != 0 or value['orders_created'] != 0 or value['errors']
            or not value['sources'] or any(s['status'] != 200 for s in value['sources'])
            or v1.dt(value['finished_at']) > v1.dt(CUTOFF)):
        raise ValueError('receipt boundary')
    candidates = {}
    for i, event in enumerate(value['events']):
        pair = (event['issuer_cik'], event['accession'])
        if (pair in candidates or event['eligible'] is not False or event['first_public_utc'] is not None
                or event['status'] != 'METADATA_DISCOVERY_NOT_ELIGIBLE'
                or not v1.dt(event['sec_accepted_utc']) <= v1.dt(event['observed_utc']) <= v1.dt(value['finished_at'])):
            raise ValueError('receipt event boundary')
        candidates[pair] = (i, event)
    if set(candidates) != {COHR, WOR}:
        raise ValueError('unreviewed receipt members')
    return candidates


def extensions(root):
    push = _receipt(_input(root, 'coherent'), 'push')
    repeat = _receipt(_input(root, 'sec_repeat'), 'schedule')
    for pair in push:
        p, r = push[pair][1], repeat[pair][1]
        if any(p[k] != r[k] for k in ('issuer_cik', 'accession', 'source_metadata_sha256', 'sec_accepted_utc', 'form', 'items_raw')):
            raise ValueError('scheduled re-observation identity differs')
        if v1.dt(p['observed_utc']) >= v1.dt(r['observed_utc']):
            raise ValueError('re-observation order')
    cohr_position, cohr = push[COHR]
    doc = _input(root,'coherent_review')
    metadata = _input(root,'coherent_metadata')
    if (cohr['source_metadata_sha256'] != PINS['coherent_metadata'][2] or str(metadata['cik']).zfill(10) != COHR[0]
            or ORIGINAL_COHR_SHA.encode() not in doc):
        raise ValueError('Coherent reviewed source association')
    filings = metadata['filings']['recent']
    positions = [i for i, accession in enumerate(filings['accessionNumber']) if accession == COHR[1]]
    if len(positions) != 1:
        raise ValueError('Coherent accession not unique')
    (i,) = positions
    filing = {key:filings[key][i] for key in ('filingDate','reportDate','acceptanceDateTime','form','items')}
    if (filing['filingDate'] != '2026-11-19' or filing['reportDate'] != '2026-11-18'
            or filing['acceptanceDateTime'] != cohr['sec_accepted_utc']
            or (filing['form'],filing['items']) != ('8-K','7.01')):
        raise ValueError('Coherent filing context')
    cohr_record = _record(
        'coherent',f'/events/{cohr_position}',cohr,COHR,'REPORTED_REPURCHASE_AUTHORIZATION',cohr['issuer'],
        'Coherent board authorized up to US$2.0 billion of common-stock repurchases',
        'The issuer-hosted 8-K reports the November 18 authorization cap, excluding fees and other related expenses. '
        'The program has no expiry, requires no share quantity and can be suspended. The filing does not disclose completed purchases or spending.',
        [clock('filing_date_as_reported',filing['filingDate']),clock('board_authorization_date_as_reported',filing['reportDate']),
         clock('sec_acceptance_utc_as_recorded',cohr['sec_accepted_utc']),
         clock('metadata_observation_utc_as_recorded',cohr['observed_utc'])],
        'collectors.html#coherent-saved-case',
        ['The cap is not cash spent or completed purchases; filing silence does not prove zero purchases.',
         'A later scheduled poll saw the same accession and metadata hash, not a fresh event or an authenticated public clock.',
         'Original issuer HTML was reviewed; the saved receipt alone proves only metadata observation.'],
        'Inspect Item 7.01 and look for separately reported executed repurchases before drawing any capital-allocation conclusion.')
    txmd = _input(root,'txmd_companion')
    _input(root,'txmd_release_clock')
    if ((txmd['issuer_cik'],txmd['accession']) != TXMD or txmd['form'] != '10-Q'
            or txmd['first_public_utc'] is not None or txmd['qualified_outcomes'] != 0
            or txmd['execution_ready'] is not False or txmd['training_ready'] is not False
            or txmd['separate_release']['accession'] != '0001213900-26-119681'
            or txmd['separate_release']['clock_sidecar_sha256'] != PINS['txmd_release_clock'][2]
            or txmd['acceptance_comparison']['ten_q_raw_header'] != '20261113160749'
            or txmd['source']['http_status'] != 200):
        raise ValueError('TXMD companion source association')
    n8,n14,mda = txmd['findings']
    if (n8['id'],n8['amount_currency'],n8['amount_as_reported'],n8['sales_year_end'],n8['recognized_quarter_end'],
        n14['id'],n14['before_currency'],n14['before_as_reported'],n14['after_currency'],n14['after_as_reported'],
        n14['sales_year_end'],n14['amendment_date'],mda['id']) != (
        'NOTE8_2025_MILESTONE','CAD','500.0 thousand','2025-12-31','2026-09-30',
        'NOTE14_2026_MILESTONE','CAD','1.0 million','CAD','approximately 0.1 million',
        '2026-12-31','2026-11-10','MDA_RATE_AND_EXPECTATION'):
        raise ValueError('TXMD review facts changed')
    txmd_record = _record(
        'txmd_companion','',txmd,TXMD,'REPORTED_LICENSE_MILESTONE_CONTEXT','TherapeuticsMD, Inc.',
        'TherapeuticsMD 10-Q distinguishes two IMVEXXY sales milestone years',
        'Note 8 reports CAD 500,000 for calendar 2025 recognized in the quarter ended September 30, 2026. '
        'Separately, Note 14 says a November 10 amendment changed the calendar-2026 amount owed from CAD 1.0 million '
        'to about CAD 100,000 for historical overpayments. The MD&A describes an unchanged future royalty rate and a lower issuer revenue expectation.',
        [clock('filing_date_as_reported','2026-11-13'),clock('amendment_date_as_reported',n14['amendment_date']),
         clock('raw_10q_observed_utc_as_recorded',txmd['source']['observed_utc'])],
        'financial-review.html#txmd-companion-10q',txmd['limitations'],
        'Compare Notes 8 and 14 against later recognition and cash disclosures, without merging the separate 8-K clock.')
    wor_position, wor = push[WOR]
    _input(root,'worthington_review')
    wor_record = _record(
        'coherent',f'/events/{wor_position}',wor,WOR,'EARLIER_DISCLOSURE_COMPARISON',wor['issuer'],
        'Worthington conference transcript: bounded earlier-disclosure comparison',
        'Six specified claims were compared. The same filing was observed again; first-public timing and whole-document novelty remain unknown.',
        [clock('sec_acceptance_utc_as_recorded',wor['sec_accepted_utc']),
         clock('metadata_observation_utc_as_recorded',wor['observed_utc'])],
        'collectors.html#worthington-saved-chronology',
        ['Matched claims are not independent new events; unreviewed statements retain unknown novelty.'],
        'Read the pinned chronology and compare individual statements before inferring novelty.', reviewed=False)
    return [cohr_record, txmd_record, wor_record], {wor_record['id']:'EARLIER_DISCLOSURE_CONTROL_NO_NEW_QUALIFIED_FACT'}


def build(root):
    root = Path(root)
    first = v1.build(root)
    for path, expected in first.items():
        if (root / path).read_bytes() != expected:
            raise ValueError('immutable original ranking changed')
    index, package = build_package(root)
    reviewed, excludes = extensions(root)
    index['records'] += reviewed
    index['sources'] = {**index['sources'], **{key:{'path':path,'bytes':size,'sha256':sha} for key,(path,size,sha) in PINS.items()}}
    index['coverage']['scope'] = (
        '905 retained scanner records plus three reviewed follow-up records (two rankable, one excluded control). '
        'Not marketwide, point-in-time, predictive or executable.'
    )
    result = v1._project(index,CUTOFF,RUBRIC,v1.ELIGIBLE|{
        'REPORTED_REPURCHASE_AUTHORIZATION','REPORTED_LICENSE_MILESTONE_CONTEXT'},excludes)
    result['limitations'][2] = 'Seven supported entries; no placeholders added to reach ten.'
    result['input_snapshot'] = v1.pin(v1.OUTPUT,package[v1.OUTPUT])
    rubric_raw = encoded(RUBRIC)
    result['rubric_sha256'] = v1.sha(rubric_raw)
    snapshot_raw = encoded(result)
    snapshot_path = v1.BASE+'snapshots/'+v1.sha(snapshot_raw)+'.json'
    rubric_path = v1.BASE+'rubrics/'+v1.sha(rubric_raw)+'.json'
    manifest_raw = encoded({'schema_version':1,'snapshot':v1.pin(snapshot_path,snapshot_raw),
        'rubric':v1.pin(rubric_path,rubric_raw),'execution_ready':False,'training_ready':False})
    manifests = v1.BASE+'releases/'+v1.sha(manifest_raw)+'.json'
    return {snapshot_path:snapshot_raw,rubric_path:rubric_raw,manifests:manifest_raw}


def verify_originals(coherent_path, txmd_path, companion):
    """Optional local-file recheck. Neither original goes into published output."""
    from lxml import html
    coherent = Path(coherent_path).read_bytes()
    if len(coherent) != 29296 or v1.sha(coherent) != ORIGINAL_COHR_SHA:
        raise ValueError('Coherent original bytes')
    cohr_text = ' '.join(html.fromstring(coherent).text_content().split())
    if not all(term in cohr_text for term in (
            'On November 18, 2026', 'up to $2.0 billion of its common stock', 'exclusive of any fees',
            'has no expiration date', 'does not obligate the Company', 'may be suspended or discontinued')):
        raise ValueError('Coherent original terms')
    if COHR[0].encode() not in coherent or COHR[1].encode() not in coherent:
        raise ValueError('Coherent original identity')
    raw = Path(txmd_path).read_bytes()
    source = companion['source']
    if len(raw) != source['raw_bytes'] or v1.sha(raw) != source['raw_sha256']:
        raise ValueError('TXMD original bytes')
    header = raw.split(b'<DOCUMENT>',1)[0]
    if (TXMD[1].encode() not in header or not re.search(rb'CENTRAL INDEX KEY:\s+0000025743',header)
            or not re.search(rb'FILED AS OF DATE:\s+20261113',header)
            or b'<ACCEPTANCE-DATETIME>20261113160749' not in header):
        raise ValueError('TXMD original identity or clock')
    primary, = [d for d in re.findall(rb'<DOCUMENT>.*?</DOCUMENT>',raw,re.S)
                if re.search(rb'<TYPE>10-Q\s',d.split(b'<TEXT>',1)[0])]
    if b'<FILENAME>ea0308826-10q_therapeutics.htm' not in primary.split(b'<TEXT>',1)[0]:
        raise ValueError('TXMD primary document name')
    body = primary[primary.index(b'<html'):primary.rindex(b'</html>')+7]
    if v1.sha(body) != source['primary_html_sha256']:
        raise ValueError('TXMD primary HTML hash')
    normalized = ' '.join(html.fromstring(body).text_content().split())
    for key, span in source['evidence_spans'].items():
        text = normalized[span['normalized_character_start']:span['normalized_character_end']]
        if v1.sha(text.encode()) != span['normalized_utf8_sha256']:
            raise ValueError('TXMD normalized span: '+key)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1])
    parser.add_argument('--write',action='store_true')
    parser.add_argument('--verify-originals',nargs=2,metavar=('COHR_HTML','TXMD_SUBMISSION'))
    args = parser.parse_args()
    if args.verify_originals:
        verify_originals(*args.verify_originals,_input(args.root,'txmd_companion'))
    outcome = build(args.root)
    for path, raw in outcome.items():
        if args.write:
            target = args.root / path
            target.parent.mkdir(parents=True,exist_ok=True)
            try:
                with target.open('xb') as handle:
                    handle.write(raw)
            except FileExistsError:
                if target.read_bytes() != raw:
                    raise ValueError('immutable output collision')
    print(json.dumps({path:v1.pin(path,raw) for path,raw in outcome.items()},sort_keys=True))


if __name__ == '__main__':
    main()
