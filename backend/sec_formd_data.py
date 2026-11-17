"""Offline SEC Q3 2026 Form D notices; no security recommendations or trades."""
import argparse,collections,csv,datetime as dt,io,json,re,sqlite3,zipfile
from pathlib import Path
from private_prices import unique_object
from sec_prepared_data import digest
ARCHIVE='2026q3_d.zip'
URL='https://www.sec.gov/files/datastandardsinnovation/data/form-d-data-sets/'+ARCHIVE
SCHEMAS={'2026Q3_d/SIGNATURES.tsv': ['ACCESSIONNUMBER', 'SIGNATURE_SEQ_KEY', 'ISSUERNAME', 'SIGNATURENAME', 'NAMEOFSIGNER', 'SIGNATURETITLE', 'SIGNATUREDATE'], '2026Q3_d/FORMDSUBMISSION.tsv': ['ACCESSIONNUMBER', 'FILE_NUM', 'FILING_DATE', 'SIC_CODE', 'SCHEMAVERSION', 'SUBMISSIONTYPE', 'TESTORLIVE', 'OVER100PERSONSFLAG', 'OVER100ISSUERFLAG'], '2026Q3_d/RELATEDPERSONS.tsv': ['ACCESSIONNUMBER', 'RELATEDPERSON_SEQ_KEY', 'FIRSTNAME', 'MIDDLENAME', 'LASTNAME', 'STREET1', 'STREET2', 'CITY', 'STATEORCOUNTRY', 'STATEORCOUNTRYDESCRIPTION', 'ZIPCODE', 'RELATIONSHIP_1', 'RELATIONSHIP_2', 'RELATIONSHIP_3', 'RELATIONSHIPCLARIFICATION'], '2026Q3_d/ISSUERS.tsv': ['ACCESSIONNUMBER', 'IS_PRIMARYISSUER_FLAG', 'ISSUER_SEQ_KEY', 'CIK', 'ENTITYNAME', 'STREET1', 'STREET2', 'CITY', 'STATEORCOUNTRY', 'STATEORCOUNTRYDESCRIPTION', 'ZIPCODE', 'ISSUERPHONENUMBER', 'JURISDICTIONOFINC', 'ISSUER_PREVIOUSNAME_1', 'ISSUER_PREVIOUSNAME_2', 'ISSUER_PREVIOUSNAME_3', 'EDGAR_PREVIOUSNAME_1', 'EDGAR_PREVIOUSNAME_2', 'EDGAR_PREVIOUSNAME_3', 'ENTITYTYPE', 'ENTITYTYPEOTHERDESC', 'YEAROFINC_TIMESPAN_CHOICE', 'YEAROFINC_VALUE_ENTERED'], '2026Q3_d/OFFERING.tsv': ['ACCESSIONNUMBER', 'INDUSTRYGROUPTYPE', 'INVESTMENTFUNDTYPE', 'IS40ACT', 'REVENUERANGE', 'AGGREGATENETASSETVALUERANGE', 'FEDERALEXEMPTIONS_ITEMS_LIST', 'ISAMENDMENT', 'PREVIOUSACCESSIONNUMBER', 'SALE_DATE', 'YETTOOCCUR', 'MORETHANONEYEAR', 'ISEQUITYTYPE', 'ISDEBTTYPE', 'ISOPTIONTOACQUIRETYPE', 'ISSECURITYTOBEACQUIREDTYPE', 'ISPOOLEDINVESTMENTFUNDTYPE', 'ISTENANTINCOMMONTYPE', 'ISMINERALPROPERTYTYPE', 'ISOTHERTYPE', 'DESCRIPTIONOFOTHERTYPE', 'ISBUSINESSCOMBINATIONTRANS', 'BUSCOMBCLARIFICATIONOFRESP', 'MINIMUMINVESTMENTACCEPTED', 'OVER100RECIPIENTFLAG', 'TOTALOFFERINGAMOUNT', 'TOTALAMOUNTSOLD', 'TOTALREMAINING', 'SALESAMTCLARIFICATIONOFRESP', 'HASNONACCREDITEDINVESTORS', 'NUMBERNONACCREDITEDINVESTORS', 'TOTALNUMBERALREADYINVESTED', 'SALESCOMM_DOLLARAMOUNT', 'SALESCOMM_ISESTIMATE', 'FINDERSFEE_DOLLARAMOUNT', 'FINDERSFEE_ISESTIMATE', 'FINDERFEECLARIFICATIONOFRESP', 'GROSSPROCEEDSUSED_DOLLARAMOUNT', 'GROSSPROCEEDSUSED_ISESTIMATE', 'GROSSPROCEEDSUSED_CLAROFRESP', 'AUTHORIZEDREPRESENTATIVE'], '2026Q3_d/RECIPIENTS.tsv': ['ACCESSIONNUMBER', 'RECIPIENT_SEQ_KEY', 'RECIPIENTNAME', 'RECIPIENTCRDNUMBER', 'ASSOCIATEDBDNAME', 'ASSOCIATEDBDCRDNUMBER', 'STREET1', 'STREET2', 'CITY', 'STATEORCOUNTRY', 'STATEORCOUNTRYDESCRIPTION', 'ZIPCODE', 'STATES_OR_VALUE_LIST', 'DESCRIPTIONS_LIST', 'FOREIGNSOLICITATION']}
PREFIX='2026Q3_d/'
ORDER=[PREFIX+n+'.tsv' for n in ['FORMDSUBMISSION','ISSUERS','OFFERING','RELATEDPERSONS','RECIPIENTS','SIGNATURES']]
MEMBERS=set(ORDER)|{PREFIX+'FormD_metadata.json',PREFIX+'FormD_readme.html'}

def inventory(z):
    info=z.infolist()
    if len(info)!=len(MEMBERS) or {i.filename for i in info}!=MEMBERS:raise ValueError('ZIP inventory')
    if sum(i.file_size for i in info)>100_000_000 or any(i.file_size>30_000_000 or i.flag_bits&1 for i in info):raise ValueError('ZIP bounds')

def rows(z,name):
    csv.field_size_limit(2_000_000)
    with z.open(name) as f:
        r=csv.reader(io.TextIOWrapper(f,encoding='utf-8-sig',newline=''),delimiter='\t',strict=True)
        if next(r)!=SCHEMAS[name]:raise ValueError('table schema')
        for values in r:
            if len(values)!=len(SCHEMAS[name]):raise ValueError('row width')
            yield dict(zip(SCHEMAS[name],values)),values

def ingest(root,out):
    if out.exists() or out.resolve().is_relative_to(Path(__file__).resolve().parents[1]):raise ValueError('new private output outside checkout required')
    r=json.loads((root/'browser-receipt.json').read_text(),object_pairs_hook=unique_object)
    fields={'path','url','byte_count','sha256','local_verified_utc','retrieval_method','http_status','exact_download_utc'}
    if set(r)!=fields or r['path']!=ARCHIVE or r['url']!=URL or r['http_status'] is not None or r['exact_download_utc'] is not None or r['retrieval_method']!='PUBLIC_BROWSER_LINK_DOWNLOAD_NO_PRIVATE_CONTACT':raise ValueError('receipt schema')
    seen=dt.datetime.fromisoformat(r['local_verified_utc'])
    if seen.tzinfo is None or seen>dt.datetime.now(dt.timezone.utc):raise ValueError('verification clock')
    p=root/ARCHIVE
    if p.stat().st_size>10_000_000 or p.stat().st_size!=r['byte_count'] or digest(p)!=r['sha256']:raise ValueError('source integrity')
    with zipfile.ZipFile(p) as z:inventory(z)
    out.mkdir(parents=True,mode=0o700);(out/'INCOMPLETE').write_text('Incomplete. Do not use.\n')
    path=out/'offerings.sqlite';db=sqlite3.connect(path);path.chmod(0o600);db.execute('PRAGMA synchronous=FULL');db.execute('PRAGMA journal_mode=DELETE')
    counts={};sub={};dates=[];primary=collections.Counter();ciks=set();forms=collections.Counter();offering_accessions=set();indefinite=0;conflicts=0
    db.execute('CREATE TABLE formd_validation_gaps (accession TEXT,reason TEXT)')
    try:
        with zipfile.ZipFile(p) as z:
            for name in ORDER:
                label=name.removeprefix(PREFIX).removesuffix('.tsv');table='formd_'+label.lower();header=SCHEMAS[name]
                db.execute('CREATE TABLE '+table+' ('+','.join('"'+c+'" TEXT' for c in header)+')');sql='INSERT INTO '+table+' VALUES ('+','.join('?' for _ in header)+')';batch=[];count=0
                for d,v in rows(z,name):
                    acc=d['ACCESSIONNUMBER']
                    if not re.fullmatch(r'\d{10}-\d{2}-\d{6}',acc):raise ValueError('accession')
                    if label=='FORMDSUBMISSION':
                        day=dt.datetime.strptime(d['FILING_DATE'],'%d-%b-%Y').date();form=d['SUBMISSIONTYPE']
                        if acc in sub or form not in {'D','D/A'} or d['TESTORLIVE']!='LIVE':raise ValueError('submission identity')
                        if not dt.date(2026,7,1)<=day<=dt.date(2026,9,30) or day>seen.date():raise ValueError('filing date')
                        sub[acc]=form;dates.append(day.isoformat());forms[form]+=1
                    elif acc not in sub:raise ValueError('orphan accession')
                    if label=='ISSUERS':
                        if not re.fullmatch(r'\d{1,10}',d['CIK']) or int(d['CIK'])==0 or d['IS_PRIMARYISSUER_FLAG'] not in {'YES','NO'}:raise ValueError('issuer identity')
                        ciks.add(str(int(d['CIK'])).zfill(10));primary[acc]+=d['IS_PRIMARYISSUER_FLAG']=='YES'
                    if label=='OFFERING':
                        if acc in offering_accessions or d['ISAMENDMENT'] not in {'true','false'}:raise ValueError('offering identity')
                        offering_accessions.add(acc);indefinite+=d['TOTALOFFERINGAMOUNT']=='Indefinite'
                        if (d['ISAMENDMENT']=='true')!=(sub[acc]=='D/A'):
                            conflicts+=1;db.execute('INSERT INTO formd_validation_gaps VALUES (?,?)',(acc,'AMENDMENT_FORM_CONFLICT_NOT_RECONCILED'))
                    batch.append(v);count+=1
                    if len(batch)>=5000:db.executemany(sql,batch);batch=[]
                if batch:db.executemany(sql,batch)
                counts[table]=count;db.commit()
            for name in MEMBERS-set(ORDER):
                with z.open(name) as f:
                    while f.read(1024*1024):pass
        if set(primary)!=set(sub) or any(n!=1 for n in primary.values()) or offering_accessions!=set(sub):raise ValueError('missing primary issuer/offering')
        counts['formd_validation_gaps']=conflicts;db.commit();db.close();db=sqlite3.connect('file:'+str(path.resolve())+'?mode=ro',uri=True)
        if db.execute('PRAGMA quick_check').fetchone()!=('ok',):raise ValueError('database integrity')
        for table,n in counts.items():
            if db.execute('SELECT COUNT(*) FROM '+table).fetchone()[0]!=n:raise ValueError('persisted counts')
        if not dates:raise ValueError('empty submissions')
        s={'version':1,'status':'HISTORICAL_FORM_D_NOTICES_NOT_INVESTMENT_SIGNALS','completed_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'source':r,'table_rows':counts,'submissions':len(sub),'issuer_ciks_in_batch':len(ciks),'filing_date_min':min(dates),'filing_date_max':max(dates),'submission_types':dict(sorted(forms.items())),'indefinite_total_offering_amount_rows':indefinite,'amendment_form_conflicts':conflicts,'accession_joins_verified':True,'one_primary_issuer_per_submission_verified':True,'simulation_enabled':False,'orders_created':0,'limitations':['Q3 2026 as-filed Form D notices of exempt offerings, not all companies, completed financing rounds, SEC approval or registered public offerings.','D/A amendments, prior-accession references, first-sale context, amounts sold/remaining and Indefinite offering values are preserved as source text; no summation or automatic amendment consolidation.','Issuer CIKs include private issuers and pooled investment vehicles, not a current listed-company universe; count is separate from the financial/insider issuer baseline.','Business-combination checkboxes are not proof of an acquisition, merger or completed transaction.','Related-person identities, addresses, recipient details and signatures remain private. Public output contains coverage aggregates only.','Prepared data may omit source metadata or contain extraction/filing errors; original filings remain authoritative.','Exact HTTP status/download clock unavailable; local verification time is not first-public evidence. No historical decisions or orders are generated.']}
        (out/'summary.json').write_text(json.dumps(s,indent=2)+'\n');db.close();(out/'INCOMPLETE').unlink();return s
    except Exception:
        db.close();(out/'INCOMPLETE').write_text('Validation failed. Do not publish.\n');raise

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();print(json.dumps(ingest(a.root,a.out),indent=2))
