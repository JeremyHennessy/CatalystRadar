"""Bounded read-only hydration of public source evidence for one exact CIK."""
import argparse,json,sys
from pathlib import Path
from research_retrieval import load_verified,normalize_cik,SNAPSHOT,SHA,SIZE,BASE,app_link
from openfigi_evidence import read_pinned
SECTIONS=('financial','insider','disclosure','reported')
MAX_OUTPUT=500000

def resolve(records,refs,cik,key):
 if not isinstance(records,list) or len(records)>2000 or not isinstance(refs,list) or len(refs)>1000 or len(refs)!=len(set(refs)):raise ValueError('record/reference bounds')
 index={}
 for record in records:
  ref=key(record)
  if not isinstance(ref,str) or ref in index:raise ValueError('duplicate/invalid source identity')
  index[ref]=record
 selected=[]
 for ref in refs:
  if ref not in index or index[ref]['issuer_cik']!=cik:raise ValueError('missing or cross-issuer reference')
  selected.append(index[ref])
 return selected

def page(records,status,limit,offset,source_key=None):
 assessed=status not in ('NOT_EVALUATED_IN_THIS_SNAPSHOT','CIK_OUTSIDE_REVIEWED_SNAPSHOT')
 if not assessed and records:raise ValueError('unassessed evidence contradiction')
 selected=records[offset:offset+limit]
 return {'coverage':status,'source_key':source_key,'total_source_records':len(records) if assessed else None,'returned_records':len(selected),'offset':offset,'limit':limit,'next_offset':offset+len(selected) if offset+len(selected)<len(records) else None,'records':selected}

def dossier(root,cik,section='financial',limit=10,offset=0):
 ci=normalize_cik(cik)
 if ci is None or section not in SECTIONS or type(limit)is not int or not 1<=limit<=25 or type(offset)is not int or not 0<=offset<=10000:raise ValueError('dossier query bounds')
 snapshot=load_verified(root);found=[r for r in snapshot['records'] if r['issuer_cik']==ci]
 if len(found)>1:raise ValueError('duplicate company')
 entry=found[0] if found else None;loaded={};used={}
 def source(key):
  if key not in loaded:
   meta=snapshot['sources'][key]
   if type(meta['bytes'])is not int or not 0<meta['bytes']<=2000000:raise ValueError('source bound')
   data,size=read_pinned(Path(root)/meta['path'],meta['sha256'],meta['bytes'])
   if size!=meta['bytes']:raise ValueError('source size')
   loaded[key]=data;used[key]=meta
  return loaded[key]
 sections={}
 if entry is None:
  for key in SECTIONS:sections[key]=([], 'CIK_OUTSIDE_REVIEWED_SNAPSHOT',None)
 else:
  financial=source('financial')['records']
  records=resolve(financial,entry['financial_case_ids'],ci,lambda r:r['id'])
  evaluated='financial' in entry['source_keys']
  sections['financial']=(records,'SELECTED_FINANCIAL_CONTEXTS_NOT_COMPARABILITY_VERIFIED' if evaluated else 'NOT_EVALUATED_IN_THIS_SNAPSHOT','financial' if evaluated else None)
  refs=entry['insider_filing_refs'];insider_key='watchlist_insider' if 'watchlist_insider' in entry['source_keys'] else 'insider' if 'insider' in entry['source_keys'] else None
  records=[]
  if insider_key:
   obj=source(insider_key);records=resolve(obj['filings' if insider_key=='watchlist_insider' else 'insider_filings'],refs,ci,lambda r:r['batch_id']+':'+r['accession'])
  elif refs:raise ValueError('insider coverage contradiction')
  sections['insider']=(records,entry['insider_coverage'] if insider_key else 'NOT_EVALUATED_IN_THIS_SNAPSHOT',insider_key)
  refs=entry['disclosure_accessions'];evaluated='catalog' in entry['source_keys']
  records=resolve(source('catalog'),refs,ci,lambda r:r['accession']) if evaluated else []
  if not evaluated and refs:raise ValueError('disclosure coverage contradiction')
  sections['disclosure']=(records,entry['disclosure_coverage'] if evaluated else 'NOT_EVALUATED_IN_THIS_SNAPSHOT','catalog' if evaluated else None)
  reported=[];key=None
  if entry.get('finding_ref'):
   keys=[k for k in ('ieh','emerson') if k in entry['source_keys']]
   if len(keys)!=1:raise ValueError('finding source ambiguity')
   key=keys[0];finding=source(key)
   if finding['id']!=entry['finding_ref'] or finding['issuer']['cik']!=ci or finding['filing']['accession']!=entry['source_accession']:raise ValueError('reported finding identity')
   reported=[finding]
  sections['reported']=(reported,'REVIEWED_ISSUER_REPORTED_FINDING_NOT_SIGNAL' if reported else 'NOT_EVALUATED_IN_THIS_SNAPSHOT',key)
 overview={k:{'coverage':s,'total_source_records':len(r) if s not in ('NOT_EVALUATED_IN_THIS_SNAPSHOT','CIK_OUTSIDE_REVIEWED_SNAPSHOT') else None,'source_key':key} for k,(r,s,key) in sections.items()}
 records,status,key=sections[section]
 result={'interface_version':1,'status':'COMPANY_IN_REVIEWED_SNAPSHOT' if entry else 'CIK_OUTSIDE_REVIEWED_SNAPSHOT','query':{'issuer_cik':ci,'section':section,'limit':limit,'offset':offset},'snapshot':{'path':SNAPSHOT,'sha256':SHA,'bytes':SIZE,'version':3,'company_entries':108},'company_entry':entry,'investigation_url':app_link(entry['evidence_url']) if entry else None,'section_overview':overview,'selected_section':page(records,status,limit,offset,key),'verified_public_sources':{k:{**v,'published_artifact_url':BASE+v['path']} for k,v in used.items()},'holdings_linkage':snapshot['holdings_linkage'],'interpretation':['Exact CIK groups separately sourced research evidence, not an event, causal relationship, aligned time window or security identity.','Only this fixed 108-company snapshot is supported. Later findings and wider issuer directories are not implicitly incorporated.','Financial prepared end dates are coarse reported context keys, not independently verified exact accounting durations. Numerical equality or difference does not establish comparability or restatement.','Insider P/S rows include open-market or private transactions; source filing-quarter coverage is not transaction-time coverage or evidence of intent.','Disclosure concepts are filing review candidates, not confirmed deals. Reported financing/revenue findings retain their own source limits.','Unassessed/out-of-snapshot counts are null. An assessed zero is only no selected record in that source scope. Empty pagination is not absence.','Source objects are returned unchanged from public artifacts. No network access verifies original links or present availability.'], 'model_inference_performed':False,'provider_requests_made':False,'training_ready':False,'execution_ready':False}
 if len((json.dumps(result,ensure_ascii=True,indent=2)+"\n").encode())>MAX_OUTPUT:raise ValueError('dossier output bound')
 return result

def main(argv=None):
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',default=str(Path(__file__).resolve().parents[1]));p.add_argument('--cik',required=True);p.add_argument('--section',choices=SECTIONS,default='financial');p.add_argument('--limit',type=int,default=10);p.add_argument('--offset',type=int,default=0);a=p.parse_args(argv)
 try:r=dossier(**vars(a))
 except (ValueError,KeyError,TypeError,OSError):print('Dossier unavailable: invalid query or mismatched reviewed evidence. No result inferred.',file=sys.stderr);return 2
 print(json.dumps(r,indent=2));return 0
if __name__=='__main__':raise SystemExit(main())
