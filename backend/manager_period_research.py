"""Offline reporting-manager filing history; not held-company or trade inference."""
import argparse,datetime as dt,json,re,sqlite3
from pathlib import Path
from collections import Counter
from financial_pair_candidates import sha

SOURCE_URL='https://www.sec.gov/files/datastandardsinnovation/data/form-13f-data-sets/01jun2026-31aug2026_form13f.zip'
COVER=('ACCESSION_NUMBER','REPORTCALENDARORQUARTER','ISAMENDMENT','AMENDMENTNO','AMENDMENTTYPE','CONFDENIEDEXPIRED','REPORTTYPE')
FORMS={'13F-HR','13F-HR/A','13F-NT','13F-NT/A'}
def cik(value):
 if not isinstance(value,str) or not re.fullmatch('[0-9]{1,10}',value) or not int(value):raise ValueError('manager CIK')
 return str(int(value)).zfill(10)
def date(value):
 if not isinstance(value,str) or not re.fullmatch('[0-9]{2}-[A-Z]{3}-[0-9]{4}',value):raise ValueError('source date')
 return dt.datetime.strptime(value,'%d-%b-%Y').date().isoformat()
def unique_rows(rows):
 result={};rowids=set()
 for row in rows:
  r=dict(row);a=r['ACCESSION_NUMBER']
  if type(r.get('rowid')) is not int or r['rowid']<1 or r['rowid'] in rowids:raise ValueError('source row identity')
  rowids.add(r['rowid'])
  if not re.fullmatch('[0-9]{10}-[0-9]{2}-[0-9]{6}',a) or a in result:raise ValueError('duplicate source accession')
  result[a]=r
 return result

def project(submissions,covers,summaries,manager_cik=None,cohort_limit=5):
 if not 1<=len(submissions)<=20000 or type(cohort_limit) is not int or not 1<=cohort_limit<=10:raise ValueError('source/cohort bounds')
 subs=unique_rows(submissions);cover=unique_rows(covers);summary=unique_rows(summaries)
 if set(cover)!=set(subs) or set(summary)-set(subs):raise ValueError('source join coverage')
 groups={}
 for accession,s in subs.items():
  ci=cik(s['CIK']);c=cover[accession];q=summary.get(accession)
  filed=date(s['FILING_DATE']);period=date(s['PERIODOFREPORT'])
  if not '2026-06-01'<=filed<='2026-08-31' or period>filed or c['REPORTCALENDARORQUARTER']!=s['PERIODOFREPORT']:raise ValueError('source date scope')
  if s['SUBMISSIONTYPE'] not in FORMS or c['ISAMENDMENT'] not in ('','N','Y') or c['AMENDMENTTYPE'] not in ('','RESTATEMENT','NEW HOLDINGS') or c['CONFDENIEDEXPIRED'] not in ('','N','Y') or c['REPORTTYPE'] not in ('13F HOLDINGS REPORT','13F NOTICE','13F COMBINATION REPORT'):raise ValueError('source category')
  if c['AMENDMENTNO'] and not re.fullmatch('[0-9]{1,10}',c['AMENDMENTNO']):raise ValueError('amendment number')
  if q is not None and q['ISCONFIDENTIALOMITTED'] not in ('','N','Y'):raise ValueError('confidentiality flag')
  row={'accession':accession,'filing_date_as_filed':filed,'report_period_as_filed':period,'form_as_filed':s['SUBMISSIONTYPE'],'report_type_as_filed':c['REPORTTYPE'],'amendment_flag_as_filed':c['ISAMENDMENT'],'amendment_number_as_filed':c['AMENDMENTNO'],'amendment_type_as_filed':c['AMENDMENTTYPE'],'form_cover_amendment_conflict':s['SUBMISSIONTYPE'].endswith('/A')!=(c['ISAMENDMENT']=='Y'),'confidential_denied_expired_as_filed':c['CONFDENIEDEXPIRED'],'confidential_omitted_as_filed':None if q is None else q['ISCONFIDENTIALOMITTED'],'summary_record_present':q is not None,'source_rows':{'submission':s['rowid'],'cover':c['rowid'],'summary':None if q is None else q['rowid']},'sec_accession_lookup_url':'https://www.sec.gov/edgar/search/#/q='+accession,'link_status':'CONSTRUCTED_ACCESSION_LOOKUP_NOT_FETCH_VERIFIED','first_public_utc':None,'amendment_reconciled':False,'holding_changes_inferred':False}
  groups.setdefault(ci,[]).append(row)
 multi=sorted(ci for ci,rows in groups.items() if len({r['report_period_as_filed'] for r in rows})>1)
 requested=None if manager_cik is None else cik(manager_cik)
 chosen=multi[:cohort_limit] if requested is None else ([requested] if requested in groups else [])
 managers=[]
 for ci in chosen:
  rows=sorted(groups[ci],key=lambda r:(r['report_period_as_filed'],r['filing_date_as_filed'],r['accession']))
  if len(rows)>100:raise ValueError('manager filing bound')
  managers.append({'manager_cik':ci,'identity_role':'REPORTING_MANAGER_NOT_HELD_ISSUER','filings_in_retained_batch':len(rows),'report_periods_as_filed':sorted({r['report_period_as_filed'] for r in rows}),'filings':rows,'research_question':'Which distinct report periods and amendment/confidentiality contexts are present in this filing batch? Inspect originals before interpreting the manager history.','history_complete':False,'positions_assessed':False,'trade_flows_assessed':False})
 return {'version':1,'status':'REPORTING_MANAGER_FILING_HISTORY_NOT_POSITIONS_OR_TRADES','selection_mode':'LOWEST_CIK_MULTI_PERIOD_DIAGNOSTIC_COHORT' if requested is None else 'EXACT_MANAGER_CIK_QUERY','requested_manager_cik':requested,'requested_manager_present':None if requested is None else requested in groups,'selection':'Numerically smallest manager CIKs with multiple distinct report periods in the retained batch; all filings for each selected manager are retained. Diagnostic selection, not statistical sampling or performance ranking.' if requested is None else 'All filings for the exact reporting-manager CIK in this one retained batch; no name, ticker or held-issuer join.','counts':{'retained_batch_filings':len(subs),'retained_batch_manager_ciks':len(groups),'managers_with_multiple_report_periods':len(multi),'selected_managers':len(managers),'selected_filings':sum(len(m['filings']) for m in managers)},'managers':managers,'source_scope':{'source_url':SOURCE_URL,'filing_date_start':'2026-06-01','filing_date_end':'2026-08-31','source_retrieved_utc':None,'first_public_utc':None},'training_ready':False,'execution_ready':False,'limitations':['Reporting-manager CIK is not a held-company issuer CIK. No connection to the company research queue or a security is inferred.','One June–August2026 filing batch is not complete manager history or current positions. Report periods can be much older than filing dates; multiple filings may amend one period.','Amendments, restatements, new-holdings and notice forms remain separate source records. Blank flags are not independent evidence of no amendment or confidentiality; flags are not reconciled.','No holding values, shares, CUSIPs, manager names, addresses, signatures or personal contacts are published. No position changes, purchases/sales, exposure, returns or strategy are reconstructed.','An absent manager means no submission in this retained batch, not no manager, no holdings or no activity. Links are constructed accession lookups, not verified originals.','This deterministic diagnostic cohort is chosen after inspecting batch coverage; it is not preregistered, representative or a performance sample.']}

def audit(database,database_sha,archive,archive_sha,manager_cik=None,cohort_limit=5):
 for path,pin in ((database,database_sha),(archive,archive_sha)):
  if not re.fullmatch('[a-f0-9]{64}',pin) or sha(path)!=pin:raise ValueError('input hash mismatch')
 conn=sqlite3.connect(Path(database).resolve().as_uri()+'?mode=ro',uri=True);conn.row_factory=sqlite3.Row
 try:
  if conn.execute('PRAGMA quick_check').fetchone()[0]!='ok':raise ValueError('database integrity')
  subs=conn.execute('SELECT rowid,* FROM holdings_submission LIMIT 20001').fetchall()
  covers=conn.execute('SELECT rowid,'+','.join(COVER)+' FROM holdings_coverpage LIMIT 20001').fetchall()
  summaries=conn.execute('SELECT rowid,ACCESSION_NUMBER,ISCONFIDENTIALOMITTED FROM holdings_summarypage LIMIT 20001').fetchall()
  result=project(subs,covers,summaries,manager_cik,cohort_limit)
 finally:conn.close()
 if sha(database)!=database_sha or sha(archive)!=archive_sha:raise ValueError('source changed')
 result['source_scope'].update(database_sha256=database_sha,source_archive_sha256=archive_sha)
 return result
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__)
 for key in ('database','database-sha','archive','archive-sha'):p.add_argument('--'+key,required=True)
 p.add_argument('--manager-cik');p.add_argument('--cohort-limit',type=int,default=5)
 print(json.dumps(audit(**vars(p.parse_args())),indent=2))
