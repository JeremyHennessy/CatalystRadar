"""Prospective private paper ledger runner. Production admission adapters EMPTY.
No network or brokerage access. No production freezes/fills until independent feed
and private-commit adapters are admitted. Never use this output as actual execution.
"""
from copy import deepcopy
from datetime import datetime,time,timezone
from decimal import Decimal
from zoneinfo import ZoneInfo
import json,hashlib,os,fcntl
from pathlib import Path
from close_proxy import size,cost_scenario,SLIPPAGE,FEE,MODEL,instant,amount
ET=ZoneInfo('America/New_York')
ENTRY_DAYS=('2026-11-16','2026-11-17','2026-11-18','2026-11-19')
EXIT_DAY='2026-11-20'
# Adapter returns source-derived reviewed facts, not user-supplied truth booleans.
# Required: calendar, candidate, close, interval, committed_freeze.
ADAPTERS={}
def clock():return datetime.now(timezone.utc)
def canonical(x):return json.dumps(x,sort_keys=True,separators=(',',':')).encode()
def digest(x):return hashlib.sha256(canonical(x)).hexdigest()
def initial():return {'version':1,'model':MODEL,'cash':'500','initial_cash':'500','orders':[],'positions':[],'fills':[],'decisions':[],'comparator':{'type':'ZERO_INTEREST_CASH_COMPARATOR','cash':'500'},'sequence':0,'previous_hash':None}
def ready():
 if set(ADAPTERS)!={'calendar','candidate','close','interval','committed_freeze'}:raise ValueError('production admission adapters unavailable')
def validate(s):
 if s.get('model')!=MODEL or s.get('initial_cash')!='500':raise ValueError('wrong ledger')
 cash=Decimal(s['cash'])
 if not cash.is_finite() or cash<0:raise ValueError('invalid cash')
 if len(s['positions'])>5:raise ValueError('position cap')
 active=[o for o in s['orders'] if o['state'] in ('FROZEN','PENDING') and o['side']=='BUY']
 if sum((Decimal(o['reserved']) for o in active),Decimal(0))>cash:raise ValueError('over-reserved')
 if len(active)+len(s['positions'])>5:raise ValueError('exposure cap')
 if len({o['id'] for o in s['orders']})!=len(s['orders']):raise ValueError('duplicate order')
def valid_hash(value):
 return isinstance(value,str) and len(value)==64 and all(x in '0123456789abcdef' for x in value)
def calendar(session):
 c=ADAPTERS['calendar'](session)
 if c.get('session')!=session or c.get('regular_session') is not True:raise ValueError('unverified session')
 return c
def source_close(symbol,session):
 q=ADAPTERS['close'](symbol,session)
 if q.get('symbol')!=symbol or q.get('session')!=session or not valid_hash(q.get('source_sha256')):raise ValueError('close identity/provenance mismatch')
 amount(q['close']);instant(q['observed_utc']);return q

def freeze(s,session,candidate_refs=()):
 ready();validate(s);now=clock();local=now.astimezone(ET)
 if local.date().isoformat()!=session or local.time()>time(8):raise ValueError('missed prospective freeze')
 cal=calendar(session)
 if any(d['session']==session for d in s['decisions']):raise ValueError('session already frozen')
 r=deepcopy(s);new=[];records=[]
 if session in ENTRY_DAYS:
  candidates=[]
  for ref in candidate_refs:
   c=ADAPTERS['candidate'](ref)
   if instant(c['knowledge_utc'])>now:raise ValueError('future candidate evidence')
   hashes=c.get('source_hashes');observations=c.get('source_observed_utc')
   if c.get('review_passed') is not True or not isinstance(hashes,list) or not hashes or not all(valid_hash(h) for h in hashes):raise ValueError('unadmitted candidate evidence')
   if not isinstance(observations,list) or len(observations)!=len(hashes):raise ValueError('missing source observations')
   if not max(map(instant,observations))<=instant(c['reviewed_utc'])<=instant(c['knowledge_utc'])<=now:raise ValueError('invalid review timing')
   candidates.append(c)
  candidates.sort(key=lambda c:(instant(c['knowledge_utc']),c['issuer_id'],c['event_id']))
  for c in candidates:
   record={'event_id':c['event_id'],'issuer_id':c['issuer_id'],'state':'SKIPPED'}
   considered=[x for d in r['decisions'] for x in d['candidates']]+records
   known=[x for x in considered if x.get('event_id')==c['event_id'] or x.get('issuer_id')==c['issuer_id']]
   exposure=[o for o in r['orders'] if o['side']=='BUY' and o['state'] in ('FROZEN','PENDING')]
   if known or any(p['issuer_id']==c['issuer_id'] for p in r['positions']) or any(o['issuer_id']==c['issuer_id'] for o in exposure):record['reason']='duplicate event or issuer'
   elif len(exposure)+len(r['positions'])>=5:record['reason']='slot cap'
   else:
    prior=source_close(c['symbol'],cal['previous_session'])
    if instant(prior['observed_utc'])>now:raise ValueError('future prior price')
    free=Decimal(r['cash'])-sum((Decimal(o['reserved']) for o in exposure),Decimal(0))
    plan=size(prior['close'],min(free,Decimal(500)))
    if plan['quantity']==0:record['reason']='whole share unaffordable'
    else:
     order={'id':c['event_id']+':'+session,'event_id':c['event_id'],'issuer_id':c['issuer_id'],'symbol':c['symbol'],'side':'BUY','session':session,'freeze_utc':now.isoformat(),'state':'FROZEN',**plan,'candidate_evidence':c,'prior_evidence':prior}
     order['freeze_hash']=digest(order);r['orders'].append(order);new.append(order['id']);record['state']='FROZEN'
   records.append(record)
 else:
  if session<EXIT_DAY:raise ValueError('outside entry window')
  for p in r['positions']:
   old=[o for o in r['orders'] if o['side']=='SELL' and o['position_id']==p['id']]
   if old and old[-1]['state'] not in ('NO_ORDINARY_CLOSE',):continue
   if old and session<=old[-1]['session']:raise ValueError('retry must be later session')
   o={'id':p['id']+':exit:'+session,'position_id':p['id'],'issuer_id':p['issuer_id'],'symbol':p['symbol'],'quantity':p['quantity'],'side':'SELL','session':session,'freeze_utc':now.isoformat(),'state':'FROZEN'}
   o['freeze_hash']=digest(o);r['orders'].append(o);new.append(o['id'])
 completed=clock();completed_local=completed.astimezone(ET)
 if completed<now or completed_local.date().isoformat()!=session or completed_local.time()>time(8):raise ValueError('evidence review missed freeze deadline')
 for order in r['orders']:
  if order['id'] in new:
   order['freeze_utc']=completed.isoformat();order.pop('freeze_hash',None);order['freeze_hash']=digest(order)
 r['decisions'].append({'session':session,'at':completed.isoformat(),'orders':new,'candidates':records,'calendar':cal})
 validate(r);return r

def settle(s,order_id):
 ready();validate(s);r=deepcopy(s);o=next(x for x in r['orders'] if x['id']==order_id)
 if o['state'] not in ('FROZEN','PENDING'):raise ValueError('order resolved')
 # Verified immutable private commit must predate freeze deadline and target close;
 # adapter verifies actual commit content/hash, not a claimed commit timestamp field.
 frozen={k:v for k,v in o.items() if k not in ('freeze_hash','reason','commit_receipt','interval_evidence','close_evidence')};frozen['state']='FROZEN'
 if digest(frozen)!=o['freeze_hash']:raise ValueError('frozen order mutated')
 receipt=ADAPTERS['committed_freeze'](o['id'],o['freeze_hash'],o['session'])
 if not isinstance(receipt,dict) or receipt.get('verified') is not True or receipt.get('order_id')!=o['id'] or receipt.get('freeze_hash')!=o['freeze_hash']:raise ValueError('unverified committed freeze')
 if receipt.get('repository')!='JeremyHennessy/CatalystRadar-Private' or receipt.get('receipt_basis')!='TRUSTED_SERVER_RECEIPT' or not valid_hash(receipt.get('receipt_sha256')):raise ValueError('untrusted commit receipt')
 received=instant(receipt['server_received_utc']);deadline=datetime.combine(instant(o['freeze_utc']).astimezone(ET).date(),time(8),ET)
 if not instant(o['freeze_utc'])<=received<=deadline:raise ValueError('commit receipt outside prospective window')
 o['commit_receipt']=receipt
 cal=calendar(o['session']);now=clock()
 if now<instant(cal['close_utc']):raise ValueError('target session not closed')
 position=next((p for p in r['positions'] if p['id']==o.get('position_id')),None)
 start=position['entry_session'] if position else o['session']
 interval=ADAPTERS['interval'](o['symbol'],start,o['session'])
 if interval.get('symbol')!=o['symbol'] or interval.get('start')!=start or interval.get('end')!=o['session']:raise ValueError('interval identity mismatch')
 o['interval_evidence']=interval
 if interval.get('complete') is not True or interval.get('actions')!=[]:
  o['state']='PENDING';o['reason']='corporate-action interval unresolved';return r
 if instant(interval['observed_utc'])>now or instant(interval['observed_utc'])<instant(cal['close_utc']):raise ValueError('interval not observed after close')
 if type(interval.get('ordinary_close')) is not bool:
  o['state']='PENDING';o['reason']='ordinary close unknown';return r
 if interval['ordinary_close'] is False:
  o['state']='UNFILLED' if o['side']=='BUY' else 'NO_ORDINARY_CLOSE';o['reason']='halt/closure';return r
 q=source_close(o['symbol'],o['session'])
 if instant(q['observed_utc'])>now or instant(q['observed_utc'])<instant(cal['close_utc']):raise ValueError('invalid close observation')
 o['close_evidence']=q
 if o['side']=='BUY':
  scenario=cost_scenario(o,q['close'])
  if not scenario['would_fit_limit_and_reservation']:o['state']='UNFILLED';o['reason']='limit/cash';return r
  cost=Decimal(scenario['modeled_cost']);r['cash']=str(Decimal(r['cash'])-cost)
  r['positions'].append({'id':o['id'],'issuer_id':o['issuer_id'],'symbol':o['symbol'],'quantity':o['quantity'],'entry_session':o['session'],'entry_cost':str(cost)})
  fill={'modeled_price':scenario['modeled_buy_price'],'cash_change':str(-cost)}
 else:
  price=amount(q['close'])*(1-SLIPPAGE);proceeds=price*o['quantity']*(1-FEE)
  r['cash']=str(Decimal(r['cash'])+proceeds);r['positions'].remove(position)
  fill={'modeled_price':str(price),'cash_change':str(proceeds),'realized_pnl':str(proceeds-Decimal(position['entry_cost']))}
 o['state']='MODELED';r['fills'].append({'order_id':o['id'],'side':o['side'],'session':o['session'],'quantity':o['quantity'],'symbol':o['symbol'],'model':MODEL,'close_evidence':q,'interval_evidence':interval,'recorded_at':now.isoformat(),**fill});validate(r);return r

def transaction(private_root,operation,*,verified_repository):
 """Atomic append-only revisions under lock. Caller must verify live repo privacy.
No generic CLI until production repository/feed/commit adapters pass review.
"""
 if verified_repository!={'full_name':'JeremyHennessy/CatalystRadar-Private','visibility':'private'}:raise ValueError('private output only')
 root=Path(private_root).resolve();root.mkdir(parents=True,exist_ok=True)
 with (root/'.lock').open('a') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX)
  files=sorted(root.glob('[0-9]'*8+'.json'));s=initial();previous=None
  for i,p in enumerate(files,1):
   x=json.loads(p.read_text())
   if p.name!=f'{i:08}.json' or x['sequence']!=i or x['previous_hash']!=previous:raise ValueError('ledger chain invalid')
   validate(x);s=x;previous=digest(x)
  r=operation(deepcopy(s));validate(r);r['sequence']=len(files)+1;r['previous_hash']=previous
  new_decisions=r['decisions'][len(s['decisions']):]
  for decision in new_decisions:
   local=clock().astimezone(ET)
   if local.date().isoformat()!=decision['session'] or local.time()>time(8):raise ValueError('persistence missed freeze deadline')
  path=root/f'{r["sequence"]:08}.json';fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
  with os.fdopen(fd,'wb') as f:f.write(canonical(r));f.flush();os.fsync(f.fileno())
  return r
