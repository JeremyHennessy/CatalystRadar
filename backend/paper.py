"""Pure hypothetical accounting. No network/broker integration; disabled by default."""
from copy import deepcopy
from datetime import datetime,date,time,timezone
from decimal import Decimal,ROUND_FLOOR
from zoneinfo import ZoneInfo
import math,json,hashlib
from pathlib import Path
from urllib.parse import urlparse
# Empty in production: no price provider has passed admission. Tests inject synthetic fixtures.
APPROVED_PROVIDERS={}
EVIDENCE_ROOT=Path(__file__).resolve().parent.parent/'.data/market'
def clock():return datetime.now(timezone.utc)
def enabled(ledger):
 if ledger.get('simulation_enabled') is not True or not APPROVED_PROVIDERS:raise ValueError('paper execution disabled: no approved provider')

ET=ZoneInfo('America/New_York');START=date(2026,11,16);END=date(2026,11,20)
def num(x):
 if type(x) not in (int,float,str):raise ValueError('invalid numeric')
 d=Decimal(str(x))
 if not d.is_finite():raise ValueError('nonfinite numeric')
 return d
def instant(x):
 d=datetime.fromisoformat(x.replace('Z','+00:00'))
 if d.tzinfo is None:raise ValueError('timezone required')
 return d

def quote(evidence,ticker,session):
 provider=evidence.get('provider_id')
 if provider not in APPROVED_PROVIDERS:raise ValueError('unapproved price provider')
 sha=evidence.get('source_sha256','')
 if len(sha)!=64 or any(c not in '0123456789abcdef' for c in sha):raise ValueError('invalid evidence hash')
 path=(EVIDENCE_ROOT/evidence['source_path']).resolve()
 if EVIDENCE_ROOT.resolve() not in path.parents:raise ValueError('evidence path outside archive')
 raw=path.read_bytes()
 if hashlib.sha256(raw).hexdigest()!=sha:raise ValueError('evidence hash mismatch')
 q=json.loads(raw)
 if q.get('ticker')!=ticker or q.get('session')!=session:raise ValueError('quote security/session mismatch')
 actual=urlparse(q.get('source_url',''));expected=urlparse(APPROVED_PROVIDERS[provider]);prefix=expected.path.rstrip('/')+'/'
 if q.get('provider_id')!=provider or actual.scheme!='https' or actual.hostname!=expected.hostname or (actual.port or 443)!=(expected.port or 443) or actual.username or actual.password or not actual.path.startswith(prefix):raise ValueError('provider URL mismatch')
 if instant(q['observed_utc'])>clock():raise ValueError('future evidence')
 if evidence.get('close') is not None and num(evidence['close'])!=num(q['close']):raise ValueError('caller price differs from archived evidence')
 return q

def plan(ledger,event,freeze_utc,session):
 """Freeze a paper LOC order only after explicit independently verified gates."""
 enabled(ledger)
 day=date.fromisoformat(session);freeze=instant(freeze_utc).astimezone(ET)
 if abs((instant(freeze_utc)-clock()).total_seconds())>1:raise ValueError('freeze must equal authoritative run clock')
 if not START<=day<END:raise ValueError('entries only Monday through Thursday of fixed trial')
 if freeze.date()!=day or freeze.time()>time(8):raise ValueError('must freeze by08:00ET on target day')
 if event.get('status')!='OBSERVE':raise ValueError('no verified observation')
 required=('coverage_complete','price_entitlement_verified','halt_status_verified','auction_data_verified','corporate_actions_verified','eligibility_review_passed')
 if any(event.get(k) is not True for k in required):raise ValueError('unmet evidence gate')
 if not event.get('evidence_hashes') or not all(len(x)==64 and all(c in '0123456789abcdef' for c in x) for x in event['evidence_hashes']):raise ValueError('missing provenance hashes')
 if instant(event['knowledge_utc'])>instant(freeze_utc):raise ValueError('future knowledge')
 if event.get('halted') is not False:raise ValueError('unknown or halted')
 ticker=event['ticker'];eid=event['event_id']
 if any(o['event_id']==eid for o in ledger['orders']):raise ValueError('event already planned')
 active=[o for o in ledger['orders'] if o['status'] in ('RESERVED','PENDING_PRICE')]
 if any(p['ticker']==ticker for p in ledger['positions']) or any(o['ticker']==ticker for o in active):raise ValueError('issuer exposure exists')
 if len(ledger['positions'])+len(active)>=5:raise ValueError('five slot cap')
 prior_quote=quote(event['prior_evidence'],ticker,event['prior_session'])
 if instant(prior_quote['observed_utc'])>instant(event['knowledge_utc']):raise ValueError('knowledge predates market evidence')
 prior=num(prior_quote['close'])
 if prior!=num(event['prior_close']):raise ValueError('prior close differs from archived evidence')
 if prior<5:raise ValueError('price floor')
 if event.get('prior_session')!=event.get('expected_prior_session') or not event.get('prior_session'):raise ValueError('session mismatch')
 reserved=sum((num(o['reserved']) for o in active),Decimal(0));budget=min(Decimal(500),num(ledger['cash'])-reserved)
 limit=(prior*Decimal('1.03')).quantize(Decimal('.01'),rounding=ROUND_FLOOR);q=int(budget/(limit*Decimal('1.001')))
 if q<1:raise ValueError('insufficient cash')
 result=deepcopy(ledger);result['orders'].append({'id':eid+':'+session,'event_id':eid,'ticker':ticker,'session':session,'freeze_utc':freeze_utc,'quantity':q,'limit':str(limit),'reserved':str(Decimal(q)*limit*Decimal('1.001')),'status':'RESERVED','exit_session':END.isoformat(),'evidence_hashes':event['evidence_hashes']});return result

def settle_entry(ledger,order_id,evidence):
 enabled(ledger)
 result=deepcopy(ledger);order=next(o for o in result['orders'] if o['id']==order_id)
 if order['status'] not in ('RESERVED','PENDING_PRICE'):raise ValueError('already resolved')
 evidence={**quote(evidence,order['ticker'],order['session']),'source_sha256':evidence['source_sha256']}
 if evidence.get('official_auction_verified') is not True or evidence.get('halt_status_verified') is not True or evidence.get('corporate_actions_verified') is not True or not evidence.get('source_sha256'):
  order['status']='PENDING_PRICE';return result
 observed=instant(evidence['observed_utc']);closing=datetime.combine(date.fromisoformat(order['session']),time(16),ET)
 if observed<closing:raise ValueError('price observed before target close')
 if evidence.get('halted') is not False or evidence.get('auction_occurred') is not True:
  order.update(status='UNFILLED',reason='halt or no auction');return result
 price=num(evidence['close']);cost=price*order['quantity']*Decimal('1.001')
 if price<=0:raise ValueError('invalid close')
 if price>num(order['limit']) or cost>num(order['reserved']):order.update(status='UNFILLED',reason='limit/cash gate');return result
 result['cash']=float(num(result['cash'])-cost);order['status']='FILLED'
 result['fills'].append({'order_id':order_id,'session':order['session'],'ticker':order['ticker'],'quantity':order['quantity'],'price':str(price),'total_cost':str(cost),'model':'IDEALIZED_PAPER_AUCTION_NOT_ACTUAL_EXECUTION','source_sha256':evidence['source_sha256'],'observed_utc':evidence['observed_utc']})
 result['positions'].append({'ticker':order['ticker'],'quantity':order['quantity'],'entry_cost':str(cost),'entry_session':order['session'],'exit_session':order['exit_session']});return result

def plan_exit(ledger,ticker,freeze_utc):
 enabled(ledger)
 freeze=instant(freeze_utc).astimezone(ET)
 if abs((instant(freeze_utc)-clock()).total_seconds())>1:raise ValueError('exit freeze must equal authoritative run clock')
 if freeze.date()!=END or freeze.time()>time(8):raise ValueError('trial exit must be frozen by Friday08:00ET')
 result=deepcopy(ledger);position=next(p for p in result['positions'] if p['ticker']==ticker)
 if position.get('exit_order'):raise ValueError('exit already planned')
 position['exit_order']={'quantity':position['quantity'],'session':END.isoformat(),'freeze_utc':freeze_utc,'status':'PLANNED'};return result

def settle_exit(ledger,ticker,evidence):
 enabled(ledger)
 result=deepcopy(ledger);position=next(p for p in result['positions'] if p['ticker']==ticker);order=position.get('exit_order')
 if not order or order['status'] not in ('PLANNED','PENDING_PRICE'):raise ValueError('no unresolved frozen exit')
 evidence={**quote(evidence,ticker,END.isoformat()),'source_sha256':evidence['source_sha256']}
 gates=('official_auction_verified','halt_status_verified','no_corporate_action_since_entry')
 if any(evidence.get(x) is not True for x in gates) or not evidence.get('source_sha256'):
  order['status']='PENDING_PRICE';result['status']='TRIAL_END_UNRESOLVED_POSITION';return result
 if instant(evidence['observed_utc'])<datetime.combine(END,time(16),ET):raise ValueError('premature exit evidence')
 if evidence.get('halted') is not False or evidence.get('auction_occurred') is not True:
  order['status']='UNFILLED';result['status']='TRIAL_END_UNRESOLVED_POSITION';return result
 price=num(evidence['close'])
 if price<=0:raise ValueError('invalid exit price')
 proceeds=Decimal(order['quantity'])*price*Decimal('.999');pnl=proceeds-num(position['entry_cost'])
 result['cash']=float(num(result['cash'])+proceeds)
 result['fills'].append({'side':'SELL','ticker':ticker,'session':END.isoformat(),'quantity':order['quantity'],'price':str(price),'net_proceeds':str(proceeds),'realized_pnl':str(pnl),'model':'IDEALIZED_PAPER_AUCTION_NOT_ACTUAL_EXECUTION','source_sha256':evidence['source_sha256'],'observed_utc':evidence['observed_utc']})
 result['positions'].remove(position);return result
