"""Issuer-atomic metadata admission. All source responses are mocked."""
import hashlib
import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch
import scan_watchlist as scanner

class Clock(datetime):
    @classmethod
    def now(cls, tz=None):
        return cls(2026, 11, 16, 12, tzinfo=timezone.utc)

def source():
    return {'cik':1,'name':'One','tickers':['ONE'],'filings':{'recent':{
        'accessionNumber':['0000000001-26-000001','0000000001-26-000002','0000000001-26-000000'],
        'acceptanceDateTime':['2026-11-16T10:00:00Z','2026-11-16T11:00:00Z','2026-11-01T10:00:00Z'],
        'filingDate':['2026-11-16','2026-11-16','2026-11-01'],
        'primaryDocument':['one.htm','two.htm','old.htm'], 'form':['8-K','8-K','10-Q']}}}

class ScanValidationTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        (self.root/'data').mkdir()
        self.config([{'ticker':'ONE','cik':'1'}])
    def tearDown(self):self.tmp.cleanup()
    def config(self, value):
        (self.root/'data/watchlist.json').write_text(json.dumps(value))
    def scan(self, value):
        raw=json.dumps(value).encode()
        def get(arc,url,label):
            return raw,{'url':url,'retrieved_utc':'2026-11-16T12:00:02Z',
                        'sha256':hashlib.sha256(raw).hexdigest(),'status':200}
        with patch.object(scanner,'datetime',Clock),patch.object(scanner.Archive,'get',get),patch.object(scanner,'stamp',return_value='2026-11-16T12:00:05Z'):
            return scanner.scan(self.root)
    def failed(self,value):
        result=self.scan(value)
        self.assertEqual(result['events'],[])
        self.assertEqual(result['successful_issuers'],0)
        self.assertFalse(result['metadata_window_complete'])
        self.assertEqual(result['sources'][0]['validation_status'],'METADATA_VALIDATION_FAILED')
        self.assertIn('archive_path',result['sources'][0]) # rejected bytes retained
        return result
    def test_validated_source_and_dynamic_scope(self):
        result=self.scan(source())
        self.assertEqual(len(result['events']),2)
        self.assertEqual(result['sources'][0]['validation_status'],'METADATA_WINDOW_VALIDATED')
        self.assertEqual(result['scope'],'1 configured issuer metadata feeds; NOT whole market')
    def test_wrong_cik_even_with_matching_ticker(self):
        value=source();value['cik']=2;self.failed(value)
    def test_missing_cik(self):
        value=source();del value['cik'];self.failed(value)
    def test_string_tickers_are_not_an_identity_list(self):
        value=source();value['tickers']='ONE';self.failed(value)
    def test_nonstring_ticker_list(self):
        value=source();value['tickers']=['ONE',None];self.failed(value)
    def test_mapping_tickers(self):
        value=source();value['tickers']={'ONE':True};self.failed(value)
    def test_other_valid_issuer_survives_later_validation_failure(self):
        self.config([{'ticker':'ONE','cik':'1'},{'ticker':'TWO','cik':'2'}])
        # Same source passes ONE then correctly fails TWO's CIK identity.
        result=self.scan(source())
        self.assertEqual(len(result['events']),2)
        self.assertEqual({e['ticker'] for e in result['events']},{'ONE'})
        self.assertEqual(result['successful_issuers'],1)
        self.assertFalse(result['metadata_window_complete'])
        self.assertEqual([s['validation_status'] for s in result['sources']],
                         ['METADATA_WINDOW_VALIDATED','METADATA_VALIDATION_FAILED'])
    def test_missing_ticker(self):
        value=source();value['tickers']=[];self.failed(value)
    def test_bad_later_accession_does_not_leak_earlier_event(self):
        value=source();value['filings']['recent']['accessionNumber'][1]='../../other'
        self.failed(value)
    def test_bad_later_acceptance_does_not_leak_earlier_event(self):
        value=source();value['filings']['recent']['acceptanceDateTime'][1]=''
        self.failed(value)
    def test_conflicting_duplicate_discards_issuer(self):
        value=source();value['filings']['recent']['accessionNumber'][1]='0000000001-26-000001'
        self.failed(value)
    def test_exact_duplicate_is_one_discovery(self):
        value=source()
        for values in value['filings']['recent'].values():values[1]=values[0]
        self.assertEqual(len(self.scan(value)['events']),1)
    def test_column_not_list(self):
        value=source();value['filings']['recent']['primaryDocument']='abc';self.failed(value)
    def test_bad_watchlist_is_rejected_before_fetch(self):
        for config in ([{'ticker':'ONE','cik':'0'}],[{'ticker':'ONE','cik':'../1'}],
                       [{'ticker':'ONE','cik':'1'},{'ticker':'TWO','cik':'01'}],
                       [{'ticker':'ONE','cik':'1'},{'ticker':'ONE','cik':'2'}],
                       [{'ticker':'bad ticker','cik':'1'}],{'ONE':1}):
            with self.subTest(config=config):
                self.config(config)
                with patch.object(scanner.Archive,'get') as fetch:
                    with self.assertRaises(ValueError):scanner.scan(self.root)
                    fetch.assert_not_called()
    def test_denied_source_and_unattempted_sources_are_explicit(self):
        self.config([{'ticker':'ONE','cik':'1'},{'ticker':'TWO','cik':'2'}])
        with patch.object(scanner.Archive,'get',return_value=(None,{'error':'HTTP Error 403: denied'})) as fetch:
            result=scanner.scan(self.root)
        self.assertEqual(fetch.call_count,1)
        self.assertEqual([s['validation_status'] for s in result['sources']],
                         ['FETCH_FAILED','NOT_ATTEMPTED_AFTER_DENIAL'])
        self.assertEqual(result['successful_issuers'],0)
        self.assertEqual(result['orders_created'],0)

if __name__=='__main__':unittest.main()
