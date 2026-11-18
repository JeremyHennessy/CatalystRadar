"""Source-bound XBRL instance lookup references; no document requests or qualification."""
import argparse,hashlib,json,re,sqlite3,zipfile
from pathlib import Path
from openfigi_evidence import read_pinned
from financial_pair_candidates import sha,write_private
from financial_archive_facts import read_source_rows
from sec_prepared_data import inventory,SCHEMAS
PACKETS='web/company-findings/revenue-review-sample.json'
PACKET_SHA='e1f1fcdda7e59c2953d10416d52968a90a47efc615a3d933b8b0c1f4fc58d431'
PACKET_BYTES=27359

def encoded(obj):return (json.dumps(obj,ensure_ascii=True,sort_keys=True,separators=(',',':'))+'\n').encode()
def digest(raw):return hashlib.sha256(raw).hexdigest()
def reference(packet,sub):
 cik=packet['issuer_cik'];acc=packet['accession'];name=sub['instance']
 if not re.fullmatch('[0-9]{10}',cik) or not int(cik) or not re.fullmatch('[0-9]{10}-[0-9]{2}-[0-9]{6}',acc):raise ValueError('identity format')
 if not re.fullmatch('[0-9]{1,10}',sub['cik']) or not int(sub['cik']):raise ValueError('source CIK format')
 if sub['adsh']!=acc or str(int(sub['cik'])).zfill(10)!=cik or sub['name']!=packet['issuer_name_as_filed']:raise ValueError('source identity mismatch')
 if not isinstance(name,str) or not re.fullmatch('[A-Za-z0-9][A-Za-z0-9_.-]{0,74}\\.xml',name) or '..' in name:raise ValueError('unsafe or unsupported instance filename')
 base=f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{acc.replace('-','')}/"
 if packet['source_url']!=base+acc+'-index.html':raise ValueError('filing index reference')
 return {'issuer_cik':cik,'accession':acc,'issuer_name_as_filed':sub['name'],'instance_filename_as_reported':name,'constructed_instance_lookup_url':f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{acc.replace('-','')}/{name}",'filing_index_lookup_url':packet['source_url'],'source_sub_rowid':packet['source_sub_rowid'],'source_sub_row_sha256':packet['source_sub_row_sha256'],'url_verification_status':'CONSTRUCTED_FROM_RETAINED_METADATA_NOT_FETCHED','reported_document_role':'XBRL_INSTANCE_NOT_VERIFIED_PRIMARY_HTML','http_status':None,'retrieved_at':None,'availability_verified':False,'original_context_checked':False,'period_dates_inferred_from_filename':None,'comparability_verified':False}

def build(root,database,archive):
 packets,size=read_pinned(Path(root)/PACKETS,PACKET_SHA,PACKET_BYTES)
 if size!=PACKET_BYTES or len(packets['packets'])!=5:raise ValueError('packet scope')
 sources={(p['database_sha256'],p['source_archive_sha256']) for p in packets['packets']}
 if len(sources)!=1 or sources!={(sha(database),sha(archive))}:raise ValueError('source pin mismatch')
 conn=sqlite3.connect(Path(database).resolve().as_uri()+'?mode=ro',uri=True);conn.row_factory=sqlite3.Row
 try:
  with zipfile.ZipFile(archive) as z:
   inventory(z,'financial')
   if z.getinfo('sub.txt').file_size>20000000 or z.getinfo('readme.htm').file_size>2000000:raise ValueError('member bounds')
   sub_raw=z.read('sub.txt');readme=z.read('readme.htm')
   wanted={p['source_sub_rowid'] for p in packets['packets']}
   if len(wanted)!=5:raise ValueError('duplicate submission reference')
   raw=read_source_rows(z,'sub.txt',wanted);records=[];seen=set()
   for p in packets['packets']:
    identity=(p['issuer_cik'],p['accession'])
    if identity in seen:raise ValueError('duplicate issuer/accession')
    seen.add(identity);rows=list(conn.execute('SELECT rowid,* FROM financial_sub WHERE rowid=?',(p['source_sub_rowid'],)))
    if len(rows)!=1:raise ValueError('missing source row')
    row=dict(rows[0]);original=raw[row['rowid']]
    if {k:row[k] for k in SCHEMAS['sub.txt']}!=original or digest(encoded(original))!=p['source_sub_row_sha256']:raise ValueError('source row correspondence')
    records.append(reference(p,original))
 finally:conn.close()
 if sources!={(sha(database),sha(archive))}:raise ValueError('source changed')
 return {'schema_version':1,'scope':'FIVE_RETAINED_REVENUE_CANDIDATE_INSTANCE_REFERENCES_ONLY','source_packet':{'path':PACKETS,'bytes':size,'sha256':PACKET_SHA},'source_archive_sha256':next(iter(sources))[1],'database_sha256':next(iter(sources))[0],'source_sub_member_sha256':digest(sub_raw),'source_readme_sha256':digest(readme),'records':records,'limitations':['The retained SEC SUB field names a submitted XBRL instance document. A constructed lookup URL is not a fetched or verified live document.','The instance may be extracted XBRL rather than the primary inline HTML statement. No document bytes, context IDs, units, durations or accounting scope have been inspected here.','Filename characters that resemble dates or tickers do not verify period boundaries, current identity or security mapping. In particular the AMD filename is preserved without deriving a date.','The five original review packets and existing108-company queue remain unchanged. These references do not resolve missing original-context evidence.','No provider request, credential use, gate bypass, price/outcome calculation or training/trading admission is performed.'],'provider_requests_made':False,'training_ready':False,'execution_ready':False}

def run(destination,**kwargs):
 out=Path(destination).resolve()
 if out.is_relative_to(Path(__file__).resolve().parents[1]) or not out.parent.is_dir():raise ValueError('trusted external parent required')
 out.mkdir(mode=0o700,exist_ok=False);write_private(out/'INCOMPLETE',{'status':'INCOMPLETE'})
 result=build(**kwargs);write_private(out/'references.json',result);write_private(out/'COMPLETE.json',{'references_sha256':sha(out/'references.json')});(out/'INCOMPLETE').unlink();return result
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__)
 for name in ('root','database','archive','output-directory'):p.add_argument('--'+name,required=True)
 a=vars(p.parse_args());destination=a.pop('output_directory');run(destination,**a)
