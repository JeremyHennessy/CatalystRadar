"""Literal as-filed disclosure-key differences, never economic position changes."""
import argparse,json,sqlite3,zipfile
from pathlib import Path
from manager_holdings_sample import DB_SHA,ZIP_SHA,sha,one,holding
from manager_period_research import date
from sec_13f_data import SCHEMAS,inventory,rows,URL
KEY=('CUSIP','TITLEOFCLASS','PUTCALL','SSHPRNAMTTYPE','INVESTMENTDISCRETION','OTHERMANAGER')

def compare(before,after):
    def group(records):
        result={}
        for r in records:
            if not r['CUSIP'] or not r['TITLEOFCLASS']:raise ValueError('missing comparison key')
            key=tuple(r[k] for k in KEY);result.setdefault(key,[]).append(holding(r))
        return result
    a,b=group(before),group(after)
    return {'key_fields':list(KEY),'common_literal_keys':len(a.keys()&b.keys()),
      'earlier_only':[{'key':list(k),'source_rows':a[k]} for k in sorted(a.keys()-b.keys())],
      'later_only':[{'key':list(k),'source_rows':b[k]} for k in sorted(b.keys()-a.keys())],
      'repeated_key_groups_earlier':sum(len(v)>1 for v in a.values()),'repeated_key_groups_later':sum(len(v)>1 for v in b.values()),
      'economic_changes_qualified':False}

def build(database,archive):
    if sha(database)!=DB_SHA or sha(archive)!=ZIP_SHA:raise ValueError('source pin')
    c=sqlite3.connect(Path(database).resolve().as_uri()+'?mode=ro',uri=True);c.row_factory=sqlite3.Row
    needed={n:{} for n in ('SUBMISSION.tsv','COVERPAGE.tsv','SUMMARYPAGE.tsv','INFOTABLE.tsv')};filings=[];sets=[]
    try:
        for n in needed:
            if [r[1] for r in c.execute('PRAGMA table_info(holdings_'+n[:-4].lower()+')')]!=SCHEMAS[n]:raise ValueError('schema')
        manager=c.execute("SELECT CIK FROM holdings_submission WHERE SUBMISSIONTYPE IN ('13F-HR','13F-HR/A') GROUP BY CIK HAVING COUNT(DISTINCT PERIODOFREPORT)>1 ORDER BY CAST(CIK AS INTEGER) LIMIT 1").fetchone()
        if not manager:raise ValueError('no multi-period manager')
        manager=manager[0];subs=[dict(r) for r in c.execute('SELECT rowid,* FROM holdings_submission WHERE CIK=?',(manager,))]
        if len(subs)>100:raise ValueError('filing bound')
        periods=sorted({date(r['PERIODOFREPORT']) for r in subs})[:2]
        for period in periods:
            choices=[s for s in subs if date(s['PERIODOFREPORT'])==period]
            if len(choices)!=1:raise ValueError('ambiguous period/amendment filings')
            s=choices[0];acc=s['ACCESSION_NUMBER'];cover=one(c,'holdings_coverpage',acc);summary=one(c,'holdings_summarypage',acc)
            if s['SUBMISSIONTYPE']!='13F-HR' or cover['ISAMENDMENT'] not in ('','N') or cover['AMENDMENTTYPE'] or cover['AMENDMENTNO'] or cover['CONFDENIEDEXPIRED'] not in ('','N') or summary['ISCONFIDENTIALOMITTED']!='N' or cover['REPORTTYPE']!='13F HOLDINGS REPORT' or cover['REPORTCALENDARORQUARTER']!=s['PERIODOFREPORT']:raise ValueError('amendment/confidential/scope blocker')
            records=[dict(r) for r in c.execute('SELECT rowid,* FROM holdings_infotable WHERE ACCESSION_NUMBER=? ORDER BY CAST(INFOTABLE_SK AS INTEGER),rowid LIMIT 1001',(acc,))]
            if not records or len(records)>1000:raise ValueError('holding bound')
            if summary['TABLEENTRYTOTAL']!=str(len(records)):raise ValueError('declared row count mismatch')
            sets.append(records)
            for n,rs in [('SUBMISSION.tsv',[s]),('COVERPAGE.tsv',[cover]),('SUMMARYPAGE.tsv',[summary]),('INFOTABLE.tsv',records)]:
                for r in rs:needed[n][r['rowid']]=r
            filings.append({'accession':acc,'report_period':period,'filing_date':date(s['FILING_DATE']),'form_as_filed':s['SUBMISSIONTYPE'],'manager_name_as_filed':cover['FILINGMANAGER_NAME'],'row_count':len(records),'amendment_flag_as_filed':cover['ISAMENDMENT'],'amendment_type_as_filed':cover['AMENDMENTTYPE'],'confidential_omitted_as_filed':summary['ISCONFIDENTIALOMITTED'],'confidential_denied_expired_as_filed':cover['CONFDENIEDEXPIRED'],'source_rows':{'submission':s['rowid'],'cover':cover['rowid'],'summary':summary['rowid']},'source_url':f"https://www.sec.gov/Archives/edgar/data/{int(manager)}/{acc.replace('-','')}/{acc}-index.html",'source_url_status':'CONSTRUCTED_NOT_FETCHED'})
        with zipfile.ZipFile(archive) as z:
            inventory(z)
            for n,wanted in needed.items():
                seen=set()
                for i,(raw,_) in enumerate(rows(z,n),1):
                    if i in wanted:
                        if raw!={k:wanted[i][k] for k in SCHEMAS[n]}:raise ValueError('archive row mismatch')
                        seen.add(i)
                if seen!=set(wanted):raise ValueError('missing archive rows')
    finally:c.close()
    if sha(database)!=DB_SHA or sha(archive)!=ZIP_SHA:raise ValueError('source changed')
    return {'version':1,'status':'AS_FILED_LITERAL_KEY_DIFFERENCE_NOT_POSITION_OR_TRADE_CHANGE',
      'selection':'First numeric HR/HR-A manager with multiple reported periods; earliest two periods; fail rather than replace on ambiguity or source-scope blockers. Retrospective diagnostic, not representative.',
      'manager_cik':manager,'filings':filings,'comparison':compare(*sets),
      'source':{'archive_url':URL,'archive_sha256':ZIP_SHA,'database_sha256':DB_SHA,'rows_checked':sum(len(x) for x in needed.values())},
      'limitations':['Literal source-key presence only. Earlier/later-only is not purchase, sale, opened or closed economic position; common key does not prove same security or unchanged exposure.',
       'Blank amendment/denied-expired flags are unknown, not proof of no amendments or confidential releases. No amendment history reconciliation or complete-portfolio claim.',
       'Class/option/discretion/other-manager label changes can split one economic position; same labels can hide corporate actions. Names are source labels, not issuer mapping.',
       'No share/value arithmetic, security mapping, total exposure, first-public timing, prices or outcomes. Missing records outside the retained filing batch remain unknown.'],
      'first_public_utc':None,'training_ready':False,'execution_ready':False}
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('database');p.add_argument('archive');p.add_argument('output');a=p.parse_args();out=build(a.database,a.archive)
    with Path(a.output).open('x') as f:json.dump(out,f,indent=2);f.write('\n')
