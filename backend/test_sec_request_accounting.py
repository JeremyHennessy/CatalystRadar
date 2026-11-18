import copy,datetime as dt,unittest
from sec_request_accounting import *

class Accounting(unittest.TestCase):
 def setUp(self):self.events=[];self.now=START
 def add(self,kind,**fields):
  tip=self.events[-1]['sha256'] if self.events else GENESIS
  out=propose(self.events,tip,self.now.isoformat(),kind,**fields)
  self.assertFalse(out['persisted']);self.assertFalse(out['collection_enabled'])
  self.events.append(out['event']);return out
 def reserve(self,run='1',cik='0000820318'):
  return self.add('RESERVE',run_id=run,consumer='sec_metadata_watchlist_v1',issuer_cik=cik,request_id=run+':'+cik,url='https://data.sec.gov/submissions/CIK'+cik+'.json')
 def result(self,status='VALIDATED_SOURCE'):
  return self.add('OUTCOME',request_id=self.events[-1]['request_id'],status=status,source_sha256='a'*64 if status=='VALIDATED_SOURCE' else None,byte_count=5 if status=='VALIDATED_SOURCE' else None)
 def test_roundtrip_nonoperational(self):
  self.reserve();self.result();s=replay(self.events,self.now.isoformat());self.assertEqual(s['reserved_requests'],1);self.assertFalse(s['collection_enabled'])
 def test_unresolved_never_expires(self):
  self.reserve();self.now+=dt.timedelta(days=1)
  with self.assertRaises(ValueError):self.reserve('2')
 def test_all_failures_latch(self):
  for failure in FAILURES:
   self.events=[];self.now=START;self.reserve();self.result(failure);self.now+=dt.timedelta(seconds=3)
   with self.assertRaises(ValueError):self.reserve('2')
 def test_tamper_reorder_and_future(self):
  self.reserve();self.result();x=copy.deepcopy(self.events);x[0]['issuer_cik']='0000000001'
  with self.assertRaises(ValueError):replay(x,self.now.isoformat())
  with self.assertRaises(ValueError):replay(self.events[::-1],self.now.isoformat())
  with self.assertRaises(ValueError):replay(self.events,(self.now-dt.timedelta(seconds=1)).isoformat())
 def test_stale_tip_unknown_source_and_duplicate(self):
  self.reserve();self.result()
  with self.assertRaises(ValueError):propose(self.events,GENESIS,self.now.isoformat(),'OUTCOME')
  self.now+=dt.timedelta(seconds=3)
  with self.assertRaises(ValueError):self.reserve()
  with self.assertRaises(ValueError):self.reserve(cik='0000000001')
 def test_spacing_and_partial_run(self):
  self.reserve();self.result();self.now+=dt.timedelta(seconds=1)
  with self.assertRaises(ValueError):self.reserve(cik='0000012659')
  self.now+=dt.timedelta(hours=1)
  with self.assertRaises(ValueError):self.reserve('2')
 def test_boundaries(self):
  for now in (START-dt.timedelta(seconds=1),END,START+dt.timedelta(hours=14)):
   self.now=now
   with self.assertRaises(ValueError):self.reserve()
 def test_full_run_and_next_spacing(self):
  for cik in sorted(CIKS):self.reserve(cik=cik);self.result();self.now+=dt.timedelta(seconds=2)
  with self.assertRaises(ValueError):self.reserve('2')
  self.now=START+dt.timedelta(minutes=30);self.reserve('2');self.assertEqual(replay(self.events,self.now.isoformat())['reserved_runs'],2)
 def test_orphan_outcome_and_ambiguous_status(self):
  with self.assertRaises(ValueError):self.add('OUTCOME',request_id='1:x',status='VALIDATED_SOURCE',source_sha256='a'*64,byte_count=5)
  self.reserve()
  with self.assertRaises(ValueError):self.result('EMPTY_OR_FAILURE')
 def test_no_success_without_evidence(self):
  self.reserve()
  with self.assertRaises(ValueError):self.add('OUTCOME',request_id=self.events[-1]['request_id'],status='VALIDATED_SOURCE',source_sha256=None,byte_count=None)
 def test_exact_schema(self):
  self.reserve();x=copy.deepcopy(self.events);x[0]['secret']='private';x[0]['sha256']=digest(x[0])
  with self.assertRaises(ValueError):replay(x,self.now.isoformat())
 def test_daily_and_window_ceilings(self):
  events=[];run=0
  for day in range(5):
   for slot in range(26):
    run+=1
    for i,cik in enumerate(sorted(CIKS)):
     at=START+dt.timedelta(days=day,minutes=30*slot,seconds=2*i)
     for kind,fields in [('RESERVE',dict(run_id=str(run),consumer='sec_metadata_watchlist_v1',issuer_cik=cik,request_id=str(run)+':'+cik,url='https://data.sec.gov/submissions/CIK'+cik+'.json')),('OUTCOME',dict(request_id=str(run)+':'+cik,status='VALIDATED_SOURCE',source_sha256='a'*64,byte_count=5))]:
      e=dict(sequence=len(events)+1,previous_sha256=events[-1]['sha256'] if events else GENESIS,kind=kind,at=at.isoformat(),**fields);e['sha256']=digest(e);events.append(e)
   self.events=events.copy();self.now=START+dt.timedelta(days=day,hours=12,minutes=59)
   with self.assertRaises(ValueError):self.reserve(str(run+1))
  state=replay(events,(END-dt.timedelta(seconds=1)).isoformat())
  self.assertEqual((state['reserved_runs'],state['reserved_requests'],state['event_count']),(130,1300,2600))
 def test_outcome_after_expiry_still_accounts(self):
  self.now=END-dt.timedelta(seconds=1);self.reserve();self.now=END+dt.timedelta(seconds=1);self.result()
  self.assertEqual(replay(self.events,self.now.isoformat())['reserved_requests'],1)
  with self.assertRaises(ValueError):self.reserve(cik='0000012659')
