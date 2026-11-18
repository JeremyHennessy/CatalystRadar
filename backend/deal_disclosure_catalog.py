"""Public filing-metadata catalog; never publishes source narratives or inferred deals."""
import argparse,collections,datetime as dt,hashlib,json,re,os
from pathlib import Path
from deal_disclosure_evidence import audit,TAGS,VERSIONS,FORMS,canonical_hash
from financial_pair_candidates import sha,write_private

PUBLIC_FIELDS={'accession','issuer_cik','issuer_name_as_filed','form_as_filed','filing_date','concepts','disclosure_records','records_with_dimensions','sec_filing_index_url'}

def catalog(summary,records):
 if summary.get('status')!='ACQUISITION_DISPOSAL_DISCLOSURES_UNADJUDICATED' or summary.get('verified_events')!=0 or summary.get('training_ready') is not False or summary.get('execution_ready') is not False:raise ValueError('unsupported input status')
 if not isinstance(records,list) or not 0<len(records)<=10000 or len(records)!=summary['counts']['disclosure_records']:raise ValueError('input count')
 expected_selection={'tags':list(TAGS),'taxonomy_versions':list(VERSIONS),'custom':'0','abstract':'0','datatype':'textBlock'}
 if summary.get('selection')!=expected_selection:raise ValueError('selection mismatch')
 groups={};seen=set();concept_counts=collections.Counter();version_counts=collections.Counter();dimensioned=0
 for r in records:
  if any(r.get(k) is not None for k in ('event_type','event_date','announcement_utc','first_public_utc','novelty','materiality')) or r.get('training_ready') is not False or r.get('review_status')!='UNADJUDICATED_DISCLOSURE_NOT_EVENT':raise ValueError('adjudicated input not supported')
  raw=r['raw'];sub=r['submission'];acc=raw['adsh'];ci=sub['cik']
  if not re.fullmatch('[0-9]{10}-[0-9]{2}-[0-9]{6}',acc) or sub['adsh']!=acc or not re.fullmatch('[0-9]{1,10}',ci) or not int(ci):raise ValueError('source identity')
  if not isinstance(raw['rowid'],int) or isinstance(raw['rowid'],bool) or raw['rowid']<=0 or raw['rowid'] in seen:raise ValueError('source row identity')
  seen.add(raw['rowid'])
  if raw['tag'] not in TAGS or raw['version'] not in VERSIONS or r['raw_row_canonical_sha256']!=canonical_hash(raw):raise ValueError('source context/hash')
  for field,limit in [('name',500),('form',80)]:
   if not isinstance(sub[field],str) or len(sub[field])>limit or any(ord(c)<32 for c in sub[field]):raise ValueError('source label')
  if sub['form'] not in FORMS:raise ValueError('unsupported filing form')
  if not re.fullmatch('[0-9]{8}',sub['filed']):raise ValueError('filed date')
  day=dt.datetime.strptime(sub['filed'],'%Y%m%d').date().isoformat();cik=str(int(ci)).zfill(10)
  if not '2026-10-01'<=day<='2026-10-31' or not re.fullmatch('[0-9]{1,6}',raw['dimn']):raise ValueError('source batch/context')
  identity={'accession':acc,'issuer_cik':cik,'issuer_name_as_filed':sub['name'],'form_as_filed':sub['form'],'filing_date':day}
  g=groups.setdefault(acc,{'identity':identity,'concepts':{},'count':0,'dim':0})
  if g['identity']!=identity:raise ValueError('conflicting submission identity')
  concept_counts[raw['tag']]+=1;version_counts[raw['version']]+=1;dimensioned+=int(raw['dimn'])>0
  key=(raw['tag'],raw['version']);g['concepts'][key]=g['concepts'].get(key,0)+1;g['count']+=1;g['dim']+=int(raw['dimn'])>0
 if dict(concept_counts)!=summary['counts']['by_concept'] or dict(version_counts)!=summary['counts']['by_taxonomy_version'] or dimensioned!=summary['counts']['records_with_dimensions']:raise ValueError('context count mismatch')
 rows=[]
 for acc,g in sorted(groups.items()):
  identity=g['identity'];rows.append({**identity,'concepts':[{'tag':k[0],'taxonomy_version':k[1],'records':n} for k,n in sorted(g['concepts'].items())],'disclosure_records':g['count'],'records_with_dimensions':g['dim'],'sec_filing_index_url':f"https://www.sec.gov/Archives/edgar/data/{int(identity['issuer_cik'])}/{acc.replace('-','')}/{acc}-index.html"})
 if len(rows)!=summary['counts']['filings'] or len({r['issuer_cik'] for r in rows})!=summary['counts']['issuer_ciks']:raise ValueError('aggregate identity mismatch')
 if any(set(r)!=PUBLIC_FIELDS for r in rows):raise ValueError('public schema')
 data=(json.dumps(rows,separators=(',',':'))+'\n').encode()
 if len(data)>5000000:raise ValueError('public metadata size')
 manifest={'version':1,'status':'HISTORICAL_DISCLOSURE_FILING_CATALOG_NOT_CONFIRMED_DEALS','generated_at':dt.datetime.now(dt.timezone.utc).isoformat(),'filings':len(rows),'issuer_ciks':summary['counts']['issuer_ciks'],'disclosure_records':len(records),'records_with_dimensions':summary['counts']['records_with_dimensions'],'source_url':summary['source_url'],'source_archive_sha256':summary['source_archive_sha256'],'database_sha256':summary['database_sha256'],'selection':summary['selection'],'metadata':{'sha256':hashlib.sha256(data).hexdigest(),'byte_count':len(data)},'filing_date_min':min(r['filing_date'] for r in rows),'filing_date_max':max(r['filing_date'] for r in rows),'link_status':'CONSTRUCTED_FROM_FILED_IDENTIFIERS_NOT_FETCH_VERIFIED','verified_events':0,'training_ready':False,'execution_ready':False,'limitations':['Historical filing evidence selected by exact standard concepts, not confirmed deals, new announcements or investment signals.','Names and forms are as filed. CIK identifies the reporting issuer, not a target or security. No current identity, listing or ticker inference.','Filing dates are dates only, not earliest public, announcement, transaction or effective times. Text may discuss prior periods or accounting updates.','Concept counts include repeated contexts and dimensions. Multiple concepts may describe the same activity; no deduplication into events.','Links use standard SEC archive paths constructed from source CIK/accession. Availability was not fetched or independently verified; use SEC issuer search if unavailable.','No narratives, amounts, counterparties, owner details, source addresses or inferred deal fields are included. Names must be rendered as inert text.','The narrow concept/version selection is not complete M&A coverage; absence does not mean no acquisition or disposal.','Review original filings and announcements before interpreting. Price/outcome, materiality, novelty and historical availability are unqualified.']}
 return data,manifest

def save(database,database_sha,archive,archive_sha,out):
 out=Path(out).resolve()
 if out.exists() or out.is_relative_to(Path(__file__).resolve().parents[1]) or not out.parent.is_dir():raise ValueError('new trusted private output required')
 out.mkdir(mode=0o700);write_private(out/'INCOMPLETE',{})
 summary,records=audit(database,database_sha,archive,archive_sha);data,manifest=catalog(summary,records)
 p=out/'filings.json'
 with os.fdopen(os.open(p,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600),'wb') as f:f.write(data);f.flush();os.fsync(f.fileno())
 write_private(out/'summary.json',manifest)
 write_private(out/'COMPLETE.json',{'filings_sha256':sha(p),'summary_sha256':sha(out/'summary.json')});(out/'INCOMPLETE').unlink();return manifest

if __name__=='__main__':
 p=argparse.ArgumentParser()
 for n in ('database','database-sha','archive','archive-sha','out'):p.add_argument('--'+n,required=True)
 print(json.dumps(save(**vars(p.parse_args()))))
