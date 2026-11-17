"""Retrospective issuer-level split disclosure warnings, not adjustment factors."""
import argparse
from collections import Counter
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import json
from pathlib import Path
import re
import sqlite3
from financial_pair_candidates import sha,publish,write_private
from openfigi_evidence import read_pinned
from sec_notes_data import SCHEMAS

RATIO='StockholdersEquityNoteStockSplitConversionRatio1'
NARRATIVES=('StockholdersEquityNoteStockSplit','StockholdersEquityReverseStockSplit')
VERSIONS=('us-gaap/2025','us-gaap/2026')
SUB=('adsh','cik','name','form','period','fy','fp','filed','accepted','prevrpt','detail','instance')

def one(conn,query,args):
    rows=conn.execute(query,args).fetchmany(2)
    if len(rows)!=1:raise ValueError('missing or ambiguous source context')
    return dict(rows[0])
def cik(value):
    if not isinstance(value,str) or not re.fullmatch('[0-9]{1,10}',value) or not int(value):raise ValueError('invalid issuer CIK')
    return str(int(value))
def scan(conn):
    for name in ('sub','tag','dim','num','txt'):
        if [r[1] for r in conn.execute('PRAGMA table_info(notes_'+name+')')]!=SCHEMAS[name+'.tsv']:raise ValueError('source schema')
    records=[];ciks=set();accessions=set();counts=Counter();positive=0;retained_characters=0
    for table,tags,datatype in [('num',(RATIO,),'pure'),('txt',NARRATIVES,'string')]:
        query='SELECT rowid,* FROM notes_'+table+' WHERE tag IN ('+','.join('?' for _ in tags)+') AND version IN (?,?) ORDER BY rowid'
        for row in conn.execute(query,(*tags,*VERSIONS)):
            if len(records)>=10000:raise ValueError('record bound')
            raw=dict(row)
            if any(not isinstance(v,str) or len(v)>1_000_000 for k,v in raw.items() if k!='rowid'):raise ValueError('source field bound')
            retained_characters+=sum(len(v) for k,v in raw.items() if k!='rowid')
            if retained_characters>20_000_000:raise ValueError('retained text bound')
            tag=one(conn,'SELECT rowid,* FROM notes_tag WHERE tag=? AND version=?',(raw['tag'],raw['version']))
            if tag['custom']!='0' or tag['abstract']!='0' or tag['datatype']!=datatype:raise ValueError('unexpected standard taxonomy context')
            sub=one(conn,'SELECT rowid,'+','.join(SUB)+' FROM notes_sub WHERE adsh=?',(raw['adsh'],));identity=cik(sub['cik'])
            if not re.fullmatch('[0-9]{10}-[0-9]{2}-[0-9]{6}',raw['adsh']):raise ValueError('invalid accession')
            dim=one(conn,'SELECT rowid,* FROM notes_dim WHERE dimhash=?',(raw['dimh'],))
            disposition='NARRATIVE_AS_FILED_NOT_INTERPRETED'
            if table=='num':
                # Retain even unusable/empty ratios. Never invert or infer event direction.
                disposition='UNUSABLE_NUMERIC_LITERAL'
                if raw['uom']=='pure' and re.fullmatch(r'[+-]?[0-9]{1,30}(?:\.[0-9]{1,30})?',raw['value']):
                    try:
                        if Decimal(raw['value']).is_finite() and Decimal(raw['value'])>0:disposition='POSITIVE_RATIO_LITERAL_NOT_ADJUSTMENT_FACTOR';positive+=1
                    except InvalidOperation:pass
                ciks.add(identity);accessions.add(raw['adsh'])
            counts[table]+=1
            records.append({'source_table':'notes_'+table,'raw':raw,'taxonomy':tag,'submission':sub,'dimensions':dim,'disposition':disposition,'effective_date_verified':False,'share_class_verified':False,'training_ready':False})
    ratio_records=[r for r in records if r['source_table']=='notes_num'];texts=[r for r in records if r['source_table']=='notes_txt'];text_accessions={r['raw']['adsh'] for r in texts}
    counts.update(ratio_filings=len(accessions),ratio_issuers=len(ciks),positive_ratio_literals=positive,ratio_filings_with_standard_narrative=len(accessions&text_accessions),ratio_rows_with_standard_narrative=sum(r['raw']['adsh'] in text_accessions for r in ratio_records))
    return records,dict(counts),ciks

def load_pairs(directory,expected):
    p=Path(directory)
    if (p/'INCOMPLETE').exists():raise ValueError('incomplete pairs')
    marker,_=read_pinned(p/'COMPLETE.json',sha(p/'COMPLETE.json'),10000)
    reference=dict(expected);pair_sha=reference.pop('private_candidates_sha256')
    summary,_=read_pinned(p/'summary.json',marker['summary_sha256'],100000)
    if summary!=reference or marker['candidate_pairs_sha256']!=pair_sha:raise ValueError('checkpoint mismatch')
    rows,_=read_pinned(p/'candidate-pairs.json',pair_sha,100_000_000)
    if not isinstance(rows,list) or len(rows)!=summary['candidate_pairs']:raise ValueError('candidate count')
    for r in rows:
        if r.get('training_ready') is not False or r.get('comparability_verified') is not False or r.get('decision_utc') is not None or r.get('outcome') is not None:raise ValueError('qualified input not supported')
        if r.get('database_sha256')!=summary['database_sha256'] or r.get('source_archive_sha256')!=summary['source_archive_sha256']:raise ValueError('pair source binding')
        cik(r['issuer_cik_as_filed'])
    return rows

def correspondence(batches,identities):
    counts={};matches=[]
    for batch,rows in sorted(batches.items()):
        selected=[]
        for position,r in enumerate(rows):
            if cik(r['issuer_cik_as_filed']) not in identities:continue
            selected.append(r)
            matches.append({'batch':batch,'candidate_position':position,'candidate':r,'warning':'SPLIT_DISCLOSURE_AT_SAME_ISSUER_REQUIRES_SHARE_BASIS_REVIEW','same_share_class_verified':False,'split_applies_to_candidate_verified':False,'known_at_candidate_time_verified':False})
        counts[batch]={'candidate_pairs_at_same_issuer':len(selected),'issuer_count':len({cik(r['issuer_cik_as_filed']) for r in selected}),'diluted_eps_pairs_at_same_issuer':sum(r['current']['tag']=='EarningsPerShareDiluted' for r in selected)}
    return counts,matches

def audit(database,database_sha,archive,archive_sha,checkpoint,checkpoint_sha,q2_directory,q3_directory):
    if sha(database)!=database_sha or sha(archive)!=archive_sha:raise ValueError('notes input hash')
    expected,_=read_pinned(checkpoint,checkpoint_sha,1_000_000)
    dirs={'q2_2026_filing_batch':q2_directory,'q3_2026_filing_batch':q3_directory}
    if set(expected['batches'])!=set(dirs):raise ValueError('batch scope')
    batches={k:load_pairs(v,expected['batches'][k]) for k,v in dirs.items()}
    conn=sqlite3.connect(Path(database).resolve().as_uri()+'?mode=ro',uri=True);conn.row_factory=sqlite3.Row
    try:
        if conn.execute('PRAGMA quick_check').fetchone()[0]!='ok':raise ValueError('database integrity')
        records,counts,identities=scan(conn)
    finally:conn.close()
    overlap,matches=correspondence(batches,identities)
    if sha(database)!=database_sha or sha(archive)!=archive_sha:raise ValueError('notes changed during audit')
    for p in dirs.values():
        if (Path(p)/'INCOMPLETE').exists():raise ValueError('input completion changed')
    summary={'schema_version':1,'status':'RETROSPECTIVE_SPLIT_BASIS_REVIEW_WARNINGS_ONLY','notes_database_sha256':database_sha,'notes_archive_sha256':archive_sha,'financial_candidates_checkpoint_sha256':checkpoint_sha,
             'selection':{'numeric_tags':[RATIO],'narrative_tags':list(NARRATIVES),'taxonomy_versions':list(VERSIONS)},'counts':counts,'issuer_level_correspondence':overlap,
             'audit_completed_at':datetime.now(timezone.utc).isoformat(),'source_retrieval_utc':None,'source_first_public_utc':None,'known_at_candidate_time_verified':False,'corporate_action_events_verified':0,'adjustment_factors_verified':0,'training_ready':False,'execution_ready':False,
             'limitations':['Rows are disclosed facts, not unique split events. Repeated dimensions, dates, filings and narratives remain separate.',
              'Later October disclosures are retrospective audit evidence, never features known at earlier Q2/Q3 filing decisions.',
              'Same issuer CIK is not same share class. No direction, effective date, conversion adjustment, causal applicability or comparability inferred.',
              'Standard-tag selection excludes custom concepts and other taxonomy versions. Absence is not proof of no split.',
              'Ratio and narrative sharing an accession does not prove they describe the same event. Neither source date field is automatically an ex-date.',
              'Prepared-data context is retained exactly; original filing interpretation remains necessary. No price/outcome corrections or model admission.',
              'Pinned DB/ZIP identify retained inputs; prior independent ingestion audit establishes derivation, not this utility.']}
    return summary,{'notes_records':records,'candidate_warnings':matches}

if __name__=='__main__':
    p=argparse.ArgumentParser()
    for n in ('database','database-sha','archive','archive-sha','checkpoint','checkpoint-sha','q2-directory','q3-directory','output-directory'):p.add_argument('--'+n,required=True)
    a=p.parse_args();out=Path(a.output_directory).resolve()
    if out.is_relative_to(Path(__file__).resolve().parents[1]) or not out.parent.is_dir():raise ValueError('trusted private parent outside checkout required')
    out.mkdir(mode=0o700,exist_ok=False);write_private(out/'INCOMPLETE',{'status':'INCOMPLETE_NOT_USABLE'})
    args=vars(a);args.pop('output_directory');summary,evidence=audit(**args);publish(out,summary,evidence);print(json.dumps(summary))
