"""Offline same-filing context matches, NOT comparable financial facts or signals."""
import argparse
from collections import Counter,defaultdict
import datetime as dt
from decimal import Decimal,InvalidOperation
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3

TAGS={'Revenues':'USD','RevenueFromContractWithCustomerExcludingAssessedTax':'USD','NetIncomeLoss':'USD','EarningsPerShareDiluted':'USD'}
FORMS={'10-Q','10-Q/A','10-K','10-K/A'}
NUM_FIELDS=('rowid','adsh','tag','version','ddate','qtrs','uom','segments','coreg','value','footnote')

def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()

def finite(value):
    if not isinstance(value,str) or len(value)>100 or not re.fullmatch(r'[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[Ee][+-]?\d+)?',value):return False
    try:return Decimal(value).is_finite()
    except InvalidOperation:return False

def dates(period):
    if not re.fullmatch(r'\d{8}',period):raise ValueError('invalid period')
    d=dt.datetime.strptime(period,'%Y%m%d').date()
    # Exact calendar anniversary only. Leap-day/52-53-week alternatives are NOT inferred.
    return d.strftime('%Y%m%d'),d.replace(year=d.year-1).strftime('%Y%m%d')

def classify(rows,submission,taxonomy):
    """Every (accession,tag,version,unit) group has one explicit terminal disposition."""
    if not rows:return 'empty_context',None
    keys={(r['adsh'],r['tag'],r['version'],r['uom']) for r in rows}
    if len(keys)!=1 or any(r['qtrs']!='1' or r['segments']!='' or r['coreg']!='' for r in rows):return 'mixed_or_unsupported_context',None
    if submission['form'] not in FORMS:return 'unsupported_form',None
    try:current,prior=dates(submission['period'])
    except (ValueError,TypeError):return 'unsupported_period',None
    sample=rows[0]
    if not re.fullmatch(r'us-gaap/\d{4}',sample['version']):return 'nonstandard_taxonomy',None
    if sample['uom']!=TAGS[sample['tag']]:return 'unsupported_unit',None
    defs=taxonomy.get((sample['tag'],sample['version']),[])
    if len(defs)!=1:return 'missing_or_ambiguous_taxonomy',None
    definition=defs[0]
    expected_type='perShare' if sample['tag']=='EarningsPerShareDiluted' else 'monetary'
    if definition.get('datatype')!=expected_type:return 'unsupported_taxonomy_datatype',None
    if definition['custom']!='0' or definition['abstract']!='0' or definition['iord']!='D':return 'unsupported_taxonomy_context',None
    if any(n>1 for n in Counter(r['ddate'] for r in rows).values()):return 'ambiguous_context',None
    selected={date:[r for r in rows if r['ddate']==date] for date in (current,prior)}
    if any(len(v)>1 for v in selected.values()):return 'ambiguous_context',None
    if not selected[current]:return 'missing_current_calendar_period',None
    if not selected[prior]:return 'missing_prior_calendar_period',None
    a,b=selected[current][0],selected[prior][0]
    if not finite(a['value']) or not finite(b['value']):return 'missing_or_invalid_value',None
    # Footnotes can qualify displayed amounts. Retain/reject rather than erase them.
    if a['footnote'].strip() or b['footnote'].strip():return 'footnote_requires_review',None
    return 'context_matched_candidate',{'issuer_cik_as_filed':submission['cik'],'accession':sample['adsh'],
      'form':submission['form'],'fiscal_period':submission['fp'],'submission_period':submission['period'],
      'filing_date_as_filed':submission['filed'],'accepted_as_filed':submission['accepted'],
      'current':a,'prior':b,'taxonomy':definition,'comparability_verified':False,
      'first_public_utc':None,'decision_utc':None,'outcome':None,'training_ready':False}

def audit(database,expected_db_sha,archive,expected_archive_sha):
    for expected in (expected_db_sha,expected_archive_sha):
        if not re.fullmatch('[a-f0-9]{64}',expected):raise ValueError('invalid expected hash')
    before=sha(database)
    if before!=expected_db_sha or sha(archive)!=expected_archive_sha:raise ValueError('input hash mismatch')
    uri=Path(database).resolve().as_uri()+'?mode=ro'
    conn=sqlite3.connect(uri,uri=True);conn.row_factory=sqlite3.Row
    try:
        if conn.execute('PRAGMA quick_check').fetchone()[0]!='ok':raise ValueError('database integrity failure')
        subs=defaultdict(list)
        for r in conn.execute('SELECT adsh,cik,form,period,fp,filed,accepted FROM financial_sub'):subs[r['adsh']].append(dict(r))
        taxonomy=defaultdict(list)
        placeholders=','.join('?' for _ in TAGS)
        for r in conn.execute(f'SELECT rowid,* FROM financial_tag WHERE tag IN ({placeholders})',tuple(TAGS)):
            taxonomy[(r['tag'],r['version'])].append(dict(r))
        presentation=defaultdict(list)
        for r in conn.execute(f'SELECT rowid,* FROM financial_pre WHERE tag IN ({placeholders})',tuple(TAGS)):
            presentation[(r['adsh'],r['tag'],r['version'])].append(dict(r))
        groups=defaultdict(list);counts=Counter();pairs=[];dispositions=Counter()
        for raw in conn.execute(f'SELECT rowid,* FROM financial_num WHERE tag IN ({placeholders})',tuple(TAGS)):
            r={k:raw[k] for k in NUM_FIELDS};counts['target_tag_rows']+=1
            if r['segments']!='' or r['coreg']!='':counts['excluded_segment_or_coreg_rows']+=1;continue
            if r['qtrs']!='1':counts['excluded_non_single_quarter_rows']+=1;continue
            counts['single_quarter_empty_dimension_rows']+=1
            groups[(r['adsh'],r['tag'],r['version'],r['uom'])].append(r)
        for key,rows in sorted(groups.items()):
            sub=subs.get(key[0],[])
            if len(sub)!=1:reason,pair='missing_or_ambiguous_submission',None
            elif not presentation.get(key[:3]):reason,pair='missing_presentation_context',None
            else:reason,pair=classify(rows,sub[0],taxonomy)
            dispositions[reason]+=1
            if pair:
                pair.update(database_sha256=before,source_archive_sha256=expected_archive_sha,presentation=presentation[key[:3]])
                pairs.append(pair)
        if sum(dispositions.values())!=len(groups):raise ValueError('unaccounted group')
    finally:conn.close()
    if sha(database)!=before or sha(archive)!=expected_archive_sha:raise ValueError('input changed')
    summary={'schema_version':1,'status':'CONTEXT_MATCHES_NOT_COMPARABLE_FACTS',
      'database_sha256':before,'source_archive_sha256':expected_archive_sha,
      'tags':sorted(TAGS),'row_counts':dict(sorted(counts.items())),
      'context_groups':len(groups),'group_dispositions':dict(sorted(dispositions.items())),
      'candidate_pairs':len(pairs),'candidate_accessions':len({p['accession'] for p in pairs}),
      'candidate_ciks':len({p['issuer_cik_as_filed'].lstrip('0') for p in pairs}),
      'comparability_verified':False,'training_ready':False,'execution_ready':False,
      'limitations':['Same filing/tag/taxonomy/unit/qtrs/date and empty segment/coreg are necessary context checks, not proof of comparable operations or exact duration.',
      'qtrs=1 does not provide exact start dates; calendar-year matching excludes leap-day and some 52/53-week reporters.',
      'Empty segments/coreg does not itself prove total-company consolidated scope.',
      'Accepted/filed dates are preserved source fields, not authenticated first-public availability.',
      'Raw uom USD is retained with TAG datatype monetary or perShare; no unit rewriting or conversion. No arithmetic, returns, predictions, decision clocks or outcomes generated. Revisions and amendments are retained separately by accession.',
      'Four predefined tags are a narrow feasibility sample, not an unbiased company or earnings cohort. Counts across batches must not be summed as unique issuers.']}
    return summary,pairs

def write_private(path,obj):
    fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    with os.fdopen(fd,'w') as f:
        json.dump(obj,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())

def publish(out,summary,pairs):
    """Caller must create INCOMPLETE before auditing; never infer success without COMPLETE."""
    out=Path(out)
    if not (out/'INCOMPLETE').is_file():raise ValueError('missing incomplete marker')
    write_private(out/'candidate-pairs.json',pairs)
    write_private(out/'summary.json',summary)
    write_private(out/'COMPLETE.json',{'candidate_pairs_sha256':sha(out/'candidate-pairs.json'),
      'summary_sha256':sha(out/'summary.json')})
    (out/'INCOMPLETE').unlink()

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--database',required=True);p.add_argument('--database-sha256',required=True);p.add_argument('--archive',required=True);p.add_argument('--archive-sha256',required=True);p.add_argument('--output-directory',required=True);a=p.parse_args()
    out=Path(a.output_directory).resolve()
    repo=Path(__file__).resolve().parents[1]
    if out.is_relative_to(repo):raise ValueError('private output must be outside checkout')
    if not out.parent.is_dir():raise ValueError('trusted existing parent required')
    out.mkdir(mode=0o700,exist_ok=False)
    write_private(out/'INCOMPLETE',{'status':'INCOMPLETE_NOT_USABLE'})
    summary,pairs=audit(a.database,a.database_sha256,a.archive,a.archive_sha256)
    publish(out,summary,pairs)
    print(json.dumps(summary))
