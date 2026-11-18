"""Deterministic static delivery of existing verified exact-CIK dossiers."""
import argparse,hashlib,json
from pathlib import Path
from research_dossier import dossier,SECTIONS
from research_retrieval import load_verified
PAGE_SIZE=5
BASE='web/company-dossiers/v1/'
MAX_PAGE=500000
MAX_TOTAL=8000000

def encode(obj):return (json.dumps(obj,ensure_ascii=True,sort_keys=True,separators=(',',':'))+'\n').encode()
def digest(raw):return hashlib.sha256(raw).hexdigest()

def build(root):
 root=Path(root);snapshot=load_verified(root)
 ciks=[r['issuer_cik'] for r in snapshot['records']]
 if len(ciks)!=108 or len(set(ciks))!=len(ciks):raise ValueError('cohort changed')
 payloads={};companies=[];common=None
 for cik in sorted(ciks):
  company={'issuer_cik':cik,'sections':{}}
  for section in SECTIONS:
   first=dossier(root,cik,section,PAGE_SIZE,0)
   if first['status']!='COMPANY_IN_REVIEWED_SNAPSHOT':raise ValueError('company mismatch')
   shared={k:first[k] for k in ('snapshot','holdings_linkage','interpretation','model_inference_performed','provider_requests_made','training_ready','execution_ready')}
   if common is None:common=shared
   elif common!=shared:raise ValueError('shared context changed')
   selected=first['selected_section'];total=selected['total_source_records']
   meta={k:selected[k] for k in ('coverage','source_key','total_source_records')};meta['pages']=[]
   if total is not None and (type(total)is not int or not 0<=total<=1000):raise ValueError('count bound')
   for offset in range(0,total or 0,PAGE_SIZE):
    result=first if offset==0 else dossier(root,cik,section,PAGE_SIZE,offset)
    current=result['selected_section']
    if any(current[k]!=meta[k] for k in ('coverage','source_key','total_source_records')):raise ValueError('section changed')
    if result['snapshot']!=common['snapshot'] or result['query']!={'issuer_cik':cik,'section':section,'limit':PAGE_SIZE,'offset':offset}:raise ValueError('page identity changed')
    expected=min(PAGE_SIZE,total-offset)
    if current['returned_records']!=expected or len(current['records'])!=expected or current['next_offset']!=(offset+expected if offset+expected<total else None):raise ValueError('pagination mismatch')
    page={'schema_version':1,'issuer_cik':cik,'section':section,'snapshot':common['snapshot'],'selected_section':current}
    raw=encode(page)
    if len(raw)>MAX_PAGE:raise ValueError('page too large')
    path=BASE+f'{cik}/{section}-{offset:04d}.json'
    if path in payloads:raise ValueError('duplicate path')
    payloads[path]=raw
    meta['pages'].append({'path':path,'bytes':len(raw),'sha256':digest(raw),'offset':offset,'returned_records':expected,'next_offset':current['next_offset']})
   if not total and (selected['records'] or selected['returned_records'] or selected['next_offset'] is not None):raise ValueError('empty scope contradiction')
   company['sections'][section]=meta
  companies.append(company)
 # Recheck all source bytes through the existing verification/rebuild gate after projection.
 if load_verified(root)!=snapshot:raise ValueError('source changed during build')
 manifest={'schema_version':1,'page_size':PAGE_SIZE,'company_count':len(companies),'companies':companies,'sources':snapshot['sources'],**common,
 'delivery_limits':{'max_page_bytes':MAX_PAGE,'max_total_bytes':MAX_TOTAL},
 'absence_policy':'No page is generated for assessed zero or unassessed null. Preserve coverage and null versus zero; an unknown CIK is outside this fixed snapshot.',
 'consumer_contract':'Pin this manifest, validate schema and unique CIK/section/page membership, then verify selected page bytes/SHA256 and exact identity, snapshot, coverage, totals and pagination before rendering. Render source strings as inert text; only verified public records are included.'}
 raw=encode(manifest)
 if len(raw)>500000:raise ValueError('manifest too large')
 payloads[BASE+'index.json']=raw
 if len(payloads)>1000 or sum(map(len,payloads.values()))>MAX_TOTAL:raise ValueError('package bound')
 return payloads

def save(payloads,destination):
 destination=Path(destination)
 destination.mkdir(parents=True,exist_ok=False)
 marker=destination/'INCOMPLETE';marker.write_text('Static dossier build is incomplete. Do not publish.\n')
 for path,raw in payloads.items():
  if not path.startswith(BASE) or '..' in Path(path).parts:raise ValueError('unsafe output path')
  target=destination/path;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
  if target.read_bytes()!=raw:raise ValueError('persistence mismatch')
 complete={p:{'bytes':len(b),'sha256':digest(b)} for p,b in payloads.items()}
 (destination/'COMPLETE.json').write_bytes(encode(complete));marker.unlink()

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',default=str(Path(__file__).resolve().parents[1]));p.add_argument('--destination',required=True);a=p.parse_args();save(build(a.root),a.destination)
if __name__=='__main__':main()
