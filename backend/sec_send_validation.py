"""Offline send-time/response checks. No networking or collection authorization."""
import datetime as dt
import hashlib
import json
import re
from zoneinfo import ZoneInfo
from sec_request_accounting import allowed,instant,replay

TICKERS={'0000820318':'COHR','0000012659':'HRB','0000020286':'CINF','0000025743':'TXMD','0000031791':'RVTY','0000032604':'EMR','0000042582':'GT','0000091576':'KEY','0000108516':'WOR','0001770450':'XRX'}
MAX_BYTES=25_000_000
REQUIRED=('accessionNumber','filingDate','acceptanceDateTime','form','primaryDocument')

def send_time_check(events,expected_tip,request_id,now,last_actual_send_at=None):
 """Recheck a supplied intent at proposed send time, not reservation time.

Remote persistence, sender ownership and external consumers are NOT verified.
Returned local-check success never authorizes a send, including from this process.
"""
 clock=instant(now);state=replay(events,now);failures=[]
 if state['tip_sha256']!=expected_tip:failures.append('STALE_LEDGER_TIP')
 if state['halted']:failures.append('FAILURE_LATCH')
 if state['pending_request_id']!=request_id or request_id is None:failures.append('NO_MATCHING_PENDING_INTENT')
 if not allowed(clock):failures.append('ACTUAL_SEND_OUTSIDE_CANDIDATE_WINDOW')
 intent=next((e for e in reversed(events) if e['kind']=='RESERVE' and e['request_id']==request_id),None)
 if intent is not None:
  age=clock-instant(intent['at'])
  if age>dt.timedelta(seconds=60):failures.append('STALE_INTENT_REQUIRES_REVIEW')
 if last_actual_send_at is None:
  if state['reserved_requests']>1:failures.append('PREVIOUS_ACTUAL_SEND_TIME_UNKNOWN')
 else:
  previous=instant(last_actual_send_at)
  if previous>clock:failures.append('FUTURE_ACTUAL_SEND_CLOCK')
  elif clock-previous<dt.timedelta(seconds=2):failures.append('ACTUAL_SEND_SPACING_TOO_SHORT')
 return {'local_check_failures':sorted(set(failures)),'local_checks_passed':not failures,
         'collection_enabled':False,'send_authorized':False,
         'mandatory_external_blockers':['REMOTE_PERSISTENCE_AND_EXCLUSIVE_SEND_OWNERSHIP_UNVERIFIED','COMPLETE_MANAGED_HISTORY_AND_EXTERNAL_CONSUMERS_UNVERIFIED'],
         'clock_status':'CALLER_ASSERTED_NOT_AUTHENTICATED'}

def unique(pairs):
 result={}
 for k,v in pairs:
  if k in result:raise ValueError('duplicate source field')
  result[k]=v
 return result

def reject_constant(_):raise ValueError('nonfinite source JSON')

def validate_response(raw,*,issuer_cik,requested_url,final_url,http_status,sent_at,received_at,as_of,forbidden_values=()):
 """Check supplied SEC response bytes; does not retrieve/authenticate the source.

No claims about complete lookback coverage, first-public timing, filing truth,
current security mapping or a valid send authorization are made.
"""
 if issuer_cik not in TICKERS:raise ValueError('unreviewed issuer scope')
 expected='https://data.sec.gov/submissions/CIK'+issuer_cik+'.json'
 if requested_url!=expected or final_url!=expected:raise ValueError('source URL/redirect mismatch')
 if type(http_status) is not int or http_status!=200:raise ValueError('non-success source status')
 if type(raw) is not bytes or not 0<len(raw)<=MAX_BYTES:raise ValueError('source byte bound')
 sent,received,observed=map(instant,(sent_at,received_at,as_of))
 if not sent<=received<=observed:raise ValueError('invalid response clocks')
 if received-sent>dt.timedelta(seconds=30):raise ValueError('response exceeds proposed elapsed bound')
 if not isinstance(forbidden_values,(tuple,list)) or len(forbidden_values)>10 or any(not isinstance(x,str) or not 1<=len(x)<=1000 for x in forbidden_values):raise ValueError('invalid private-value filter')
 text=raw.decode('utf-8',errors='strict')
 document=json.loads(text,object_pairs_hook=unique,parse_constant=reject_constant)
 if not isinstance(document,dict):raise ValueError('source object required')
 # Check decoded strings as well as original bytes; never echo blocked values.
 decoded=json.dumps(document,ensure_ascii=False,allow_nan=False)
 if any(value.casefold() in text.casefold() or value.casefold() in decoded.casefold() for value in forbidden_values):raise ValueError('private value reflected in source')
 cik=document.get('cik')
 if not isinstance(cik,(str,int)) or isinstance(cik,bool) or not re.fullmatch(r'[0-9]{1,10}',str(cik)) or str(int(cik)).zfill(10)!=issuer_cik:raise ValueError('response issuer mismatch')
 tickers=document.get('tickers')
 if not isinstance(tickers,list) or len(tickers)>100 or not all(isinstance(t,str) and len(t)<=20 for t in tickers) or TICKERS[issuer_cik] not in tickers:raise ValueError('reported ticker context mismatch')
 filings=document.get('filings');recent=filings.get('recent') if isinstance(filings,dict) else None
 if not isinstance(recent,dict) or any(not isinstance(recent.get(k),list) for k in REQUIRED):raise ValueError('recent filing schema missing')
 count=len(recent['accessionNumber'])
 if not 0<count<=10000 or any(len(recent[k])!=count for k in REQUIRED):raise ValueError('recent filing count mismatch')
 seen=set()
 for i in range(count):
  acc=recent['accessionNumber'][i]
  if not isinstance(acc,str) or not re.fullmatch(r'[0-9]{10}-[0-9]{2}-[0-9]{6}',acc) or acc in seen:raise ValueError('invalid/duplicate accession')
  seen.add(acc)
  filed=recent['filingDate'][i]
  if not isinstance(filed,str) or not re.fullmatch(r'[0-9]{4}-[0-9]{2}-[0-9]{2}',filed):raise ValueError('invalid filing date')
  if dt.date.fromisoformat(filed)>received.astimezone(ZoneInfo('America/New_York')).date():raise ValueError('future filing date')
  accepted=instant(recent['acceptanceDateTime'][i])
  if accepted>received:raise ValueError('future acceptance timestamp')
  for k in ('form','primaryDocument'):
   value=recent[k][i]
   if not isinstance(value,str) or not 0<len(value)<=500 or any(ord(c)<32 for c in value):raise ValueError('invalid filing field')
 return {'status':'SUPPLIED_BYTES_IDENTITY_AND_RECENT_SCHEMA_VALIDATED_ONLY',
         'issuer_cik':issuer_cik,'source_url':expected,'source_sha256':hashlib.sha256(raw).hexdigest(),
         'byte_count':len(raw),'recent_rows_checked':count,'reported_ticker_present':True,
         'source_authenticity_verified':False,'complete_window_verified':False,
         'first_public_time_verified':False,'security_mapping_verified':False,
         'collection_enabled':False,'send_authorized':False}
