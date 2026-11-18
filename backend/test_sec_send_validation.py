import copy,json,unittest
from sec_request_accounting import GENESIS,propose
from sec_send_validation import send_time_check,validate_response
NOW='2026-11-23T11:00:00Z';CIK='0000820318';URL='https://data.sec.gov/submissions/CIK'+CIK+'.json'
def event(clock=NOW):return propose([],GENESIS,clock,'RESERVE',run_id='1',consumer='sec_metadata_watchlist_v1',issuer_cik=CIK,request_id='1:'+CIK,url=URL)['event']
def source():return {'cik':CIK,'tickers':['COHR'],'filings':{'recent':{'accessionNumber':['0000820318-26-000001'],'filingDate':['2026-11-20'],'acceptanceDateTime':['2026-11-20T16:00:00Z'],'form':['8-K'],'primaryDocument':['a.htm']}}}
def check(value=None,**kwargs):
 args=dict(issuer_cik=CIK,requested_url=URL,final_url=URL,http_status=200,sent_at=NOW,received_at='2026-11-23T11:00:01Z',as_of='2026-11-23T11:00:02Z');args.update(kwargs)
 return validate_response(json.dumps(value or source()).encode(),**args)
class SendValidation(unittest.TestCase):
 def test_send_recheck_never_authorizes(self):
  e=event();s=send_time_check([e],e['sha256'],'1:'+CIK,NOW)
  self.assertTrue(s['local_checks_passed']);self.assertFalse(s['send_authorized']);self.assertEqual(len(s['mandatory_external_blockers']),2)
 def test_actual_send_after_cutoff_rejected(self):
  e=event('2026-11-27T23:59:59Z');s=send_time_check([e],e['sha256'],'1:'+CIK,'2026-11-28T00:00:00Z')
  self.assertIn('ACTUAL_SEND_OUTSIDE_CANDIDATE_WINDOW',s['local_check_failures'])
 def test_stale_tip_intent_and_spacing(self):
  e=event();s=send_time_check([e],GENESIS,'1:'+CIK,'2026-11-23T11:01:01Z','2026-11-23T11:01:00Z')
  for code in ('STALE_LEDGER_TIP','STALE_INTENT_REQUIRES_REVIEW','ACTUAL_SEND_SPACING_TOO_SHORT'):self.assertIn(code,s['local_check_failures'])
 def test_missing_intent_rejected(self):
  self.assertFalse(send_time_check([],GENESIS,None,NOW)['local_checks_passed'])
 def test_valid_bytes_not_source_authentication(self):
  x=check();self.assertEqual(x['recent_rows_checked'],1);self.assertFalse(x['source_authenticity_verified']);self.assertFalse(x['complete_window_verified']);self.assertFalse(x['send_authorized'])
 def test_status_redirect_clock_failures(self):
  for kw in ({'http_status':403},{'http_status':True},{'final_url':'https://other.invalid/'},{'received_at':'2026-11-23T11:00:31Z','as_of':'2026-11-23T11:00:32Z'},{'received_at':'2026-11-23T10:59:59Z'}):
   with self.assertRaises(ValueError):check(**kw)
 def test_identity_schema_and_future_acceptance(self):
  for field,value in [('cik','1'),('tickers',['OTHER']),('filings',{})]:
   x=source();x[field]=value
   with self.assertRaises(ValueError):check(x)
  x=source();x['filings']['recent']['acceptanceDateTime'][0]='2027-01-01T00:00:00Z'
  with self.assertRaises(ValueError):check(x)
 def test_duplicate_json_rejected(self):
  raw=b'{"cik":"0000820318","cik":"1"}'
  with self.assertRaises(ValueError):validate_response(raw,issuer_cik=CIK,requested_url=URL,final_url=URL,http_status=200,sent_at=NOW,received_at=NOW,as_of=NOW)
 def test_secret_never_returned(self):
  x=source();x['extra']='hidden-contact@example.test'
  with self.assertRaisesRegex(ValueError,'private value reflected'):check(x,forbidden_values=['hidden-contact@example.test'])
 def test_rows_mismatch_and_empty_rejected(self):
  for values in ([],['2026-11-20','2026-11-21']):
   x=source();x['filings']['recent']['filingDate']=values
   with self.assertRaises(ValueError):check(x)

 def test_future_filing_date_rejected(self):
  x=source();x['filings']['recent']['filingDate'][0]='2027-01-01'
  with self.assertRaises(ValueError):check(x)
 def test_retrieval_after_cutoff_can_be_accounted_without_authorization(self):
  x=check(sent_at='2026-11-27T23:59:59Z',received_at='2026-11-28T00:00:01Z',as_of='2026-11-28T00:00:02Z')
  self.assertFalse(x['send_authorized'])

 def test_overflow_and_nested_nonfinite_rejected(self):
  base=json.dumps(source())
  for fragment in ('1e999','-1e999','{"nested":[1e999]}','NaN','Infinity'):
   raw=(base[:-1]+', "unknown":'+fragment+'}').encode()
   with self.assertRaises(ValueError):validate_response(raw,issuer_cik=CIK,requested_url=URL,final_url=URL,http_status=200,sent_at=NOW,received_at=NOW,as_of=NOW)
