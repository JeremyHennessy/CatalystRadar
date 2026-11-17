"""Offline denial diagnostics: bounded, sanitized and never retried."""
import io
import os
import json
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import patch
from discover_sec import Archive, http_error_diagnostic
import scan_watchlist

class HttpDiagnosticsTests(unittest.TestCase):
 def setUp(self):
  identity=patch.dict(os.environ,{"SEC_CONTACT_EMAIL":"fixture@example.invalid"});identity.start();self.addCleanup(identity.stop)
 def test_fixed_categories_without_body_or_headers(self):
  for phrase, category in [('Undeclared Automated Tool','UNDECLARED_AUTOMATED_TOOL_RESPONSE'),('Request Rate Threshold Exceeded','RATE_THRESHOLD_RESPONSE'),('Access Denied','ACCESS_DENIED_RESPONSE'),('other','HTTP_ERROR_UNCLASSIFIED')]:
   with self.subTest(phrase=phrase):
    body=io.BytesIO((phrase+' private-marker@example.test').encode())
    error=urllib.error.HTTPError('https://data.sec.gov/test',403,'private reason',{'Set-Cookie':'private-cookie'},body)
    result=http_error_diagnostic(error)
    self.assertEqual(result['category'],category)
    self.assertTrue(body.closed)
    self.assertNotIn('private',json.dumps(result))
 def test_bounded_body_does_not_classify_beyond_limit(self):
  body=io.BytesIO(b'x'*4096+b'Undeclared Automated Tool')
  result=http_error_diagnostic(urllib.error.HTTPError('url',403,'denied',{},body))
  self.assertEqual(result,{'category':'HTTP_ERROR_UNCLASSIFIED','body_bytes_examined':4096,'body_truncated':True})
 def test_unreadable_body_is_still_closed(self):
  class Broken(io.BytesIO):
   def read(self,*args):raise OSError('private details')
  body=Broken();result=http_error_diagnostic(urllib.error.HTTPError('url',403,'denied',{},body))
  self.assertTrue(body.closed);self.assertEqual(result['category'],'HTTP_ERROR_BODY_UNAVAILABLE')
 def test_archive_records_structured_status_and_no_raw_denial(self):
  with tempfile.TemporaryDirectory() as temp:
   body=io.BytesIO(b'Access Denied private-marker')
   error=urllib.error.HTTPError('https://data.sec.gov/test',403,'private reason',{},body)
   with patch('discover_sec.HTTP.open',side_effect=error) as request:
    raw,meta=Archive(Path(temp),'unchanged-agent').get('https://data.sec.gov/test','test.json')
   self.assertIsNone(raw);self.assertEqual(request.call_count,1)
   self.assertEqual(meta['status'],403);self.assertEqual(meta['error'],'HTTP Error 403')
   self.assertEqual(meta['http_diagnostic']['category'],'ACCESS_DENIED_RESPONSE')
   self.assertNotIn('private',Path(temp,'manifest.jsonl').read_text())
   self.assertFalse(Path(temp,'test.json').exists())
 def test_scan_retains_sanitized_diagnostic_and_stops_after_denial(self):
  for status in (403,429):
   with self.subTest(status=status),tempfile.TemporaryDirectory() as temp:
    root=Path(temp);(root/'data').mkdir()
    (root/'data/watchlist.json').write_text(json.dumps([{'ticker':'ONE','cik':'1'},{'ticker':'TWO','cik':'2'}]))
    error=urllib.error.HTTPError('https://data.sec.gov/test',status,'private reason',{},io.BytesIO(b'Request Rate Threshold Exceeded private-marker'))
    with patch('discover_sec.HTTP.open',side_effect=error) as request:
     report=scan_watchlist.scan(root)
    self.assertEqual(request.call_count,1)
    self.assertEqual(report['sources'][0]['status'],status)
    self.assertEqual(report['sources'][0]['http_diagnostic']['category'],'RATE_THRESHOLD_RESPONSE')
    self.assertEqual(report['sources'][1]['validation_status'],'NOT_ATTEMPTED_AFTER_DENIAL')
    self.assertEqual(report['events'],[]);self.assertEqual(report['orders_created'],0)
    self.assertNotIn('private',json.dumps(report['sources']))

if __name__=='__main__':unittest.main()
