"""Prepared-source going-concern contexts for review, never a financial-risk classifier."""
import argparse, collections, datetime as dt, hashlib, json, re, sqlite3, zipfile
from pathlib import Path
from company_offering_notices import canonical,digest,sha,pinned_json,cik,accession,safe_name,COHORT_SHA
from sec_notes_data import SCHEMAS,inventory,rows,URL
ZIP_SHA='44d1b48909babe6611fcf59ff5bd273281616acbf2b91567e9597a51f924cee1'
DB_SHA='f2e9a91fb48a3c91fc47d2eff55d4cc63f77157cabab9e96278815621f10e597'
SUMMARY_SHA='374ea3d921e53749750b08b3b97619d4c9b808fbb1961208e3a60726642d7b73'
TYPES={'DisclosureOfGoingConcernExplanatory':'textBlock','SubstantialDoubtAboutGoingConcernTextBlock':'textBlock','SubstantialDoubtAboutGoingConcernWithinOneYear':'boolean','SubstantialDoubtAboutGoingConcernConditionsOrEvents':'string','SubstantialDoubtAboutGoingConcernManagementsPlansSubstantialDoubtNotAlleviated':'string'}
VERSIONS={'DisclosureOfGoingConcernExplanatory':{'ifrs/2025'},**{t:{'us-gaap/2025','us-gaap/2026'} for t in TYPES if t!='DisclosureOfGoingConcernExplanatory'}}
ZIP_BYTES=91722505
TOTALS={'txt':271414,'sub':6670,'tag':151113,'dim':103874}
FORMS={'10-Q','10-Q/A','10-K','10-K/A','10-KT','20-F','20-F/A','40-F','6-K','6-K/A','8-K','8-K/A','S-1','S-1/A','S-4','S-4/A','F-1','F-1/A','F-4','F-4/A','POS AM'}
def selected(d):return d['tag'] in TYPES and d['version'] in VERSIONS[d['tag']]
def row(d,n):return {'rowid':n,'fields':d,'canonical_row_sha256':digest(canonical(d))}
def verify(archive,database):
 if Path(archive).stat().st_size!=ZIP_BYTES or sha(archive)!=ZIP_SHA or sha(database)!=DB_SHA:raise ValueError('source pin')
 kept={};pins={};excluded=0
 with sqlite3.connect(Path(database).resolve().as_uri()+'?mode=ro',uri=True) as db,zipfile.ZipFile(archive) as z:
  inventory(z)
  if db.execute('pragma quick_check').fetchone()!=('ok',):raise ValueError('DB integrity')
  for label,total in TOTALS.items():
   name=label+'.tsv';table='notes_'+label
   if [r[1] for r in db.execute('pragma table_info('+table+')')]!=SCHEMAS[name]:raise ValueError('DB schema')
   cur=db.execute('select rowid,* from '+table+' order by rowid');out=[];n=0
   for n,(d,v) in enumerate(rows(z,name),1):
    actual=cur.fetchone()
    if actual is None or actual[0]!=n or list(actual[1:])!=v:raise ValueError('ZIP DB correspondence')
    take=selected(d) if label=='txt' else d['adsh'] in accessions if label=='sub' else (d['tag'],d['version']) in tags if label=='tag' else d['dimhash'] in dims
    if take:out.append(row(d,n))
    elif label=='txt':excluded+=1
   if n!=total or cur.fetchone() is not None:raise ValueError('table count')
   kept[label]=out
   if label=='txt':
    if len(out)>1000 or sum(len(r['fields']['value']) for r in out)>5000000:raise ValueError('selection bound')
    accessions={r['fields']['adsh'] for r in out};tags={(r['fields']['tag'],r['fields']['version']) for r in out};dims={r['fields']['dimh'] for r in out}
   with z.open(name) as f:h=hashlib.file_digest(f,'sha256').hexdigest()
   pins[label]={'member':name,'member_sha256':h,'rows_verified':n,'table':table}
 if sha(archive)!=ZIP_SHA or sha(database)!=DB_SHA:raise ValueError('changed input')
 return kept,pins,excluded

def unique_map(items,key):
 out={}
 for r in items:
  k=key(r['fields'])
  if k in out:raise ValueError('ambiguous source join')
  out[k]=r
 return out

def project(cohort,data):
 if len(cohort)!=len(set(cohort)) or any(cik(c)!=c for c in cohort):raise ValueError('cohort')
 subs=unique_map(data['sub'],lambda d:d['adsh']);tags=unique_map(data['tag'],lambda d:(d['tag'],d['version']));dims=unique_map(data['dim'],lambda d:d['dimhash']);seen=set();records=[];private=[]
 for raw in data['txt']:
  x=raw['fields'];n=raw['rowid'];a=accession(x['adsh'])
  if n in seen or not selected(x):raise ValueError('TXT selection identity')
  seen.add(n)
  try:s=subs[a];t=tags[x['tag'],x['version']];d=dims[x['dimh']]
  except KeyError:raise ValueError('missing source join') from None
  tax=t['fields'];sub=s['fields'];dim=d['fields'];identity=cik(sub['cik'])
  if identity not in cohort:raise ValueError('selected source outside fixed company cohort')
  if tax['custom']!='0' or tax['abstract']!='0' or tax['datatype']!=TYPES[x['tag']]:raise ValueError('standard taxonomy type')
  if sub['form'] not in FORMS:raise ValueError('unsupported form')
  filed=dt.datetime.strptime(sub['filed'],'%Y%m%d').date()
  if not dt.date(2026,10,1)<=filed<=dt.date(2026,10,31):raise ValueError('filing batch')
  if not re.fullmatch(r'[0-9]{8}',x['ddate']) or not re.fullmatch(r'[0-9]{1,3}',x['qtrs']) or not re.fullmatch(r'[0-9]{1,3}',x['dimn']) or not re.fullmatch(r'0x[0-9a-fA-F]{8,64}',x['dimh']):raise ValueError('prepared context format')
  if not re.fullmatch(r'[A-Za-z0-9_:.\-]{1,500}',x['context']) or x['coreg']!='' or x['escaped'] not in {'0','1'} or not re.fullmatch(r'[A-Za-z0-9-]{0,20}',x['lang']):raise ValueError('context privacy/schema')
  if dim['segt'] not in {'0','1'} or (int(x['dimn'])==0)!=(dim['segments']==''):raise ValueError('dimension correspondence')
  status='UNINTERPRETED_DISCLOSURE' if tax['datatype']=='textBlock' else 'UNINTERPRETED_SPECIFIC_STRING_DISCLOSURE';boolean=None
  if tax['datatype']=='boolean':
   if x['value'] not in {'true','false','1','0'}:raise ValueError('boolean lexical form')
   boolean=x['value'] in {'true','1'};status='TRUE_AS_REPORTED' if boolean else 'FALSE_AS_REPORTED'
  provenance={label:{'rowid':r['rowid'],'canonical_row_sha256':r['canonical_row_sha256']} for label,r in [('txt',raw),('sub',s),('tag',t),('dim',d)]}
  records.append({'id':'notes-txt-'+str(n),'issuer_cik':identity,'issuer_name_as_filed':safe_name(sub['name']),'accession':a,'form_as_filed':sub['form'],'filing_date_as_reported':filed.isoformat(),'concept':x['tag'],'taxonomy_version':x['version'],'datatype':tax['datatype'],'status':status,'boolean_value_as_reported':boolean,'qualification':'PREPARED_SOURCE_NOT_ORIGINAL_QUALIFIED','context':{k:x[k] for k in ('context','ddate','qtrs','dimh','dimn','lang','escaped')},'dimension_metadata':{'segt_as_reported':dim['segt'],'segments_utf8_sha256':digest(dim['segments'].encode()),'raw_dim_segments_published':False,'exact_original_dimension_qnames_verified':False},'value_utf8_sha256':digest(x['value'].encode()),'source_rows':provenance,'event_date':None,'first_public_utc':None,'risk_conclusion':None,'sec_accession_lookup_url':'https://www.sec.gov/edgar/search/#/q='+a,'lookup_status':'CONSTRUCTED_ACCESSION_SEARCH_NOT_FETCHED'})
  private.append({'txt':raw,'submission':s,'taxonomy':t,'dimensions':d})
 records.sort(key=lambda r:(r['issuer_cik'],r['filing_date_as_reported'],r['accession'],r['source_rows']['txt']['rowid']))
 companies=[{'issuer_cik':c,'records':[r for r in records if r['issuer_cik']==c]} for c in sorted({r['issuer_cik'] for r in records})]
 counts={'cohort_ciks':len(cohort),'selected_ciks':len(companies),'selected_filings':len({r['accession'] for r in records}),'selected_contexts':len(records),'cohort_ciks_without_selected_contexts':len(cohort)-len(companies),'status_counts':dict(sorted(collections.Counter(r['status'] for r in records).items())),'dimension_count_distribution':dict(sorted(collections.Counter(r['context']['dimn'] for r in records).items())),'concept_counts':dict(sorted(collections.Counter(r['concept'] for r in records).items())),'silently_dropped_selected_contexts':0}
 return companies,counts,private

def build(root,archive,database,summary):
 index=pinned_json(Path(root)/'web/company-investigation/v1/index.json',COHORT_SHA,2400000);s=pinned_json(summary,SUMMARY_SHA,20000);r=s['source']
 if r!={'path':'2026_10_notes.zip','url':URL,'byte_count':91722505,'sha256':ZIP_SHA,'local_verified_utc':'2026-11-17T19:57:55.179466+00:00','retrieval_method':'PUBLIC_BROWSER_LINK_DOWNLOAD_NO_PRIVATE_CONTACT','http_status':None,'exact_download_utc':None}:raise ValueError('receipt')
 cohort=[x['issuer_cik'] for x in index['directory']]
 if len(cohort)!=8035:raise ValueError('cohort census')
 data,pins,excluded=verify(archive,database);companies,counts,private=project(cohort,data)
 if (counts['selected_contexts'],counts['selected_filings'],counts['selected_ciks'])!=(123,108,97):raise ValueError('reviewed census changed')
 counts.update({'source_txt_rows':TOTALS['txt'],'txt_rows_outside_fixed_concept_version_selection':excluded})
 if excluded+counts['selected_contexts']!=TOTALS['txt']:raise ValueError('conservation')
 public={'schema_version':1,'status':'PREPARED_GOING_CONCERN_CONTEXTS_FOR_ORIGINAL_REVIEW_NOT_RISK_CLASSIFICATION','cohort_ciks':sorted(cohort),'cohort_without_records_status':'NO_SELECTED_STANDARD_CONTEXT_IN_PINNED_OCTOBER_NOTES_BATCH','outside_cohort_status':'NOT_EVALUATED','counts':counts,'companies':companies,'selection':{'concept_datatypes':TYPES,'versions_by_concept':{k:sorted(v) for k,v in VERSIONS.items()},'custom':'0','abstract':'0','value_filter':None},'sources':{'cohort':{'path':'web/company-investigation/v1/index.json','sha256':COHORT_SHA},'archive':r,'database_sha256':DB_SHA,'ingestion_summary_sha256':SUMMARY_SHA,'tables':pins},'limitations':['Concept presence is a source review lead, not a financial-risk conclusion, current substantial doubt, default, bankruptcy, prediction or trading signal.','False is the filer-reported value in one context, not no financial risk; separate issuer CIKs and contexts are never propagated or merged.','Narrative and specific strings are uninterpreted. Whole text, persons, amounts, contact details and raw DIM segment strings remain private. Verbatim context IDs may contain member-like company cues; those cues are not verified QName or identity mappings.','ddate/qtrs are prepared context fields, not verified exact duration boundaries or knowledge time. Context IDs and filename-like cues must not be parsed into event dates.','A historical context can include later management plans or events; no backdating to its reported period is permitted. Filing date, local verification and event/first-public dates are distinct.','Original documents and exact dimension QName semantics are not verified by this prepared-source projection; no original-source or accounting-comparability qualification is claimed.','Scoped absence excludes custom tags, other concepts/versions, untagged text and other batches. It does not mean no substantial doubt or no financial risk.','Multiple contexts can repeat or dimension a disclosure; records are not unique events. No event deduplication or issuer-wide consolidation occurs.','Official prepared archive is the verified source citation. Constructed SEC accession searches are unfetched and not verified original-filing links.'],'next_action':'Review the original filing and exact context, period and dimensional scope before interpreting any assertion; preserve subsequent-event timing.','training_ready':False,'execution_ready':False,'provider_requests_made':False}
 if len(canonical(public))>700000:raise ValueError('public bound')
 return public,private

def save(root,archive,database,summary,out):
 out=Path(out).resolve()
 if out.exists() or not out.parent.is_dir() or out.is_relative_to(Path(__file__).resolve().parents[1]):raise ValueError('new private destination')
 out.mkdir(mode=0o700)
 def write(n,v):
  p=out/n;p.write_bytes(canonical(v));p.chmod(0o600)
 write('INCOMPLETE',{});public,private=build(root,archive,database,summary);write('evidence.json',private);write('contexts.json',public);write('COMPLETE.json',{'private_sha256':sha(out/'evidence.json'),'public_sha256':sha(out/'contexts.json')});(out/'INCOMPLETE').unlink();return public
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--root',default=str(Path(__file__).resolve().parents[1]));p.add_argument('--archive',required=True);p.add_argument('--database',required=True);p.add_argument('--summary',required=True);p.add_argument('--out',required=True);a=p.parse_args();print(json.dumps(save(a.root,a.archive,a.database,a.summary,a.out)['counts'],sort_keys=True))
