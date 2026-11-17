"""Synthetic date coverage and retained response fixtures, never market evidence."""
import base64,hashlib,json,tempfile,unittest
from datetime import datetime
from pathlib import Path
from price_session_audit import scheduled,compare,audit
from private_prices import metadata

def sha(b):return hashlib.sha256(b).hexdigest()
class Tests(unittest.TestCase):
 def test_actual_window_schedule_count(self):
  ds=scheduled('2026-06-26','2026-11-16');self.assertEqual(len(ds),100);self.assertNotIn('2026-07-03',ds);self.assertNotIn('2026-09-07',ds)
 def test_early_close_is_session(self):
  self.assertEqual(scheduled('2026-11-26','2026-11-27'),['2026-11-27']);self.assertEqual(scheduled('2026-12-24','2026-12-25'),['2026-12-24']);self.assertIn('2026-07-02',scheduled('2026-07-02','2026-07-03'))
 def test_edge_and_interior_missing_not_hidden(self):
  full=scheduled('2026-11-12','2026-11-16')
  for omit in full:
   r=compare([x for x in full if x!=omit],'2026-11-12','2026-11-16');self.assertEqual(r['missing_scheduled_dates'],[omit]);self.assertFalse(r['matches_scheduled_date_set'])
 def test_weekend_holiday_outside_dates_unexpected(self):
  r=compare(['2026-07-02','2026-07-03','2026-07-04','2026-07-06'],'2026-07-02','2026-07-03');self.assertEqual(r['unexpected_dates'],['2026-07-03','2026-07-04','2026-07-06'])
 def test_invalid_or_unreviewed_year_and_duplicate(self):
  for ds in [['2026-11-12','2026-11-12'],['2027-01-04'],['20261112'],['2026-02-30']]:
   with self.assertRaises(ValueError):compare(ds,'2026-11-12','2026-11-16')
  with self.assertRaises(ValueError):scheduled('2026-11-16','2026-11-12')
 def fixture(self,p):
  obs='2026-11-17T20:00:00+00:00';rows={d:{'1. open':'1','2. high':'2','3. low':'1','4. close':'2','5. volume':'10'} for d in ['2026-11-12','2026-11-13','2026-11-16']}
  raw=json.dumps({'Meta Data':{'2. Symbol':'TEST','3. Last Refreshed':'2026-11-16','5. Time Zone':'US/Eastern'},'Time Series (Daily)':rows}).encode();q=metadata(raw,'TEST',datetime.fromisoformat(obs))
  snap={'symbol':'TEST','observed_utc':obs,'source_endpoint':'https://www.alphavantage.co/query','source_function':'TIME_SERIES_DAILY','source_outputsize':'compact','response_base64':base64.b64encode(raw).decode(),'response_sha256':sha(raw),'quality':q}
  b=json.dumps(snap).encode();(p/'2026-test.json').write_bytes(b)
  ref={'symbol':'TEST','observed_utc':obs,'snapshot_sha256':sha(b),'response_sha256':sha(raw),'first_session':'2026-11-12','last_session':'2026-11-16','rows':3};m=json.dumps({'snapshots':[ref]}).encode();(p/'manifest.json').write_bytes(m);return sha(m)
 def test_end_to_end_no_gate_promotion(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);h=self.fixture(p);s,e=audit(p,p/'manifest.json',h,'2026-11-12','2026-11-16')
   self.assertEqual(s['symbols_matching_date_set'],1);self.assertFalse(s['training_ready']);self.assertFalse(e[0]['prior_quality']['calendar_complete']);self.assertNotIn('response_base64',str(s))
 def test_snapshot_mutation_fails(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);h=self.fixture(p);(p/'2026-test.json').write_text('{}')
   with self.assertRaises(ValueError):audit(p,p/'manifest.json',h,'2026-11-12','2026-11-16')
 def test_missing_file_fails(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);h=self.fixture(p);(p/'2026-test.json').unlink()
   with self.assertRaises(ValueError):audit(p,p/'manifest.json',h,'2026-11-12','2026-11-16')
if __name__=='__main__':unittest.main()
