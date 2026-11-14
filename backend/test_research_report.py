import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from build_research_report import build

class ResearchReportTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root/'data/sec-snapshots').mkdir(parents=True)
        payload=json.dumps({'cik':123,'filings':{'recent':{'accessionNumber':['a'], 'form':['8-K']}}}).encode()
        sha=hashlib.sha256(payload).hexdigest()
        self.archive=self.root/'data/sec-snapshots/example.json'
        self.archive.write_bytes(payload)
        self.write('data/latest_scan.json',{'sources':[{'status':200,'archive_path':'data/sec-snapshots/example.json','sha256':sha,'retrieved_utc':'2026-11-14T10:00:00Z','url':'https://data.sec.gov/example'}]})
        self.review={'accession':'a','issuer_cik':'123','issuer':'Example','status':'OUTSIDE_SIGNAL_FAMILIES','source_sha256':'f'*64,'reviewed_utc':'2026-11-14T11:00:00Z'}
        self.write('data/filing_reviews.json',{'records':[self.review]})
        self.write('data/provenance.json',{'sources':[{'status':200,'sha256':'f'*64}]})
    def write(self,name,obj):
        (self.root/name).write_text(json.dumps(obj))
    def run_report(self):
        return build(self.root,'2026-11-14T12:00:00Z')
    def test_real_bytes_connected_but_no_outcomes_invented(self):
        r=self.run_report()
        self.assertEqual(r['counts']['metadata_identity_matched'],1)
        self.assertEqual(r['counts']['qualified_observations'],0)
        self.assertIsNone(r['records'][0]['outcome'])
        self.assertFalse(r['trade_eligible'])
        self.assertTrue(r['temporal_and_split_audits'].startswith('NOT_RUN'))
    def test_missing_archive_retains_record(self):
        self.archive.unlink();r=self.run_report()
        self.assertEqual(r['counts']['reviewed_records'],1)
        self.assertEqual(r['counts']['metadata_bytes_verified'],0)
    def test_changed_archive_retains_record(self):
        self.archive.write_bytes(b'{}')
        self.assertEqual(self.run_report()['counts']['metadata_identity_matched'],0)
    def test_metadata_issuer_must_match(self):
        self.review['issuer_cik']='456';self.write('data/filing_reviews.json',{'records':[self.review]})
        self.assertEqual(self.run_report()['counts']['metadata_identity_matched'],0)
    def test_metadata_accession_must_match(self):
        self.review['accession']='b';self.write('data/filing_reviews.json',{'records':[self.review]})
        self.assertEqual(self.run_report()['counts']['metadata_identity_matched'],0)
    def test_duplicate_reviews_rejected(self):
        self.write('data/filing_reviews.json',{'records':[self.review,self.review]})
        with self.assertRaises(ValueError):self.run_report()
    def test_path_traversal_rejected(self):
        scan=json.loads((self.root/'data/latest_scan.json').read_text())
        scan['sources'][0]['archive_path']='data/../elsewhere.json';self.write('data/latest_scan.json',scan)
        with self.assertRaises(ValueError):self.run_report()
    def test_future_observation_flagged(self):
        scan=json.loads((self.root/'data/latest_scan.json').read_text())
        scan['sources'][0]['retrieved_utc']='2026-11-15T10:00:00Z';self.write('data/latest_scan.json',scan)
        self.assertIn('METADATA_OBSERVED_AFTER_REPORT', self.run_report()['records'][0]['blockers'])
    def test_conflicting_duplicate_accession_not_matched(self):
        payload=json.dumps({'cik':123,'filings':{'recent':{'accessionNumber':['a','a'], 'form':['8-K','10-Q']}}}).encode()
        self.archive.write_bytes(payload)
        scan=json.loads((self.root/'data/latest_scan.json').read_text())
        scan['sources'][0]['sha256']=hashlib.sha256(payload).hexdigest();self.write('data/latest_scan.json',scan)
        self.assertEqual(self.run_report()['counts']['metadata_identity_matched'],0)
    def test_reproducible_same_inputs_clock(self):
        self.assertEqual(self.run_report(),self.run_report())

if __name__=='__main__':unittest.main()
