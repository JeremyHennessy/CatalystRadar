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

LAYER_PINS = {
    'offerings': {'path':'web/company-findings/formd-notice-history.json','bytes':450574,'sha256':'38b21e9f921c6be5ce8db840d9f400d0dcb1ff8b9a25709cb451fbdad4db3d22'},
    'going_concern': {'path':'web/company-findings/going-concern-contexts.json','bytes':304958,'sha256':'4aef0578d20f4f391decf33738917ae4c7e97d36d38ea2f41b69704e666f0170'},
    'assertions': {'path':'web/company-findings/financial-assertion-audit.json','bytes':44334,'sha256':'1540ffdad2a5b31ee8bd024657621cd1d08c3e551903aa9b2e3275372d6eab90'}}
LAYER_SECTIONS = tuple(LAYER_PINS)


def validate_layer(index, section, obj):
    """Validate a pinned public projection, not a fresh original-document audit."""
    cohort=[r['issuer_cik'] for r in index['directory']]
    if len(cohort)!=len(set(cohort)) or obj['schema_version']!=1 or any(obj[k] is not False for k in ('training_ready','execution_ready','provider_requests_made')):
        raise ValueError('layer cohort/schema/qualification')
    members=set(cohort); groups={}; seen=set()
    def add(ci, rid, pointer, record):
        if ci not in members or exact_cik(ci)!=ci or (ci,rid) in seen:
            raise ValueError('layer membership/duplicate')
        seen.add((ci,rid));groups.setdefault(ci,[]).append({'record_id':rid,'source_record':record,'source_ref':{'path':LAYER_PINS[section]['path'],'json_pointer':pointer,'object_sha256':source.digest(record)}})
    if section in ('offerings','going_concern'):
        if obj['cohort_ciks']!=cohort or obj['sources']['cohort']!={'path':INDEX['path'],'sha256':INDEX['sha256']}:
            raise ValueError('sidecar cohort pin')
        company_seen=set(); ids=set()
        for i,company in enumerate(obj['companies']):
            ci=company['issuer_cik']
            if ci in company_seen or not company['records']:
                raise ValueError('duplicate/empty sidecar company')
            company_seen.add(ci)
            for j,r in enumerate(company['records']):
                if r['issuer_cik']!=ci or not re.fullmatch('[0-9]{10}-[0-9]{2}-[0-9]{6}',r['accession']):
                    raise ValueError('sidecar record identity')
                source.dt.date.fromisoformat(r['filing_date_as_reported'])
                if r['first_public_utc'] is not None or r['event_date'] is not None:
                    raise ValueError('unreviewed event/public clock')
                if section=='offerings':
                    if company['status']!='RETAINED_FORM_D_NOTICE_METADATA' or r['form_as_filed'] not in ('D','D/A') or r['amendment_flag'] not in ('FALSE_AS_REPORTED','TRUE_AS_REPORTED') or r['previous_accession_status'] not in ('MISSING_AS_REPORTED','OUTSIDE_RETAINED_BATCH','PRESENT_IN_RETAINED_BATCH') or r['primary_issuer_as_reported']!='YES' or r['financing_completion_verified'] is not False or r['security_identity_verified'] is not False:
                        raise ValueError('offering status')
                    rid=ci+':'+r['accession']+':'+str(r['source_rows']['ISSUERS']['rowid'])
                else:
                    allowed={'textBlock':('UNINTERPRETED_DISCLOSURE',None),'boolean':('FALSE_AS_REPORTED',False),'string':('UNINTERPRETED_SPECIFIC_STRING_DISCLOSURE',None)}
                    if r['datatype'] not in allowed or (r['status']!=allowed[r['datatype']][0] or r['boolean_value_as_reported'] is not allowed[r['datatype']][1]) or r['qualification']!='PREPARED_SOURCE_NOT_ORIGINAL_QUALIFIED' or r['risk_conclusion'] is not None:
                        raise ValueError('going-concern interpretation')
                    rid=r['id']
                if rid in ids:raise ValueError('duplicate source record ID')
                ids.add(rid);add(ci,rid,f'/companies/{i}/records/{j}',r)
        from collections import Counter
        records=[r['source_record'] for rows in groups.values() for r in rows]
        if section=='offerings':
            if obj['status']!='HISTORICAL_COMPANY_FORM_D_NOTICES_NOT_FINANCING_EVENTS' or obj['counts']['selected_issuer_associations']!=len(records) or obj['counts']['selected_distinct_submissions']!=len({r['accession'] for r in records}) or obj['counts']['forms']!=dict(Counter(r['form_as_filed'] for r in records)):
                raise ValueError('offering source census')
        else:
            if obj['status']!='PREPARED_GOING_CONCERN_CONTEXTS_FOR_ORIGINAL_REVIEW_NOT_RISK_CLASSIFICATION' or obj['counts']['selected_contexts']!=len(records) or obj['counts']['selected_filings']!=len({r['accession'] for r in records}) or obj['counts']['status_counts']!=dict(Counter(r['status'] for r in records)):
                raise ValueError('going-concern source census')
        expected=(187,223) if section=='offerings' else (97,123)
        if (len(groups),len(ids))!=expected or obj['counts']['selected_ciks']!=len(groups):
            raise ValueError('sidecar conservation')
    elif section=='assertions':
        if obj['status']!='SOURCE_REPORTED_ASSERTION_AND_ARITHMETIC_REVIEW_NOT_QUALIFIED_GROWTH' or obj['qualified_growth_count']!=0 or obj['qualified_outcomes']!=0:
            raise ValueError('assertion aggregate status')
        statuses={'NOT_SUPPORTED_GRAMMAR','SUPPORTED_REPORTED_ASSERTIONS_NOT_COMPARABILITY'}
        packages=set();pairs=0;supported=0
        for i,r in enumerate(obj['packages']):
            rid=r['package_id']
            if rid in packages or rid!=r['accession'] or r['status'] not in statuses:
                raise ValueError('assertion package/status')
            packages.add(rid);filers=set()
            if not r['filers_as_reported'] or r['first_public_utc'] is not None:
                raise ValueError('assertion filers/clock')
            if (r['status']=='NOT_SUPPORTED_GRAMMAR') != (len(r['metric_pairs'])==0):
                raise ValueError('unsupported assertion pairs')
            metric_names=set()
            for pair in r['metric_pairs']:
                if pair['metric'] in metric_names or any(pair[k] is not False for k in ('comparability_verified','training_ready','execution_ready')):
                    raise ValueError('assertion metric/qualification')
                metric_names.add(pair['metric'])
            pairs+=len(r['metric_pairs']);supported+=bool(r['metric_pairs'])
            for f in r['filers_as_reported']:
                ci=f['cik']
                if ci in filers:raise ValueError('duplicate assertion filer')
                filers.add(ci);add(ci,rid,f'/packages/{i}',r)
        if (len(packages),len(groups),len(seen),supported,pairs)!=(11,12,12,3,7) or obj['counts']!={'packages':11,'supported_packages':3,'unsupported_packages':8,'metric_pairs':7}:
            raise ValueError('assertion inventory conservation')
    else:raise ValueError('layer section')
    return groups


def load_layer(root,index,section):
    if section not in LAYER_PINS:raise ValueError('layer section')
    obj=pinned(root,LAYER_PINS[section]);groups=validate_layer(index,section,obj)
    if section=='assertions':
        paths={'ieh_revenue':'ieh-reported-revenue','ieh_results':'ieh-reported-quarterly-results','vita_revenue':'vitaspring-revenue','vita_loss':'vitaspring-net-loss','txmd_annotation':'frozen-outcome-txmd-source-review'}
        if set(obj['released_sources'])!=set(paths):raise ValueError('assertion source versions')
        for key,filename in paths.items():
            pin=obj['released_sources'][key]
            if pin['path']!='web/company-findings/'+filename+'.json' or type(pin['bytes']) is not int or not 1<=pin['bytes']<=20000:raise ValueError('assertion source path/bound')
            related=pinned(root,pin)
            ci=related['issuer_cik'] if key=='txmd_annotation' else related['issuer']['cik']
            acc=related['accession'] if key=='txmd_annotation' else related['filing']['accession']
            if ci not in groups or not any(r['source_record']['accession']==acc and r['source_record']['metric_pairs'] for r in groups[ci]):raise ValueError('assertion released-source association')
    return obj,groups


def layer_metadata(obj,section):
    return {'layer_snapshot':LAYER_PINS[section], 'layer_source_context':{k:v for k,v in obj.items() if k not in ('companies','cohort_ciks','packages')},
            'validation_scope':'PINNED_PUBLISHED_PROJECTION_AND_ASSOCIATIONS_NOT_FRESH_ORIGINAL_AUDIT'}


def layer_evidence(root,index,cik,section,limit=5,offset=0):
    bounds(limit,offset,5);ci=exact_cik(cik)
    obj,groups=load_layer(root,index,section)
    out=envelope(index);out.update(layer_metadata(obj,section))
    out.update(mode='evidence',issuer_cik=ci,section=section,company_url=company_url(ci),offset=offset)
    if ci not in {r['issuer_cik'] for r in index['directory']}:
        coverage='OUTSIDE_FIXED_COHORT_UNASSESSED';total=None
    elif section=='assertions' and ci not in groups:
        coverage='NOT_ASSESSED_IN_FIXED_ELEVEN_PACKAGE_ASSERTION_INVENTORY';total=None
    else:
        coverage=('RETAINED_ASSERTION_PACKAGE_WITH_SOURCE_SPECIFIC_GRAMMAR_STATUS' if section=='assertions' else obj['status']) if ci in groups else obj['cohort_without_records_status']
        total=len(groups.get(ci,[]))
    out.update(coverage=coverage,total_records=total,records=groups.get(ci,[])[offset:offset+limit])
    if total is None:
        out.update(returned_records=0,next_offset=None);return out
    return finish_page(out,limit)


def layer_search(root,index,name=None,cik=None,section=None,limit=20,offset=0):
    bounds(limit,offset,20)
    obj,groups=load_layer(root,index,section)
    query=normalize_name(name) if name is not None else None
    ci=exact_cik(cik) if cik is not None else None
    matches=[]
    for r in index['directory']:
        labels=[s for s in r['names_as_reported'] if query is None or query in normalize_source_label(s)]
        if query is None or labels:matches.append((r,labels))
    count=len(matches) if query is not None else None
    rows=[{'company':r,'matched_source_labels':labels if query is not None else [],'company_url':company_url(r['issuer_cik'])} for r,labels in matches if r['issuer_cik'] in groups and (ci is None or r['issuer_cik']==ci)]
    out=envelope(index);out.update(layer_metadata(obj,section))
    out.update(mode='search',query={'name':name,'issuer_cik':ci,'section':section},global_name_matching_ciks=count,name_ambiguous=count is not None and count>1,
               exact_cik_coverage=('IN_FIXED_COMPANY_COHORT' if any(r['issuer_cik']==ci for r in index['directory']) else 'OUTSIDE_FIXED_COHORT_UNASSESSED') if ci else None,
               total_records=len(rows),offset=offset,records=rows[offset:offset+limit],layer_filter_meaning='HAS_RETAINED_SOURCE_RECORD_NOT_QUALIFIED_ACTIVITY_OR_RISK')
    return finish_page(out,limit)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('mode', choices=('search','evidence'))
    p.add_argument('--root',default=str(Path(__file__).resolve().parents[1]))
    p.add_argument('--name');p.add_argument('--cik');p.add_argument('--section',choices=SECTIONS+LAYER_SECTIONS)
    p.add_argument('--limit',type=int);p.add_argument('--offset',type=int,default=0)
    a=p.parse_args()
    try:
        if a.mode=='evidence' and (a.name is not None or a.cik is None or a.section is None):
            raise ValueError('evidence requires CIK/section, no name')
        index=load(a.root)
        if a.section in LAYER_SECTIONS:
            result=layer_search(a.root,index,a.name,a.cik,a.section,a.limit if a.limit is not None else 20,a.offset) if a.mode=='search' else layer_evidence(a.root,index,a.cik,a.section,a.limit if a.limit is not None else 5,a.offset)
        else:
            result=search(index,a.name,a.cik,a.section,a.limit if a.limit is not None else 20,a.offset) if a.mode=='search' else evidence(a.root,index,a.cik,a.section,a.limit if a.limit is not None else 5,a.offset)
        raw=output_bytes(result)
    except (ValueError,KeyError,TypeError,OSError,IndexError):
        print('Company evidence retrieval failed validation; no result.',file=sys.stderr)
        return 2
    sys.stdout.buffer.write(raw)
    return 0
if __name__=='__main__':
    raise SystemExit(main())
