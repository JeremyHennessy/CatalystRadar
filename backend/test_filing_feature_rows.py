import copy
import json
from pathlib import Path
import tempfile
import unittest
from archive_reviewed_filings import run
from private_archive_checkpoint import create,read_checkpoint
from filing_feature_rows import build,header_features,read_recorded_features
from test_archive_reviewed_filings import document,review

class FeatureTests(unittest.TestCase):
    def setUp(self):
        self.t=tempfile.TemporaryDirectory();self.addCleanup(self.t.cleanup)
        self.root=Path(self.t.name);self.reviews=self.root/'reviews.json';self.archive=self.root/'archive'
        self.raw=document().replace(b'</SEC-HEADER>',b'CONFORMED SUBMISSION TYPE: 8-K\nITEM INFORMATION: Results of Operations and Financial Condition\n</SEC-HEADER>')
        import hashlib
        r=review();r.update(source_sha256=hashlib.sha256(self.raw).hexdigest(),status='EARNINGS_REVIEW_PENDING',reason='Comparable earnings unknown')
        self.reviews.write_text(json.dumps({'records':[r]}))
        run([r],self.archive,get=lambda _:self.raw,clock=lambda:'2026-11-14T10:00:00Z',sleep=lambda _:None)
        self.report=build(self.reviews,self.archive,'2026-11-14T12:00:00Z')
        self.check=read_checkpoint(create(self.reviews,self.archive,'2026-11-14T11:00:00Z'),self.reviews.read_bytes(),'2026-11-14T12:00:00Z')
    def read(self,r=None):return read_recorded_features(r or self.report,self.reviews.read_bytes(),self.check,'2026-11-14T13:00:00Z')
    def test_features_current_clock_no_financial_claims(self):
        row=self.report['rows'][0]
        self.assertEqual(row['features'][1]['value'],1)
        self.assertIsNone(row['financial_comparators']);self.assertIsNone(row['decision_utc'])
        self.assertFalse(row['eligible']);self.assertEqual(len(self.read()),1)
    def test_header_span_points_to_exact_bytes(self):
        import hashlib
        span=self.report['rows'][0]['features'][0]['sources'][0]['header_span']
        self.assertEqual(hashlib.sha256(self.raw[span['byte_start']:span['byte_end']]).hexdigest(),span['sha256'])
    def test_exhibit_mentions_do_not_count(self):
        raw=self.raw.replace(b'ITEM INFORMATION: Results of Operations and Financial Condition\n',b'')+b'<DOCUMENT>Results of Operations and Financial Condition</DOCUMENT>'
        values,_=header_features(raw,'123',review()['accession'])
        self.assertEqual(values['header_reports_results_of_operations'],0)
    def test_missing_original_retains_row(self):
        next(self.archive.glob('*.txt')).unlink();r=build(self.reviews,self.archive,'2026-11-14T12:00:00Z')
        self.assertEqual(len(r['rows']),1);self.assertEqual(r['rows'][0]['features'],[])
    def test_changed_original_retains_row(self):
        next(self.archive.glob('*.txt')).write_bytes(b'changed')
        self.assertEqual(build(self.reviews,self.archive)['structural_feature_rows'],0)
    def test_compute_before_observation_not_admitted(self):
        self.assertEqual(build(self.reviews,self.archive,'2026-11-14T09:00:00Z')['structural_feature_rows'],0)
    def test_recorded_artifact_cannot_gain_financial_qualification(self):
        r=copy.deepcopy(self.report);r['rows'][0]['eligible']=True
        with self.assertRaises(ValueError):self.read(r)
    def test_source_checkpoint_mismatch_rejected(self):
        r=copy.deepcopy(self.report);r['rows'][0]['features'][0]['sources'][0]['observed_utc']='2026-11-14T09:00:00Z'
        with self.assertRaises(ValueError):self.read(r)
    def test_unknown_computation_clock_rejected(self):
        r=copy.deepcopy(self.report);r['computed_at']='2027-01-01T00:00:00Z'
        with self.assertRaises(ValueError):self.read(r)
    def test_invalid_span_rejected(self):
        r=copy.deepcopy(self.report);r['rows'][0]['features'][0]['sources'][0]['header_span']['byte_end']=999999
        with self.assertRaises(ValueError):self.read(r)

if __name__=='__main__':unittest.main()
