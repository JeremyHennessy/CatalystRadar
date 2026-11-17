"""Bounded offline Q3 2026 SEC crowdfunding and Regulation A prepared data."""
import argparse, collections, csv, datetime as dt, io, json, re, sqlite3, zipfile
from pathlib import Path
from private_prices import unique_object
from sec_prepared_data import digest
SCHEMAS={'cf': {'2026Q3_cf/FORM_C_DISCLOSURE.tsv': ['ACCESSION_NUMBER', 'COMPENSATIONAMOUNT', 'FINANCIALINTEREST', 'SECURITYOFFEREDTYPE', 'SECURITYOFFEREDOTHERDESC', 'NOOFSECURITYOFFERED', 'PRICE', 'PRICEDETERMINATIONMETHOD', 'OFFERINGAMOUNT', 'OVERSUBSCRIPTIONACCEPTED', 'OVERSUBSCRIPTIONALLOCATIONTYPE', 'DESCOVERSUBSCRIPTION', 'MAXIMUMOFFERINGAMOUNT', 'DEADLINEDATE', 'CURRENTEMPLOYEES', 'TOTALASSETMOSTRECENTFISCALYEAR', 'TOTALASSETPRIORFISCALYEAR', 'CASHEQUIMOSTRECENTFISCALYEAR', 'CASHEQUIPRIORFISCALYEAR', 'ACTRECEIVEDRECENTFISCALYEAR', 'ACTRECEIVEDPRIORFISCALYEAR', 'SHORTTERMDEBTMRECENTFISCALYEAR', 'SHORTTERMDEBTPRIORFISCALYEAR', 'LONGTERMDEBTRECENTFISCALYEAR', 'LONGTERMDEBTPRIORFISCALYEAR', 'REVENUEMOSTRECENTFISCALYEAR', 'REVENUEPRIORFISCALYEAR', 'COSTGOODSSOLDRECENTFISCALYEAR', 'COSTGOODSSOLDPRIORFISCALYEAR', 'TAXPAIDMOSTRECENTFISCALYEAR', 'TAXPAIDPRIORFISCALYEAR', 'NETINCOMEMOSTRECENTFISCALYEAR', 'NETINCOMEPRIORFISCALYEAR'], '2026Q3_cf/FORM_C_ISSUER_JURISDICTIONS.tsv': ['ACCESSION_NUMBER', 'ID', 'ISSUEJURISDICTIONSECUROFFERING'], '2026Q3_cf/FORM_C_ISSUER_SIGNATURE.tsv': ['ACCESSION_NUMBER', 'ID', 'ISSUER', 'ISSUERSIGNATURE', 'ISSUERTITLE'], '2026Q3_cf/FORM_C_SUBMISSION.tsv': ['ACCESSION_NUMBER', 'SUBMISSION_TYPE', 'FILING_DATE', 'CIK', 'FILE_NUMBER', 'PERIOD'], '2026Q3_cf/FORM_C_ISSUER_INFORMATION.tsv': ['ACCESSION_NUMBER', 'ISAMENDMENT', 'PROGRESSUPDATE', 'NATUREOFAMENDMENT', 'NAMEOFISSUER', 'LEGALSTATUSFORM', 'LEGALSTATUSOTHERDESC', 'JURISDICTIONORGANIZATION', 'DATEINCORPORATION', 'STREET1', 'STREET2', 'CITY', 'STATEORCOUNTRY', 'ZIPCODE', 'ISSUERWEBSITE', 'COMPANYNAME', 'ISCOISSUER', 'COMMISSIONCIK', 'COMMISSIONFILENUMBER', 'CRDNUMBER'], '2026Q3_cf/FORM_C_COISSUER_INFORMATION.tsv': ['ACCESSION_NUMBER', 'ID', 'ISEDGARFILER', 'COISSUERCIK', 'NAMEOFCOISSUER', 'LEGALSTATUSFORM', 'LEGALSTATUSOTHERDESC', 'JURISDICTIONORGANIZATION', 'DATEINCORPORATION', 'STREET1', 'STREET2', 'CITY', 'STATEORCOUNTRY', 'ZIPCODE', 'COISSUERWEBSITE'], '2026Q3_cf/FORM_C_SIGNATURE.tsv': ['ACCESSION_NUMBER', 'ID', 'PERSONSIGNATURE', 'PERSONTITLE', 'SIGNATUREDATE']}, 'rega': {'2026Q3_rega/REG_A_CERT_SUSPENSION_Z.tsv': ['ACCESSION_NUMBER', 'CS_ID', 'SECURITIESCLASSTITLE', 'CERTIFICATIONFILENUMBER', 'APPROXRECORDHOLDERS'], '2026Q3_rega/REG_A_EMPLOYEES_INFO.tsv': ['ACCESSION_NUMBER', 'EMP_ID', 'ISSUERNAME', 'JURISDICTIONORGANIZATION', 'YEARINCORPORATION', 'CIK', 'SICCODE', 'FULLTIMEEMPLOYEES', 'PARTTIMEEMPLOYEES'], '2026Q3_rega/REG_A_EQUITIES_DEBT.tsv': ['ACCESSION_NUMBER', 'ED_ID', 'TYPE', 'NAME', 'OUTSTANDING', 'CUSIP', 'PUBLICYTRADED'], '2026Q3_rega/REG_A_ISSUER_INFO.tsv': ['ACCESSION_NUMBER', 'STREET1', 'STREET2', 'CITY', 'STATEORCOUNTRY', 'ZIPCODE', 'PHONENUMBER', 'CONNECTIONNAME', 'INDUSTRYGROUP', 'CASHEQUIVALENTS', 'INVESTMENTSECURITIES', 'TOTALINVESTMENTS', 'ACCOUNTSRECEIVABLE', 'LOANS', 'PROPERTYPLANTEQUIPMENT', 'PROPERTYANDEQUIPMENT', 'TOTALASSETS', 'ACCOUNTSPAYABLE', 'POLICYLIABILITIESANDACCRUALS', 'DEPOSITS', 'LONGTERMDEBT', 'TOTALLIABILITIES', 'TOTALSTOCKHOLDEREQUITY', 'TOTALLIABILITIESANDEQUITY', 'TOTALREVENUES', 'TOTALINTERESTINCOME', 'COSTANDEXPENSESAPPLTOREVENUES', 'TOTALINTERESTEXPENSES', 'DEPRECIATIONANDAMORTIZATION', 'NETINCOME', 'EARNINGSPERSHAREBASIC', 'EARNINGSPERSHAREDILUTED', 'NAMEAUDITOR', 'CERTIFYIFTRUE', 'CERTIFYIFNOTDISQUALIFIED', 'CERTIFYIFBADACTOR', 'JURISDICTIONSOFSECOFFEREDNONE', 'JURISDICTIONSOFSECOFFEREDSAME', 'IFUNREGSITEREDNONE', 'SECURITIESACTEXCEMPTION'], '2026Q3_rega/REG_A_ITEM_INFO_K.tsv': ['ACCESSION_NUMBER', 'INFO_ID', 'ISSUERNAME', 'CIK', 'JURISDICTIONORGANIZATION'], '2026Q3_rega/REG_A_ITEM_KZ.tsv': ['ACCESSION_NUMBER', 'FORMINDICATION', 'ISSUERNAME', 'FISCALYEAREND', 'STREET1', 'STREET2', 'CITY', 'STATEORCOUNTRY', 'ZIPCODE', 'PHONENUMBER', 'REGARULE257'], '2026Q3_rega/REG_A_ITEM_SECURITIES_K.tsv': ['ACCESSION_NUMBER', 'SI_ID', 'ISSUEDSECURITIESTITLE'], '2026Q3_rega/REG_A_JURISDICTION.tsv': ['ACCESSION_NUMBER', 'JID', 'TYPE', 'ISSUEJURISDICTIONOFFERING'], '2026Q3_rega/REG_A_SECURITIES_ISSUED.tsv': ['ACCESSION_NUMBER', 'SECURITY_ID', 'SECURITIESISSUERNAME', 'SECURITIESISSUERTITLE', 'SECURITIESISSUEDTOTALAMOUNT', 'SECURITIESPRINCIPALHOLDERAMT', 'SECURITIESISSUEDAGGREGATEAMT', 'AGGREGATECONSIDERATIONBASIS'], '2026Q3_rega/REG_A_SECURITIES_OFFERED.tsv': ['ACCESSION_NUMBER', 'SO_ID', 'SECURITIESOFFEREDTYPES', 'SECURITIESOFFEREDOTHERDESC'], '2026Q3_rega/REG_A_SIGNATURE_Z.tsv': ['ACCESSION_NUMBER', 'SIGN_ID', 'CIK', 'REGULATIONISSUERNAME1', 'REGULATIONISSUERNAME2', 'SIGNATUREBY', 'SIGNATURE_DATE', 'TITLE'], '2026Q3_rega/REG_A_SUBMISSION.tsv': ['ACCESSION_NUMBER', 'SUBMISSIONTYPE', 'ISSUERCIK', 'DOSFILENUMBER', 'OFFERINGFILENUMBER', 'SHELLCOMPANYFLAG', 'SUCCESSORFILINGFLAG', 'REPORTINGPERIOD', 'FILING_DATE', 'FILE_NUMBER'], '2026Q3_rega/REG_A_SUMMARY_INFO_KZ.tsv': ['ACCESSION_NUMBER', 'SINFO_ID', 'COMMISSIONFILENUMBER', 'OFFERINGQUALIFICATIONDATE', 'OFFERINGCOMMENCEDATE', 'QUALIFIEDSECURITIESSOLD', 'OFFERINGSECURITIESSOLD', 'PORTIONSECURITIESSOLDISSUER', 'PORTIONSOLDSECURITYHOLDERS', 'PRICEPERSECURITY', 'AGGREGRATEOFFERINGPRICE', 'AGGREGRATEOFFERINGPRICEHOLDERS', 'UNDERWRITERFEES', 'SALESCOMMISSIONSFEE', 'FINDERSFEES', 'AUDITORFEES', 'LEGALFEES', 'PROMOTERSFEES', 'BLUESKYFEES', 'CRDNUMBERBROKERDEALER', 'ISSUERNETPROCEEDS', 'CLARIFICATIONRESPONSES'], '2026Q3_rega/REG_A_SUMMARY_INFO.tsv': ['ACCESSION_NUMBER', 'INDICATETIER1TIER2OFFERING', 'FINANCIALSTATEMENTAUDITSTATUS', 'OFFERDELAYEDCONTINUOUSFLAG', 'OFFERINGYEARFLAG', 'OFFERINGAFTERQUALIFFLAG', 'OFFERINGBESTEFFORTSFLAG', 'SOLICITATIONPROPOSEDOFFERFLAG', 'RESALESECURITIESAFFILIATESFLAG', 'SECURITIESOFFERED', 'OUTSTANDINGSECURITIES', 'PRICEPERSECURITY', 'ISSUERAGGREGATEOFFERING', 'SECURITYHOLDERAGGEGATE', 'QUALIFICATIONOFFERINGAGGREGATE', 'CONCURRENTOFFERINGAGGREGATE', 'TOTALAGGREGATEOFFERING', 'UNDERWRITERSERVICEPROVIDERNAME', 'UNDERWRITERSFEES', 'SALECOMMISSIONSSVCPROVIDERNAME', 'SALECOMMISSIONSSVCEROVIDERFEE', 'FINDERSFEESSERVICEPROVIDERNAME', 'FINDERFEESFEE', 'AUDITORSERVICEPROVIDERNAME', 'AUDITORFEES', 'LEGALSERVICEPROVIDERNAME', 'LEGALFEES', 'PROMOTERSSERVICEPROVIDERNAME', 'PROMOTERSFEES', 'BLUESKYSERVICEPROVIDERNAME', 'BLUESKYFEES', 'BROKERDEALERCRDNUMBER', 'ESTIMATEDNETAMOUNT', 'CLARIFICATIONRESPONSES'], '2026Q3_rega/REG_A_SUMMARY_NAMES_KZ.tsv': ['ACCESSION_NUMBER', 'NID', 'SINFO_ID', 'NAME_TYPE', 'NAME']}}
MEMBERS={'cf': ['2026Q3_cf/FORM_C_DISCLOSURE.tsv', '2026Q3_cf/FORM_C_ISSUER_JURISDICTIONS.tsv', '2026Q3_cf/FORM_C_ISSUER_SIGNATURE.tsv', '2026Q3_cf/FORM_C_SUBMISSION.tsv', '2026Q3_cf/FORM_C_ISSUER_INFORMATION.tsv', '2026Q3_cf/FORM_C_COISSUER_INFORMATION.tsv', '2026Q3_cf/FORM_C_SIGNATURE.tsv', '2026Q3_cf/cf_metadata.json', '2026Q3_cf/cf_readme.html'], 'rega': ['2026Q3_rega/REG_A_CERT_SUSPENSION_Z.tsv', '2026Q3_rega/REG_A_EMPLOYEES_INFO.tsv', '2026Q3_rega/REG_A_EQUITIES_DEBT.tsv', '2026Q3_rega/REG_A_ISSUER_INFO.tsv', '2026Q3_rega/REG_A_ITEM_INFO_K.tsv', '2026Q3_rega/REG_A_ITEM_KZ.tsv', '2026Q3_rega/REG_A_ITEM_SECURITIES_K.tsv', '2026Q3_rega/REG_A_JURISDICTION.tsv', '2026Q3_rega/REG_A_SECURITIES_ISSUED.tsv', '2026Q3_rega/REG_A_SECURITIES_OFFERED.tsv', '2026Q3_rega/REG_A_SIGNATURE_Z.tsv', '2026Q3_rega/REG_A_SUBMISSION.tsv', '2026Q3_rega/REG_A_SUMMARY_INFO_KZ.tsv', '2026Q3_rega/REG_A_SUMMARY_INFO.tsv', '2026Q3_rega/REG_A_SUMMARY_NAMES_KZ.tsv', '2026Q3_rega/RegA_metadata.json', '2026Q3_rega/RegA_readme.html']}
URLS={'cf':'https://www.sec.gov/files/dera/data/crowdfunding-offerings-data-sets/2026q3_cf.zip','rega':'https://www.sec.gov/files/datastandardsinnovation/data/regulation-data-sets/2026q3_rega.zip'}
SUB={'cf':'2026Q3_cf/FORM_C_SUBMISSION.tsv','rega':'2026Q3_rega/REG_A_SUBMISSION.tsv'}
FORMS={'cf':{'C','C/A','C-U','C-AR','C-AR/A','C-TR','C-W','C/A-W','C-TR-W','C-U-W','C-AR-W','C-AR/A-W'},'rega':{'1-A','1-A/A','1-A POS','1-K','1-K/A','1-Z','1-Z/A'}}

def inventory(z,kind):
    rows=z.infolist()
    if len(rows)!=len(MEMBERS[kind]) or {r.filename for r in rows}!=set(MEMBERS[kind]):raise ValueError('ZIP member set')
    if sum(r.file_size for r in rows)>20_000_000 or any(r.file_size>5_000_000 or r.flag_bits&1 for r in rows):raise ValueError('ZIP bounds')

def rows(z,kind,name):
    csv.field_size_limit(2_000_000)
    with z.open(name) as f:
        r=csv.reader(io.TextIOWrapper(f,encoding='utf-8-sig',newline=''),delimiter='\t',strict=True)
        if next(r)!=SCHEMAS[kind][name]:raise ValueError('table schema')
        for values in r:
            if len(values)!=len(SCHEMAS[kind][name]):raise ValueError('row width')
            yield dict(zip(SCHEMAS[kind][name],values)),values

def ingest(root,out):
    if out.exists() or out.resolve().is_relative_to(Path(__file__).resolve().parents[1]):raise ValueError('new private output outside checkout required')
    receipts=json.loads((root/'browser-receipts.json').read_text(),object_pairs_hook=unique_object)
    if not isinstance(receipts,list) or len(receipts)!=2:raise ValueError('receipt inventory')
    verified={}
    for r in receipts:
        fields={'path','url','byte_count','sha256','local_verified_utc','retrieval_method','http_status','exact_download_utc'}
        if not isinstance(r,dict) or set(r)!=fields:raise ValueError('receipt schema')
        kinds=[k for k in URLS if r['url']==URLS[k] and r['path']==f'2026q3_{k}.zip']
        if len(kinds)!=1 or kinds[0] in verified or r['http_status'] is not None or r['exact_download_utc'] is not None or r['retrieval_method']!='PUBLIC_BROWSER_LINK_DOWNLOAD_NO_PRIVATE_CONTACT':raise ValueError('receipt identity')
        seen=dt.datetime.fromisoformat(r['local_verified_utc'])
        if seen.tzinfo is None or seen>dt.datetime.now(dt.timezone.utc):raise ValueError('verification clock')
        p=root/r['path']
        if p.stat().st_size>2_000_000 or p.stat().st_size!=r['byte_count'] or digest(p)!=r['sha256']:raise ValueError('source integrity')
        with zipfile.ZipFile(p) as z:inventory(z,kinds[0])
        verified[kinds[0]]=(r,seen)
    out.mkdir(parents=True,mode=0o700);(out/'INCOMPLETE').write_text('Unverified build. Do not use.\n')
    path=out/'offerings.sqlite';db=sqlite3.connect(path);path.chmod(0o600);db.execute('PRAGMA synchronous=FULL');db.execute('PRAGMA journal_mode=DELETE')
    counts={};datasets={}
    try:
        for kind in ['cf','rega']:
            r,seen=verified[kind];accs=set();ciks=set();forms=collections.Counter();dates=[];coissuer_missing=0
            with zipfile.ZipFile(root/r['path']) as z:
                for name in [SUB[kind]]+sorted(set(SCHEMAS[kind])-{SUB[kind]}):
                    table=kind+'_'+Path(name).stem.lower();header=SCHEMAS[kind][name]
                    db.execute('CREATE TABLE '+table+' ('+','.join('"'+c+'" TEXT' for c in header)+')');sql='INSERT INTO '+table+' VALUES ('+','.join('?' for _ in header)+')';batch=[];count=0
                    for d,v in rows(z,kind,name):
                        acc=d['ACCESSION_NUMBER']
                        if not re.fullmatch(r'\d{10}-\d{2}-\d{6}',acc):raise ValueError('accession')
                        if name==SUB[kind]:
                            cik=d['CIK' if kind=='cf' else 'ISSUERCIK'];form=d['SUBMISSION_TYPE' if kind=='cf' else 'SUBMISSIONTYPE'];day=dt.datetime.strptime(d['FILING_DATE'],'%Y%m%d' if kind=='cf' else '%d-%b-%Y').date()
                            if acc in accs or not re.fullmatch(r'\d{1,10}',cik) or int(cik)==0 or form not in FORMS[kind]:raise ValueError('submission identity')
                            if not dt.date(2026,7,1)<=day<=dt.date(2026,9,30) or day>seen.date():raise ValueError('filing date')
                            accs.add(acc);ciks.add(str(int(cik)).zfill(10));forms[form]+=1;dates.append(day.isoformat())
                        elif acc not in accs:raise ValueError('orphan accession')
                        if kind=='cf' and name.endswith('FORM_C_COISSUER_INFORMATION.tsv'):
                            value=d['COISSUERCIK']
                            if value and (not re.fullmatch(r'\d{1,10}',value) or int(value)==0):raise ValueError('coissuer CIK')
                            coissuer_missing+=value==''
                        batch.append(v);count+=1
                        if len(batch)>=5000:db.executemany(sql,batch);batch=[]
                    if batch:db.executemany(sql,batch)
                    counts[table]=count;db.commit()
                for name in set(MEMBERS[kind])-set(SCHEMAS[kind]):
                    with z.open(name) as f:
                        while f.read(1024*1024):pass
            if not dates:raise ValueError('empty submissions')
            datasets[kind]={'source':r,'submissions':len(accs),'submission_issuer_ciks':len(ciks),'submission_types':dict(sorted(forms.items())),'filing_date_min':min(dates),'filing_date_max':max(dates),'accession_joins_verified':True}
            if kind=='cf':datasets[kind]['coissuer_rows_without_cik']=coissuer_missing
        db.commit();db.close();db=sqlite3.connect('file:'+str(path.resolve())+'?mode=ro',uri=True)
        if db.execute('PRAGMA quick_check').fetchone()!=('ok',):raise ValueError('database integrity')
        for table,n in counts.items():
            if db.execute('SELECT COUNT(*) FROM '+table).fetchone()[0]!=n:raise ValueError('persisted count')
        s={'version':1,'status':'HISTORICAL_CF_REGA_AS_FILED_NOT_SIGNALS','completed_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'datasets':datasets,'table_rows':counts,'simulation_enabled':False,'orders_created':0,'limitations':['Q3 2026 prepared filings, not all companies or complete offering histories. Dataset issuer counts remain separate, not added to existing issuer coverage.','Crowdfunding statements, amendments, progress updates, annual reports, terminations and withdrawals are distinct submission types, not unique successful financing rounds.','Regulation A offering statements, amendments/post-qualification amendments, annual reports and exit reports are retained separately; filing is not proof of qualification, SEC endorsement or completed proceeds.','Source amendment flags, offering amounts, financial fields and date context remain verbatim, not reconciled, summed or interpreted as current comparable facts.','Co-issuers with missing CIKs remain unlinked and are explicitly counted; no invented entity mappings.','Raw addresses, signatures and personal/provider details remain private. Only aggregate coverage is published.','Only accession joins are verified; no claim that all table-specific identity links or prior-quarter histories have been reconciled.','Exact download clocks/HTTP status unavailable; local verification timestamps are not first-public or historical trading evidence. No orders or paper fills are generated.']}
        (out/'summary.json').write_text(json.dumps(s,indent=2)+'\n');db.close();(out/'INCOMPLETE').unlink();return s
    except Exception:
        db.close();(out/'INCOMPLETE').write_text('Validation failed. Do not publish.\n');raise

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();print(json.dumps(ingest(a.root,a.out),indent=2))
