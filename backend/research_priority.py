"""Retrospective documentary research priorities, never predicted trades or returns."""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from research_scanner import build_package, encoded, OUTPUT

CUTOFF = '2026-11-19T18:57:49Z'
INDEX_SHA = '6c11b89a1c133c0d2a8f6da7ca3726ff9ef4da14dbe6564c16015c090e1e7182'
ELIGIBLE = {'REPORTED_REVENUE', 'REPORTED_LOSS', 'REPORTED_FINANCING', 'REPORTED_EXCHANGE', 'REPORTED_VOTES'}
BASE = 'web/trade-ideas/v1/'
RUBRIC = {
 'schema_version': 1, 'id': 'documentary-research-priority-v1',
 'declared_cutoff_utc': CUTOFF,
 'purpose': 'Documentary investigation priority only; no likelihood, direction, expected return or trade conviction.',
 'selection': 'All 905 records of the pinned released scanner. Only source-reviewed financial/event categories eligible. Exact same registrant-set/accession financial findings consolidated as one review thesis; not economic-event deduplication.',
 'weights': {'source_review':40,'accession_citation':20,'exact_period_context':20,'declared_filing_age':20},
 'rules': {'source_review':'1 only for SOURCE_REVIEWED_WITH_LIMITS; original narrow extraction, not truth or tradability.',
 'accession_citation':'1 if one or more exact source accession citations exist.',
 'exact_period_context':'1 if explicit source_exact_period starts and ends exist; otherwise null, not zero or assumed comparable.',
 'declared_filing_age':'1 for explicit source filing date 0–30 days before cutoff; 0.5 for31–90;0 older; missing null. Filing age is not novelty, first-public or availability.',
 'unknowns':'Unknown factor is null with null points. Score sums only known points, never renormalized. Coverage is separate. Null market data does not become zero.',
 'ties':'Descending score, newest explicit filing date (unknown last), sorted exact registrant CIK set, then stable thesis ID; not expected performance.',
 'consolidation':'Exact sorted issuer CIK set plus exact accession set; revenue/loss share FINANCIAL family. Other source categories distinct.',
 'clock_policy':'Retrospective build at fixed cutoff, not historical known-at-time replay. Eligible/scored record clocks must not exceed cutoff except explicitly planned future dates. Original source objects and clocks preserved; no assumed first-public.'},
 'excluded_contexts':['FILER_IDENTITY','SECURITY_CONTEXT','ORIGINAL_REVIEW_REQUIRED'],
 'not_evaluated_extensions':['TXMD companion 10-Q','COHR newer filing','WOR newer filing'],
 'execution_ready':False, 'training_ready':False
}

def sha(raw): return hashlib.sha256(raw).hexdigest()
def dt(s): return datetime.fromisoformat(s.replace('Z','+00:00')).astimezone(timezone.utc)
def pin(path, raw): return {'path':path,'bytes':len(raw),'sha256':sha(raw)}
def group_key(r):
 family='FINANCIAL' if r['category'] in {'REPORTED_REVENUE','REPORTED_LOSS'} else r['category']
 return '|'.join([family,','.join(sorted(a['issuer_cik'] for a in r['issuer_associations'])),','.join(sorted(r['source_accessions']))])
def filing_label(r):
 for c in r['clocks']:
  if c['meaning'] in {'filing_date_as_reported','filing_date_as_filed_YYYYMMDD'}:
   value=c['value_as_reported']
   return datetime.strptime(value,'%Y%m%d').date().isoformat() if len(value)==8 and value.isdigit() else dt(value).date().isoformat()
 return None
def facts(r, cutoff):
 filing=[]; periods=[]
 for c in r['clocks']:
  kind=c['meaning']; value=c['value_as_reported']
  if kind=='source_exact_period':
   start=datetime.fromisoformat(value['start']);end=datetime.fromisoformat(value['end'])
   if start>end or end.date()>cutoff.date(): raise ValueError('invalid exact period')
   periods.append(value)
  elif isinstance(value,str):
   try: day=datetime.strptime(value,'%Y%m%d').date() if len(value)==8 and value.isdigit() else dt(value).date()
   except ValueError: raise ValueError('invalid source clock')
   if (day>cutoff.date() or ('T' in value and dt(value)>cutoff)) and kind!='planned_redemption_not_completion': raise ValueError('source clock after cutoff')
   if kind in {'filing_date_as_reported','filing_date_as_filed_YYYYMMDD'}:filing.append(day)
 if len(set(filing))>1: raise ValueError('conflicting filing dates')
 age=(cutoff.date()-filing[0]).days if filing else None
 return [
  {'id':'source_review','weight':40,'value':1,'points':40,'meaning':RUBRIC['rules']['source_review']},
  {'id':'accession_citation','weight':20,'value':1,'points':20,'meaning':RUBRIC['rules']['accession_citation']},
  {'id':'exact_period_context','weight':20,'value':1 if periods else None,'points':20 if periods else None,'meaning':RUBRIC['rules']['exact_period_context']},
  {'id':'declared_filing_age','weight':20,'value':None if age is None else 1 if age<=30 else .5 if age<=90 else 0,'points':None if age is None else 20 if age<=30 else 10 if age<=90 else 0,'age_days':age,'meaning':RUBRIC['rules']['declared_filing_age']}]

def project(index, cutoff=CUTOFF):
 if cutoff!=CUTOFF:raise ValueError('versioned cutoff immutable')
 end=dt(cutoff); decisions=[]; groups={}; seen=set()
 for r in index['records']:
  if r['id'] in seen:raise ValueError('duplicate source record')
  seen.add(r['id'])
  reason=None
  if r['evidence_state']!='SOURCE_REVIEWED_WITH_LIMITS':reason='ORIGINAL_REVIEW_REQUIRED'
  elif r['category'] not in ELIGIBLE:reason='DOCUMENTARY_CONTEXT_NOT_FINANCIAL_EVENT'
  if reason:
   decisions.append({'source_id':r['id'],'decision':'EXCLUDED','reason':reason,'source_ref':r['source_ref']});continue
  if r['execution_ready'] is not False or r['training_ready'] is not False or not r['source_accessions']:raise ValueError('source qualification or citation')
  factors=facts(r,end)
  groups.setdefault(group_key(r),[]).append((r,factors))
 ideas=[]
 for key,rows in sorted(groups.items()):
  rows.sort(key=lambda x:(-sum(f['points'] or 0 for f in x[1]),x[0]['id']))
  r,factors=rows[0]; ident='research-'+sha(key.encode())[:24]
  for source,_ in rows:decisions.append({'source_id':source['id'],'decision':'INCLUDED_IN_THESIS','thesis_id':ident,'source_ref':source['source_ref']})
  ideas.append({'id':ident,'title':r['title'],'issuer_associations':r['issuer_associations'],'category':r['category'],
   'status':'WATCH','actionability':'UNPRICED_NOT_ACTIONABLE','research_priority_score':sum(f['points'] or 0 for f in factors),'factors':factors,
   'coverage':{'known_factor_weight':sum(f['weight'] for f in factors if f['value'] is not None),'total_factor_weight':100,'current_price':None,'security_mapping':None,'corporate_action_continuity':None,'first_public_verified':None,'return_outcome':None,'expected_return':None},
   'declared_filing_date':filing_label(r),'source_clocks':r['clocks'],'source_ref':r['source_ref'],'source_records':[x[0] for x in rows],
   'source_links':[{'label':x[0]['title'],'path':'web/'+x[0]['investigation_path'],'source_id':x[0]['id']} for x in rows],
   'summary':r['summary'],'blockers':['No verified current executable price or liquidity.','Halt status and actual trading-session eligibility are unknown.','Effective-dated security mapping and corporate-action continuity are unknown.','CIK is registrant identity, not security mapping.','No qualified outcome or expected-return model.','First-public timing and event novelty unverified.']+r['unknowns'],
   'next_action':r['next_action'],'execution_ready':False,'training_ready':False})
 ideas.sort(key=lambda x:(-x['research_priority_score'],-int((x['declared_filing_date'] or '0000-00-00').replace('-','')),','.join(sorted(a['issuer_cik'] for a in x['issuer_associations'])),x['id']))
 for rank,x in enumerate(ideas,1):x['rank']=rank
 return {'schema_version':1,'cutoff_utc':cutoff,'mode':'RETROSPECTIVE_RESEARCH_PRIORITY','heading':'Top 10 research priorities, not actionable trades',
  'actionability':'UNPRICED_NOT_ACTIONABLE','rubric_id':RUBRIC['id'],'counts':{'evaluated':len(seen),'eligible_source_records':sum(len(x) for x in groups.values()),'excluded':sum(d['decision']=='EXCLUDED' for d in decisions),'consolidated_theses':len(ideas),'returned':min(10,len(ideas)),'actionable_trades':0,'paper_trades_placed':0},
  'ideas':ideas[:10],'all_scored_candidates':[{'id':x['id'],'rank':x['rank'],'research_priority_score':x['research_priority_score'],'factors':x['factors'],'coverage':x['coverage'],'source_ids':[r['id'] for r in x['source_records']]} for x in ideas],'candidate_decisions':sorted(decisions,key=lambda x:x['source_id']),
  'scope':index['coverage'],'limitations':['Retrospective snapshot of a selected released evidence corpus, not market-wide screening or a historical point-in-time test.','No source record is an independent economic event. Same issuer can have distinct obligations; dual filers remain distinct.','Five or fewer than ten entries is not missing data silently padded with weaker candidates.','No probabilities, price targets, allocations, order instructions or expected return.'],
  'not_evaluated_extensions':RUBRIC['not_evaluated_extensions'],'source_pins':index['sources'],'execution_ready':False,'training_ready':False,'provider_requests_made':False}

def build(root):
 root=Path(root);index,payloads=build_package(root)
 raw=(root/OUTPUT).read_bytes()
 if sha(raw)!=INDEX_SHA or raw!=payloads[OUTPUT]:raise ValueError('scanner pin or exact rebuild mismatch')
 for path,expected in payloads.items():
  if (root/path).read_bytes()!=expected:raise ValueError('detail shard changed')
 result=project(index);result['input_snapshot']=pin(OUTPUT,raw)
 rubric_raw=encoded(RUBRIC); result['rubric_sha256']=sha(rubric_raw)
 raw=encoded(result);path=BASE+'snapshots/'+sha(raw)+'.json'
 latest={'schema_version':1,'snapshot':pin(path,raw),'rubric':pin(BASE+'rubric.json',rubric_raw),'execution_ready':False,'training_ready':False}
 return {path:raw,BASE+'rubric.json':rubric_raw,BASE+'latest.json':encoded(latest)}

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',default=str(Path(__file__).resolve().parents[1]));p.add_argument('--write',action='store_true');a=p.parse_args();out=build(a.root)
 for path,raw in out.items():
  if a.write:
   dest=Path(a.root)/path;dest.parent.mkdir(parents=True,exist_ok=True)
   if dest.exists() and dest.read_bytes()!=raw:raise ValueError('immutable output collision')
   dest.write_bytes(raw)
 print(json.dumps({p:pin(p,b) for p,b in out.items()},sort_keys=True))
if __name__=='__main__':main()
