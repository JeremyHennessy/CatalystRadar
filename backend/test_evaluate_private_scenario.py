import unittest,tempfile,json
from pathlib import Path
from unittest.mock import patch
from contextlib import ExitStack
from datetime import datetime,timezone
import evaluate_private_scenario as e
class TestEvaluation(unittest.TestCase):
 def setUp(self):
  self.t=tempfile.TemporaryDirectory();self.root=Path(self.t.name)
  for sub in ('scenarios','scenario-receipts','prices'):(self.root/'data'/sub).mkdir(parents=True)
  (self.root/'data/scenarios'/f'{e.PLAN}.json').write_text('{}')
  self.receipt={'verified':True,'plan_sha256':e.PLAN,'proof':{'run':{'id':e.RUN}}}
  self.receipt['receipt_sha256']=e.digest(self.receipt['proof'])
  (self.root/'data/scenario-receipts'/f'{e.PLAN}.json').write_text(json.dumps(self.receipt))
  self.s=ExitStack();self.s.enter_context(patch.object(e,'gate',return_value=(self.root,'b'*40)));self.s.enter_context(patch.object(e,'privacy'))
  self.s.enter_context(patch.object(e,'clock',return_value=datetime(2026,11,17,12,tzinfo=timezone.utc)))
  self.real_ready=e.collection_ready
  self.s.enter_context(patch.object(e,'collection_ready',return_value=True))
  self.v=self.s.enter_context(patch.object(e,'verify',return_value=self.receipt))
  self.calc=self.s.enter_context(patch.object(e,'evaluate',return_value={'model':e.MODEL,'plan_sha256':e.PLAN,'evaluated_at':'2026-11-17T12:00:00Z','records':[{'status':'AWAITING_FUTURE_EXIT_DATA'}]}))
 def tearDown(self):self.s.close();self.t.cleanup()
 def test_private_append_and_daily_idempotency(self):
  r=e.run();self.assertEqual(r['new_vendor_calls'],0);self.assertEqual(r['counts'],{'AWAITING_FUTURE_EXIT_DATA':1})
  self.assertEqual(e.run()['status'],'UNCHANGED_INPUTS_ALREADY_EVALUATED_UTC_DATE');self.calc.assert_called_once()
 def test_no_receipt_no_evaluation(self):
  (self.root/'data/scenario-receipts'/f'{e.PLAN}.json').unlink();self.assertRaises(FileNotFoundError,e.run);self.calc.assert_not_called()
 def test_changed_receipt_stops(self):
  self.v.return_value={**self.receipt,'proof':{'run':{'id':999}}};self.assertRaises(ValueError,e.run);self.calc.assert_not_called()
 def test_no_action_source_explicit_unknown(self):
  actions,a=e.known_actions(self.root,datetime.now(timezone.utc));self.assertEqual(actions,[]);self.assertEqual(a['coverage'],'NO_CONNECTED_COMPLETE_ACTION_SOURCE')
 def test_outside_window(self):
  with patch.object(e,'clock',return_value=datetime(2026,11,14,tzinfo=timezone.utc)):self.assertRaises(ValueError,e.run)
  self.calc.assert_not_called()

 def test_real_evaluator_missing_entry_stays_unavailable(self):
  import mechanical_scenario as m
  def quote(symbol,session):return {'symbol':symbol,'session':session,'close':'20','source_sha256':'a'*64,'observed_utc':'2026-11-14T12:00:00Z'}
  with patch.object(m,'clock',return_value=datetime(2026,11,14,19,tzinfo=timezone.utc)):plan=m.freeze(quote)
  receipt={'verified':True,'plan_sha256':plan['plan_sha256'],'receipt_basis':'TRUSTED_SERVER_RECEIPT','repository':'JeremyHennessy/CatalystRadar-Private','server_received_utc':'2026-11-14T19:00:00Z','proof':{'run':{'id':e.RUN}}};receipt['receipt_sha256']=e.digest(receipt['proof'])
  (self.root/'data/scenarios'/f"{plan['plan_sha256']}.json").write_text(json.dumps(plan))
  (self.root/'data/scenario-receipts'/f"{plan['plan_sha256']}.json").write_text(json.dumps(receipt))
  with patch.object(e,'PLAN',plan['plan_sha256']),patch.object(e,'verify',return_value=receipt),patch.object(e,'evaluate',m.evaluate),patch.object(m,'clock',return_value=datetime(2026,11,17,12,tzinfo=timezone.utc)):
   result=e.run();self.assertEqual(result['counts']['ENTRY_SOURCE_UNAVAILABLE'],5)
   report=json.loads(next((self.root/'data/scenario-evaluations').glob('*.json')).read_text());self.assertIsNone(report['predictive_performance']);self.assertFalse(report['primary_book_changed'])
 def test_invalid_action_date_rejected(self):
  import hashlib
  src=self.root/'data/source.txt';src.write_text('SYNTHETIC ONLY')
  row={'symbol':'TEST','source_path':'data/source.txt','source_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'observed_utc':'2026-11-14T12:00:00Z','kind':'DIVIDEND','effective_session':'2026-11-19garbage'}
  (self.root/'data/action-observations.json').write_text(json.dumps({'mode':'POSITIVE_OBSERVATIONS_ONLY','records':[row]}))
  self.assertRaises(ValueError,e.known_actions,self.root,datetime(2026,11,17,tzinfo=timezone.utc))

 def test_delayed_new_snapshot_re_evaluates_same_day(self):
  e.run();(self.root/'data/prices/new.json').write_text('SYNTHETIC NEW SNAPSHOT INPUT')
  r=e.run();self.assertEqual(r['status'],'CONDITIONAL_REPORT_SAVED_PRIVATELY');self.assertEqual(self.calc.call_count,2)
  self.assertEqual(len(list((self.root/'data/scenario-evaluations').glob('*.json'))),2)

 def test_collector_not_ready_no_report_or_receipt_request(self):
  with patch.object(e,'collection_ready',return_value=False):r=e.run()
  self.assertEqual(r['status'],'WAITING_FOR_CURRENT_COLLECTION_NO_REPORT_CREATED');self.v.assert_not_called();self.calc.assert_not_called()
  self.assertFalse((self.root/'data/scenario-evaluations').exists())

 def test_readiness_stale_checkpoint_no_lookup(self):
  (self.root/'data/latest-collection.json').write_text(json.dumps({'observed_utc':'2026-11-16T12:00:00Z'}))
  with patch.object(e,'lookup')as lookup:self.assertFalse(self.real_ready(self.root,datetime(2026,11,17,12,tzinfo=timezone.utc)));lookup.assert_not_called()
 def test_readiness_current_requires_actual_prior_quotes(self):
  names='COHR HRB CINF TXMD RVTY EMR GT KEY WOR XRX SPY'.split()
  (self.root/'data/latest-collection.json').write_text(json.dumps({'observed_utc':'2026-11-17T11:59:00Z','symbols':[{'symbol':x}for x in names]}))
  def quote(root,symbol,session):
   self.assertEqual(session,'2026-11-16');return {'observed_utc':'2026-11-17T11:58:00Z'}
  with patch.object(e,'lookup',side_effect=quote):self.assertTrue(self.real_ready(self.root,datetime(2026,11,17,12,tzinfo=timezone.utc)))
  with patch.object(e,'lookup',side_effect=ValueError('missing prior')):self.assertFalse(self.real_ready(self.root,datetime(2026,11,17,12,tzinfo=timezone.utc)))
