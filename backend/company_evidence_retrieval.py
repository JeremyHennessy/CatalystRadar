"""Read-only deterministic retrieval from one rebuilt public company snapshot."""
import argparse
import hashlib
import json
import re
import sys
import unicodedata
from pathlib import Path
sys.dont_write_bytecode = True  # CLI imports must not create repository cache files.
import company_investigation as source
from openfigi_evidence import read_pinned

INDEX = {'path': source.BASE+'index.json', 'bytes': 1834945, 'sha256': 'c488e6b0aab25ef2e8b0434e2a518bfb44c03af93c4bbba5ec6dd42682ada013'}
SECTIONS = ('prepared', 'insider', 'disclosure', 'scanner')
MAX_OUTPUT = 250000

def normalize_name(value):
    if not isinstance(value, str) or not 1 <= len(value) <= 120 or any(unicodedata.category(c).startswith('C') for c in value):
        raise ValueError('name bounds/control')
    result = ' '.join(unicodedata.normalize('NFC', value).casefold().split())
    if not result or len(result) > 240:
        raise ValueError('empty/expanded name')
    return result

def exact_cik(value):
    if not isinstance(value, str) or not re.fullmatch('[0-9]{1,10}', value) or not int(value):
        raise ValueError('ASCII nonzero CIK required')
    return value.zfill(10)

def bounds(limit, offset, maximum):
    if type(limit) is not int or not 1 <= limit <= maximum or type(offset) is not int or not 0 <= offset <= 100000:
        raise ValueError('page bounds')

def pinned(root, pin):
    obj, size = read_pinned(Path(root)/pin['path'], pin['sha256'], pin['bytes'])
    if size != pin['bytes']:
        raise ValueError('size mismatch')
    return obj

def load(root):
    """No cache: verify published bytes and rebuild all public source associations."""
    index = pinned(root, INDEX)
    rebuilt, _ = source.build(root)
    if rebuilt != index:
        raise ValueError('snapshot rebuild mismatch')
    return index

def envelope(index):
    return {'snapshot': INDEX, 'source_versions': index['sources'], 'scope': index['counts'],
            'limitations': index['limitations'], 'execution_ready': False, 'training_ready': False,
            'provider_requests_made': False, 'first_public_utc': None}

def search(index, name=None, cik=None, section=None, limit=20, offset=0):
    """index must come from load(); matching is literal, never ticker resolution."""
    bounds(limit, offset, 20)
    if section is not None and section not in SECTIONS:
        raise ValueError('section')
    query = normalize_name(name) if name is not None else None
    ci = exact_cik(cik) if cik is not None else None
    matches = []
    for r in index['directory']:
        labels = [s for s in r['names_as_reported'] if query is None or query in normalize_source_label(s)]
        if query is None or labels:
            matches.append((r, labels))
    global_count = len(matches) if query is not None else None
    count_key = {'prepared':'prepared_batches','insider':'insider_filings','disclosure':'disclosure_filings','scanner':'scanner_records'}
    rows = [{'company':r, 'matched_source_labels':labels if query is not None else [],
             'company_url':company_url(r['issuer_cik'])} for r,labels in matches
            if (ci is None or r['issuer_cik']==ci) and (section is None or r['source_counts'][count_key[section]]>0)]
    out = envelope(index)
    out.update(mode='search', query={'name':name,'issuer_cik':ci,'section':section},
               global_name_matching_ciks=global_count, name_ambiguous=global_count is not None and global_count>1,
               exact_cik_coverage=('IN_FIXED_COMPANY_COHORT' if any(r['issuer_cik']==ci for r in index['directory']) else 'OUTSIDE_FIXED_COHORT_UNASSESSED') if ci else None,
               total_records=len(rows), offset=offset, records=rows[offset:offset+limit])
    return finish_page(out, limit)

def normalize_source_label(s):
    return ' '.join(unicodedata.normalize('NFC', s).casefold().split())

def company_url(ci):
    return 'https://jeremyhennessy.github.io/CatalystRadar/web/datasets.html?company_cik='+ci+'#company-investigation'

def evidence(root, index, cik, section, limit=5, offset=0):
    bounds(limit, offset, 5)
    ci = exact_cik(cik)
    if section not in SECTIONS:
        raise ValueError('section')
    out = envelope(index)
    out.update(mode='evidence', issuer_cik=ci, section=section, company_url=company_url(ci), offset=offset)
    entries = [r for r in index['directory'] if r['issuer_cik']==ci]
    if not entries:
        out.update(coverage='OUTSIDE_FIXED_COHORT_UNASSESSED', total_records=None, records=[], returned_records=0, next_offset=None)
        return out
    if len(entries)!=1:
        raise ValueError('duplicate company')
    b = entries[0]['detail_bucket']
    pins = [p for p in index['detail_shards'] if p['bucket']==b]
    if len(pins)!=1 or pins[0]['path']!=source.BASE+'details/'+b+'.json':
        raise ValueError('company shard path')
    shard = pinned(root, pins[0])
    if shard['bucket']!=b or [r['issuer_cik'] for r in shard['companies']]!=pins[0]['issuer_ciks'] or len(set(pins[0]['issuer_ciks']))!=len(pins[0]['issuer_ciks']):
        raise ValueError('company shard membership')
    companies = [r for r in shard['companies'] if r['issuer_cik']==ci]
    if len(companies)!=1:
        raise ValueError('company membership')
    selected = companies[0][section]
    out.update(coverage=selected['status'], company_shard=pins[0], source_context=index['source_context'])
    if section=='insider':
        reference = selected['record']
        rows=[]
        if reference is not None:
            p=reference['filing_detail_shard']
            if p['path']!='web/insider-full/v1/details/'+p['bucket']+'.json' or p['byte_count']>1000000:
                raise ValueError('insider shard path/bound')
            obj=pinned(root, {'path':p['path'],'bytes':p['byte_count'],'sha256':p['sha256']})
            identities=[r['issuer_cik'] for r in obj['issuers']]
            if obj['bucket']!=p['bucket'] or len(identities)!=len(set(identities)) or identities.count(ci)!=1:
                raise ValueError('insider membership')
            issuer=next(r for r in obj['issuers'] if r['issuer_cik']==ci)
            seen=set()
            for i,r in enumerate(issuer['filings']):
                key=(r['batch_id'],r['accession'])
                if key in seen or r['issuer_cik']!=ci:
                    raise ValueError('duplicate/wrong-CIK filing')
                seen.add(key)
                rows.append({'source_record':r,'source_ref':{'path':p['path'],'issuer_cik':ci,'filing_index':i,'object_sha256':source.digest(r)}})
            if len(rows)!=reference['source_record']['filings'] or sum(x['source_record']['selected_transaction_rows'] for x in rows)!=reference['source_record']['selected_transaction_rows']:
                raise ValueError('insider conservation')
            out['insider_source_summary']=reference
    else:
        rows=selected['records']
        seen=set()
        for row in rows:
            ref=row['source_ref']; key=(ref['key'],ref['json_pointer'])
            r=row['source_record']
            membership=(r['cik']==ci if section=='prepared' else r['issuer_cik']==ci if section=='disclosure' else any(a['issuer_cik']==ci for a in r['issuer_associations']))
            if key in seen or not membership or source.digest(r)!=ref['object_sha256']:
                raise ValueError('duplicate/reference/identity mismatch')
            seen.add(key)
    out.update(total_records=len(rows), records=rows[offset:offset+limit])
    return finish_page(out,limit)

def finish_page(out, limit):
    out['returned_records']=len(out['records'])
    out['next_offset']=out['offset']+limit if out['offset']+limit<out['total_records'] else None
    return out

def output_bytes(result):
    raw=source.encoded(result)
    if len(raw)>MAX_OUTPUT:
        raise ValueError('output bound')
    return raw

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('mode', choices=('search','evidence'))
    p.add_argument('--root',default=str(Path(__file__).resolve().parents[1]))
    p.add_argument('--name');p.add_argument('--cik');p.add_argument('--section',choices=SECTIONS)
    p.add_argument('--limit',type=int);p.add_argument('--offset',type=int,default=0)
    a=p.parse_args()
    try:
        if a.mode=='evidence' and (a.name is not None or a.cik is None or a.section is None):
            raise ValueError('evidence requires CIK/section, no name')
        index=load(a.root)
        result=search(index,a.name,a.cik,a.section,a.limit if a.limit is not None else 20,a.offset) if a.mode=='search' else evidence(a.root,index,a.cik,a.section,a.limit if a.limit is not None else 5,a.offset)
        raw=output_bytes(result)
    except (ValueError,KeyError,TypeError,OSError,IndexError):
        print('Company evidence retrieval failed validation; no result.',file=sys.stderr)
        return 2
    sys.stdout.buffer.write(raw)
    return 0
if __name__=='__main__':
    raise SystemExit(main())
