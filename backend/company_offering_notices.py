"""Offline exact-CIK Form D notice metadata; never an offering lifecycle or security join."""
import argparse, collections, datetime as dt, hashlib, json, re, sqlite3, unicodedata, zipfile
from pathlib import Path
from sec_formd_data import inventory, rows, SCHEMAS, URL
COHORT_SHA='c488e6b0aab25ef2e8b0434e2a518bfb44c03af93c4bbba5ec6dd42682ada013'
ZIP_SHA='03669a23e724645a8bbcad51822cf7f4b27f91c3f2bedac9dcff3c23e68e84bf'
DB_SHA='20a5492b9f0997c40397f504fa5dcc3df88cbb538e7275665cec603eaeb772b8'
SUMMARY_SHA='09ce5a8f3eb50ea83c85207e0c410e07ff467086cbe7e0cec10fa8ef45f06624'
TABLES={'FORMDSUBMISSION':15952,'ISSUERS':16160,'OFFERING':15952}
FLAGS=['ISEQUITYTYPE','ISDEBTTYPE','ISOPTIONTOACQUIRETYPE','ISSECURITYTOBEACQUIREDTYPE','ISPOOLEDINVESTMENTFUNDTYPE','ISTENANTINCOMMONTYPE','ISMINERALPROPERTYTYPE','ISOTHERTYPE']
ACC=re.compile(r'[0-9]{10}-[0-9]{2}-[0-9]{6}')
def canonical(x):return (json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=True)+'\n').encode()
def digest(b):return hashlib.sha256(b).hexdigest()
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def unique(pairs):
 d={}
 for k,v in pairs:
  if k in d:raise ValueError('duplicate JSON key')
  d[k]=v
 return d
def pinned_json(p,h,limit):
 with Path(p).open('rb') as f:b=f.read(limit+1)
 if len(b)>limit or digest(b)!=h:raise ValueError('JSON pin/bound')
 return json.loads(b,object_pairs_hook=unique,parse_constant=lambda x:(_ for _ in ()).throw(ValueError('nonfinite')))
def cik(v):
 if not isinstance(v,str) or not re.fullmatch(r'[0-9]{1,10}',v) or int(v)==0:raise ValueError('issuer CIK')
 return str(int(v)).zfill(10)
def accession(v):
 if not isinstance(v,str) or not ACC.fullmatch(v):raise ValueError('accession')
 return v
def safe_name(v):
 if not isinstance(v,str) or not 1<=len(v)<=500 or any(unicodedata.category(c).startswith('C') for c in v):raise ValueError('issuer name')
 return v

def receipt(s):
 r=s.get('source',{})
 if set(r)!={'path','url','byte_count','sha256','local_verified_utc','retrieval_method','http_status','exact_download_utc'} or r['path']!='2026q3_d.zip' or r['url']!=URL or r['sha256']!=ZIP_SHA or type(r['byte_count']) is not int or r['byte_count']!=3652689 or r['http_status'] is not None or r['exact_download_utc'] is not None or r['retrieval_method']!='PUBLIC_BROWSER_LINK_DOWNLOAD_NO_PRIVATE_CONTACT':raise ValueError('receipt')
 t=dt.datetime.fromisoformat(r['local_verified_utc'])
 if t.tzinfo is None or t>dt.datetime.now(dt.timezone.utc):raise ValueError('local clock')
 return r

def verified_tables(archive,database):
 if Path(archive).stat().st_size>10000000 or sha(archive)!=ZIP_SHA or sha(database)!=DB_SHA:raise ValueError('source pin')
 data={};pins={}
 with sqlite3.connect('file:'+str(Path(database).resolve())+'?mode=ro',uri=True) as db,zipfile.ZipFile(archive) as z:
  if db.execute('PRAGMA quick_check').fetchone()!=('ok',):raise ValueError('database integrity')
  inventory(z)
  for label,total in TABLES.items():
   name='2026Q3_d/'+label+'.tsv';table='formd_'+label.lower();header=SCHEMAS[name]
   if [r[1] for r in db.execute('PRAGMA table_info('+table+')')]!=header:raise ValueError('DB schema')
   cur=db.execute('SELECT rowid,* FROM '+table+' ORDER BY rowid');out=[]
   for n,(d,v) in enumerate(rows(z,name),1):
    actual=cur.fetchone()
    if actual is None or actual[0]!=n or list(actual[1:])!=v:raise ValueError('ZIP DB correspondence')
    out.append({'rowid':n,'fields':d,'canonical_row_sha256':digest(canonical(d))})
   if len(out)!=total or cur.fetchone() is not None:raise ValueError('table census')
   data[label]=out
   with z.open(name) as f:h=hashlib.file_digest(f,'sha256').hexdigest()
   pins[label]={'member':name,'member_sha256':h,'rows':total,'table':table}
 if sha(database)!=DB_SHA or sha(archive)!=ZIP_SHA:raise ValueError('source changed')
 return data,pins

def project(cohort,tables):
 if len(cohort)!=len(set(cohort)) or any(cik(c)!=c for c in cohort):raise ValueError('cohort identity')
 cohort=set(cohort);subs={};offers={};issuer_keys=set();byacc=collections.defaultdict(set)
 for key,target in [('FORMDSUBMISSION',subs),('OFFERING',offers)]:
  for row in tables[key]:
   a=accession(row['fields']['ACCESSIONNUMBER'])
   if a in target:raise ValueError('duplicate submission/offering')
   target[a]=row
 if set(subs)!=set(offers):raise ValueError('accession correspondence')
 for r in tables['ISSUERS']:
  d=r['fields'];a=accession(d['ACCESSIONNUMBER']);c=cik(d['CIK']);role=d['IS_PRIMARYISSUER_FLAG'];key=(a,d['ISSUER_SEQ_KEY'])
  if a not in subs or role not in {'YES','NO'} or key in issuer_keys or (c,role) in byacc[a]:raise ValueError('issuer join ambiguity')
  issuer_keys.add(key);byacc[a].add((c,role))
 if set(byacc)!=set(subs) or any(sum(role=='YES' for c,role in identities)!=1 for identities in byacc.values()):raise ValueError('primary issuer correspondence')
 parent={a:r['fields']['PREVIOUSACCESSIONNUMBER'] for a,r in offers.items()}
 def cycle(a):
  seen=set();p=a
  while p in parent and ACC.fullmatch(parent[p] or ''):
   if p in seen:return True
   seen.add(p);p=parent[p]
  return False
 selected=[];private=[];outside=0
 for r in tables['ISSUERS']:
  d=r['fields'];c=cik(d['CIK'])
  if c not in cohort:outside+=1;continue
  a=d['ACCESSIONNUMBER'];s=subs[a]['fields'];o=offers[a]['fields'];form=s['SUBMISSIONTYPE']
  if form not in {'D','D/A'} or s['TESTORLIVE']!='LIVE':raise ValueError('selected form/live')
  day=dt.datetime.strptime(s['FILING_DATE'],'%d-%b-%Y').date()
  if not dt.date(2026,7,1)<=day<=dt.date(2026,9,30):raise ValueError('filing scope')
  prior=o['PREVIOUSACCESSIONNUMBER'];valid=bool(ACC.fullmatch(prior));state='MISSING_AS_REPORTED' if not prior else 'INVALID_REDACTED' if not valid else 'PRESENT_IN_RETAINED_BATCH' if prior in subs else 'OUTSIDE_RETAINED_BATCH'
  amend={'true':'TRUE_AS_REPORTED','false':'FALSE_AS_REPORTED','':'MISSING'}.get(o['ISAMENDMENT'],'UNKNOWN_REDACTED')
  flags={f:{'true':'TRUE_AS_REPORTED','false':'FALSE_AS_REPORTED','':'MISSING_AS_REPORTED'}.get(o[f],'UNKNOWN_REDACTED') for f in FLAGS}
  source_rows={key:{'rowid':x['rowid'],'canonical_row_sha256':x['canonical_row_sha256']} for key,x in [('FORMDSUBMISSION',subs[a]),('ISSUERS',r),('OFFERING',offers[a])]}
  selected.append({'issuer_cik':c,'issuer_name_as_filed':safe_name(d['ENTITYNAME']),'accession':a,'form_as_filed':form,'filing_date_as_reported':day.isoformat(),'primary_issuer_as_reported':d['IS_PRIMARYISSUER_FLAG'],'amendment_flag':amend,'form_amendment_conflict':None if amend not in {'TRUE_AS_REPORTED','FALSE_AS_REPORTED'} else ((form=='D/A')!=(amend=='TRUE_AS_REPORTED')),'previous_accession':prior if valid else None,'previous_accession_status':state,'declared_predecessor_same_cik_and_role':(c,d['IS_PRIMARYISSUER_FLAG']) in byacc[prior] if state=='PRESENT_IN_RETAINED_BATCH' else None,'self_reference':prior==a,'retained_reference_cycle':cycle(a),'security_type_flags_as_reported':flags,'source_rows':source_rows,'sec_accession_lookup_url':'https://www.sec.gov/edgar/search/#/q='+a,'lookup_status':'CONSTRUCTED_ACCESSION_SEARCH_NOT_FETCHED','event_date':None,'first_public_utc':None,'financing_completion_verified':False,'security_identity_verified':False})
  private.append({'issuer_cik':c,'accession':a,'submission':subs[a],'issuer':r,'offering':offers[a]})
 selected.sort(key=lambda x:(x['issuer_cik'],x['filing_date_as_reported'],x['accession'],x['source_rows']['ISSUERS']['rowid']))
 companies=[]
 for c in sorted({x['issuer_cik'] for x in selected}):
  rr=[x for x in selected if x['issuer_cik']==c];companies.append({'issuer_cik':c,'status':'RETAINED_FORM_D_NOTICE_METADATA','records':rr})
 counts={'cohort_ciks':len(cohort),'selected_ciks':len(companies),'cohort_ciks_without_selected_notices':len(cohort)-len(companies),'selected_issuer_associations':len(selected),'selected_distinct_submissions':len({x['accession'] for x in selected}),'source_issuer_rows':len(tables['ISSUERS']),'issuer_rows_outside_cohort':outside,'rejected_or_silently_dropped_rows':0,'forms':dict(sorted(collections.Counter(x['form_as_filed'] for x in selected).items())),'previous_accession_states':dict(sorted(collections.Counter(x['previous_accession_status'] for x in selected).items())),'form_amendment_conflicts':sum(x['form_amendment_conflict'] is True for x in selected),'self_references':sum(x['self_reference'] for x in selected),'cycle_associations':sum(x['retained_reference_cycle'] for x in selected)}
 if counts['selected_issuer_associations']+outside!=len(tables['ISSUERS']):raise ValueError('conservation')
 return companies,counts,private

def build(root,archive,database,summary):
 index=pinned_json(Path(root)/'web/company-investigation/v1/index.json',COHORT_SHA,2400000);s=pinned_json(summary,SUMMARY_SHA,20000);r=receipt(s)
 cohort=[x['issuer_cik'] for x in index['directory']]
 if len(cohort)!=8035 or index['counts']['company_ciks']!=8035:raise ValueError('cohort census')
 tables,pins=verified_tables(archive,database);companies,counts,private=project(cohort,tables)
 if (counts['selected_ciks'],counts['selected_issuer_associations'],counts['selected_distinct_submissions'])!=(187,223,223):raise ValueError('reviewed selection changed')
 result={'schema_version':1,'status':'HISTORICAL_COMPANY_FORM_D_NOTICES_NOT_FINANCING_EVENTS','cohort_ciks':sorted(cohort),'cohort_without_records_status':'NO_SELECTED_ISSUER_NOTICE_IN_PINNED_Q3_FORM_D_BATCH','outside_cohort_status':'NOT_EVALUATED','counts':counts,'companies':companies,'sources':{'cohort':{'path':'web/company-investigation/v1/index.json','sha256':COHORT_SHA},'archive':r,'database_sha256':DB_SHA,'ingestion_summary_sha256':SUMMARY_SHA,'tables':pins},'filing_scope':{'start':'2026-07-01','end':'2026-09-30'},'first_public_utc':None,'limitations':['Exact issuer CIK association only; not a listed-security, manager, owner, ticker or name match.','Source filings are notices of exempt offerings, not SEC approval, completed financing, amounts raised or investment signals.','A D/A and declared previous accession do not establish supersession, a complete amendment chain or a reconstructed offering lifecycle. Blank previous accession is not first-ever; outside-batch reference is not invalid.','Filing dates are not event, first-sale, first-public or observation times. Download/HTTP clocks remain unknown; local verification is distinct.','Checkbox states are filer assertions only. Blank is missing as reported, not independently verified false or security eligibility.','Scoped no-record is only absence from this pinned prepared-data batch; it is not no financing or no activity.','Constructed accession lookup links were not fetched or verified as original documents. Prepared data may contain extraction errors; original filings remain authoritative.','Issuer names are inert as-filed labels, not current identity. No owner, contact, address, amount, narrative or security identity is published.'],'training_ready':False,'execution_ready':False,'provider_requests_made':False}
 if len(canonical(result))>900000:raise ValueError('public size')
 return result,private

def save(root,archive,database,summary,out):
 out=Path(out).resolve()
 if out.exists() or not out.parent.is_dir() or out.is_relative_to(Path(__file__).resolve().parents[1]):raise ValueError('new private destination')
 out.mkdir(mode=0o700)
 def write(name,obj):
  p=out/name;p.write_bytes(canonical(obj));p.chmod(0o600)
 write('INCOMPLETE',{});public,private=build(root,archive,database,summary);write('evidence.json',private);write('notices.json',public);write('COMPLETE.json',{'evidence_sha256':sha(out/'evidence.json'),'public_sha256':sha(out/'notices.json')});(out/'INCOMPLETE').unlink();return public
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--root',default=str(Path(__file__).resolve().parents[1]));p.add_argument('--archive',required=True);p.add_argument('--database',required=True);p.add_argument('--summary',required=True);p.add_argument('--out',required=True);a=p.parse_args();print(json.dumps(save(a.root,a.archive,a.database,a.summary,a.out)['counts'],sort_keys=True))
