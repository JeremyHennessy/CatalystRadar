"""Separate conditional raw-close illustration. NOT a strategy, order or fill book.
Private vendor data only. No network, publishing or changes to primary paper ledger.
"""
from datetime import datetime,timezone
from pathlib import Path
import hashlib,json,os,fcntl
from decimal import Decimal
from close_proxy import size,cost_scenario,SLIPPAGE,FEE,instant,amount
from proxy_runner import digest,valid_hash
UNIVERSE=('CINF','COHR','EMR','GT','HRB','KEY','RVTY','TXMD','WOR','XRX')
PRIOR='2026-11-13';ENTRY='2026-11-16';EXIT='2026-11-20'
DEADLINE=instant('2026-11-16T13:00:00Z')
MODEL='CONDITIONAL_RAW_CLOSE_MECHANICAL_ILLUSTRATION'
ASSUMPTIONS=['unchanged share basis','no cash or stock distributions','ordinary trading available','daily close proxy obtainable with modeled slippage']
def protocol():
 return {'version':'1','fee':str(FEE),'slippage':str(SLIPPAGE),'price_floor':'5','limit_buffer':'1.03','slot_cap':'100','max_slots':5,'price_vintage':'FIRST_VALID_ARCHIVED_POST_SESSION_OBSERVATION','implementation_hashes':{name:hashlib.sha256((Path(__file__).parent/name).read_bytes()).hexdigest() for name in ('mechanical_scenario.py','close_proxy.py','private_close_adapter.py')}}
def clock():return datetime.now(timezone.utc)

def freeze(lookup):
 started=clock()
 if not instant('2026-11-13T21:00:00Z')<=started<=DEADLINE:raise ValueError('outside prospective freeze window')
 records=[];selected=0;reserved=Decimal(0)
 for symbol in UNIVERSE:
  record={'symbol':symbol,'state':'UNAVAILABLE'}
  try:q=lookup(symbol,PRIOR)
  except (ValueError,OSError,KeyError):record['reason']='PRIOR_SOURCE_UNAVAILABLE';records.append(record);continue
  if not valid_hash(q.get('source_sha256')):raise ValueError('missing prior source hash')
  if q.get('symbol')!=symbol or q.get('session')!=PRIOR or instant(q['observed_utc'])>started:raise ValueError('source not available at freeze')
  record['prior_evidence']=q
  if amount(q['close'])<5:record.update(state='SKIPPED',reason='PREDECLARED_PRICE_FLOOR')
  elif selected>=5:record.update(state='SKIPPED',reason='PREDECLARED_FIVE_SLOT_CAP')
  else:
   p=size(q['close'],Decimal(500)-reserved)
   if p['quantity']==0:record.update(state='SKIPPED',reason='WHOLE_SHARE_UNAFFORDABLE')
   else:record.update(state='SELECTED',quantity=p['quantity'],limit=p['limit'],reserved=p['reserved']);selected+=1;reserved+=Decimal(p['reserved'])
  records.append(record)
 completed=clock()
 if completed<started or completed>DEADLINE:raise ValueError('freeze missed cutoff')
 plan={'model':MODEL,'scenario_id':'MECHANICAL_CONTROL_2026_11_16','initial_cash':'500','protocol':protocol(),'entry_session':ENTRY,'exit_session':EXIT,'prior_session':PRIOR,'freeze_utc':completed.isoformat(),'universe':list(UNIVERSE),'ranking':'ALPHABETICAL_NO_CATALYST_SCORE','records':records,'assumptions':ASSUMPTIONS,'actions_and_halts_verified':False,'use':'ILLUSTRATION_NOT_STRATEGY_OR_EXECUTION','reserved':str(reserved)}
 plan['plan_sha256']=digest(plan);return plan

def evaluate(plan,lookup,*,receipt,known_actions=()):
 """Arithmetic only after immutable plan receipt. Unknown actions remain explicit.
 Caller must verify receipt via trusted-server adapter; no production wrapper yet.
 """
 unhashed={k:v for k,v in plan.items() if k!='plan_sha256'}
 if plan.get('model')!=MODEL or digest(unhashed)!=plan.get('plan_sha256') or plan.get('universe')!=list(UNIVERSE):raise ValueError('plan identity changed')
 if not isinstance(receipt,dict) or receipt.get('verified') is not True or receipt.get('plan_sha256')!=plan['plan_sha256'] or receipt.get('receipt_basis')!='TRUSTED_SERVER_RECEIPT':raise ValueError('missing trusted prospective receipt')
 if not instant(plan['freeze_utc'])<=instant(receipt['server_received_utc'])<=DEADLINE:raise ValueError('late receipt')
 now=clock()
 if plan.get('protocol')!=protocol():raise ValueError('protocol or implementation differs from frozen plan')
 if receipt.get('repository')!='JeremyHennessy/CatalystRadar-Private' or not valid_hash(receipt.get('receipt_sha256')) or instant(receipt['server_received_utc'])>now:raise ValueError('untrusted or future receipt')
 records=[]
 for frozen in plan['records']:
  r={'symbol':frozen['symbol'],'selection_state':frozen['state'],'status':'NOT_SELECTED','assumptions':ASSUMPTIONS}
  if frozen['state']!='SELECTED':r['reason']=frozen.get('reason');records.append(r);continue
  if frozen['symbol'] in known_actions:r['status']='SUPPRESSED_KNOWN_ACTION_INCOMPARABLE';records.append(r);continue
  if now<instant(ENTRY+'T21:00:00Z'):r['status']='AWAITING_FUTURE_ENTRY_DATA';records.append(r);continue
  try:e=lookup(frozen['symbol'],ENTRY)
  except (ValueError,OSError,KeyError):r['status']='ENTRY_SOURCE_UNAVAILABLE';records.append(r);continue
  if e.get('vintage_policy')!='FIRST_OBSERVED':raise ValueError('outcome vintage policy mismatch')
  if not valid_hash(e.get('source_sha256')):raise ValueError('missing entry source hash')
  if e.get('symbol')!=frozen['symbol'] or e.get('session')!=ENTRY or not instant(ENTRY+'T21:00:00Z')<=instant(e['observed_utc'])<=now:raise ValueError('invalid entry evidence')
  scenario=cost_scenario(frozen,e['close']);r['entry_evidence']=e
  if not scenario['would_fit_limit_and_reservation']:r['status']='CONDITION_LIMIT_NOT_MET';records.append(r);continue
  r.update(status='AWAITING_FUTURE_EXIT_DATA',hypothetical_entry_cost=scenario['modeled_cost'])
  if now<instant(EXIT+'T21:00:00Z'):records.append(r);continue
  try:x=lookup(frozen['symbol'],EXIT)
  except (ValueError,OSError,KeyError):r['status']='EXIT_SOURCE_UNAVAILABLE';records.append(r);continue
  if x.get('vintage_policy')!='FIRST_OBSERVED':raise ValueError('outcome vintage policy mismatch')
  if not valid_hash(x.get('source_sha256')):raise ValueError('missing exit source hash')
  if x.get('symbol')!=frozen['symbol'] or x.get('session')!=EXIT or not instant(EXIT+'T21:00:00Z')<=instant(x['observed_utc'])<=now:raise ValueError('invalid exit evidence')
  proceeds=amount(x['close'])*(1-SLIPPAGE)*frozen['quantity']*(1-FEE)
  r.update(status='CONDITIONAL_ARITHMETIC_ONLY_UNVERIFIED_ASSUMPTIONS',exit_evidence=x,hypothetical_exit_proceeds=str(proceeds),hypothetical_cash_change=str(proceeds-Decimal(scenario['modeled_cost'])))
  records.append(r)
 return {'model':MODEL,'plan_sha256':plan['plan_sha256'],'records':records,'protocol':plan['protocol'],'evaluated_at':now.isoformat(),'receipt':receipt,'primary_book_changed':False,'predictive_performance':None,'market_alpha':None,'comparison':'500_NON_INTEREST_CASH_ONLY','assumptions_verified':False}


def append_evaluation(root,report):
 """Immutable private report revisions, never a replacement of prior arithmetic.
 Subsequent evaluations remain explicit restatements with their own source hashes.
 """
 root=Path(root)
 if root.is_symlink():raise ValueError('symlink output forbidden')
 root.mkdir(parents=True,exist_ok=True)
 with (root/'.lock').open('a') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX)
  payload=json.dumps(report,sort_keys=True,separators=(',',':')).encode();sha=hashlib.sha256(payload).hexdigest();target=root/(sha+'.json')
  if target.exists():
   if target.is_symlink() or target.read_bytes()!=payload:raise ValueError('immutable evaluation conflict')
   return sha
  fd=os.open(target,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
  with os.fdopen(fd,'wb') as f:f.write(payload);f.flush();os.fsync(f.fileno())
  return sha
