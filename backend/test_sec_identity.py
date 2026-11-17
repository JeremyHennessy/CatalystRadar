import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from sec_identity import contact_email, user_agent
from discover_sec import Archive
import scan_watchlist


class IdentityTests(unittest.TestCase):
    def test_valid_contact_only_in_request_agent(self):
        with patch.dict(os.environ, {'SEC_CONTACT_EMAIL':'fixture@example.invalid'}):
            self.assertIn('fixture@example.invalid',user_agent(contact_email()))

    def test_missing_invalid_and_header_injection_fail_without_leak(self):
        for value in ('','secret-marker','fixture@example.invalid\nX: injection',' x@example.com','x@y.example\r'):
            with patch.dict(os.environ, {'SEC_CONTACT_EMAIL':value}):
                with self.assertRaises(ValueError) as e:contact_email()
                if value:self.assertNotIn(value,str(e.exception))

    def test_missing_contact_stops_before_network_or_output(self):
        with tempfile.TemporaryDirectory() as d,patch.dict(os.environ,{'SEC_CONTACT_EMAIL':''}),patch.object(Archive,'get') as get:
            with self.assertRaises(ValueError):scan_watchlist.scan(Path(d))
            get.assert_not_called();self.assertEqual(list(Path(d).iterdir()),[])

    def test_request_error_never_logs_contact(self):
        with tempfile.TemporaryDirectory() as d,patch('discover_sec.HTTP.open',side_effect=ValueError('fixture@example.invalid')):
            raw,meta=Archive(Path(d),'contact fixture@example.invalid').get('https://data.sec.gov/test','source.json')
            self.assertIsNone(raw)
            self.assertNotIn('fixture@example.invalid',json.dumps(meta))
            self.assertNotIn('fixture@example.invalid',(Path(d)/'manifest.jsonl').read_text())

    def test_reflected_contact_is_not_published_and_stops(self):
        with tempfile.TemporaryDirectory() as d,patch.dict(os.environ,{'SEC_CONTACT_EMAIL':'fixture@example.invalid'}):
            root=Path(d);(root/'data').mkdir()
            (root/'data/watchlist.json').write_text(json.dumps([{'ticker':'ONE','cik':'1'},{'ticker':'TWO','cik':'2'}]))
            raw=b'{"reflected":"fixture\\u0040example.invalid"}'
            with patch.object(Archive,'get',return_value=(raw,{'url':'https://data.sec.gov/test','status':200})) as get:
                report=scan_watchlist.scan(root)
            self.assertEqual(get.call_count,1)
            self.assertFalse((root/'data/sec-snapshots').exists())
            self.assertNotIn('fixture@example.invalid',json.dumps(report))
            self.assertFalse(report['metadata_window_complete'])
            self.assertEqual(report['orders_created'],0)

    def test_sec_opener_never_follows_redirects(self):
        import urllib.request
        from discover_sec import HTTP, NoRedirect
        handlers=[h for h in HTTP.handlers if isinstance(h,urllib.request.HTTPRedirectHandler)]
        self.assertEqual(len(handlers),1)
        self.assertIsInstance(handlers[0],NoRedirect)
        request=urllib.request.Request('https://data.sec.gov/test',headers={'User-Agent':'fixture@example.invalid'})
        for status in (301,302,303,307,308):
            self.assertIsNone(handlers[0].redirect_request(request,None,status,'redirect',{},'https://unapproved.invalid/'))

    def test_redirect_does_not_issue_second_request(self):
        import urllib.request, urllib.response, urllib.error
        from email.message import Message
        from discover_sec import NoRedirect
        seen=[]
        class SyntheticHTTPS(urllib.request.HTTPSHandler):
            def https_open(self,request):
                seen.append(request.full_url)
                headers=Message();headers['Location']='https://unapproved.invalid/'
                response=urllib.response.addinfourl(io.BytesIO(b'redirect'),headers,request.full_url,302)
                response.msg='Found'
                return response
        opener=urllib.request.build_opener(NoRedirect(),SyntheticHTTPS())
        with self.assertRaises(urllib.error.HTTPError):
            opener.open(urllib.request.Request('https://data.sec.gov/test',headers={'User-Agent':'fixture@example.invalid'}))
        self.assertEqual(seen,['https://data.sec.gov/test'])
