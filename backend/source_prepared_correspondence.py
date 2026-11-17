"""Candidate correspondence of retained inline and prepared facts, not equivalence."""
import argparse
from collections import Counter
import calendar
import hashlib
import datetime as dt
from decimal import Decimal
from pathlib import Path
import re
import sqlite3
import json
from inline_occurrence_evidence import audit as occurrence_audit
from financial_pair_candidates import sha,finite,publish,write_private

USD={'namespace':'http://www.xbrl.org/2003/iso4217','local_name':'USD'}
SHARES={'namespace':'http://www.xbrl.org/2003/instance','local_name':'shares'}

def match(group,submission,rows,definitions,presentation):
    f=group['occurrences'][0]
    if f['dimension_or_scenario_present']:return 'dimension_or_scenario_unassessed',None
    if any(x['numeric_conversion_verified'] is not True for x in group['occurrences']):return 'numeric_interpretation_unavailable',None
    if group['numeric_relation'] not in {'SINGLE_OCCURRENCE','NUMERICALLY_EQUAL'}:return 'conflicting_occurrence_values',None
    if not group['declared_decimals_equal']:return 'different_declared_decimals',None
    if not re.fullmatch(r'[0-9]{1,10}',str(submission['cik'])) or int(submission['cik'])!=int(f['issuer_identifier_as_filed']):return 'issuer_mismatch',None
    if submission['form'] not in {'10-Q','10-Q/A','10-K','10-K/A'}:return 'unsupported_form',None
    period=f['period']
    if period['kind']!='duration':return 'unsupported_period',None
    start=dt.date.fromisoformat(period['startDate']);end=dt.date.fromisoformat(period['endDate'])
    months=(end.year-start.year)*12+end.month-start.month+1
    if start.day!=1 or end.day!=calendar.monthrange(end.year,end.month)[1] or months not in {3,6,9,12}:return 'calendar_span_unassessed',None
    qtrs=str(months//3) # Candidate filter only: prepared data has no exact start date.
    tag=f['concept']['local_name'];version='us-gaap/'+f['concept']['namespace'].rsplit('/',1)[-1]
    definitions=[d for d in definitions if d['tag']==tag and d['version']==version]
    if len(definitions)!=1:return 'missing_or_ambiguous_taxonomy',None
    d=definitions[0];per_share=tag=='EarningsPerShareDiluted'
    unit={'kind':'divide','numerator':[USD],'denominator':[SHARES]} if per_share else {'kind':'simple','measures':[USD]}
    if f['unit']!=unit or d['datatype']!=('perShare' if per_share else 'monetary') or d['custom']!='0' or d['abstract']!='0' or d['iord']!='D':return 'unsupported_unit_or_taxonomy',None
    pre=[r for r in presentation if r['tag']==tag and r['version']==version]
    if not pre:return 'missing_presentation',None
    candidates=[r for r in rows if r['tag']==tag and r['version']==version and r['ddate']==end.strftime('%Y%m%d') and r['qtrs']==qtrs and r['uom']=='USD' and r['segments']=='' and r['coreg']=='']
    if len(candidates)!=1:return 'missing_or_ambiguous_prepared_row',None
    row=candidates[0]
    if not finite(row['value']):return 'missing_or_invalid_prepared_value',None
    if row['footnote'].strip():return 'prepared_footnote_requires_review',None
    equal=Decimal(row['value'])==Decimal(f['numeric_value'])
    return ('candidate_numeric_equal' if equal else 'candidate_numeric_different'),{'source_group':group,'prepared_submission':submission,'prepared_num':row,'prepared_tag':d,'prepared_presentation':pre,
      'candidate_qtrs_filter':qtrs,'numeric_equal':equal,'exact_prepared_start_date_verified':False,'comparability_verified':False,'training_ready':False}

def audit(archive,archive_sha,member,member_sha,database,db_sha,prepared_archive,prepared_sha,manifest,manifest_sha):
    from private_prices import unique_object
    def invalid_constant(v):raise ValueError('nonstandard JSON constant')
    with Path(manifest).open('rb') as f:manifest_bytes=f.read(100001)
    if len(manifest_bytes)>100000 or hashlib.sha256(manifest_bytes).hexdigest()!=manifest_sha:raise ValueError('identity manifest bounds/hash mismatch')
    receipt=json.loads(manifest_bytes.decode('utf-8'),object_pairs_hook=unique_object,parse_constant=invalid_constant)
    accession=receipt['accession']
    if receipt['zip_sha256']!=archive_sha or receipt['primary_member_sha256']!=member_sha or receipt['primary_member']!=member:raise ValueError('identity manifest mismatch')
    if not re.fullmatch(r'[0-9]{10}-[0-9]{2}-[0-9]{6}',accession):raise ValueError('invalid accession')
    if not re.fullmatch(r'[a-f0-9]{64}',db_sha) or not re.fullmatch(r'[a-f0-9]{64}',prepared_sha):raise ValueError('invalid expected hashes')
    if sha(database)!=db_sha or sha(prepared_archive)!=prepared_sha:raise ValueError('prepared input hash mismatch')
    source_summary,groups=occurrence_audit(archive,archive_sha,member,member_sha)
    c=sqlite3.connect(Path(database).resolve().as_uri()+'?mode=ro',uri=True);c.row_factory=sqlite3.Row
    try:
        if c.execute('PRAGMA quick_check').fetchone()[0]!='ok':raise ValueError('database integrity failure')
        subs=[dict(r) for r in c.execute('select rowid,* from financial_sub where adsh=? limit 2',(accession,))]
        if len(subs)!=1:raise ValueError('missing or ambiguous submission')
        if str(int(subs[0]['cik']))!=receipt['issuer_cik_verified'] or subs[0]['period']!=receipt['period_of_report'].replace('-',''):raise ValueError('submission identity mismatch')
        expected_url=f"https://www.sec.gov/Archives/edgar/data/{receipt['issuer_cik_verified']}/{accession.replace('-','')}/{accession}-xbrl.zip"
        if receipt['source_url']!=expected_url:raise ValueError('source identity URL mismatch')
        rows=[dict(r) for r in c.execute('select rowid,* from financial_num where adsh=? limit 100001',(accession,))]
        if len(rows)>100000:raise ValueError('filing row bounds')
        pre=[dict(r) for r in c.execute('select rowid,* from financial_pre where adsh=? limit 100001',(accession,))]
        if len(pre)>100000:raise ValueError('presentation bounds')
        defs=[]
        for tag,version in sorted({(f['concept']['local_name'],'us-gaap/'+f['concept']['namespace'].rsplit('/',1)[-1]) for g in groups for f in g['occurrences']}):
            defs.extend(dict(r) for r in c.execute('select rowid,* from financial_tag where tag=? and version=? limit 2',(tag,version)))
        counts=Counter();results=[]
        for group in groups:
            disposition,candidate=match(group,subs[0],rows,defs,pre);counts[disposition]+=1
            results.append({'group_id':group['group_id'],'disposition':disposition,'candidate':candidate,'source_group':group if candidate is None else None})
        if sha(database)!=db_sha or sha(prepared_archive)!=prepared_sha:raise ValueError('prepared input changed')
    finally:c.close()
    summary={'schema_version':1,'status':'CANDIDATE_SOURCE_PREPARED_CORRESPONDENCE_NOT_EQUIVALENCE','archive_sha256':archive_sha,'raw_member_sha256':member_sha,'prepared_database_sha256':db_sha,'prepared_archive_sha256':prepared_sha,'accession_from_pinned_manifest':accession,'identity_manifest_sha256':manifest_sha,
      'source_occurrence_count':source_summary['source_occurrence_count'],'source_local_group_count':len(groups),'group_dispositions':dict(sorted(counts.items())),
      'exact_prepared_start_date_verified':False,'comparability_verified':False,'training_ready':False,'execution_ready':False,
      'limitations':['Hash-pinned manifest links previously independently audited source identity; the manifest is local evidence, not independently authenticated by this tool.',
      'Calendar-month span supplies a candidate qtrs filter only; prepared rows do not prove exact source duration or comparable accounting scope.',
      'Prepared EPS USD plus perShare datatype is checked against the explicit inline USD/shares unit, not inferred from unit ID.',
      'Hash-pinned inputs do not alone prove database derivation from the ZIP; prior ingestion audits supply that lineage.',
      'No dimensional joins, growth, timing admission, historical availability, outcomes or training qualification.']}
    return summary,results

if __name__=='__main__':
    p=argparse.ArgumentParser()
    for key in ['archive','archive-sha256','member','member-sha256','database','database-sha256','prepared-archive','prepared-archive-sha256','manifest','manifest-sha256','output-directory']:p.add_argument('--'+key,required=True)
    a=p.parse_args();out=Path(a.output_directory).resolve()
    if out.is_relative_to(Path(__file__).resolve().parents[1]) or not out.parent.is_dir():raise ValueError('trusted private parent outside checkout required')
    out.mkdir(mode=0o700,exist_ok=False);write_private(out/'INCOMPLETE',{'status':'INCOMPLETE_NOT_USABLE'})
    summary,results=audit(a.archive,a.archive_sha256,a.member,a.member_sha256,a.database,a.database_sha256,a.prepared_archive,a.prepared_archive_sha256,a.manifest,a.manifest_sha256)
    publish(out,summary,results);print(json.dumps(summary))
