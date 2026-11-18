"""Exact source-row multiset reconciliation, not trades or economic position changes."""
import argparse,collections,datetime as dt,hashlib,json,re,sqlite3,zipfile
from pathlib import Path
from company_offering_notices import canonical,digest,sha,pinned_json,cik,accession
from sec_13f_data import SCHEMAS,inventory,rows,day,URL,ARCHIVE
ZIP_SHA='4db97d5652e262de51617971104e06313211de4d092e6bcb5d7bf34ee7efe054'
DB_SHA='5117bb2573288481d336dde11232ffb8bc64cb04a495f0fc179a64bf0e2aafda'
SUMMARY_SHA='f95e8216d201c20ca30f57ee5741c9b1487cd3e651e741cd347af41d7046b069'
ZIP_BYTES=100719015
TOTALS={'SUBMISSION':11852,'COVERPAGE':11852,'SUMMARYPAGE':10036}
INFO_TOTAL=3830274
FIELDS=SCHEMAS['INFOTABLE.tsv'][2:]
POLICY={'id':'all-explicit-first-restatement-pairs-retained-jun-aug2026-v1','inventory':'Exact pinned June-August2026 prepared13F archive only','group_key':['normalized manager CIK','SUBMISSION PERIODOFREPORT parsed date'],'candidate':'Exactly two submissions; one13F-HR with cover ISAMENDMENT=N and one13F-HR/A with Y, RESTATEMENT and AMENDMENTNO=1','eligibility':['Original filing date strictly earlier than amendment','Both REPORTTYPE exactly13F HOLDINGS REPORT','COVER/SUB report periods agree'],'value_or_outcome_filter':None,'confidentiality_filter':None,'selection_is_retrospective_not_authenticated_preregistration':True,'matching':'Exact multiset of13 INFOTABLE raw text fields excluding accession and SK only; no normalization or numeric comparison'}
def rawrow(d,n):return {'rowid':n,'fields':d,'canonical_row_sha256':digest(canonical(d))}
def index(rr):
 d={}
 for r in rr:
  a=accession(r['fields']['ACCESSION_NUMBER'])
  if a in d:raise ValueError('duplicate accession table row')
  d[a]=r
 return d

def choose(tables):
 sub=index(tables['SUBMISSION']);cover=index(tables['COVERPAGE']);summ=index(tables['SUMMARYPAGE'])
 if set(sub)!=set(cover) or not set(summ)<=set(sub):raise ValueError('source joins')
 groups=collections.defaultdict(list)
 for a,r in sub.items():
  d=r['fields'];groups[(cik(d['CIK']),day(d['PERIODOFREPORT']).isoformat())].append(a);day(d['FILING_DATE'])
 candidates=[];eligible=[];pre=collections.Counter()
 for (manager,period),aa in sorted(groups.items()):
  if len(aa)!=2:pre['NOT_EXACTLY_TWO_SUBMISSIONS']+=1;continue
  originals=[a for a in aa if sub[a]['fields']['SUBMISSIONTYPE']=='13F-HR' and cover[a]['fields']['ISAMENDMENT']=='N']
  amendments=[a for a in aa if sub[a]['fields']['SUBMISSIONTYPE']=='13F-HR/A' and cover[a]['fields']['ISAMENDMENT']=='Y' and cover[a]['fields']['AMENDMENTTYPE']=='RESTATEMENT' and cover[a]['fields']['AMENDMENTNO']=='1']
  if len(originals)!=1 or len(amendments)!=1:pre['NOT_EXPLICIT_ORIGINAL_AND_FIRST_RESTATEMENT']+=1;continue
  original,amendment=originals[0],amendments[0];reasons=[]
  if day(sub[original]['fields']['FILING_DATE'])>=day(sub[amendment]['fields']['FILING_DATE']):reasons.append('ORIGINAL_FILING_DATE_NOT_STRICTLY_EARLIER')
  if any(cover[a]['fields']['REPORTTYPE']!='13F HOLDINGS REPORT' for a in aa):reasons.append('NOT_BOTH_HOLDINGS_REPORT')
  if any(day(cover[a]['fields']['REPORTCALENDARORQUARTER']).isoformat()!=period for a in aa):reasons.append('COVER_SUB_PERIOD_MISMATCH')
  p={'manager_cik':manager,'report_period_as_filed':period,'original_accession':original,'amendment_accession':amendment,'exclusion_reasons':reasons};candidates.append(p)
  if not reasons:eligible.append(p)
 return candidates,eligible,{'source_submissions':len(sub),'manager_period_groups':len(groups),'pre_candidate_exclusion_counts':dict(sorted(pre.items())),'candidate_groups':len(candidates),'eligible_pairs':len(eligible),'excluded_candidate_groups':len(candidates)-len(eligible)},sub,cover,summ

def verify(archive,database):
 if Path(archive).stat().st_size!=ZIP_BYTES or sha(archive)!=ZIP_SHA or sha(database)!=DB_SHA:raise ValueError('source pin')
 tables={};pins={}
 with sqlite3.connect(Path(database).resolve().as_uri()+'?mode=ro',uri=True) as db,zipfile.ZipFile(archive) as z:
  inventory(z)
  if db.execute('PRAGMA quick_check').fetchone()!=('ok',):raise ValueError('DB integrity')
  for label,total in TOTALS.items():
   table='holdings_'+label.lower();name=label+'.tsv'
   if [r[1] for r in db.execute('pragma table_info('+table+')')]!=SCHEMAS[name]:raise ValueError('schema')
   cur=db.execute('SELECT rowid,* FROM '+table+' ORDER BY rowid');out=[]
   for n,(d,v) in enumerate(rows(z,name),1):
    r=cur.fetchone()
    if r is None or r[0]!=n or list(r[1:])!=v:raise ValueError('ZIP DB correspondence')
    out.append(rawrow(d,n))
   if len(out)!=total or cur.fetchone() is not None:raise ValueError('source count')
   tables[label]=out
   with z.open(name) as f:h=hashlib.file_digest(f,'sha256').hexdigest()
   pins[label]={'member_sha256':h,'rows_verified':total}
  candidates,pairs,census,sub,cover,summ=choose(tables);aa={p[k] for p in pairs for k in ('original_accession','amendment_accession')}
  if len(aa)>200:raise ValueError('selection bound')
  if [r[1] for r in db.execute('pragma table_info(holdings_infotable)')]!=SCHEMAS['INFOTABLE.tsv']:raise ValueError('INFO schema')
  info={a:[] for a in aa};cur=db.execute('SELECT rowid,* FROM holdings_infotable WHERE ACCESSION_NUMBER IN ('+','.join('?' for a in aa)+') ORDER BY rowid',tuple(sorted(aa)));selected_count=0;seen=set();n=0
  for n,(d,v) in enumerate(rows(z,'INFOTABLE.tsv'),1):
   if d['ACCESSION_NUMBER'] not in aa:continue
   actual=cur.fetchone()
   if actual is None or actual[0]!=n or list(actual[1:])!=v:raise ValueError('INFO ZIP DB correspondence')
   key=(d['ACCESSION_NUMBER'],d['INFOTABLE_SK'])
   if key in seen:raise ValueError('duplicate source key')
   seen.add(key);selected_count+=1
   if selected_count>100000:raise ValueError('selected INFO bound')
   info[d['ACCESSION_NUMBER']].append(rawrow(d,n))
  if n!=INFO_TOTAL or cur.fetchone() is not None:raise ValueError('INFO census')
  with z.open('INFOTABLE.tsv') as f:h=hashlib.file_digest(f,'sha256').hexdigest()
  pins['INFOTABLE']={'member_sha256':h,'source_rows_scanned':n,'selected_rows_verified':selected_count,'nonselected_rows_not_compared_to_database':n-selected_count}
 if sha(archive)!=ZIP_SHA or sha(database)!=DB_SHA:raise ValueError('changed input')
 return candidates,pairs,census,sub,cover,summ,info,pins

def multiset(left,right):
 def bucket(rr):
  b=collections.defaultdict(list)
  for r in rr:
   d=r['fields']
   if set(d)!=set(SCHEMAS['INFOTABLE.tsv']) or any(not isinstance(v,str) for v in d.values()):raise ValueError('INFO field set')
   b[tuple(d[f] for f in FIELDS)].append({'rowid':r['rowid'],'source_key':d['INFOTABLE_SK'],'full_row_sha256':r['canonical_row_sha256']})
  return b
 l,r=bucket(left),bucket(right);matched=0;lineage=[]
 for key in sorted(set(l)|set(r)):
  a,b=l.get(key,[]),r.get(key,[]);m=min(len(a),len(b));matched+=m
  lineage.append({'comparison_fields':dict(zip(FIELDS,key)),'comparison_sha256':digest(canonical(dict(zip(FIELDS,key)))),'original_occurrences':a,'amendment_occurrences':b,'exact_matched_multiplicity':m})
 result={'original_source_rows':len(left),'amendment_source_rows':len(right),'exact_matched_row_multiplicity':matched,'original_unmatched_row_multiplicity':len(left)-matched,'amendment_unmatched_row_multiplicity':len(right)-matched}
 return result,lineage

def flag(v):return {'N':'N_AS_REPORTED','Y':'Y_AS_REPORTED','':'UNKNOWN_BLANK_AS_REPORTED'}.get(v,'UNKNOWN_REDACTED')
def filing(a,sub,cover,summ,actual):
 s=sub[a];c=cover[a];z=summ.get(a);sd=s['fields'];cd=c['fields'];zd=z['fields'] if z else {}
 rawcount=zd.get('TABLEENTRYTOTAL','');count=int(rawcount) if re.fullmatch(r'[0-9]{1,9}',rawcount) else None
 return {'accession':a,'form_as_filed':sd['SUBMISSIONTYPE'],'filing_date_as_reported':day(sd['FILING_DATE']).isoformat(),'report_period_as_filed':day(sd['PERIODOFREPORT']).isoformat(),'cover_report_period_as_filed':day(cd['REPORTCALENDARORQUARTER']).isoformat(),'is_amendment_as_reported':flag(cd['ISAMENDMENT']),'amendment_type_as_reported':cd['AMENDMENTTYPE'] if cd['AMENDMENTTYPE'] in {'','RESTATEMENT','NEW HOLDINGS'} else 'UNKNOWN_REDACTED','amendment_number_as_reported':cd['AMENDMENTNO'] if re.fullmatch(r'[0-9]{0,3}',cd['AMENDMENTNO']) else None,'confidential_omitted_as_reported':flag(zd.get('ISCONFIDENTIALOMITTED','')),'confidential_denied_expired_as_reported':flag(cd['CONFDENIEDEXPIRED']),'summary_present':z is not None,'summary_table_entry_total':count,'summary_count_matches_retained_rows':count==actual if count is not None else None,'info_presence':'SOURCE_ROWS_PRESENT' if actual else 'NO_SOURCE_ROWS_NOT_VERIFIED_ZERO_HOLDINGS','source_rows':{k:{'rowid':r['rowid'],'canonical_row_sha256':r['canonical_row_sha256']} for k,r in [('SUBMISSION',s),('COVERPAGE',c),('SUMMARYPAGE',z)] if r},'sec_accession_lookup_url':'https://www.sec.gov/edgar/search/#/q='+a,'lookup_status':'CONSTRUCTED_ACCESSION_SEARCH_NOT_FETCHED'}

def build(archive,database,summary):
 s=pinned_json(summary,SUMMARY_SHA,20000);receipt=s['source']
 if receipt!={'path':ARCHIVE,'url':URL,'byte_count':ZIP_BYTES,'sha256':ZIP_SHA,'local_verified_utc':'2026-11-17T20:14:42.208535+00:00','retrieval_method':'PUBLIC_BROWSER_LINK_DOWNLOAD_NO_PRIVATE_CONTACT','http_status':None,'exact_download_utc':None}:raise ValueError('receipt')
 candidates,pairs,census,sub,cover,summ,info,pins=verify(archive,database);records=[];private=[]
 for p in pairs:
  a,b=p['original_accession'],p['amendment_accession'];counts,lineage=multiset(info[a],info[b]);original=filing(a,sub,cover,summ,len(info[a]));amended=filing(b,sub,cover,summ,len(info[b]))
  records.append({**p,'id':p['manager_cik']+'-'+p['report_period_as_filed'],'status':'EXACT_SOURCE_ROW_MULTISET_RECONCILIATION_NOT_POSITION_CHANGES','original':original,'amendment':amended,'reconciliation':counts,'private_match_lineage_sha256':digest(canonical(lineage)),'both_omitted_flags_explicit_N':all(x['confidential_omitted_as_reported']=='N_AS_REPORTED' for x in [original,amended]),'complete_holdings_verified':False,'supersession_verified':False,'security_identity_verified':False,'first_public_utc':None})
  private.append({'pair':p,'original_source_rows':info[a],'amendment_source_rows':info[b],'matching_lineage':lineage,'original_metadata':{'submission':sub[a],'cover':cover[a],'summary':summ.get(a)},'amendment_metadata':{'submission':sub[b],'cover':cover[b],'summary':summ.get(b)}})
 if (len(candidates),len(records))!=(36,32):raise ValueError('reviewed census changed')
 census.update({'selected_INFO_rows':sum(x['reconciliation']['original_source_rows']+x['reconciliation']['amendment_source_rows'] for x in records),'pairs_both_omitted_flags_explicit_N':sum(x['both_omitted_flags_explicit_N'] for x in records),'qualified_complete_holdings_pairs':0,'summary_count_mismatch_filings':sum(f['summary_count_matches_retained_rows'] is False for x in records for f in [x['original'],x['amendment']]),'filings_without_INFO_source_rows':sum(f['info_presence']!='SOURCE_ROWS_PRESENT' for x in records for f in [x['original'],x['amendment']])})
 public={'schema_version':1,'status':'BOUNDED_MANAGER_SOURCE_RESTATEMENT_RECONCILIATION_NOT_TRADING_FLOWS','policy':POLICY,'policy_sha256':digest(canonical(POLICY)),'counts':census,'candidate_groups':candidates,'pairs':records,'sources':{'archive':receipt,'database_sha256':DB_SHA,'summary_sha256':SUMMARY_SHA,'tables':pins},'comparison_fields':FIELDS,'out_of_selection_status':'NOT_EVALUATED_UNDER_FIXED_PAIR_POLICY','limitations':['Manager CIK identifies the filer, not any held issuer/security. No company or ticker/name join is made.','Pairs are selected by exact manager/report-period and explicit filing flags, not a verified predecessor accession, supersession or complete amendment chain.','Thirteen raw INFO text fields are compared exactly as a multiset, excluding only accession and source key. No normalization, numeric difference, economic position/security matching or trading-flow interpretation occurs.','Duplicate multiplicity is preserved. Matched rows are identical source records, not independently verified identical economic positions; unmatched rows may reflect any textual, classification, numeric or other source difference.','Blank confidentiality flags mean unknown, not N. Even two explicit N flags do not prove complete holdings; confidential positions, omission rules and original disclosures are not independently resolved.','Filing date and report period remain distinct. Retrospective local verification is not first-public or decision-time evidence. Historical reports are not current ownership.','Missing INFO source rows are not a verified zero portfolio. Summary row counts are diagnostics, not a guarantee of completeness; mismatches do not silently exclude a pair.','Original filing lookup links are constructed/unfetched; the pinned prepared archive is the verified citation. Raw positions, names, identifiers, shares, values and matching lineage remain private.','All candidate exclusions are preserved. The32eligiblepairs are not all amendments, all managers or a representative sample. No sums across periods, forecasts, rankings or orders are produced.'],'training_ready':False,'execution_ready':False,'provider_requests_made':False}
 if len(canonical(public))>300000:raise ValueError('public bound')
 return public,private

def save(archive,database,summary,out):
 out=Path(out).resolve()
 if out.exists() or not out.parent.is_dir() or out.is_relative_to(Path(__file__).resolve().parents[1]):raise ValueError('new private destination')
 out.mkdir(mode=0o700)
 def write(n,v):
  p=out/n;p.write_bytes(canonical(v));p.chmod(0o600)
 write('INCOMPLETE',{});public,private=build(archive,database,summary);write('evidence.json',private);write('reconciliation.json',public);write('COMPLETE.json',{'public_sha256':sha(out/'reconciliation.json'),'private_sha256':sha(out/'evidence.json')});(out/'INCOMPLETE').unlink();return public
if __name__=='__main__':
 p=argparse.ArgumentParser()
 for k in ['archive','database','summary','out']:p.add_argument('--'+k,required=True)
 a=p.parse_args();print(json.dumps(save(a.archive,a.database,a.summary,a.out)['counts'],sort_keys=True))
