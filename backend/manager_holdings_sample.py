"""Bounded SEC as-filed manager review; no issuer mapping or holdings changes."""
import argparse,hashlib,json,sqlite3,zipfile
from pathlib import Path
from sec_13f_data import inventory,rows,SCHEMAS,URL
DB_SHA='5117bb2573288481d336dde11232ffb8bc64cb04a495f0fc179a64bf0e2aafda'
ZIP_SHA='4db97d5652e262de51617971104e06313211de4d092e6bcb5d7bf34ee7efe054'
def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()
def one(c,table,acc):
    found=c.execute('SELECT rowid,* FROM '+table+' WHERE ACCESSION_NUMBER=?',(acc,)).fetchall()
    if len(found)!=1:raise ValueError('missing or ambiguous filing context')
    return dict(found[0])
def holding(row):
    keep=('INFOTABLE_SK','NAMEOFISSUER','TITLEOFCLASS','CUSIP','FIGI','PUTCALL','SSHPRNAMTTYPE','INVESTMENTDISCRETION','OTHERMANAGER')
    if any(not isinstance(row[k],str) or len(row[k])>500 for k in keep):raise ValueError('public field bounds')
    return {'source_data_row':row['rowid'],**{k:row[k] for k in keep},'security_identity_verified':False}
def build(database,archive,*,all_selected_rows=False):
    if sha(database)!=DB_SHA or sha(archive)!=ZIP_SHA:raise ValueError('source pin')
    c=sqlite3.connect(Path(database).resolve().as_uri()+'?mode=ro',uri=True);c.row_factory=sqlite3.Row
    needed={name:{} for name in ('SUBMISSION.tsv','COVERPAGE.tsv','SUMMARYPAGE.tsv','INFOTABLE.tsv')}
    filings=[]
    try:
        for name in needed:
            if [r[1] for r in c.execute('PRAGMA table_info(holdings_'+name[:-4].lower()+')')]!=SCHEMAS[name]:raise ValueError('schema')
        managers=[r[0] for r in c.execute("SELECT DISTINCT CIK FROM holdings_submission WHERE SUBMISSIONTYPE IN ('13F-HR','13F-HR/A') ORDER BY CAST(CIK AS INTEGER) LIMIT 3")]
        for manager in managers:
            submissions=c.execute("SELECT rowid,* FROM holdings_submission WHERE CIK=? AND SUBMISSIONTYPE IN ('13F-HR','13F-HR/A') ORDER BY ACCESSION_NUMBER LIMIT 2",(manager,)).fetchall()
            for sub in submissions:
                sub=dict(sub);acc=sub['ACCESSION_NUMBER'];cover=one(c,'holdings_coverpage',acc);summary=one(c,'holdings_summarypage',acc)
                if cover['REPORTCALENDARORQUARTER']!=sub['PERIODOFREPORT']:raise ValueError('report period conflict')
                total=c.execute('SELECT COUNT(*) FROM holdings_infotable WHERE ACCESSION_NUMBER=?',(acc,)).fetchone()[0]
                if all_selected_rows and total>1000:raise ValueError('full filing row bound')
                limit=1000 if all_selected_rows else 10
                selected=[dict(r) for r in c.execute('SELECT rowid,* FROM holdings_infotable WHERE ACCESSION_NUMBER=? ORDER BY CAST(INFOTABLE_SK AS INTEGER),rowid LIMIT ?',(acc,limit))]
                for name,records in [('SUBMISSION.tsv',[sub]),('COVERPAGE.tsv',[cover]),('SUMMARYPAGE.tsv',[summary]),('INFOTABLE.tsv',selected)]:
                    for r in records:needed[name][r['rowid']]=r
                filings.append({'manager_cik':manager,'manager_name_as_filed':cover['FILINGMANAGER_NAME'],
                    'accession':acc,'submission_type':sub['SUBMISSIONTYPE'],'filing_date_as_filed':sub['FILING_DATE'],
                    'report_period_as_filed':sub['PERIODOFREPORT'],'amendment_as_filed':cover['ISAMENDMENT'],
                    'amendment_number_as_filed':cover['AMENDMENTNO'],'amendment_type_as_filed':cover['AMENDMENTTYPE'],
                    'amendment_flag_conflict':sub['SUBMISSIONTYPE'].endswith('/A')!=(cover['ISAMENDMENT']=='Y'),
                    'confidential_omission_as_filed':summary['ISCONFIDENTIALOMITTED'],
                    'report_type_as_filed':cover['REPORTTYPE'],'source_holding_rows':total,
                    'displayed_rows':len(selected),'omitted_from_sample_rows':total-len(selected),
                    'holdings':[holding(r) for r in selected],
                    'source_url':f"https://www.sec.gov/Archives/edgar/data/{int(manager)}/{acc.replace('-','')}/{acc}-index.html",
                    'source_url_status':'CONSTRUCTED_FROM_RETAINED_IDENTIFIERS_NOT_FETCHED',
                    'source_submission_row':sub['rowid'],'source_cover_row':cover['rowid'],'source_summary_row':summary['rowid'],
                    'first_public_utc':None,'held_issuer_mapping_verified':False,'changes_computed':False})
        with zipfile.ZipFile(archive) as z:
            inventory(z)
            for name,wanted in needed.items():
                seen=set()
                for n,(raw,_) in enumerate(rows(z,name),1):
                    if n in wanted:
                        if raw!={k:wanted[n][k] for k in SCHEMAS[name]}:raise ValueError('original archive row mismatch')
                        seen.add(n)
                if seen!=set(wanted):raise ValueError('source rows absent')
    finally:c.close()
    if sha(database)!=DB_SHA or sha(archive)!=ZIP_SHA:raise ValueError('source changed')
    return {'version':1,'scope':('COMPLETE_SELECTED_FILING_ROWS_NOT_COMPLETE_PORTFOLIO' if all_selected_rows else 'BOUNDED_AS_FILED_MANAGER_SAMPLE_NOT_PORTFOLIO_OR_TRADE_FLOW'),
        'selection':('First three reporting-manager CIKs numerically among HR/HR-A forms; first two accession-sorted filings each; first ten INFOTABLE_SK-sorted rows per filing. No value/rank/price selection.' if not all_selected_rows else 'Same first three reporting-manager CIKs and first two accession-sorted filings; all retained rows per selected filing, capped at1000 or rejected. No value/rank/price selection.'),
        'source':{'archive_url':URL,'archive_sha256':ZIP_SHA,'database_sha256':DB_SHA,'raw_rows_checked':sum(len(v) for v in needed.values())},
        'filings':filings,'training_ready':False,'execution_ready':False,
        'limitations':['Reporting-manager CIK is not held-issuer CIK. Names, class titles, CUSIP and FIGI are exact source strings, not verified historical identity or current ticker mappings.',
        'One filing batch June–August2026, delayed report periods; no inferred purchases, sales, new/discontinued positions or portfolio changes.',
        'Amendments remain as filed, not reconciled; no restatement/additions replacement or chronological confidential-release reconstruction. Confidentiality omissions prevent complete portfolio conclusions; row coverage describes this filing only.' if all_selected_rows else 'Amendments remain as filed, not reconciled; confidentiality omissions and truncated sample prevent complete holdings conclusions.',
        'No share counts, values, portfolio totals, contacts, addresses, signatures or raw narratives published.',
        'Blank option flag does not establish common-stock ownership. Shares/principal type and other-manager reference remain as filed; no look-through aggregation.',
        'SEC filing-reported identifiers only, not licensed security-list or commercial enrichment. No provider requests.']}
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('database');p.add_argument('archive');p.add_argument('output');a=p.parse_args();result=build(a.database,a.archive)
    with Path(a.output).open('x') as f:json.dump(result,f,indent=2);f.write('\n')
