"""Offline fixed CUSIP series of reported outstanding FTD balances, not flows."""
import argparse,datetime as dt,hashlib,json,re,sqlite3,zipfile
from pathlib import Path
from financial_pair_candidates import sha,write_private
from sec_prepared_data import ftd_rows
ZIP_SHA='d54748d8ecba8c56c3caf41e8d0cd9cc1886275dff7a9dbd9b1c4da87cf56178'
DB_SHA='360491837fa5a8fd45d9d7c3b6b06a19324954bc839e203f2ad6235e88b14cae'
FIELDS=['settlement_date','cusip','symbol','quantity','description','previous_day_price']
SOURCE='https://www.sec.gov/files/data/fails-deliver-data/cnsfails202610b.zip'
GUIDANCE='https://www.sec.gov/data/foiadocsfailsdatahtm'
def digest(data):return hashlib.sha256(data).hexdigest()
def canonical(row):return json.dumps(list(row),ensure_ascii=True,separators=(',',':')).encode()
def iso(date):return dt.datetime.strptime(date,'%Y%m%d').date().isoformat()
def project(rows,all_cusips=False):
 if type(all_cusips) is not bool:raise ValueError('selection mode')
 if not isinstance(rows,list) or not 1<=len(rows)<=100000:raise ValueError('row bounds')
 by={};dates=set();groups={}
 for n,r in enumerate(rows,1):
  if not isinstance(r,(list,tuple)) or len(r)!=6 or any(not isinstance(v,str) for v in r):raise ValueError('source schema')
  date,ci,symbol,qty,description,_=r
  if not re.fullmatch('[0-9]{8}',date) or not '2026-10-15'<=iso(date)<='2026-10-31' or not re.fullmatch('[A-Z0-9*@#]{9}',ci) or not re.fullmatch('[0-9]{1,30}',qty):raise ValueError('source date/identity/quantity')
  if len(symbol)>32 or len(description)>200 or any(ord(c)<32 or ord(c)>126 for c in symbol+description):raise ValueError('labels')
  key=(ci,date)
  if key in by:raise ValueError('duplicate CUSIP/date')
  by[key]=(r,n);dates.add(date);groups.setdefault(ci,[]).append(r)
 dates=sorted(dates)
 if len(dates)>16:raise ValueError('date count')
 chosen=sorted(groups) if all_cusips else sorted(groups)[:5];series=[]
 if len(chosen)>20000:raise ValueError('CUSIP count')
 for ci in chosen:
  observations=[]
  for date in (sorted(r[0] for r in groups[ci]) if all_cusips else dates):
   cell={'settlement_date_as_reported':iso(date),'status':'NO_SOURCE_ROW','outstanding_fail_shares_as_reported':None,'symbol_as_reported':None,'description_as_reported':None,'source_row':None}
   if (ci,date) in by:
    row,n=by[ci,date];cell.update(status='REPORTED_BALANCE',outstanding_fail_shares_as_reported=row[3],symbol_as_reported=row[2],description_as_reported=row[4],source_row={'sqlite_rowid':n,'archive_line_1based':n+1,'full_six_field_canonical_sha256':digest(canonical(row))})
   observations.append(cell)
  series.append({'cusip_as_reported':ci,'identity_scope':'SOURCE_CUSIP_ONLY_NOT_VERIFIED_ISSUER_OR_CURRENT_SECURITY','issuer_cik':None,'issuer_mapping_verified':False,'current_security_identity_verified':False,'observations':observations,'reported_observations':len(groups[ci]),'unreported_date_slots':len(dates)-len(groups[ci])})
 result={'version':1,'status':'HISTORICAL_OUTSTANDING_SETTLEMENT_BALANCES_NOT_TRADING_SIGNAL','selection':'First five lexicographically smallest source CUSIPs in the entire retained file; every source settlement date shown. Diagnostic selection after inspecting batch coverage, not a representative sample or performance ranking.',
 'counts':{'source_rows':len(rows),'source_cusips':len(groups),'source_settlement_dates':len(dates),'selected_cusips':len(chosen),'reported_selected_observations':sum(s['reported_observations'] for s in series),'unreported_selected_date_slots':sum(s['unreported_date_slots'] for s in series)},
 'settlement_dates_as_reported':[iso(d) for d in dates],'series':series,
 'measure':'Aggregate net shares failing delivery outstanding on the stated settlement date, not new daily fails.',
 'missing_convention':'NO_SOURCE_ROW retains a null numeric value rather than inventing an explicit source zero. SEC says zero net balances after September 16, 2008 produce no row. Absence is not a current-market or full-history claim.',
 'provenance':{'source_url':SOURCE,'guidance_url':GUIDANCE,'guidance_checked_date':'2026-11-18','source_zip_sha256':ZIP_SHA,'database_sha256':DB_SHA,'source_retrieved_utc':None,'first_public_utc':None,'historical_availability_verified':False},
 'limitations':['Do not sum balances across dates. No new-fail volume, age, carryover, resolution rate or common underlying participants are inferred.','Balances may involve long or short sales. This is not short interest, threshold-list status or evidence of abusive activity, manipulation or a squeeze.','CUSIP, symbol and description are source-reported identifiers/labels only; no issuer CIK, security-class continuity, corporate-action or current ticker mapping is established.','The selected descriptions include different instrument types. No independent common-stock classification is asserted.','Only this retained October2026 file is covered. Data accuracy, release timing and current balances are not guaranteed.','Previous-day prices are omitted; no dollar totals, returns, execution prices, participant identity or trade recommendations are computed.'],
 'training_ready':False,'execution_ready':False,'cross_date_balance_sum':None,'short_interest':None,'manipulation_assessed':False}

 if all_cusips:
  result['selection']='All source CUSIPs and reported rows in this one retained file. No ranking or issuer/security join.'
  result['observation_representation']='SPARSE_REPORTED_ROWS_USE_SHARED_DATE_AXIS_FOR_NO_SOURCE_ROW'
 return result

def audit(archive,database,all_cusips=False):
 archive=Path(archive);database=Path(database)
 if archive.stat().st_size>4000000 or sha(archive)!=ZIP_SHA or sha(database)!=DB_SHA:raise ValueError('source pins')
 with zipfile.ZipFile(archive) as z:
  if z.namelist()!=['cnsfails202610b.txt'] or z.infolist()[0].file_size>10000000:raise ValueError('archive inventory/bounds')
  rows,_trailer_integrity_total=ftd_rows(z) # Checksum only, never an economic measure or output.
 if len(rows)!=63157:raise ValueError('source census')
 conn=sqlite3.connect(database.resolve().as_uri()+'?mode=ro',uri=True)
 try:
  if conn.execute('pragma quick_check').fetchone()[0]!='ok' or [r[1] for r in conn.execute('pragma table_info(ftd)')]!=FIELDS:raise ValueError('database schema/integrity')
  stored=conn.execute('select rowid,* from ftd order by rowid limit 100001').fetchall()
  if len(stored)!=len(rows) or any(r[0]!=n or list(r[1:])!=source for n,(r,source) in enumerate(zip(stored,rows),1)):raise ValueError('source-to-database mismatch')
 finally:conn.close()
 if sha(archive)!=ZIP_SHA or sha(database)!=DB_SHA:raise ValueError('source changed')
 return project(rows,all_cusips)

def save(archive,database,out):
 out=Path(out).resolve()
 if out.exists() or not out.parent.is_dir() or out.is_relative_to(Path(__file__).resolve().parents[1]):raise ValueError('new private output required')
 out.mkdir(mode=0o700);write_private(out/'INCOMPLETE',{});result=audit(archive,database);write_private(out/'series.json',result);write_private(out/'COMPLETE.json',{'series_sha256':sha(out/'series.json')});(out/'INCOMPLETE').unlink();return result
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--archive',required=True);p.add_argument('--database',required=True);p.add_argument('--out',required=True);a=p.parse_args();save(a.archive,a.database,a.out)
