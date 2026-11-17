"""Offline bounded SEC June–August 2026 Form 13F ingestion; no trading signals."""
import argparse, collections, csv, datetime as dt, hashlib, io, json, re, sqlite3, zipfile
from pathlib import Path
from private_prices import unique_object
from sec_prepared_data import digest, finite_number
ARCHIVE = '01jun2026-31aug2026_form13f.zip'
URL = 'https://www.sec.gov/files/datastandardsinnovation/data/form-13f-data-sets/' + ARCHIVE
SCHEMAS = {'COVERPAGE.tsv': ['ACCESSION_NUMBER', 'REPORTCALENDARORQUARTER', 'ISAMENDMENT', 'AMENDMENTNO', 'AMENDMENTTYPE', 'CONFDENIEDEXPIRED', 'DATEDENIEDEXPIRED', 'DATEREPORTED', 'REASONFORNONCONFIDENTIALITY', 'FILINGMANAGER_NAME', 'FILINGMANAGER_STREET1', 'FILINGMANAGER_STREET2', 'FILINGMANAGER_CITY', 'FILINGMANAGER_STATEORCOUNTRY', 'FILINGMANAGER_ZIPCODE', 'REPORTTYPE', 'FORM13FFILENUMBER', 'CRDNUMBER', 'SECFILENUMBER', 'PROVIDEINFOFORINSTRUCTION5', 'ADDITIONALINFORMATION'], 'INFOTABLE.tsv': ['ACCESSION_NUMBER', 'INFOTABLE_SK', 'NAMEOFISSUER', 'TITLEOFCLASS', 'CUSIP', 'FIGI', 'VALUE', 'SSHPRNAMT', 'SSHPRNAMTTYPE', 'PUTCALL', 'INVESTMENTDISCRETION', 'OTHERMANAGER', 'VOTING_AUTH_SOLE', 'VOTING_AUTH_SHARED', 'VOTING_AUTH_NONE'], 'OTHERMANAGER.tsv': ['ACCESSION_NUMBER', 'OTHERMANAGER_SK', 'CIK', 'FORM13FFILENUMBER', 'CRDNUMBER', 'SECFILENUMBER', 'NAME'], 'OTHERMANAGER2.tsv': ['ACCESSION_NUMBER', 'SEQUENCENUMBER', 'CIK', 'FORM13FFILENUMBER', 'CRDNUMBER', 'SECFILENUMBER', 'NAME'], 'SIGNATURE.tsv': ['ACCESSION_NUMBER', 'NAME', 'TITLE', 'PHONE', 'SIGNATURE', 'CITY', 'STATEORCOUNTRY', 'SIGNATUREDATE'], 'SUBMISSION.tsv': ['ACCESSION_NUMBER', 'FILING_DATE', 'SUBMISSIONTYPE', 'CIK', 'PERIODOFREPORT'], 'SUMMARYPAGE.tsv': ['ACCESSION_NUMBER', 'OTHERINCLUDEDMANAGERSCOUNT', 'TABLEENTRYTOTAL', 'TABLEVALUETOTAL', 'ISCONFIDENTIALOMITTED']}
ORDER = ['SUBMISSION.tsv','COVERPAGE.tsv','SUMMARYPAGE.tsv','OTHERMANAGER.tsv','OTHERMANAGER2.tsv','SIGNATURE.tsv','INFOTABLE.tsv']
MEMBERS = set(ORDER) | {'FORM13F_metadata.json','FORM13F_readme.htm'}

def inventory(z):
    info=z.infolist()
    if len(info)!=len(MEMBERS) or {i.filename for i in info}!=MEMBERS: raise ValueError('ZIP members')
    if sum(i.file_size for i in info)>700_000_000 or any(i.file_size>500_000_000 or i.flag_bits&1 for i in info): raise ValueError('ZIP bounds')

def rows(z,name):
    csv.field_size_limit(2_000_000)
    with z.open(name) as f:
        r=csv.reader(io.TextIOWrapper(f,encoding='utf-8-sig',newline=''),delimiter='\t',strict=True)
        if next(r)!=SCHEMAS[name]: raise ValueError('table schema')
        for values in r:
            if len(values)!=len(SCHEMAS[name]): raise ValueError('row width')
            yield dict(zip(SCHEMAS[name],values)),values

def day(value):
    return dt.datetime.strptime(value,'%d-%b-%Y').date()

def ingest(root,out):
    if out.exists() or out.resolve().is_relative_to(Path(__file__).resolve().parents[1]): raise ValueError('new private output outside checkout required')
    r=json.loads((root/'browser-receipt.json').read_text(),object_pairs_hook=unique_object)
    fields={'path','url','byte_count','sha256','local_verified_utc','retrieval_method','http_status','exact_download_utc'}
    if set(r)!=fields or r['path']!=ARCHIVE or r['url']!=URL or r['http_status'] is not None or r['exact_download_utc'] is not None or r['retrieval_method']!='PUBLIC_BROWSER_LINK_DOWNLOAD_NO_PRIVATE_CONTACT': raise ValueError('receipt schema')
    seen=dt.datetime.fromisoformat(r['local_verified_utc'])
    if seen.tzinfo is None or seen>dt.datetime.now(dt.timezone.utc): raise ValueError('verification clock')
    p=root/ARCHIVE
    if p.stat().st_size>120_000_000 or p.stat().st_size!=r['byte_count'] or digest(p)!=r['sha256']: raise ValueError('source integrity')
    with zipfile.ZipFile(p) as z: inventory(z)
    out.mkdir(mode=0o700,parents=True);(out/'INCOMPLETE').write_text('Unverified build. Do not use.\n')
    dbpath=out/'holdings.sqlite';db=sqlite3.connect(dbpath);dbpath.chmod(0o600)
    db.execute('PRAGMA synchronous=FULL');db.execute('PRAGMA journal_mode=DELETE')
    db.execute('CREATE TABLE holdings_validation_gaps (accession TEXT, reason TEXT)')
    counts={};accessions=set();managers=set();dates=[];periods=[];forms=collections.Counter();amendments=collections.Counter();singletons={};holding_acc=set();cusips=set();empty_cusip=0; submission_context={}; conflicts=0
    try:
        with zipfile.ZipFile(p) as z:
            for name in ORDER:
                table='holdings_'+name[:-4].lower();header=SCHEMAS[name]
                db.execute('CREATE TABLE '+table+' ('+','.join('"'+c+'" TEXT' for c in header)+')')
                sql='INSERT INTO '+table+' VALUES ('+','.join('?' for c in header)+')';batch=[];count=0;keys=set()
                for data,values in rows(z,name):
                    acc=data['ACCESSION_NUMBER']
                    if not re.fullmatch(r'\d{10}-\d{2}-\d{6}',acc): raise ValueError('accession')
                    if name=='SUBMISSION.tsv':
                        filing=day(data['FILING_DATE']);period=day(data['PERIODOFREPORT']);cik=data['CIK'];form=data['SUBMISSIONTYPE']
                        if acc in accessions or not re.fullmatch(r'\d{1,10}',cik) or int(cik)==0: raise ValueError('submission identity')
                        if not dt.date(2026,6,1)<=filing<=dt.date(2026,8,31) or period>filing or filing>seen.date(): raise ValueError('submission dates')
                        if form not in {'13F-HR','13F-HR/A','13F-NT','13F-NT/A'}: raise ValueError('submission type')
                        submission_context[acc]=(form,period);accessions.add(acc);managers.add(str(int(cik)).zfill(10));dates.append(filing.isoformat());periods.append(period.isoformat());forms[form]+=1
                    elif acc not in accessions: raise ValueError('orphan accession')
                    if name in {'COVERPAGE.tsv','SUMMARYPAGE.tsv','SIGNATURE.tsv'}:
                        if acc in keys: raise ValueError('duplicate singleton accession')
                        keys.add(acc)
                    if name=='COVERPAGE.tsv':
                        if data['ISAMENDMENT'] not in {'','Y','N'} or data['AMENDMENTTYPE'] not in {'','RESTATEMENT','NEW HOLDINGS'}: raise ValueError('amendment vocabulary')
                        
                        if day(data['REPORTCALENDARORQUARTER'])!=submission_context[acc][1]: raise ValueError('report period mismatch')
                        if (data['ISAMENDMENT']=='Y')!=submission_context[acc][0].endswith('/A'):
                            conflicts+=1;db.execute('INSERT INTO holdings_validation_gaps VALUES (?,?)',(acc,'FORM_COVER_AMENDMENT_CONFLICT_NOT_RECONCILED'))
                        amendments[data['AMENDMENTTYPE'] or '(blank)']+=1
                    if name=='INFOTABLE.tsv':
                        holding_acc.add(acc)
                        if data['CUSIP']: cusips.add(data['CUSIP'])
                        else: empty_cusip+=1
                        for c in ['VALUE','SSHPRNAMT','VOTING_AUTH_SOLE','VOTING_AUTH_SHARED','VOTING_AUTH_NONE']: finite_number(data[c])
                    batch.append(values);count+=1
                    if len(batch)>=5000:db.executemany(sql,batch);batch=[]
                if batch:db.executemany(sql,batch)
                counts[table]=count;db.commit()
                if name in {'COVERPAGE.tsv','SIGNATURE.tsv'} and keys!=accessions: raise ValueError('missing required singleton')
            for name in MEMBERS-set(ORDER):
                with z.open(name) as f:
                    while f.read(1024*1024):pass
        counts['holdings_validation_gaps']=conflicts;db.commit();db.close();db=sqlite3.connect('file:'+str(dbpath.resolve())+'?mode=ro',uri=True)
        if db.execute('PRAGMA quick_check').fetchone()!=('ok',): raise ValueError('database integrity')
        for table,n in counts.items():
            if db.execute('SELECT COUNT(*) FROM '+table).fetchone()[0]!=n: raise ValueError('persisted row count')
        if not dates: raise ValueError('empty submissions')
        summary={'version':1,'status':'HISTORICAL_13F_AS_FILED_NOT_LIVE_HOLDINGS','completed_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'source':r,'table_rows':counts,'filing_manager_ciks':len(managers),'submissions':len(accessions),'submissions_with_holding_rows':len(holding_acc),'holding_cusip_strings':len(cusips),'holding_rows_missing_cusip':empty_cusip,'filing_date_min':min(dates),'filing_date_max':max(dates),'report_period_min':min(periods),'report_period_max':max(periods),'submission_types':dict(sorted(forms.items())),'amendment_types':dict(sorted(amendments.items())),'amendment_form_cover_conflicts':conflicts,'accession_joins_verified':True,'simulation_enabled':False,'orders_created':0,'limitations':['June–August2026 as-filed submission batch, not all managers, securities or current holdings.','Manager CIKs identify reporting institutions, not held-security issuers; do not add them to issuer coverage.','Amendments, restatements, added holdings, report periods and confidential-omission context are preserved separately; rows are not deduplicated current positions.','VALUE in this source is reported dollars, not thousands; amounts remain exact source text with shares/principal, options and voting/discretion context. No aggregate portfolio value is computed.','CUSIPs are source strings, not verified ticker/issuer mappings. Holdings are delayed, may concern old periods, and are not purchase/sale transactions or investment signals.','Conflicting amendment flags are preserved in a private validation table, not automatically reconciled.','Raw holdings, addresses, phone numbers and signatures remain private; only coverage aggregates are published.','Browser status and exact download clock unavailable; local verification time is not first-public evidence.']}
        (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');db.close();(out/'INCOMPLETE').unlink();return summary
    except Exception:
        db.close();(out/'INCOMPLETE').write_text('Validation failed. Do not publish.\n');raise

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();print(json.dumps(ingest(a.root,a.out),indent=2))
