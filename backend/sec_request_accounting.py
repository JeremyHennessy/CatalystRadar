"""Pure offline accounting for a PROPOSED managed SEC metadata consumer.

No network, filesystem writes, scheduler, lease expiry or collection permission.
A caller must persist a returned event with atomic compare-and-swap before a
future runner could use it. Hashes are integrity checks, not authenticated clocks
or proof that source validation occurred. Unmanaged consumers are outside scope.
"""
import datetime as dt
import hashlib
import json
import re

UTC=dt.timezone.utc
START=dt.datetime(2026,11,23,11,tzinfo=UTC)
END=dt.datetime(2026,11,28,tzinfo=UTC)
CIKS=frozenset(('0000820318','0000012659','0000020286','0000025743','0000031791','0000032604','0000042582','0000091576','0000108516','0001770450'))
GENESIS='0'*64
MAX_EVENTS=2600
FAILURES=frozenset(('HTTP_403','HTTP_429','AUTH_FAILURE','QUOTA_EXHAUSTED','NETWORK_FAILURE','VALIDATION_FAILURE','UNEXPECTED_SCHEMA','PARTIAL_RESPONSE'))
COMMON={'sequence','previous_sha256','kind','at','sha256'}
RESERVE={'run_id','consumer','issuer_cik','request_id','url'}
OUTCOME={'request_id','status','source_sha256','byte_count'}

def instant(value):
 if not isinstance(value,str):raise ValueError('UTC timestamp required')
 try:x=dt.datetime.fromisoformat(value.replace('Z','+00:00'))
 except ValueError:raise ValueError('invalid timestamp') from None
 if x.tzinfo is None or x.utcoffset()!=dt.timedelta(0):raise ValueError('UTC timestamp required')
 return x

def digest(event):
 return hashlib.sha256(json.dumps({k:v for k,v in event.items() if k!='sha256'},sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()

def allowed(now):
 return START<=now<END and now.weekday()<5 and now.hour>=11

def replay(events,as_of):
 """Validate entire bounded supplied ledger; never infer completeness externally."""
 now=instant(as_of)
 if not isinstance(events,list) or len(events)>MAX_EVENTS:raise ValueError('bounded ledger required')
 tip=GENESIS;previous=None;pending=None;halted=False;requests={};runs={};day_runs={};last_run=None;last_reserved=None
 for number,event in enumerate(events,1):
  if not isinstance(event,dict):raise ValueError('invalid event')
  kind=event.get('kind');fields=RESERVE if kind=='RESERVE' else OUTCOME if kind=='OUTCOME' else None
  if fields is None or set(event)!=COMMON|fields:raise ValueError('exact event schema required')
  if type(event['sequence']) is not int or event['sequence']!=number or event['previous_sha256']!=tip or event['sha256']!=digest(event):raise ValueError('event chain mismatch')
  at=instant(event['at'])
  if at>now or (previous and at<previous):raise ValueError('future or reversed event clock')
  if kind=='RESERVE':
   if pending is not None or halted:raise ValueError('unresolved request or failure stop')
   if not allowed(at):raise ValueError('outside candidate window')
   run=event['run_id'];cik=event['issuer_cik'];rid=event['request_id']
   if not isinstance(run,str) or not re.fullmatch(r'[1-9][0-9]{0,19}',run):raise ValueError('invalid run')
   if cik not in CIKS or event['consumer']!='sec_metadata_watchlist_v1':raise ValueError('unreviewed managed scope')
   if event['url']!='https://data.sec.gov/submissions/CIK'+cik+'.json' or rid!=run+':'+cik or rid in requests:raise ValueError('invalid or duplicate request')
   if last_reserved and at-last_reserved<dt.timedelta(seconds=2):raise ValueError('request spacing violation')
   day=at.date().isoformat()
   if run not in runs:
    if len(runs)>=130 or day_runs.get(day,0)>=26:raise ValueError('run ceiling reached')
    if last_run is not None:
     if len(runs[last_run]['ciks'])!=10:raise ValueError('previous run scope incomplete')
     if at-runs[last_run]['started']<dt.timedelta(minutes=30):raise ValueError('run spacing violation')
    runs[run]={'started':at,'day':day,'ciks':set()};day_runs[day]=day_runs.get(day,0)+1
   elif run!=last_run or runs[run]['day']!=day:raise ValueError('reopened or cross-day run')
   runs[run]['ciks'].add(cik)
   if len(requests)>=1300:raise ValueError('request ceiling reached')
   requests[rid]=event;pending=rid;last_reserved=at;last_run=run
  else:
   rid=event['request_id'];status=event['status']
   if pending is None or rid!=pending:raise ValueError('outcome without matching unresolved intent')
   if status=='VALIDATED_SOURCE':
    if not isinstance(event['source_sha256'],str) or not re.fullmatch(r'[a-f0-9]{64}',event['source_sha256']) or type(event['byte_count']) is not int or not 0<event['byte_count']<=25000000:raise ValueError('successful receipt evidence required')
   elif status in FAILURES:
    if event['source_sha256'] is not None or event['byte_count'] is not None:raise ValueError('failure body metadata withheld')
    halted=True
   else:raise ValueError('unknown outcome')
   pending=None
  previous=at;tip=event['sha256']
 return {'tip_sha256':tip,'event_count':len(events),'reserved_requests':len(requests),'reserved_runs':len(runs),
         'pending_request_id':pending,'halted':halted,'collection_enabled':False,
         'scope':'SUPPLIED_MANAGED_LEDGER_ONLY_NOT_GLOBAL_ENFORCEMENT',
         'trust':'Caller must verify ledger completeness, durable CAS persistence and source receipts; hashes do not establish authenticity.'}

def propose(events,expected_tip,as_of,kind,**fields):
 """Return an UNPERSISTED candidate event, never permission to issue a request."""
 state=replay(events,as_of)
 if expected_tip!=state['tip_sha256']:raise ValueError('stale compare-and-swap expectation')
 event={'sequence':len(events)+1,'previous_sha256':expected_tip,'kind':kind,'at':instant(as_of).isoformat(),**fields}
 # Prevent keyword overrides of protocol fields before signing.
 if set(fields)&COMMON:raise ValueError('protocol override prohibited')
 event['sha256']=digest(event)
 replay(events+[event],as_of)
 return {'event':event,'expected_prior_tip':expected_tip,'persisted':False,'collection_enabled':False,
         'required_next_step':'Separate independently reviewed durable compare-and-swap persistence; no source call is authorized by this result.'}
