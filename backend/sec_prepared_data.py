"""Offline bounded ingestion of retained SEC prepared datasets; no network or trading."""
import argparse, collections, csv, datetime as dt, hashlib, io, json, re, sqlite3, zipfile
from decimal import Decimal, InvalidOperation
from pathlib import Path
from private_prices import unique_object as unique

SOURCES={
 '2026q3.zip':('financial','https://www.sec.gov/files/dera/data/financial-statement-data-sets/2026q3.zip'),
 '2026q3_form345.zip':('insider','https://www.sec.gov/files/datastandardsinnovation/data/insider-transactions-data-sets/2026q3_form345.zip'),
 'cnsfails202610b.zip':('ftd','https://www.sec.gov/files/data/fails-deliver-data/cnsfails202610b.zip')}
MEMBERS={
 'financial':{'sub.txt','pre.txt','num.txt','tag.txt','readme.htm'},
 'insider':{'DERIV_HOLDING.tsv','DERIV_TRANS.tsv','FOOTNOTES.tsv','NONDERIV_HOLDING.tsv','NONDERIV_TRANS.tsv','OWNER_SIGNATURE.tsv','REPORTINGOWNER.tsv','SUBMISSION.tsv','FORM_345_metadata.json','FORM_345_readme.htm'},
 'ftd':{'cnsfails202610b.txt'}}
SCHEMAS={'sub.txt': ['adsh', 'cik', 'name', 'sic', 'countryba', 'stprba', 'cityba', 'zipba', 'bas1', 'bas2', 'baph', 'countryma', 'stprma', 'cityma', 'zipma', 'mas1', 'mas2', 'countryinc', 'stprinc', 'ein', 'former', 'changed', 'afs', 'wksi', 'fye', 'form', 'period', 'fy', 'fp', 'filed', 'accepted', 'prevrpt', 'detail', 'instance', 'nciks', 'aciks'], 'pre.txt': ['adsh', 'report', 'line', 'stmt', 'inpth', 'rfile', 'tag', 'version', 'plabel', 'negating'], 'num.txt': ['adsh', 'tag', 'version', 'ddate', 'qtrs', 'uom', 'segments', 'coreg', 'value', 'footnote'], 'tag.txt': ['tag', 'version', 'custom', 'abstract', 'datatype', 'iord', 'crdr', 'tlabel', 'doc'], 'DERIV_HOLDING.tsv': ['ACCESSION_NUMBER', 'DERIV_HOLDING_SK', 'SECURITY_TITLE', 'SECURITY_TITLE_FN', 'CONV_EXERCISE_PRICE', 'CONV_EXERCISE_PRICE_FN', 'TRANS_FORM_TYPE', 'TRANS_FORM_TYPE_FN', 'EXERCISE_DATE', 'EXERCISE_DATE_FN', 'EXPIRATION_DATE', 'EXPIRATION_DATE_FN', 'UNDLYNG_SEC_TITLE', 'UNDLYNG_SEC_TITLE_FN', 'UNDLYNG_SEC_SHARES', 'UNDLYNG_SEC_SHARES_FN', 'UNDLYNG_SEC_VALUE', 'UNDLYNG_SEC_VALUE_FN', 'SHRS_OWND_FOLWNG_TRANS', 'SHRS_OWND_FOLWNG_TRANS_FN', 'VALU_OWND_FOLWNG_TRANS', 'VALU_OWND_FOLWNG_TRANS_FN', 'DIRECT_INDIRECT_OWNERSHIP', 'DIRECT_INDIRECT_OWNERSHIP_FN', 'NATURE_OF_OWNERSHIP', 'NATURE_OF_OWNERSHIP_FN'], 'DERIV_TRANS.tsv': ['ACCESSION_NUMBER', 'DERIV_TRANS_SK', 'SECURITY_TITLE', 'SECURITY_TITLE_FN', 'CONV_EXERCISE_PRICE', 'CONV_EXERCISE_PRICE_FN', 'TRANS_DATE', 'TRANS_DATE_FN', 'DEEMED_EXECUTION_DATE', 'DEEMED_EXECUTION_DATE_FN', 'TRANS_FORM_TYPE', 'TRANS_CODE', 'EQUITY_SWAP_INVOLVED', 'EQUITY_SWAP_TRANS_CD_FN', 'TRANS_TIMELINESS', 'TRANS_TIMELINESS_FN', 'TRANS_SHARES', 'TRANS_SHARES_FN', 'TRANS_TOTAL_VALUE', 'TRANS_TOTAL_VALUE_FN', 'TRANS_PRICEPERSHARE', 'TRANS_PRICEPERSHARE_FN', 'TRANS_ACQUIRED_DISP_CD', 'TRANS_ACQUIRED_DISP_CD_FN', 'EXCERCISE_DATE', 'EXCERCISE_DATE_FN', 'EXPIRATION_DATE', 'EXPIRATION_DATE_FN', 'UNDLYNG_SEC_TITLE', 'UNDLYNG_SEC_TITLE_FN', 'UNDLYNG_SEC_SHARES', 'UNDLYNG_SEC_SHARES_FN', 'UNDLYNG_SEC_VALUE', 'UNDLYNG_SEC_VALUE_FN', 'SHRS_OWND_FOLWNG_TRANS', 'SHRS_OWND_FOLWNG_TRANS_FN', 'VALU_OWND_FOLWNG_TRANS', 'VALU_OWND_FOLWNG_TRANS_FN', 'DIRECT_INDIRECT_OWNERSHIP', 'DIRECT_INDIRECT_OWNERSHIP_FN', 'NATURE_OF_OWNERSHIP', 'NATURE_OF_OWNERSHIP_FN'], 'FOOTNOTES.tsv': ['ACCESSION_NUMBER', 'FOOTNOTE_ID', 'FOOTNOTE_TXT'], 'NONDERIV_HOLDING.tsv': ['ACCESSION_NUMBER', 'NONDERIV_HOLDING_SK', 'SECURITY_TITLE', 'SECURITY_TITLE_FN', 'TRANS_FORM_TYPE', 'TRANS_FORM_TYPE_FN', 'SHRS_OWND_FOLWNG_TRANS', 'SHRS_OWND_FOLWNG_TRANS_FN', 'VALU_OWND_FOLWNG_TRANS', 'VALU_OWND_FOLWNG_TRANS_FN', 'DIRECT_INDIRECT_OWNERSHIP', 'DIRECT_INDIRECT_OWNERSHIP_FN', 'NATURE_OF_OWNERSHIP', 'NATURE_OF_OWNERSHIP_FN'], 'NONDERIV_TRANS.tsv': ['ACCESSION_NUMBER', 'NONDERIV_TRANS_SK', 'SECURITY_TITLE', 'SECURITY_TITLE_FN', 'TRANS_DATE', 'TRANS_DATE_FN', 'DEEMED_EXECUTION_DATE', 'DEEMED_EXECUTION_DATE_FN', 'TRANS_FORM_TYPE', 'TRANS_CODE', 'EQUITY_SWAP_INVOLVED', 'EQUITY_SWAP_TRANS_CD_FN', 'TRANS_TIMELINESS', 'TRANS_TIMELINESS_FN', 'TRANS_SHARES', 'TRANS_SHARES_FN', 'TRANS_PRICEPERSHARE', 'TRANS_PRICEPERSHARE_FN', 'TRANS_ACQUIRED_DISP_CD', 'TRANS_ACQUIRED_DISP_CD_FN', 'SHRS_OWND_FOLWNG_TRANS', 'SHRS_OWND_FOLWNG_TRANS_FN', 'VALU_OWND_FOLWNG_TRANS', 'VALU_OWND_FOLWNG_TRANS_FN', 'DIRECT_INDIRECT_OWNERSHIP', 'DIRECT_INDIRECT_OWNERSHIP_FN', 'NATURE_OF_OWNERSHIP', 'NATURE_OF_OWNERSHIP_FN'], 'OWNER_SIGNATURE.tsv': ['ACCESSION_NUMBER', 'OWNERSIGNATURENAME', 'OWNERSIGNATUREDATE'], 'REPORTINGOWNER.tsv': ['ACCESSION_NUMBER', 'RPTOWNERCIK', 'RPTOWNERNAME', 'RPTOWNER_RELATIONSHIP', 'RPTOWNER_TITLE', 'RPTOWNER_TXT', 'RPTOWNER_STREET1', 'RPTOWNER_STREET2', 'RPTOWNER_CITY', 'RPTOWNER_STATE', 'RPTOWNER_ZIPCODE', 'RPTOWNER_STATE_DESC', 'FILE_NUMBER'], 'SUBMISSION.tsv': ['ACCESSION_NUMBER', 'FILING_DATE', 'PERIOD_OF_REPORT', 'DATE_OF_ORIG_SUB', 'NO_SECURITIES_OWNED', 'NOT_SUBJECT_SEC16', 'FORM3_HOLDINGS_REPORTED', 'FORM4_TRANS_REPORTED', 'DOCUMENT_TYPE', 'ISSUERCIK', 'ISSUERNAME', 'ISSUERTRADINGSYMBOL', 'REMARKS', 'AFF10B5ONE']}
ACC=re.compile(r'\d{10}-\d{2}-\d{6}')

def digest(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
 return h.hexdigest()

def inventory(z,kind):
 infos=z.infolist()
 if len(infos)!=len(MEMBERS[kind]) or {x.filename for x in infos}!=MEMBERS[kind]:raise ValueError('unexpected or duplicate ZIP members')
 if sum(x.file_size for x in infos)>1_200_000_000 or any(x.file_size>1_000_000_000 or x.flag_bits&1 for x in infos):raise ValueError('ZIP bounds/encryption')
 return infos

def tab_rows(z,name):
 csv.field_size_limit(2_000_000)
 with z.open(name) as f:
  reader=csv.reader(io.TextIOWrapper(f,encoding='utf-8-sig',newline=''),delimiter='\t',strict=True)
  header=next(reader)
  if name not in SCHEMAS or header!=SCHEMAS[name]:raise ValueError('table header')
  yield header
  for row in reader:
   if len(row)!=len(header):raise ValueError('table row width')
   yield row

def finite_number(value):
 if value=='':return
 if len(value)>100:raise ValueError('numeric bound')
 try:
  if not Decimal(value).is_finite():raise ValueError('nonfinite number')
 except InvalidOperation:raise ValueError('invalid number')

def ftd_rows(z):
 with z.open('cnsfails202610b.txt') as f:
  lines=io.TextIOWrapper(f,encoding='ascii',newline='')
  if lines.readline().rstrip('\r\n')!='SETTLEMENT DATE|CUSIP|SYMBOL|QUANTITY (FAILS)|DESCRIPTION|PRICE':raise ValueError('FTD header')
  seen=set();rows=[];total=0;trailer=[]
  for line in lines:
   line=line.rstrip('\r\n')
   if line.startswith('Trailer '):trailer.append(line);continue
   if trailer:raise ValueError('FTD data after trailer')
   r=line.split('|')
   if len(r)!=6:raise ValueError('FTD row width')
   date,cusip,symbol,qty,description,price=r
   day=dt.datetime.strptime(date,'%Y%m%d').date()
   # Filename second half includes October15 as actually provided; never silently discard it.
   if not dt.date(2026,10,15)<=day<=dt.date(2026,10,31):raise ValueError('FTD period')
   if not re.fullmatch('[A-Z0-9*@#]{9}',cusip) or len(symbol)>32 or any(ord(c)<32 for c in symbol) or not re.fullmatch('[0-9]{1,30}',qty):raise ValueError('FTD identity/quantity')
   if price!='.':finite_number(price)
   key=(date,cusip)
   if key in seen:raise ValueError('duplicate FTD identity')
   seen.add(key);total+=int(qty);rows.append(r)
  if trailer!=[f'Trailer record count {len(rows)}',f'Trailer total quantity of shares {total}']:raise ValueError('FTD trailer mismatch')
  if not rows:raise ValueError('empty FTD')
  return rows,total

def public_issuers(db):
    """Allowlisted issuer-level coverage only; no ownership-person fields or financial values."""
    issuers={}
    for kind,query in [('financial','SELECT cik,name FROM financial_sub'),('insider','SELECT ISSUERCIK,ISSUERNAME,ISSUERTRADINGSYMBOL FROM insider_submission')]:
        for row in db.execute(query):
            cik=str(int(row[0])).zfill(10)
            r=issuers.setdefault(cik,{'cik':cik,'names':set(),'reported_tickers':set(),'financial_submissions':0,'insider_submissions':0})
            r['names'].add(row[1]);r[kind+'_submissions']+=1
            if kind=='insider' and row[2]:r['reported_tickers'].add(row[2])
    return [dict(r,names=sorted(r['names']),reported_tickers=sorted(r['reported_tickers'])) for cik,r in sorted(issuers.items())]

def write_public_outputs(out,summary,db):
    raw=(json.dumps(public_issuers(db),separators=(',',':'))+'\n').encode()
    summary['issuer_metadata']={'sha256':hashlib.sha256(raw).hexdigest(),'byte_count':len(raw)}
    (out/'issuers.json').write_bytes(raw)
    (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')

def ingest(root,out):
 if out.resolve().is_relative_to(Path(__file__).resolve().parents[1]):raise ValueError('private output must be outside this checkout')
 if out.exists():raise ValueError('new private output directory required')
 records=json.loads((root/'browser-receipts.json').read_text(),object_pairs_hook=unique)
 fields={'path','url','byte_count','sha256','local_verified_utc','retrieval_method','http_status','exact_download_utc'}
 if len(records)!=len(SOURCES) or {r['path'] for r in records}!=set(SOURCES):raise ValueError('receipt source set')
 now=dt.datetime.now(dt.timezone.utc)
 for r in records:
  if set(r)!=fields or r['url']!=SOURCES[r['path']][1] or r['http_status'] is not None or r['exact_download_utc'] is not None or r['retrieval_method']!='PUBLIC_BROWSER_LINK_DOWNLOAD_NO_PRIVATE_CONTACT':raise ValueError('receipt fields')
  time=dt.datetime.fromisoformat(r['local_verified_utc'])
  if time.tzinfo is None or time>now:raise ValueError('receipt clock')
  p=root/r['path']
  if p.stat().st_size>100_000_000 or p.stat().st_size!=r['byte_count'] or digest(p)!=r['sha256']:raise ValueError('archive integrity')
  with zipfile.ZipFile(p) as z:inventory(z,SOURCES[r['path']][0])
 out.mkdir(parents=True,mode=0o700)
 (out/'INCOMPLETE').write_text('Build in progress; not validated for use or publication.\n')
 db=sqlite3.connect(out/'prepared.sqlite');db.execute('PRAGMA journal_mode=DELETE');db.execute('PRAGMA synchronous=FULL')
 tables={};issuer_summary={};financial_acc=set();insider_acc=set();forms=collections.Counter();dates={};num_counts=collections.Counter();num_missing=0
 try:
  for filename,(kind,url) in SOURCES.items():
   with zipfile.ZipFile(root/filename) as z:
    inventory(z,kind)
    if kind=='ftd':
     rows,total=ftd_rows(z);db.execute('CREATE TABLE ftd (settlement_date TEXT,cusip TEXT,symbol TEXT,quantity TEXT,description TEXT,previous_day_price TEXT)');db.executemany('INSERT INTO ftd VALUES (?,?,?,?,?,?)',rows);tables['ftd']=len(rows)
     ftd={'rows':len(rows),'distinct_cusips':len({r[1] for r in rows}),'distinct_nonempty_symbols':len({r[2] for r in rows if r[2]}),'missing_symbol_rows':sum(not r[2] for r in rows),'symbols_exceeding_documented_10_chars':sum(len(r[2])>10 for r in rows),'settlement_dates':dict(sorted(collections.Counter(r[0] for r in rows).items())),'missing_previous_day_prices':sum(r[5]=='.' for r in rows),'trailer_record_count_verified':True,'trailer_quantity_checksum_verified':True}
     db.commit()
     continue
    # Parent submission tables must be read before dependent numeric/ownership tables.
    names=sorted(n for n in MEMBERS[kind] if n.endswith(('.txt','.tsv')))
    first='sub.txt' if kind=='financial' else 'SUBMISSION.tsv';names.remove(first);names.insert(0,first)
    for name in names:
     table=kind+'_'+name.split('.')[0].lower();it=tab_rows(z,name);header=next(it)
     db.execute('CREATE TABLE "'+table+'" ('+','.join('"'+c+'" TEXT' for c in header)+')')
     sql='INSERT INTO "'+table+'" VALUES ('+','.join('?' for _ in header)+')';batch=[];count=0
     for row in it:
      data=dict(zip(header,row));acc=data.get('adsh',data.get('ACCESSION_NUMBER'))
      if acc is not None and not ACC.fullmatch(acc):raise ValueError('accession syntax')
      if name==first:
       cik=data['cik'] if kind=='financial' else data['ISSUERCIK'];form=data['form'] if kind=='financial' else data['DOCUMENT_TYPE'];date=data['filed'] if kind=='financial' else data['FILING_DATE']
       if not re.fullmatch(r'\d{1,10}',cik) or int(cik)<1:raise ValueError('issuer CIK')
       accs=financial_acc if kind=='financial' else insider_acc
       if acc in accs:raise ValueError('duplicate submission')
       accs.add(acc);cik=cik.zfill(10);item=issuer_summary.setdefault(cik,{'cik':cik,'financial_submissions':0,'insider_submissions':0});item[kind+'_submissions']+=1;forms[kind+':'+form]+=1
       day=dt.datetime.strptime(date,'%Y%m%d' if kind=='financial' else '%d-%b-%Y').date()
       if not dt.date(2026,7,1)<=day<=dt.date(2026,9,30):raise ValueError('submission outside quarter')
       dates.setdefault(kind,set()).add(day.isoformat())
      elif acc is not None and acc not in (financial_acc if kind=='financial' else insider_acc):raise ValueError('orphan table accession')
      if name=='num.txt':
       finite_number(data['value']);num_missing+=data['value']=='';num_counts['rows']+=1
      batch.append(row);count+=1
      if len(batch)>=5000:db.executemany(sql,batch);batch=[]
     if batch:db.executemany(sql,batch)
     tables[table]=count;db.commit()
    # Reading all remaining documentation members to EOF verifies their ZIP CRC too.
    for name in MEMBERS[kind]-set(names):
     with z.open(name) as f:
      while f.read(1024*1024):pass
  db.commit();db.close()
  db=sqlite3.connect('file:'+str((out/'prepared.sqlite').resolve())+'?mode=ro',uri=True)
  if db.execute('PRAGMA quick_check').fetchone()!=('ok',):raise ValueError('persisted database integrity')
  for table,count in tables.items():
   if db.execute('SELECT COUNT(*) FROM '+table).fetchone()[0]!=count:raise ValueError('persisted row count mismatch')
  summary={'version':1,'status':'PREPARED_DATA_BASELINE_NOT_LIVE_SIGNALS','completed_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'sources':records,'table_rows':tables,'issuer_counts':{'financial':len({c for c,r in issuer_summary.items() if r['financial_submissions']}),'insider':len({c for c,r in issuer_summary.items() if r['insider_submissions']}),'union':len(issuer_summary)},'submission_form_counts':dict(sorted(forms.items())),'filing_date_ranges':{k:{'min':min(v),'max':max(v)} for k,v in dates.items()},'financial_numeric_missing_values':num_missing,'ftd':ftd,'simulation_enabled':False,'orders_created':0,'limitations':['Quarterly financial and insider baseline is not live coverage or all historical SEC records.','Values remain source text with units, periods, segments, footnotes and amendments; no growth/profitability or insider sentiment inferred.','FTD is lagged outstanding settlement balances, not daily new fails; do not sum across dates as a current outstanding quantity.','FTD does not prove short selling or abusive activity; its previous-day prices cannot satisfy execution gates.','Browser HTTP status and exact download timestamps were not exposed; local verification times are not first-public or source-observed clocks.','Raw ownership names/addresses/signatures and numeric tables remain private; public output is aggregate coverage only.']}
  write_public_outputs(out,summary,db)
  db.close();(out/'INCOMPLETE').unlink();return summary
 except Exception:
  db.close();(out/'INCOMPLETE').write_text('Ingestion failed. Do not publish outputs or treat database as complete.\n');raise

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();s=ingest(a.root,a.out);print(json.dumps({k:s[k] for k in ['table_rows','issuer_counts','ftd']}))
