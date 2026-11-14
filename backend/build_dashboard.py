"""Generate public dashboard from honest paper state and public-source research."""
from pathlib import Path
from datetime import datetime,timezone
import json
from build_research_report import build as build_research_report
ROOT=Path(__file__).resolve().parent.parent

def build(root=ROOT):
 ledger=json.loads((root/'data/paper_ledger.json').read_text());reviews=json.loads((root/'data/filing_reviews.json').read_text())['records']
 state={'generated_at':datetime.now(timezone.utc).isoformat(),'mode':'paper','window':{'start':'2026-11-16','end':'2026-11-20','timezone':'America/New_York'},'feeds':[{'name':'SEC filings','status':'manual_verified_sample','as_of':'2026-11-14T16:51:10Z','detail':'Nine official daily indexes, eleven original full filings. Ten-issuer bounded sample reviewed; not exhaustive live coverage.'},{'name':'Price and liquidity','status':'disconnected','as_of':None,'detail':'No authorized reliable price feed connected. Daily closes are not automatically auction prices.'},{'name':'Trading halts','status':'not_connected','as_of':None,'detail':'Unknown halt status blocks entries.'},{'name':'Paper execution','status':'disabled','as_of':None,'detail':'No orders until all source, calendar, liquidity, auction and halt gates pass.'}], 'portfolio':{'initial_cash':ledger['initial_cash'],'cash':ledger['cash'],'equity':None,'realized_pnl':None,'unrealized_pnl':None,'positions':ledger['positions'],'trades':ledger['fills'],'orders':ledger['orders'],'currency':'USD'},'discovery':{'filing_paths':4076,'issuers':3066,'index_days':9,'archived_filings':11,'reviewed_filings':10,'eligible_signals':0},'signals':[{'ticker':None,'issuer':r['issuer'],'family':r['status'],'status':r['status'],'reason':r['reason'],'source_url':r['source_url'],'source_published_at':None,'retrieved_at':r['reviewed_utc'],'accession':r['accession'],'eligible':False} for r in reviews], 'blockers':['Price/volume/auction feed not connected or validated','Historical halt evidence not connected','Three source reviews need further financial or guidance comparison','Live schedule not activated; browser refresh only reloads saved evidence','Paper book is disabled and empty; no results or guaranteed returns']}
 # Sanitized one-time verification metadata only; never read private vendor data here.
 price_status=root/'data/price_feed_status.json'
 if price_status.exists():
  p=json.loads(price_status.read_text())
  expected={'status','verified_at','symbols_tested','rows_per_symbol','first_session','last_session','execution_ready','scheduled_collection_verified'}
  if set(p)!=expected or p['status']!='private_daily_snapshot_tested' or p['execution_ready'] is not False or p['scheduled_collection_verified'] is not False:raise ValueError('unreviewed price status schema')
  if type(p['symbols_tested']) is not int or p['symbols_tested']!=11 or type(p['rows_per_symbol']) is not int or p['rows_per_symbol']!=100:raise ValueError('unreviewed coverage change')
  for key in ('verified_at','first_session','last_session'):datetime.fromisoformat(p[key])
  state['feeds'][1].update(status='snapshot_only',as_of=p['verified_at'],detail='Private daily-price collection tested for 11 symbols, 100 observations each through November 13, 2026. Raw, unadjusted daily data only; not realtime or execution-ready. Scheduled collection not yet verified.')
  state['blockers'][0]='Private daily histories are stored; corporate-action, halt and execution validation remain incomplete'
 scanpath=root/'data/latest_scan.json'
 if scanpath.exists():
  scan=json.loads(scanpath.read_text());state['feeds'][0].update(status='snapshot_only',as_of=scan['finished_at'],detail=f"{scan['successful_issuers']}/{scan['configured_issuers']} configured issuer metadata feeds checked; {len(scan['events'])} filing discoveries, not eligible signals. Trial-week schedule configured; not continuous or realtime.")
  state['activity']=[{'at':scan['finished_at'],'detail':f"Manual SEC poll: {len(scan['events'])} metadata discoveries; zero orders."}]
 if (root/'data/scan_schedule.json').exists():
  state['blockers']=[x for x in state['blockers'] if not x.startswith('Live schedule')]
  state['blockers'].append('Trial-week SEC metadata schedule configured; successful scheduled execution not yet verified' if not scanpath.exists() or scan.get('github_event_name')!='schedule' else 'SEC metadata polling has run on schedule; this is not an executable price feed')
 # Public event retrieval timestamps refer to actual source reads, not review completion.
 provenance=json.loads((root/'data/provenance.json').read_text())['sources']
 byhash={r.get('sha256'):r.get('retrieved_utc') for r in provenance if r.get('sha256')}
 for signal,review in zip(state['signals'],reviews):
  signal['retrieved_at']=byhash.get(review['source_sha256']);signal['reviewed_at']=review['reviewed_utc']
 report=build_research_report(root, generated_at=state['generated_at'])
 report_json=json.dumps(report,indent=2)+'\n'
 (root/'data/research_report.json').write_text(report_json)
 (root/'web/research_report.json').write_text(report_json)
 (root/'web/app-data.json').write_text(json.dumps(state,indent=2));return state
if __name__=='__main__':build();print('Dashboard generated from saved public evidence; no scans or trades executed.')
