"""Generate public dashboard from honest paper state and public-source research."""
from pathlib import Path
from datetime import datetime,timezone
import json
from build_research_report import build as build_research_report
from scan_status import summarize_scan
from price_status import summarize_price_status
ROOT=Path(__file__).resolve().parent.parent

def build(root=ROOT, *, preserve_research_report=False):
 if preserve_research_report:
  # Validate before any output write; never regenerate a held research artifact.
  data_report=(root/'data/research_report.json').read_bytes()
  web_report=(root/'web/research_report.json').read_bytes()
  if data_report!=web_report or not isinstance(json.loads(data_report),dict):raise ValueError('Saved research report copies missing, invalid or different')
 ledger=json.loads((root/'data/paper_ledger.json').read_text());reviews=json.loads((root/'data/filing_reviews.json').read_text())['records']
 state={'generated_at':datetime.now(timezone.utc).isoformat(),'mode':'paper','window':{'start':'2026-11-16','end':'2026-11-20','timezone':'America/New_York'},'feeds':[{'name':'SEC filings','status':'manual_verified_sample','as_of':'2026-11-14T16:51:10Z','detail':'Nine official daily indexes, eleven original full filings. Ten-issuer bounded sample reviewed; not exhaustive live coverage.'},{'name':'Price and liquidity','status':'disconnected','as_of':None,'detail':'No authorized reliable price feed connected. Daily closes are not automatically auction prices.'},{'name':'Trading halts','status':'not_connected','as_of':None,'detail':'Unknown halt status blocks entries.'},{'name':'Paper execution','status':'disabled','as_of':None,'detail':'No orders until all source, calendar, liquidity, auction and halt gates pass.'}], 'portfolio':{'initial_cash':ledger['initial_cash'],'cash':ledger['cash'],'equity':None,'realized_pnl':None,'unrealized_pnl':None,'positions':ledger['positions'],'trades':ledger['fills'],'orders':ledger['orders'],'currency':'USD'},'discovery':{'filing_paths':4076,'issuers':3066,'index_days':9,'archived_filings':11,'reviewed_filings':10,'eligible_signals':0},'signals':[{'ticker':None,'issuer':r['issuer'],'family':r['status'],'status':r['status'],'reason':r['reason'],'source_url':r['source_url'],'source_published_at':None,'retrieved_at':r['reviewed_utc'],'accession':r['accession'],'eligible':False} for r in reviews], 'blockers':['Price/volume/auction feed not connected or validated','Historical halt evidence not connected','Three source reviews need further financial or guidance comparison','Live schedule not activated; browser refresh only reloads saved evidence','Paper book is disabled and empty; no results or guaranteed returns']}
 # Sanitized verification and collection metadata only; never read private vendor data here.
 price_status=root/'data/price_feed_status.json'
 if price_status.exists():
  state['feeds'][1].update(summarize_price_status(json.loads(price_status.read_text())))
  state['blockers'][0]='Historical daily snapshots were reviewed; current storage and redistribution eligibility must be verified before further collection; corporate-action, halt and execution validation remain incomplete'
 scanpath=root/'data/latest_scan.json'
 if scanpath.exists():
  scan=json.loads(scanpath.read_text());state['feeds'][0].update(status='snapshot_only',as_of=scan['finished_at'],detail=f"{scan['successful_issuers']}/{scan['configured_issuers']} configured issuer metadata feeds checked; {len(scan['events'])} filing discoveries, not eligible signals. Trial-week schedule configured; not continuous or realtime.")
  scan_status=summarize_scan(scan)
  state['activity']=[{'at':scan['finished_at'],'detail':scan_status['activity']}]
 if (root/'data/scan_schedule.json').exists():
  state['blockers']=[x for x in state['blockers'] if not x.startswith('Live schedule')]
  state['blockers'].append(summarize_scan(scan if scanpath.exists() else None)['schedule_note'])
 # Public event retrieval timestamps refer to actual source reads, not review completion.
 provenance=json.loads((root/'data/provenance.json').read_text())['sources']
 byhash={r.get('sha256'):r.get('retrieved_utc') for r in provenance if r.get('sha256')}
 for signal,review in zip(state['signals'],reviews):
  signal['retrieved_at']=byhash.get(review['source_sha256']);signal['reviewed_at']=review['reviewed_utc']
 if not preserve_research_report:
  report=build_research_report(root, generated_at=state['generated_at'])
  report_json=json.dumps(report,indent=2)+'\n'
  (root/'data/research_report.json').write_text(report_json)
  (root/'web/research_report.json').write_text(report_json)
 # Display only explicit aggregate checkpoints, never private originals or vendor prices.
 updates=[]
 for filename,mode,clock,fields,title,note in [
  ('filing_comparisons.json','RETROSPECTIVE_REPORTED_PAIR_NOT_QUALIFIED','analysis_utc',[('reported_comparisons','source events'),('reported_metric_pairs','metric pairs')],'Reported financial comparisons','Multiple metrics from one event are not independent samples. Historical availability and outcomes remain unresolved.'),
  ('financial_admission_rehearsal.json','SOURCE_GROUNDED_FINANCIAL_ADMISSION_REHEARSAL','computed_at',[('rows','reviewed cases'),('reported_pair_rows','narrative comparison rows'),('explicit_same_event_bundles','explicit same-event bundles'),('positive_dividend_declaration_rows','dividend declarations')],'Source-to-fact rehearsal','Saved source analysis, not re-extraction in this build. Declaration dates do not establish ex-dates or entitlement. Unknown facts remain unknown.')]:
  path=root/'data'/filename
  if not path.exists():continue
  value=json.loads(path.read_text())
  if value.get('mode')!=mode:raise ValueError('Unexpected research artifact mode')
  stamp=value.get(clock);datetime.fromisoformat(stamp)
  counts=value.get('counts',value);metrics=[]
  for key,label in fields:
   n=counts.get(key)
   if type(n) is not int or n<0:raise ValueError('Invalid research artifact count')
   metrics.append({'label':label,'value':n})
  updates.append({'title':title,'as_of':stamp,'metrics':metrics,'note':note,'url':'https://github.com/JeremyHennessy/CatalystRadar/blob/main/data/'+filename})
 state['research_updates']=updates
 (root/'web/app-data.json').write_text(json.dumps(state,indent=2));return state
if __name__=='__main__':
 import argparse
 parser=argparse.ArgumentParser()
 parser.add_argument('--preserve-research-report',action='store_true',help='Refresh dashboard only; keep both research reports byte-for-byte unchanged')
 args=parser.parse_args()
 build(preserve_research_report=args.preserve_research_report)
 print('Dashboard generated from saved public evidence; no scans or trades executed. Research reports '+('preserved unchanged.' if args.preserve_research_report else 'regenerated.'))
