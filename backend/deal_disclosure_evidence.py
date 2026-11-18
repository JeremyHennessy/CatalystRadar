"""Source-bound acquisition/disposal disclosure review records; never inferred events."""
import argparse, collections, datetime as dt, hashlib, json, re, sqlite3
from pathlib import Path
from financial_pair_candidates import sha, publish, write_private
from sec_notes_data import SCHEMAS
from split_basis_evidence import one, cik, SUB

TAGS=('BusinessCombinationDisclosureTextBlock','MergersAcquisitionsAndDispositionsDisclosuresTextBlock','DisposalGroupsIncludingDiscontinuedOperationsDisclosureTextBlock','AssetAcquisitionTextBlock')
VERSIONS=('us-gaap/2025','us-gaap/2026')
FORMS={'10-Q','10-Q/A','10-K','10-K/A','10-KT','20-F','20-F/A','40-F','6-K','6-K/A','8-K','8-K/A','S-1','S-1/A','S-4','S-4/A','F-1','F-1/A','F-4','F-4/A','POS AM'}

def canonical_hash(row):
 return hashlib.sha256(json.dumps({k:v for k,v in row.items() if k!='rowid'},sort_keys=True,separators=(',',':'),ensure_ascii=True).encode()).hexdigest()

def scan(db):
 for name in ('sub','tag','dim','txt'):
  if [r[1] for r in db.execute('PRAGMA table_info(notes_'+name+')')]!=SCHEMAS[name+'.tsv']:raise ValueError('source schema')
 rows=[];counts=collections.Counter();versions=collections.Counter();forms=collections.Counter();accessions=set();issuers=set();chars=0;dimensioned=0;empty=0
 query='SELECT rowid,* FROM notes_txt WHERE tag IN ('+','.join('?' for _ in TAGS)+') AND version IN (?,?) ORDER BY rowid'
 for source in db.execute(query,(*TAGS,*VERSIONS)):
  if len(rows)>=10000:raise ValueError('record bound')
  raw=dict(source)
  if any(not isinstance(v,str) or len(v)>1_000_000 for k,v in raw.items() if k!='rowid'):raise ValueError('source field bound')
  chars+=sum(len(v) for k,v in raw.items() if k!='rowid')
  if chars>20_000_000:raise ValueError('source aggregate bound')
  if not re.fullmatch(r'[0-9]{10}-[0-9]{2}-[0-9]{6}',raw['adsh']):raise ValueError('accession')
  taxonomy=one(db,'SELECT rowid,* FROM notes_tag WHERE tag=? AND version=?',(raw['tag'],raw['version']))
  if taxonomy['custom']!='0' or taxonomy['abstract']!='0' or taxonomy['datatype']!='textBlock':raise ValueError('taxonomy context')
  sub=one(db,'SELECT rowid,'+','.join(SUB)+' FROM notes_sub WHERE adsh=?',(raw['adsh'],));identity=cik(sub['cik'])
  if not re.fullmatch('[0-9]{8}',sub['filed']):raise ValueError('filing date')
  filed=dt.datetime.strptime(sub['filed'],'%Y%m%d').date()
  if not dt.date(2026,10,1)<=filed<=dt.date(2026,10,31):raise ValueError('filing batch')
  dim=one(db,'SELECT rowid,* FROM notes_dim WHERE dimhash=?',(raw['dimh'],))
  if not re.fullmatch('[0-9]{1,6}',raw['dimn']):raise ValueError('dimension count')
  dimensioned+=int(raw['dimn'])>0;empty+=not raw['value'];counts[raw['tag']]+=1;versions[raw['version']]+=1;forms[sub['form'] if sub['form'] in FORMS else 'OTHER_AS_FILED']+=1;accessions.add(raw['adsh']);issuers.add(identity)
  rows.append({'source_table':'notes_txt','raw':raw,'raw_row_canonical_sha256':canonical_hash(raw),'value_utf8_sha256':hashlib.sha256(raw['value'].encode()).hexdigest(),'taxonomy':taxonomy,'submission':sub,'dimensions':dim,'review_status':'UNADJUDICATED_DISCLOSURE_NOT_EVENT','event_type':None,'event_date':None,'announcement_utc':None,'first_public_utc':None,'novelty':None,'materiality':None,'training_ready':False})
 if not rows:raise ValueError('no supported disclosure records')
 return rows,{'disclosure_records':len(rows),'filings':len(accessions),'issuer_ciks':len(issuers),'by_concept':dict(sorted(counts.items())),'by_taxonomy_version':dict(sorted(versions.items())),'by_filing_form':dict(sorted(forms.items())),'records_with_dimensions':dimensioned,'empty_text_records':empty,'text_utf8_bytes':sum(len(r['raw']['value'].encode()) for r in rows)}

def audit(database,database_sha,archive,archive_sha):
 for path,digest in [(database,database_sha),(archive,archive_sha)]:
  if not re.fullmatch('[a-f0-9]{64}',digest) or sha(path)!=digest:raise ValueError('input hash')
 db=sqlite3.connect(Path(database).resolve().as_uri()+'?mode=ro',uri=True);db.row_factory=sqlite3.Row
 try:
  if db.execute('PRAGMA quick_check').fetchone()[0]!='ok':raise ValueError('database integrity')
  rows,counts=scan(db)
 finally:db.close()
 if sha(database)!=database_sha or sha(archive)!=archive_sha:raise ValueError('changed input')
 summary={'version':1,'status':'ACQUISITION_DISPOSAL_DISCLOSURES_UNADJUDICATED','database_sha256':database_sha,'source_archive_sha256':archive_sha,'source_url':'https://www.sec.gov/files/dera/data/financial-statement-notes-data-sets/2026_10_notes.zip','selection':{'tags':list(TAGS),'taxonomy_versions':list(VERSIONS),'custom':'0','abstract':'0','datatype':'textBlock'},'counts':counts,'audit_completed_at':dt.datetime.now(dt.timezone.utc).isoformat(),'source_retrieval_utc':None,'source_first_public_utc':None,'verified_events':0,'training_ready':False,'execution_ready':False,'limitations':['Records are selected disclosure contexts, not unique deals, new announcements, completed transactions or trading signals. Multiple concepts and dimensions can describe the same activity.','A disclosure may contain prior-period activity, denial, planned transactions, accounting updates or no activity. No event, target, amount, materiality or novelty is extracted from taxonomy alone.','Accession, filing date, reporting period and source context dates are not announcement or effective dates. Retrospective collection is not historical decision-time availability.','Exact standard concepts and two taxonomy versions only; custom concepts, other versions and untagged disclosures are outside scope. Absence is not evidence of no acquisition or divestiture.','Raw prepared TXT including escaping, language, footnotes, duration, context and dimensions stays private and uninterpreted. It is not original filing byte evidence.','Full TXT canonical row hash excludes SQLite rowid; value hash covers UTF-8 of retained text exactly, without HTML unescape, normalization or inference.','Database and archive pins identify retained inputs. Prior full-field ingestion audit establishes derivation; this utility does not authenticate source clocks or independently prove database-to-archive derivation.','Queue fields remain unknown until source interpretation and independent temporal/security qualification. No paper-engine activation or price/outcome/model admission.']}
 return summary,rows

if __name__=='__main__':
 p=argparse.ArgumentParser()
 for n in ('database','database-sha','archive','archive-sha','output-directory'):p.add_argument('--'+n,required=True)
 a=p.parse_args();out=Path(a.output_directory).resolve()
 if out.is_relative_to(Path(__file__).resolve().parents[1]) or not out.parent.is_dir():raise ValueError('trusted private parent required')
 out.mkdir(mode=0o700,exist_ok=False);write_private(out/'INCOMPLETE',{'status':'INCOMPLETE_NOT_USABLE'})
 args=vars(a);args.pop('output_directory');summary,rows=audit(**args);publish(out,summary,rows);print(json.dumps(summary))
