"""Offline October2026 SEC statement/notes ingestion. Context retained, no trading."""
import argparse,csv,datetime as dt,hashlib,io,json,re,sqlite3,zipfile
from pathlib import Path
from private_prices import unique_object
from sec_prepared_data import digest,finite_number
URL='https://www.sec.gov/files/dera/data/financial-statement-notes-data-sets/2026_10_notes.zip'
ARCHIVE='2026_10_notes.zip'
SCHEMAS={'sub.tsv': ['adsh', 'cik', 'name', 'sic', 'countryba', 'stprba', 'cityba', 'zipba', 'bas1', 'bas2', 'baph', 'countryma', 'stprma', 'cityma', 'zipma', 'mas1', 'mas2', 'countryinc', 'stprinc', 'ein', 'former', 'changed', 'afs', 'wksi', 'fye', 'form', 'period', 'fy', 'fp', 'filed', 'accepted', 'prevrpt', 'detail', 'instance', 'nciks', 'aciks', 'pubfloatusd', 'floatdate', 'floataxis', 'floatmems'], 'tag.tsv': ['tag', 'version', 'custom', 'abstract', 'datatype', 'iord', 'crdr', 'tlabel', 'doc'], 'dim.tsv': ['dimhash', 'segments', 'segt'], 'ren.tsv': ['adsh', 'report', 'rfile', 'menucat', 'shortname', 'longname', 'roleuri', 'parentroleuri', 'parentreport', 'ultparentrpt'], 'cal.tsv': ['adsh', 'grp', 'arc', 'negative', 'ptag', 'pversion', 'ctag', 'cversion'], 'pre.tsv': ['adsh', 'report', 'line', 'stmt', 'inpth', 'tag', 'version', 'prole', 'plabel', 'negating'], 'num.tsv': ['adsh', 'tag', 'version', 'ddate', 'qtrs', 'uom', 'dimh', 'iprx', 'value', 'footnote', 'footlen', 'dimn', 'coreg', 'durp', 'datp', 'dcml'], 'txt.tsv': ['adsh', 'tag', 'version', 'ddate', 'qtrs', 'iprx', 'lang', 'dcml', 'durp', 'datp', 'dimh', 'dimn', 'coreg', 'escaped', 'srclen', 'txtlen', 'footnote', 'footlen', 'context', 'value']}
ORDER=['sub.tsv','tag.tsv','dim.tsv','ren.tsv','cal.tsv','pre.tsv','num.tsv','txt.tsv']
MEMBERS=set(ORDER)|{'readme.htm','notes-metadata.json'}

def inventory(z):
 rows=z.infolist()
 if len(rows)!=len(MEMBERS) or {r.filename for r in rows}!=MEMBERS:raise ValueError('ZIP member set')
 if sum(r.file_size for r in rows)>1_200_000_000 or any(r.file_size>600_000_000 or r.flag_bits&1 for r in rows):raise ValueError('ZIP bounds')

def rows(z,name):
 csv.field_size_limit(20_000_000)
 with z.open(name) as source:
  r=csv.reader(io.TextIOWrapper(source,encoding='utf-8-sig',newline=''),delimiter='\t',strict=True)
  header=next(r)
  if header!=SCHEMAS[name]:raise ValueError('table schema')
  for values in r:
   if len(values)!=len(header):raise ValueError('row width')
   yield dict(zip(header,values)),values

def write_outputs(out,summary,db):
 items={}
 for cik,name in db.execute('SELECT cik,name FROM notes_sub'):
  cik=str(int(cik)).zfill(10);r=items.setdefault(cik,{'cik':cik,'names':set(),'notes_submissions':0});r['names'].add(name);r['notes_submissions']+=1
 public=[dict(r,names=sorted(r['names'])) for _,r in sorted(items.items())]
 raw=(json.dumps(public,separators=(',',':'))+'\n').encode();summary['issuer_metadata']={'sha256':hashlib.sha256(raw).hexdigest(),'byte_count':len(raw)}
 (out/'issuers.json').write_bytes(raw);(out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')

def ingest(root,out):
 if out.resolve().is_relative_to(Path(__file__).resolve().parents[1]) or out.exists():raise ValueError('new private output outside checkout required')
 r=json.loads((root/'browser-receipt.json').read_text(),object_pairs_hook=unique_object)
 fields={'path','url','byte_count','sha256','local_verified_utc','retrieval_method','http_status','exact_download_utc'}
 if set(r)!=fields or r['path']!=ARCHIVE or r['url']!=URL or r['http_status'] is not None or r['exact_download_utc'] is not None or r['retrieval_method']!='PUBLIC_BROWSER_LINK_DOWNLOAD_NO_PRIVATE_CONTACT':raise ValueError('receipt schema')
 seen_at=dt.datetime.fromisoformat(r['local_verified_utc'])
 if seen_at.tzinfo is None or seen_at>dt.datetime.now(dt.timezone.utc):raise ValueError('verification clock')
 p=root/ARCHIVE
 if p.stat().st_size>100_000_000 or p.stat().st_size!=r['byte_count'] or digest(p)!=r['sha256']:raise ValueError('source integrity')
 with zipfile.ZipFile(p) as z:inventory(z)
 out.mkdir(parents=True,mode=0o700);(out/'INCOMPLETE').write_text('Unverified/in-progress data. Do not publish.\n')
 db=sqlite3.connect(out/'notes.sqlite');db.execute('PRAGMA journal_mode=DELETE');db.execute('PRAGMA synchronous=FULL')
 db.execute('CREATE TABLE notes_validation_gaps (source_table TEXT,row_number INTEGER,accession TEXT,tag TEXT,version TEXT,reason TEXT)')
 counts={};accessions=set();tags=set();dimensions=set();ciks=set();dates=set();missing_values=0;missing_tags=set();gap_rows=0
 try:
  with zipfile.ZipFile(p) as z:
   for name in ORDER:
    table='notes_'+name[:-4];header=SCHEMAS[name]
    db.execute('CREATE TABLE '+table+' ('+','.join('"'+c+'" TEXT' for c in header)+')');sql='INSERT INTO '+table+' VALUES ('+','.join('?' for _ in header)+')';batch=[];count=0
    for data,values in rows(z,name):
     acc=data.get('adsh')
     if acc is not None and not re.fullmatch(r'\d{10}-\d{2}-\d{6}',acc):raise ValueError('accession')
     if name=='sub.tsv':
      if acc in accessions:raise ValueError('duplicate submission')
      cik=data['cik'];day=dt.datetime.strptime(data['filed'],'%Y%m%d').date()
      if not re.fullmatch(r'\d{1,10}',cik) or int(cik)<1 or not dt.date(2026,10,1)<=day<=dt.date(2026,10,31):raise ValueError('submission identity/period')
      accessions.add(acc);ciks.add(str(int(cik)).zfill(10));dates.add(day.isoformat())
     elif acc is not None and acc not in accessions:raise ValueError('orphan submission reference')
     if name=='tag.tsv':
      key=(data['tag'],data['version'])
      if key in tags:raise ValueError('duplicate tag key')
      tags.add(key)
     if name=='dim.tsv':
      if data['dimhash'] in dimensions:raise ValueError('duplicate dimension key')
      dimensions.add(data['dimhash'])
     if name in {'num.tsv','txt.tsv','pre.tsv'} and (data['tag'],data['version']) not in tags:
      if name!='num.tsv':raise ValueError('orphan taxonomy reference')
      missing_tags.add((data['tag'],data['version']));gap_rows+=1
      db.execute('INSERT INTO notes_validation_gaps VALUES (?,?,?,?,?,?)',(name,count+1,acc,data['tag'],data['version'],'MISSING_SOURCE_TAG_DEFINITION_NOT_QUALIFIED'))
     if name in {'num.tsv','txt.tsv'} and data['dimh'] not in dimensions:raise ValueError('orphan dimension reference')
     if name=='cal.tsv' and any((data[a],data[b]) not in tags for a,b in [('ptag','pversion'),('ctag','cversion')]):raise ValueError('orphan calculation tag')
     if name=='num.tsv':finite_number(data['value']);missing_values+=data['value']==''
     batch.append(values);count+=1
     if len(batch)>=5000:db.executemany(sql,batch);batch=[]
    if batch:db.executemany(sql,batch)
    counts[table]=count;db.commit()
   for name in MEMBERS-set(ORDER):
    with z.open(name) as f:
     while f.read(1024*1024):pass
  counts['notes_validation_gaps']=gap_rows
  db.commit();db.close();db=sqlite3.connect('file:'+str((out/'notes.sqlite').resolve())+'?mode=ro',uri=True)
  if db.execute('PRAGMA quick_check').fetchone()!=('ok',):raise ValueError('database integrity')
  for table,n in counts.items():
   if db.execute('SELECT COUNT(*) FROM '+table).fetchone()[0]!=n:raise ValueError('persisted count mismatch')
  if not dates:raise ValueError('empty submissions')
  summary={'version':1,'status':'STATEMENTS_AND_NOTES_BASELINE_NOT_LIVE_SIGNALS','completed_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'source':r,'table_rows':counts,'issuer_ciks':len(ciks),'submissions':len(accessions),'filing_date_min':min(dates),'filing_date_max':max(dates),'numeric_missing_values':missing_values,'submission_and_dimension_joins_verified':True,'taxonomy_joins_complete':gap_rows==0,'numeric_rows_missing_tag_definitions':gap_rows,'missing_tag_definition_keys':len(missing_tags),'simulation_enabled':False,'orders_created':0,'limitations':['October2026 as-filed prepared statements and notes, not all companies/history or a live feed.','Numeric/text rows retain taxonomy, period, unit/language, dimension hash, co-registrant, precision, duration and footnote context; they are not unique comparable facts.','Dimension, calculation and presentation tables are retained; no silent company-wide aggregation.','Text is retained privately as untrusted source data, not rendered HTML or interpreted instructions.','Missing source taxonomy definitions are retained and explicitly flagged, never invented, dropped or qualified.','No acquisition, legal allegation, outcome, financial recommendation or trading eligibility is inferred from note text.','Exact browser download time and HTTP status unavailable; local verification time is not first-public evidence.']}
  write_outputs(out,summary,db);db.close();(out/'INCOMPLETE').unlink();return summary
 except Exception:
  db.close();(out/'INCOMPLETE').write_text('Build failed validation. Do not publish or use as complete.\n');raise

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();s=ingest(a.root,a.out);print(json.dumps({k:s[k] for k in ['table_rows','issuer_ciks','submissions','filing_date_min','filing_date_max']}))
