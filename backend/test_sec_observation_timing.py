"""Synthetic archived-response regression tests; no provider calls."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import discover_sec

ACC='0000000001-26-000001'
RECENT='2026-11-14T12:00:00+00:00'
HISTORY='2026-11-14T12:01:00+00:00'
DOCUMENT='2026-11-14T12:02:00+00:00'

def columns(present=True, form='8-K'):
    return {k:([v] if present else []) for k,v in {
        'accessionNumber':ACC,'filingDate':'2026-11-12',
        'acceptanceDateTime':'2026-11-12T23:00:00Z',
        'form':form,'primaryDocument':'report.htm'}.items()}

class ObservationTests(unittest.TestCase):
    def run_case(self, recent=False, historical=True, conflict=False, document=True):
        root=Path(self.tmp.name)/'archive'
        responses=[(json.dumps({'name':'Synthetic issuer','tickers':['TEST'],
            'filings':{'recent':columns(recent),'files':([{'name':'history.json',
            'filingFrom':'2026-11-01','filingTo':'2026-11-13'}] if historical else [])}}).encode(), RECENT)]
        if historical: responses.append((json.dumps(columns(form='8-K/A' if conflict else '8-K')).encode(),HISTORY))
        responses.append(((f'<SEC-DOCUMENT>{ACC}').encode() if document else b'<html>blocked</html>',DOCUMENT))
        def get(archive,url,label):
            raw,when=responses.pop(0)
            return raw,{'url':url,'path':label,'retrieved_utc':when,'sha256':hashlib.sha256(raw).hexdigest()}
        with patch.object(discover_sec.Archive,'get',get):
            return discover_sec.run(root,[{'cik':'1','ticker':'TEST'}],
                '2026-11-01T00:00:00Z','2026-11-13T23:59:00Z','synthetic')
    def setUp(self):self.tmp=tempfile.TemporaryDirectory()
    def tearDown(self):self.tmp.cleanup()
    def test_naive_timestamp_rejected(self):
        with self.assertRaisesRegex(ValueError,'explicit timezone'):
            discover_sec.parse('2026-11-14T12:00:00')
    def test_history_uses_own_retrieval_not_recent(self):
        event=self.run_case()['events'][0]
        self.assertEqual(event['discovered_utc'],HISTORY)
        self.assertEqual(event['metadata_observations'][0]['path'],'history.json')
        self.assertEqual(event['document_observed_utc'],DOCUMENT)
        self.assertIsNone(event['first_public_utc'])
        self.assertNotEqual(event['sec_accepted_utc'],event['discovered_utc'])
    def test_identical_duplicate_keeps_both_source_vintages(self):
        event=self.run_case(recent=True)['events'][0]
        self.assertEqual(event['discovered_utc'],RECENT)
        self.assertEqual(len(event['metadata_observations']),2)
        self.assertTrue(all(len(o['sha256'])==64 for o in event['metadata_observations']))
    def test_conflicting_revision_does_not_silently_replace(self):
        report=self.run_case(recent=True,conflict=True)
        self.assertEqual(report['events'],[])
        self.assertEqual(report['issuers'][0]['status'],'INCOMPLETE')
        self.assertIn('conflicting duplicate',report['issuers'][0]['errors'][0])
    def test_invalid_document_has_no_content_observation(self):
        event=self.run_case(document=False)['events'][0]
        self.assertIsNone(event['document_observed_utc'])
        self.assertEqual(event['status'],'INVALID_DOCUMENT_RESPONSE')
    def test_absent_rows_are_not_deletions_or_historical_evidence(self):
        report=self.run_case(historical=False)
        self.assertEqual(report['events'],[])
        self.assertFalse(report['historical_availability_verified'])
        self.assertFalse(report['coverage_complete_for_orders'])
        self.assertIn('DOES_NOT_PROVE_DELETION',report['absence_semantics'])

if __name__=='__main__':unittest.main()
