"""Bounded private conditional illustration evaluation; no vendor calls or trading.
Original frozen code/protocol and server receipt must still match. Delayed/missing
snapshots stay explicit; this is not the primary catalyst strategy or paper book.
"""
import json,hashlib,re
from pathlib import Path
from datetime import datetime,timezone,date,timedelta
from collections import Counter
from private_scenario import gate
from collect import privacy
from freeze_receipt import verify
from private_close_adapter import lookup
from mechanical_scenario import evaluate,append_evaluation,instant,MODEL
from proxy_runner import digest
PLAN='b7d125d608e246ed472b59fa3603fa2a843ddad5b2e2d089f73913dfa7a05f34'
COMMIT='1598a1fc4a179a0a8fee4eccbd82041cb9d9fbe7'
RUN=43632065122
WORKFLOW='2cb9e886b5b496dbffe8bc84e76a8a1606b26751'
def clock():return datetime.now(timezone.utc)

def known_actions(root,now):
 path=root/'data/action-observations.json'
 if not path.exists():return [],{'coverage':'NO_CONNECTED_COMPLETE_ACTION_SOURCE','observations':[]}
 if path.is_symlink():raise ValueError('unsafe action observation file')
 obj=json.loads(path.read_text());positive=[];audit=[]
 if obj.get('mode')!='POSITIVE_OBSERVATIONS_ONLY' or not isinstance(obj.get('records'),list):raise ValueError('unknown action schema')
 for row in obj['records']:
  if not isinstance(row,dict) or not isinstance(row.get('symbol'),str) or not re.fullmatch('[A-Z]{1,5}',row['symbol']) or not isinstance(row.get('source_sha256'),str) or not re.fullmatch('[a-f0-9]{64}',row['source_sha256']):raise ValueError('invalid action identity/provenance')
  source=(root/row['source_path']).resolve()
  if root.resolve() not in source.parents or source.is_symlink():raise ValueError('action source outside private archive')
  if hashlib.sha256(source.read_bytes()).hexdigest()!=row['source_sha256']:raise ValueError('action source hash mismatch')
  if instant(row['observed_utc'])>now:raise ValueError('future action source')
  if row.get('kind') not in ('SPLIT','DIVIDEND','MERGER','SPINOFF','SYMBOL_CHANGE','OTHER_DISTRIBUTION'):raise ValueError('unknown action type')
  effective=date.fromisoformat(row['effective_session']).isoformat()
  if '2026-11-16'<=effective<='2026-11-20':positive.append(row['symbol']);audit.append(row)
 return sorted(set(positive)),{'coverage':'MANUAL_POSITIVE_ASSERTIONS_BOUND_TO_SOURCE_BYTES_NOT_COMPLETE_HISTORY','observations':audit}

def collection_ready(root,now):
 path=root/'data/latest-collection.json'
 if not path.exists():return False
 if path.is_symlink():raise ValueError('unsafe collection checkpoint')
 checkpoint=json.loads(path.read_text());observed=instant(checkpoint['observed_utc']).astimezone(timezone.utc)
 if observed>now:raise ValueError('future collection checkpoint')
 if observed.date()!=now.date():return False
 symbols=checkpoint.get('symbols')
 expected=('COHR','HRB','CINF','TXMD','RVTY','EMR','GT','KEY','WOR','XRX','SPY')
 if not isinstance(symbols,list) or len(symbols)!=11 or {x.get('symbol')for x in symbols}!=set(expected):return False
 prior=now.date()-timedelta(days=1)
 while prior.weekday()>=5:prior-=timedelta(days=1)
 for symbol in expected:
  try:q=lookup(root/'data/prices',symbol,prior.isoformat())
  except (ValueError,OSError,KeyError):return False
  if instant(q['observed_utc']).astimezone(timezone.utc).date()!=now.date():return False
 return True

def run():
 root,_=gate();privacy();now=clock()
 if not datetime(2026,11,17,tzinfo=timezone.utc)<=now<datetime(2026,11,22,tzinfo=timezone.utc):raise ValueError('outside fixed evaluation window')
 for path in (root/'data',root/'data/scenarios',root/'data/scenario-receipts',root/'data/prices',root/'data/scenario-evaluations'):
  if path.is_symlink():raise ValueError('unsafe private path')
 if not collection_ready(root,now):return {'status':'WAITING_FOR_CURRENT_COLLECTION_NO_REPORT_CREATED','primary_book_changed':False,'new_vendor_calls':0}
 plan=json.loads((root/'data/scenarios'/f'{PLAN}.json').read_text())
 stored=json.loads((root/'data/scenario-receipts'/f'{PLAN}.json').read_text())
 if stored.get('verified')is not True or stored.get('plan_sha256')!=PLAN:raise ValueError('original receipt missing')
 # Re-read immutable original evidence; never dispatch or trust a local claim alone.
 receipt=verify(run_id=RUN,commit_sha=COMMIT,ledger_path='data/scenarios/'+PLAN+'.json',order_id=None,freeze_hash=PLAN,session='2026-11-16',expected_workflow_blob_sha=WORKFLOW,scenario=True)
 if digest(stored['proof'])!=stored['receipt_sha256']:raise ValueError('stored receipt proof corrupted')
 # API descriptive/status fields can evolve. Match immutable evidence identity,
 # while retaining original proof and the newly authenticated verification.
 for key in ('plan_sha256','freeze_hash','repository','server_received_utc'):
  if receipt.get(key)!=stored.get(key):raise ValueError('receipt identity changed')
 for key in ('commit_sha','ledger_blob_sha','ledger_sha256','workflow_blob_sha'):
  if receipt['proof'].get(key)!=stored['proof'].get(key):raise ValueError('receipt content binding changed')
 for key in ('id','head_sha','run_attempt','event','path','created_at'):
  if receipt['proof']['run'].get(key)!=stored['proof']['run'].get(key):raise ValueError('receipt run identity changed')
 dest=root/'data/scenario-evaluations'
 # Shared workflow concurrency serializes runs. Unchanged inputs are idempotent;
 # new delayed snapshots permit a later append-only evaluation even the same day.
 inputs=[]
 for file in sorted((root/'data/prices').glob('*.json')):
  if file.is_symlink():raise ValueError('unsafe snapshot input')
  inputs.append([file.name,hashlib.sha256(file.read_bytes()).hexdigest()])
 action_file=root/'data/action-observations.json'
 if action_file.exists():
  if action_file.is_symlink():raise ValueError('unsafe action input')
  inputs.append(['action-observations',hashlib.sha256(action_file.read_bytes()).hexdigest()])
 input_fingerprint=digest(inputs)
 if dest.exists():
  for file in dest.glob('*.json'):
   old=json.loads(file.read_text())
   if hashlib.sha256(file.read_bytes()).hexdigest()!=file.stem:raise ValueError('existing report hash mismatch')
   if old.get('model')!=MODEL or old.get('plan_sha256')!=PLAN:raise ValueError('existing report belongs to different plan/model')
   if instant(old['evaluated_at']).date()==now.date() and old.get('input_fingerprint')==input_fingerprint:return {'status':'UNCHANGED_INPUTS_ALREADY_EVALUATED_UTC_DATE','primary_book_changed':False}
 actions,action_audit=known_actions(root,now)
 report=evaluate(plan,lambda symbol,session:lookup(root/'data/prices',symbol,session,first_observed=True),receipt=receipt,known_actions=actions)
 report['input_fingerprint']=input_fingerprint
 report['original_receipt_sha256']=stored['receipt_sha256']
 report['action_observation_audit']=action_audit
 report['data_delay_warning']='First archived post-session observations can arrive next day or later. Missing dates remain unavailable; data is not realtime.'
 report['role']='SEPARATE_MECHANICAL_CONTROL_NOT_PRIMARY_CATALYST_STRATEGY'
 privacy();sha=append_evaluation(dest,report)
 return {'status':'CONDITIONAL_REPORT_SAVED_PRIVATELY','report_sha256':sha,'counts':dict(Counter(r['status']for r in report['records'])),'primary_book_changed':False,'new_vendor_calls':0,'data_may_be_delayed_or_incomplete':True}
