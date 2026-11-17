"""Offline exact FIGI-string correspondence; never historical security qualification."""
import argparse
from datetime import datetime
from collections import Counter,defaultdict
import json
from pathlib import Path
import re
import sqlite3
from financial_pair_candidates import sha,publish,write_private
from openfigi_evidence import audit as mapping_audit,figi_valid

COVER=('ACCESSION_NUMBER','REPORTCALENDARORQUARTER','ISAMENDMENT','AMENDMENTNO','AMENDMENTTYPE','CONFDENIEDEXPIRED','DATEDENIEDEXPIRED','DATEREPORTED','REASONFORNONCONFIDENTIALITY','REPORTTYPE')

def index_mappings(summary):
    index=defaultdict(list)
    for job in summary['mappings']:
        for n,candidate in enumerate(job['candidates']):
            by_id=defaultdict(list)
            for scope in ('figi','compositeFIGI','shareClassFIGI'):
                identifier=candidate[scope]
                if not figi_valid(identifier):raise ValueError('invalid candidate identifier')
                by_id[identifier].append(scope)
            for identifier,scopes in by_id.items():
                index[identifier].append({'query_ticker':job['query_ticker'],'request_position':job['request_position'],'candidate_position':n,'matching_identifier_fields':scopes})
    return index

def scan(conn,mapping):
    index=index_mappings(mapping);counts=Counter();unique=defaultdict(set);selected=[]
    for rowid,identifier in conn.execute('SELECT rowid,FIGI FROM holdings_infotable'):
        counts['holding_rows']+=1
        if counts['holding_rows']>5000000:raise ValueError('row bound exceeded')
        if not isinstance(identifier,str) or len(identifier)>1000:raise ValueError('FIGI source field is not text')
        if not identifier.strip():reason='blank'
        elif figi_valid(identifier):reason='valid_checksum'
        else:reason='invalid_structure_or_checksum'
        counts[reason+'_rows']+=1
        if identifier.strip():unique[reason].add(identifier)
        if reason=='valid_checksum' and identifier in index:
            selected.append((rowid,identifier))
            if len(selected)>50000:raise ValueError('match bound exceeded')
    pairs=[];tickers=Counter();scopes=Counter();options=Counter();periods=Counter();forms=Counter();accessions=set();identifiers=set()
    for rowid,identifier in selected:
        raw=conn.execute('SELECT rowid,* FROM holdings_infotable WHERE rowid=?',(rowid,)).fetchall()
        if len(raw)!=1:raise ValueError('ambiguous holding row')
        fact=dict(raw[0]);accession=fact['ACCESSION_NUMBER']
        if fact['FIGI']!=identifier or not re.fullmatch(r'\d{10}-\d{2}-\d{6}',accession):raise ValueError('source identity mismatch')
        subs=conn.execute('SELECT rowid,* FROM holdings_submission WHERE ACCESSION_NUMBER=?',(accession,)).fetchall()
        covers=conn.execute('SELECT rowid,'+','.join(COVER)+' FROM holdings_coverpage WHERE ACCESSION_NUMBER=?',(accession,)).fetchall()
        if len(subs)!=1 or len(covers)!=1:raise ValueError('missing or ambiguous filing context')
        sub=dict(subs[0]);cover=dict(covers[0])
        if sub['SUBMISSIONTYPE'] not in ('13F-HR','13F-HR/A','13F-NT','13F-NT/A') or fact['PUTCALL'] not in ('','Put','Call'):raise ValueError('unsupported public category')
        if not re.fullmatch(r'\d{2}-[A-Z]{3}-\d{4}',sub['PERIODOFREPORT']):raise ValueError('unsupported report date')
        datetime.strptime(sub['PERIODOFREPORT'],'%d-%b-%Y')
        if cover['REPORTCALENDARORQUARTER']!=sub['PERIODOFREPORT']:raise ValueError('conflicting report period')
        matches=index[identifier]
        # Sets avoid counting one holding twice when FIGI equals compositeFIGI.
        for ticker in {m['query_ticker'] for m in matches}:tickers[ticker]+=1
        for scope in {s for m in matches for s in m['matching_identifier_fields']}:scopes[scope]+=1
        accessions.add(accession);identifiers.add(identifier);options[fact['PUTCALL'] or '(blank)']+=1;periods[sub['PERIODOFREPORT']]+=1;forms[sub['SUBMISSIONTYPE']]+=1
        pairs.append({'holding':fact,'submission':sub,'cover_context':cover,'mapping_matches':matches,'historical_security_link_verified':False,'training_ready':False,'amendment_flag_conflict':(sub['SUBMISSIONTYPE'].endswith('/A') != (cover['ISAMENDMENT']=='Y'))})
    counts.update({reason+'_distinct_strings':len(values) for reason,values in unique.items()})
    for reason in ('blank','valid_checksum','invalid_structure_or_checksum'):counts.setdefault(reason+'_rows',0)
    summary={'status':'EXACT_SOURCE_REPORTED_IDENTIFIER_CORRESPONDENCE_ONLY','census':dict(sorted(counts.items())),
      'identifiers_shared_across_query_tickers':sum(len({m['query_ticker'] for m in matches})>1 for matches in index.values()),'matched_amendment_flag_conflicts':sum(p['amendment_flag_conflict'] for p in pairs),'matched_holding_rows':len(pairs),'matched_accessions':len(accessions),'matched_identifier_strings':len(identifiers),
      'matched_rows_by_query_ticker':dict(sorted(tickers.items())),'matched_rows_by_identifier_field':dict(sorted(scopes.items())),
      'matched_rows_by_putcall_as_filed':dict(sorted(options.items())),'matched_rows_by_report_period_as_filed':dict(sorted(periods.items())),
      'matched_rows_by_submission_type':dict(sorted(forms.items())),
      'historical_security_link_verified':False,'training_ready':False,'execution_ready':False,
      'limitations':['Current mapping and historical source-reported identifiers are exact string matches, not verified historical ticker ownership or issuer-CIK links.',
      'FIGI, compositeFIGI and shareClassFIGI scopes remain separate; a row can match multiple fields. Field counts are not additive.',
      'Reporting manager CIK is not held-security issuer CIK. Report periods, amendments, options and as-filed class labels are retained privately, not reconciled into current positions.',
      'Valid identifier checksum is not proof the filer reported the right security. Blank and invalid source identifiers remain counted; none is repaired or guessed.',
      'No valuation, portfolio aggregation, purchase/sale signal, returns, model admission or execution. Current observation clocks are not historical availability.',
      'Pinned DB and ZIP hashes identify inputs; prior independently verified ingestion establishes their derivation, not this correspondence utility.']}
    return summary,pairs

def audit(database,database_sha,archive,archive_sha,request,request_sha,response,response_sha,receipt,receipt_sha):
    for value in (database_sha,archive_sha):
        if not re.fullmatch('[a-f0-9]{64}',value):raise ValueError('invalid input hash')
    if sha(database)!=database_sha or sha(archive)!=archive_sha:raise ValueError('source hash mismatch')
    mapping,_=mapping_audit(request,request_sha,response,response_sha,receipt,receipt_sha)
    conn=sqlite3.connect(Path(database).resolve().as_uri()+'?mode=ro',uri=True);conn.row_factory=sqlite3.Row
    try:
        if conn.execute('PRAGMA quick_check').fetchone()[0]!='ok':raise ValueError('database integrity failure')
        summary,pairs=scan(conn,mapping)
    finally:conn.close()
    if sha(database)!=database_sha or sha(archive)!=archive_sha:raise ValueError('source changed during audit')
    summary.update(schema_version=1,database_sha256=database_sha,source_archive_sha256=archive_sha,mapping_request_sha256=request_sha,mapping_response_sha256=response_sha,mapping_receipt_sha256=receipt_sha,mapping_observed_at=mapping['observed_at'])
    return summary,{'source_lineage':{k:v for k,v in summary.items() if k.endswith('sha256')},'correspondences':pairs}

if __name__=='__main__':
    p=argparse.ArgumentParser()
    for name in ('database','database-sha','archive','archive-sha','request','request-sha','response','response-sha','receipt','receipt-sha','output-directory'):p.add_argument('--'+name,required=True)
    a=p.parse_args();out=Path(a.output_directory).resolve()
    if out.is_relative_to(Path(__file__).resolve().parents[1]) or not out.parent.is_dir():raise ValueError('trusted private parent outside checkout required')
    out.mkdir(mode=0o700,exist_ok=False);write_private(out/'INCOMPLETE',{'status':'INCOMPLETE_NOT_USABLE'})
    args=vars(a);args.pop('output_directory');summary,evidence=audit(**args);publish(out,summary,evidence)
    print(json.dumps(summary))
