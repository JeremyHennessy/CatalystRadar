"""Bounded offline Q2 insider retention. Source records are not trades or signals."""
import argparse, collections, datetime as dt, hashlib, json, re, sqlite3, zipfile
from pathlib import Path
from private_prices import unique_object
from sec_prepared_data import SCHEMAS, digest, inventory, tab_rows
ARCHIVE='2026q2_form345.zip'
URL='https://www.sec.gov/files/datastandardsinnovation/data/insider-transactions-data-sets/'+ARCHIVE
ORDER=['SUBMISSION.tsv']+sorted(x for x in SCHEMAS if x.endswith('.tsv') and x!='SUBMISSION.tsv')
FIELDS={'path','url','byte_count','sha256','local_verified_utc','retrieval_method','http_status','exact_download_utc'}
def category(value,allowed):return value if value in allowed else 'MISSING' if value=='' else 'UNKNOWN'
def invalid_constant(_):raise ValueError('nonfinite JSON')
def row_bytes(row):return (json.dumps(list(row),ensure_ascii=False,separators=(',',':'))+'\n').encode()
def save(path,value):
    with path.open('x',encoding='utf8') as f:
        path.chmod(0o600);json.dump(value,f,indent=2);f.write('\n');f.flush()
        import os
        os.fsync(f.fileno())
def ingest(root,out):
    root,out=Path(root),Path(out)
    if out.exists() or out.resolve().is_relative_to(Path(__file__).resolve().parents[1]):raise ValueError('new private output outside checkout required')
    with (root/'browser-receipt.json').open('rb') as f:raw=f.read(100_001)
    if len(raw)>100_000:raise ValueError('receipt bound')
    full=json.loads(raw,object_pairs_hook=unique_object,parse_constant=invalid_constant)
    if not isinstance(full,dict) or not FIELDS<=full.keys():raise ValueError('receipt fields')
    r={k:full[k] for k in sorted(FIELDS)}
    if r['path']!=ARCHIVE or r['url']!=URL or r['retrieval_method']!='PUBLIC_BROWSER_LINK_DOWNLOAD_NO_PRIVATE_CONTACT' or r['http_status'] is not None or r['exact_download_utc'] is not None:raise ValueError('receipt identity')
    now=dt.datetime.now(dt.timezone.utc);seen=dt.datetime.fromisoformat(r['local_verified_utc'])
    if seen.tzinfo is None or seen>now:raise ValueError('clock')
    p=root/ARCHIVE
    if type(r['byte_count']) is not int or not 0<r['byte_count']<=50_000_000 or p.stat().st_size!=r['byte_count'] or digest(p)!=r['sha256']:raise ValueError('source integrity')
    with zipfile.ZipFile(p) as z:
        infos=inventory(z,'insider')
        if sum(x.file_size for x in infos)>500_000_000:raise ValueError('expanded bound')
        if z.testzip() is not None:raise ValueError('CRC')
    out.mkdir(parents=True,mode=0o700);marker=out/'INCOMPLETE';marker.write_text('Not verified. Do not use.\n');marker.chmod(0o600)
    path=out/'insider.sqlite';db=sqlite3.connect(path);path.chmod(0o600)
    counts={};hashes={};accs=set();ciks=set();dates=[];forms=collections.Counter();codes=collections.Counter();directions=collections.Counter()
    try:
        db.execute('PRAGMA synchronous=FULL');db.execute('PRAGMA journal_mode=DELETE')
        with zipfile.ZipFile(p) as z:
            for name in ORDER:
                header=SCHEMAS[name];table='insider_'+name[:-4].lower();it=tab_rows(z,name);next(it)
                db.execute('CREATE TABLE '+table+' ('+','.join('"'+c+'" TEXT' for c in header)+')')
                sql='INSERT INTO '+table+' VALUES ('+','.join('?' for _ in header)+')';batch=[];n=0;h=hashlib.sha256();keys=set()
                for row in it:
                    n+=1
                    if n>1_000_000:raise ValueError('row bound')
                    d=dict(zip(header,row));acc=d['ACCESSION_NUMBER']
                    if not re.fullmatch(r'[0-9]{10}-[0-9]{2}-[0-9]{6}',acc):raise ValueError('accession')
                    if name=='SUBMISSION.tsv':
                        day=dt.datetime.strptime(d['FILING_DATE'],'%d-%b-%Y').date();cik=d['ISSUERCIK']
                        if acc in accs or not re.fullmatch(r'[0-9]{1,10}',cik) or int(cik)==0:raise ValueError('submission identity')
                        if not dt.date(2026,4,1)<=day<=dt.date(2026,6,30) or day>seen.date():raise ValueError('filing quarter')
                        accs.add(acc);ciks.add(str(int(cik)));dates.append(day.isoformat());forms[category(d['DOCUMENT_TYPE'],{'3','3/A','4','4/A','5','5/A'})]+=1
                    elif acc not in accs:raise ValueError('orphan accession')
                    keyfield=next((c for c in header if c.endswith('_SK')),None)
                    if name=='FOOTNOTES.tsv':keyfield='FOOTNOTE_ID'
                    if keyfield:
                        key=(acc,d[keyfield])
                        if not key[1] or key in keys:raise ValueError('duplicate or empty source identity')
                        keys.add(key)
                    if name=='NONDERIV_TRANS.tsv':
                        code=category(d['TRANS_CODE'],set('ACDEFGHIJLMOPSUWXZ'));direction=category(d['TRANS_ACQUIRED_DISP_CD'],{'A','D'})
                        codes[code]+=1;directions[code+':'+direction]+=1
                    h.update(row_bytes(row));batch.append(row)
                    if len(batch)==5000:db.executemany(sql,batch);batch=[]
                if batch:db.executemany(sql,batch)
                counts[table]=n;hashes[table]=h.hexdigest();db.commit()
        if not accs:raise ValueError('empty submissions')
        db.commit();db.close()
        db=sqlite3.connect('file:'+str(path.resolve())+'?mode=ro',uri=True)
        if db.execute('PRAGMA quick_check').fetchone()!=('ok',):raise ValueError('database integrity')
        for table,n in counts.items():
            h=hashlib.sha256();actual=0
            for row in db.execute('SELECT * FROM '+table+' ORDER BY rowid'):h.update(row_bytes(row));actual+=1
            if actual!=n or h.hexdigest()!=hashes[table]:raise ValueError('persisted source fields')
        db.close()
        if digest(p)!=r['sha256']:raise ValueError('source changed')
        summary={'version':1,'status':'HISTORICAL_INSIDER_FILING_BATCH_NOT_SIGNALS','completed_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'source':r,'source_receipt_sha256':hashlib.sha256(raw).hexdigest(),'table_rows':counts,'table_canonical_row_sha256':hashes,'database_sha256':digest(path),'database_byte_count':path.stat().st_size,'submissions':len(accs),'issuer_ciks':len(ciks),'filing_date_min':min(dates),'filing_date_max':max(dates),'submission_forms':dict(sorted(forms.items())),'nonderivative_codes':dict(sorted(codes.items())),'nonderivative_code_direction':dict(sorted(directions.items())),'accession_joins_verified':True,'full_field_persistence_verified':True,'simulation_enabled':False,'orders_created':0,'limitations':['Q2 2026 filing-date batch, not transaction quarter or current holdings. Amendments and repeated records remain separate.','P/S includes open-market OR private transactions; codes and direction contradictions are retained, not interpreted as intent or signals.','Owner fields, footnotes, values and all raw rows remain private. Public output contains only aggregate metadata.','Submission AFF10B5ONE does not establish transaction-level plan applicability.','Local verification/completion clocks are not download, publication, or historical decision clocks. No deduplicated issuer union, training qualification or trades inferred.']}
        save(out/'summary.json',summary);save(out/'COMPLETE.json',{'database_sha256':summary['database_sha256'],'summary_sha256':digest(out/'summary.json')});marker.unlink();return summary
    except Exception:
        db.close();raise
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--root',type=Path,required=True);a.add_argument('--out',type=Path,required=True);v=a.parse_args();print(json.dumps(ingest(v.root,v.out),indent=2))
