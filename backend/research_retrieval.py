"""Read-only deterministic retrieval from one reviewed research snapshot.

No natural-language inference, model calls, provider access, order or file writes.
"""
import argparse,json,re,sys
from pathlib import Path
from openfigi_evidence import read_pinned
from research_lead_index import build,PATHS

SNAPSHOT='web/company-findings/research-lead-index-v3.json'
SHA='3d8db27dc45ed84fa44d5604e1839aa2aa9e1f263f2ed9e18cef04aed7a0e4e3'
SIZE=281154
BASE='https://jeremyhennessy.github.io/CatalystRadar/'
CATEGORIES=('FINANCIAL_CONTEXT_REVIEW','INSIDER_ORIGINAL_FILING_REVIEW','ACQUISITION_DISPOSAL_DISCLOSURE_REVIEW','ISSUER_REPORTED_COMPARISON_REVIEW','ISSUER_REPORTED_FINANCING_REVIEW')

def normalize_cik(value):
 if value is None:return None
 if not isinstance(value,str) or not re.fullmatch('[0-9]{1,10}',value) or not int(value):raise ValueError('CIK must be one to ten nonzero ASCII digits')
 return str(int(value)).zfill(10)

def load_verified(root):
 root=Path(root).resolve();snapshot,size=read_pinned(root/SNAPSHOT,SHA,SIZE)
 if size!=SIZE or snapshot.get('version')!=3 or snapshot.get('training_ready') is not False or snapshot.get('execution_ready') is not False:raise ValueError('unsupported snapshot')
 sources=snapshot.get('sources')
 if not isinstance(sources,dict) or set(sources)!=set(PATHS):raise ValueError('source inventory')
 for key,path in PATHS.items():
  if sources[key].get('path')!=path:raise ValueError('source path mismatch')
 rebuilt=build(root,{key:sources[key]['sha256'] for key in PATHS})
 if rebuilt!=snapshot:raise ValueError('snapshot derivation mismatch')
 return snapshot

def app_link(path):
 if path in ('company-ieh.html','company.html#debt-offering') or re.fullmatch(r'financial-review\.html\?cik=[0-9]{10}',path) or re.fullmatch(r'insider-review\.html#[0-9]{10}-[0-9]{2}-[0-9]{6}',path):return BASE+'web/'+path
 raise ValueError('unsupported app destination')

def retrieve(root,cik=None,category=None,limit=20,offset=0):
 ci=normalize_cik(cik)
 if category is not None and category not in CATEGORIES:raise ValueError('unsupported category')
 if type(limit) is not int or not 1<=limit<=100 or type(offset) is not int or not 0<=offset<=10000:raise ValueError('pagination bounds')
 snapshot=load_verified(root);all_rows=snapshot['records']
 matches=[r for r in all_rows if (ci is None or r['issuer_cik']==ci) and (category is None or category in r['research_types'])]
 selected=matches[offset:offset+limit];results=[]
 for row in selected:
  links=[]
  for key in row['source_keys']:
   source=snapshot['sources'][key]
   links.append({'source_key':key,**source,'published_artifact_url':BASE+source['path']})
  results.append({'entry':row,'investigation_url':app_link(row['evidence_url']),'additional_insider_review_urls':[app_link(p) for p in row.get('insider_evidence_urls',[])],'source_artifacts':links})
 return {'interface_version':1,'status':'MATCHES_IN_REVIEWED_SNAPSHOT' if matches else 'NO_MATCHES_IN_REVIEWED_SNAPSHOT','query':{'issuer_cik':ci,'category':category,'limit':limit,'offset':offset},'snapshot':{'path':SNAPSHOT,'sha256':SHA,'bytes':SIZE,'company_entries':len(all_rows),'version':3},'matching_company_entries':len(matches),'returned_company_entries':len(results),'requested_cik_present_in_snapshot':None if ci is None else any(r['issuer_cik']==ci for r in all_rows),'next_offset':offset+len(results) if offset+len(results)<len(matches) else None,'results':results,'holdings_linkage':snapshot['holdings_linkage'],'interpretation':'Exact retrieval of saved research questions and evidence references only. A company entry is not a confirmed event, signal, ranking or independent training sample.','no_match_meaning':'No matching entry in this specific 108-company reviewed snapshot and selected category, not no company, no financing, no insider activity or no disclosure. An empty page can also mean the requested offset is beyond the matches.','link_semantics':'Links navigate existing app views and published source artifacts. Local hashes verify the retained artifact versions; no network request checks current URL content or availability. SEC original-link qualifications remain in each source.','model_inference_performed':False,'provider_requests_made':False,'training_ready':False,'execution_ready':False}

def main(argv=None):
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--root',default=str(Path(__file__).resolve().parents[1]))
 parser.add_argument('--cik');parser.add_argument('--category',choices=CATEGORIES)
 parser.add_argument('--limit',type=int,default=20);parser.add_argument('--offset',type=int,default=0)
 args=parser.parse_args(argv)
 try:response=retrieve(**vars(args))
 except (ValueError,KeyError,TypeError,OSError):
  print('Retrieval failed: invalid query or unavailable/mismatched reviewed evidence. No result inferred.',file=sys.stderr);return 2
 print(json.dumps(response,indent=2));return 0
if __name__=='__main__':raise SystemExit(main())
