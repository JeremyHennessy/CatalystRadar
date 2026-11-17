"""Offline financial history baseline; retains as-filed contexts, never generates trades."""
import argparse,datetime as dt,json,re,sqlite3,zipfile
from pathlib import Path
from private_prices import unique_object
from sec_prepared_data import digest,inventory,tab_rows,finite_number,SCHEMAS
ARCHIVE='2026q2.zip'
URL='https://www.sec.gov/files/dera/data/financial-statement-data-sets/'+ARCHIVE
ORDER=['sub.txt','tag.txt','pre.txt','num.txt']

def ingest(root,out):
    if out.exists() or out.resolve().is_relative_to(Path(__file__).resolve().parents[1]):raise ValueError('new private output outside checkout required')
    r=json.loads((root/'browser-receipt.json').read_text(),object_pairs_hook=unique_object)
    fields={'path','url','byte_count','sha256','local_verified_utc','retrieval_method','http_status','exact_download_utc'}
    if set(r)!=fields or r['path']!=ARCHIVE or r['url']!=URL or r['http_status'] is not None or r['exact_download_utc'] is not None or r['retrieval_method']!='PUBLIC_BROWSER_LINK_DOWNLOAD_NO_PRIVATE_CONTACT':raise ValueError('receipt schema')
    seen=dt.datetime.fromisoformat(r['local_verified_utc'])
    if seen.tzinfo is None or seen>dt.datetime.now(dt.timezone.utc):raise ValueError('verification clock')
    p=root/ARCHIVE
    if p.stat().st_size>100_000_000 or p.stat().st_size!=r['byte_count'] or digest(p)!=r['sha256']:raise ValueError('source integrity')
    with zipfile.ZipFile(p) as z:inventory(z,'financial')
    out.mkdir(parents=True,mode=0o700);(out/'INCOMPLETE').write_text('Unverified history. Do not use.\n')
    path=out/'financial.sqlite';db=sqlite3.connect(path);path.chmod(0o600);db.execute('PRAGMA synchronous=FULL');db.execute('PRAGMA journal_mode=DELETE')
    db.execute('CREATE TABLE financial_validation_gaps (source_table TEXT,row_number INTEGER,accession TEXT,tag TEXT,version TEXT,reason TEXT)')
    counts={};accs=set();ciks=set();dates=[];tags=set();missing_keys=set();gaps=0;empty=0
    try:
        with zipfile.ZipFile(p) as z:
            for name in ORDER:
                table='financial_'+name[:-4];header=SCHEMAS[name];it=tab_rows(z,name);next(it)
                db.execute('CREATE TABLE '+table+' ('+','.join('"'+c+'" TEXT' for c in header)+')');sql='INSERT INTO '+table+' VALUES ('+','.join('?' for c in header)+')';count=0;batch=[]
                for values in it:
                    d=dict(zip(header,values));acc=d.get('adsh')
                    if acc is not None and not re.fullmatch(r'\d{10}-\d{2}-\d{6}',acc):raise ValueError('accession')
                    if name=='sub.txt':
                        day=dt.datetime.strptime(d['filed'],'%Y%m%d').date();cik=d['cik']
                        if acc in accs or not re.fullmatch(r'\d{1,10}',cik) or int(cik)==0:raise ValueError('submission identity')
                        if not dt.date(2026,4,1)<=day<=dt.date(2026,6,30) or day>seen.date():raise ValueError('filing quarter')
                        accs.add(acc);ciks.add(str(int(cik)).zfill(10));dates.append(day.isoformat())
                    elif acc is not None and acc not in accs:raise ValueError('orphan accession')
                    if name=='tag.txt':
                        key=(d['tag'],d['version'])
                        if key in tags:raise ValueError('duplicate taxonomy identity')
                        tags.add(key)
                    if name in {'pre.txt','num.txt'} and (d['tag'],d['version']) not in tags:
                        missing_keys.add((d['tag'],d['version']));gaps+=1
                        db.execute('INSERT INTO financial_validation_gaps VALUES (?,?,?,?,?,?)',(name,count+1,acc,d['tag'],d['version'],'MISSING_TAG_DEFINITION_NOT_QUALIFIED'))
                    if name=='num.txt':finite_number(d['value']);empty+=d['value']==''
                    batch.append(values);count+=1
                    if len(batch)>=5000:db.executemany(sql,batch);batch=[]
                if batch:db.executemany(sql,batch)
                counts[table]=count;db.commit()
            with z.open('readme.htm') as f:
                while f.read(1024*1024):pass
        counts['financial_validation_gaps']=gaps;db.commit();db.close();db=sqlite3.connect('file:'+str(path.resolve())+'?mode=ro',uri=True)
        if db.execute('PRAGMA quick_check').fetchone()!=('ok',):raise ValueError('database integrity')
        for table,n in counts.items():
            if db.execute('SELECT COUNT(*) FROM '+table).fetchone()[0]!=n:raise ValueError('persisted rows')
        if not dates:raise ValueError('empty submissions')
        s={'version':1,'status':'HISTORICAL_FINANCIAL_Q2_NOT_COMPARABLE_FACTS','completed_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'source':r,'table_rows':counts,'issuer_ciks':len(ciks),'submissions':len(accs),'filing_date_min':min(dates),'filing_date_max':max(dates),'numeric_empty_values':empty,'accession_joins_verified':True,'taxonomy_joins_complete':gaps==0,'rows_missing_tag_definitions':gaps,'missing_tag_definition_keys':len(missing_keys),'simulation_enabled':False,'orders_created':0,'limitations':['Q2 2026 filing-date batch, not necessarily fiscal Q2 facts or all historical filings. Issuer count is separate from other batches and not added without deduplication.','Values retain accession, taxonomy version, period, duration in quarters, units, segments, co-registrants, footnotes and presentation context. Repeated periods and amendments are not silently consolidated.','Numeric rows are not unique comparable facts. No automatic quarter-over-quarter growth, financial totals, signals or recommendations are inferred.','Missing taxonomy definitions, if present, remain explicitly flagged and unqualified, never dropped or invented.','All four source tables are retained privately. Only aggregate coverage is public; no source values or private addresses are published.','Exact browser status/download clock unavailable; local verification time is not first-public or prospective decision evidence. No orders, historical decisions or simulated fills.']}
        (out/'summary.json').write_text(json.dumps(s,indent=2)+'\n');db.close();(out/'INCOMPLETE').unlink();return s
    except Exception:
        db.close();(out/'INCOMPLETE').write_text('Validation failed. Do not publish.\n');raise

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();print(json.dumps(ingest(a.root,a.out),indent=2))
