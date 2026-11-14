import unittest,tempfile,json,base64,hashlib
from pathlib import Path
from datetime import datetime
from unittest.mock import patch
import close_proxy as c
class TestCloseProxy(unittest.TestCase):
 def test_budget(self):
  for p in ('5','20','99','100','500'):
   s=c.size(p,500);self.assertLessEqual(c.Decimal(s['reserved']),100)
   self.assertEqual(c.cost_scenario(s,p)['fills_created'],0)
 def test_cash(self):
  self.assertEqual(c.size(20,0)['quantity'],0)
  self.assertRaises(ValueError,c.size,20,-1)
  self.assertRaises(ValueError,c.size,20,501)
 def test_no_fractions(self):self.assertEqual(c.size(100,500)['quantity'],0)
 def test_bad_numbers(self):
  for n in (True,'NaN','Infinity',0,-1):self.assertRaises(ValueError,c.size,n,500)
 def test_adverse_cost(self):
  s=c.size(20,500);r=c.cost_scenario(s,20)
  self.assertEqual(r['modeled_buy_price'],'20.0500');self.assertEqual(r['orders_created'],0)
  self.assertFalse(c.cost_scenario(s,21)['would_fit_limit_and_reservation'])
 def test_tampered_reservation(self):
  s=c.size(20,500);s['reserved']='100';self.assertRaises(ValueError,c.cost_scenario,s,20)
 def test_envelope(self):
  raw=json.dumps({'Time Series (Daily)':{'2026-11-13':{'4. close':'20'}}}).encode()
  e={'symbol':'TEST','source_endpoint':'https://www.alphavantage.co/query','source_function':'TIME_SERIES_DAILY','source_outputsize':'compact','scope':'PRIVATE_PERSONAL_RESEARCH_ONLY','observed_utc':'2026-11-14T12:00:00Z','response_base64':base64.b64encode(raw).decode(),'response_sha256':hashlib.sha256(raw).hexdigest(),'quality':{'synthetic':True}}
  with tempfile.TemporaryDirectory() as d,patch.object(c,'metadata',return_value={'synthetic':True}):
   p=Path(d)/'x';p.write_text(json.dumps(e));now=datetime.fromisoformat('2026-11-14T13:00:00+00:00')
   r=c.read_envelope(p,symbol='TEST',session='2026-11-13',now=now);self.assertFalse(r['execution_eligible'])
   self.assertRaises(ValueError,c.read_envelope,p,symbol='OTHER',session='2026-11-13',now=now)
   e['response_sha256']='0'*64;p.write_text(json.dumps(e));self.assertRaises(ValueError,c.read_envelope,p,symbol='TEST',session='2026-11-13',now=now)
 def test_real_parser_missing_date_checks_hash_first(self):
  from private_prices import metadata
  now=datetime.fromisoformat('2026-11-14T13:00:00+00:00')
  raw=json.dumps({'Meta Data':{'2. Symbol':'TEST','5. Time Zone':'US/Eastern','3. Last Refreshed':'2026-11-13'},'Time Series (Daily)':{'2026-11-13':{'1. open':'10','2. high':'11','3. low':'9','4. close':'10','5. volume':'100'}}}).encode()
  e={'symbol':'TEST','source_endpoint':'https://www.alphavantage.co/query','source_function':'TIME_SERIES_DAILY','source_outputsize':'compact','scope':'PRIVATE_PERSONAL_RESEARCH_ONLY','observed_utc':now.isoformat(),'response_base64':base64.b64encode(raw).decode(),'response_sha256':hashlib.sha256(raw).hexdigest(),'quality':metadata(raw,'TEST',now)}
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'x';p.write_text(json.dumps(e))
   self.assertRaises(c.MissingSessionError,c.read_envelope,p,symbol='TEST',session='2026-11-12',now=now)
   e['response_sha256']='0'*64;p.write_text(json.dumps(e))
   with self.assertRaisesRegex(ValueError,'hash mismatch'):c.read_envelope(p,symbol='TEST',session='2026-11-12',now=now)
