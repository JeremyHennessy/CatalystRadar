"""Pinned existing evidence navigation by issuer CIK; no event inference."""
import argparse,datetime as dt,hashlib,json,re
from pathlib import Path
from openfigi_evidence import read_pinned
from financial_insider_links import validate_financial
from deal_disclosure_catalog import PUBLIC_FIELDS
from deal_disclosure_evidence import TAGS,VERSIONS,FORMS

PATHS={'financial':'web/company-findings/financial-review.json','catalog':'web/disclosure-catalog/filings.json','manifest':'web/disclosure-catalog/summary.json'}
def integer(v,minimum=0):
 if type(v) is not int or v<minimum:raise ValueError('invalid count')
 return v
def project(financial,rows,manifest):
 groups=validate_financial(financial)
 if manifest.get('status')!='HISTORICAL_DISCLOSURE_FILING_CATALOG_NOT_CONFIRMED_DEALS' or manifest.get('verified_events')!=0 or manifest.get('training_ready') is not False or manifest.get('execution_ready') is not False:raise ValueError('catalog state')
 expected_selection={'tags':list(TAGS),'taxonomy_versions':list(VERSIONS),'custom':'0','abstract':'0','datatype':'textBlock'}
 if manifest.get('selection')!=expected_selection or manifest.get('link_status')!='CONSTRUCTED_FROM_FILED_IDENTIFIERS_NOT_FETCH_VERIFIED':raise ValueError('catalog selection/link state')
 if manifest.get('source_url')!='https://www.sec.gov/files/dera/data/financial-statement-notes-data-sets/2026_10_notes.zip':raise ValueError('catalog source URL')
 for field in ('source_archive_sha256','database_sha256'):
  if not isinstance(manifest.get(field),str) or not re.fullmatch('[a-f0-9]{64}',manifest[field]):raise ValueError('source pin')
 for field in ('filings','issuer_ciks','disclosure_records','records_with_dimensions'):integer(manifest.get(field))
 if not isinstance(rows,list) or not 1<=len(rows)<=10000:raise ValueError('catalog bounds')
 seen=set();by={};contexts=dimensions=0
 for r in rows:
  if not isinstance(r,dict) or set(r)!=PUBLIC_FIELDS:raise ValueError('catalog allowlist')
  acc=r['accession'];ci=r['issuer_cik']
  if not isinstance(ci,str) or not re.fullmatch('[0-9]{10}',ci) or not int(ci) or not re.fullmatch('[0-9]{10}-[0-9]{2}-[0-9]{6}',acc) or acc in seen:raise ValueError('catalog identity')
  seen.add(acc)
  name=r['issuer_name_as_filed']
  if not isinstance(name,str) or not 1<=len(name)<=500 or any(ord(c)<32 for c in name) or r['form_as_filed'] not in FORMS:raise ValueError('catalog labels')
  day=dt.date.fromisoformat(r['filing_date']).isoformat()
  if not '2026-10-01'<=day<='2026-10-31':raise ValueError('catalog date scope')
  url=f"https://www.sec.gov/Archives/edgar/data/{int(ci)}/{acc.replace('-','')}/{acc}-index.html"
  if r['sec_filing_index_url']!=url:raise ValueError('source link')
  concepts=r['concepts'];keys=set();total=0
  if not isinstance(concepts,list) or not 1<=len(concepts)<=8:raise ValueError('concept bounds')
  for c in concepts:
   if set(c)!={'tag','taxonomy_version','records'} or c['tag'] not in TAGS or c['taxonomy_version'] not in VERSIONS:raise ValueError('concept scope')
   key=(c['tag'],c['taxonomy_version'])
   if key in keys:raise ValueError('duplicate concept')
   keys.add(key);total+=integer(c['records'],1)
  n=integer(r['disclosure_records'],1);d=integer(r['records_with_dimensions'])
  if total!=n or d>n:raise ValueError('context count')
  contexts+=n;dimensions+=d;by.setdefault(ci,[]).append(r)
 if (len(rows),len(by),contexts,dimensions)!=(manifest['filings'],manifest['issuer_ciks'],manifest['disclosure_records'],manifest['records_with_dimensions']):raise ValueError('catalog totals')
 if (min(r['filing_date'] for r in rows),max(r['filing_date'] for r in rows))!=(manifest['filing_date_min'],manifest['filing_date_max']):raise ValueError('catalog date bounds')
 companies=[];selected=[]
 for key,g in sorted(groups.items()):
  ci=key.zfill(10);matches=sorted(by.get(ci,[]),key=lambda r:r['accession']);selected+=matches
  companies.append({'issuer_cik':ci,'financial_case_ids':sorted(c['id'] for c in g['financial_cases']),'disclosure_accessions':[r['accession'] for r in matches],'disclosure_records':sum(r['disclosure_records'] for r in matches),'status':'SELECTED_HISTORICAL_DISCLOSURE_REQUIRES_ORIGINAL_REVIEW' if matches else 'NO_SELECTED_DISCLOSURE_IN_THIS_OCTOBER_CONCEPT_CATALOG','relationship':'EXACT_REPORTING_ISSUER_CIK_ONLY','same_event_verified':False,'temporal_alignment_verified':False,'security_identity_verified':False,'confirmed_deal':None,'first_public_utc':None})
 return {'version':1,'status':'ISSUER_DISCLOSURE_NAVIGATION_NOT_CONFIRMED_EVENTS','selection':'All existing financial-review issuers, joined only on exact normalized issuer CIK to every matching filing in the pinned October disclosure catalog. No name, ticker, timing, price or outcome join.','counts':{'financial_issuers':len(companies),'financial_contexts':sum(len(c['financial_case_ids']) for c in companies),'issuers_with_selected_disclosures':sum(bool(c['disclosure_accessions']) for c in companies),'issuers_without_selected_disclosures':sum(not c['disclosure_accessions'] for c in companies),'selected_filings':len(selected),'selected_disclosure_records':sum(r['disclosure_records'] for r in selected)},'companies':companies,'disclosure_filings':selected,'catalog_scope':{'filings':len(rows),'issuer_ciks':len(by),'disclosure_records':contexts,'selection':manifest['selection'],'source_url':manifest['source_url'],'source_archive_sha256':manifest['source_archive_sha256'],'database_sha256':manifest['database_sha256'],'filing_date_min':manifest['filing_date_min'],'filing_date_max':manifest['filing_date_max'],'link_status':manifest['link_status']},'training_ready':False,'execution_ready':False,'limitations':['Concepts select historical disclosure records, not verified acquisitions, disposals, new announcements or material events. Narratives may negate, repeat or describe past accounting.','CIK links the reporting issuer only, not a target, security, common transaction, causal explanation or investment thesis. Financial periods and October filing dates are not temporally aligned.','No selected filing means no match in this narrow retained concept/version/filing batch, not no acquisition or disposal. All cohort issuers remain represented.','Names remain source-associated as-filed labels; render as inert text. SEC links are constructed source-index lookups, not newly fetched or guaranteed available.','No raw narrative, target, deal amount, owner data, forecast, ranking or trading qualification is published. Original review is required; first-public and decision-time availability remain unknown.']}
def build(root,pins):
 data={};sources={}
 for key,path in PATHS.items():
  data[key],size=read_pinned(Path(root)/path,pins[key],5_000_000)
  sources[key]={'path':path,'sha256':pins[key],'bytes':size}
 if data['manifest']['metadata']!={'sha256':pins['catalog'],'byte_count':sources['catalog']['bytes']}:raise ValueError('catalog manifest pin')
 result=project(data['financial'],data['catalog'],data['manifest']);result['sources']=sources;result['generated_at']=dt.datetime.now(dt.timezone.utc).isoformat();return result
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--out',required=True)
 for key in PATHS:p.add_argument('--'+key+'-sha',required=True)
 a=p.parse_args();out=Path(a.out)
 if out.exists():raise ValueError('refuse overwrite')
 result=build(a.root,{k:getattr(a,k+'_sha') for k in PATHS})
 out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result['counts']))
