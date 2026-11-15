import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from candidate_rehearsal import summarize_latest,canonical
from normalize_candidates import normalize

class RehearsalTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
        (self.root/'data/sec-observations').mkdir(parents=True);(self.root/'data/sec-snapshots').mkdir()
        raw=json.dumps({'cik':1,'filings':{'recent':{
            'accessionNumber':['0000000001-20-000001'],'form':['8-K'],
            'filingDate':['2020-01-01'],'acceptanceDateTime':['2020-01-01T12:00:00Z'],'primaryDocument':['x.htm']}}}).encode()
        sha=hashlib.sha256(raw).hexdigest();self.snapshot=self.root/'data/sec-snapshots'/f'{sha}.json';self.snapshot.write_bytes(raw)
        self.report={'run_id':'20261116T120000000000Z','started_at':'2026-11-16T12:00:00Z',
            'finished_at':'2026-11-16T12:00:05Z','errors':[],
            'sources':[{'url':'https://data.sec.gov/submissions/CIK0000000001.json','ticker':'TEST',
                'request_utc':'2026-11-16T12:00:01Z','retrieved_utc':'2026-11-16T12:00:02Z',
                'sha256':sha,'byte_count':len(raw),'archive_path':str(self.snapshot.relative_to(self.root))}]}
        self.receipt=self.root/'data/sec-observations'/f"{self.report['run_id']}.json";self.save()
    def save(self):self.receipt.write_text(json.dumps(self.report))
    def result(self):return summarize_latest(self.root,self.report,'2026-11-16T13:00:00Z')
    def test_real_path_reproduces_normalizer_and_unknowns(self):
        out=self.result();normalized=normalize([self.report],self.root)
        self.assertEqual(out['status'],'REHEARSAL_AVAILABLE');self.assertEqual(out['counts']['metadata_candidates'],1)
        self.assertEqual(out['counts']['older_than_96h_candidates'],1)
        self.assertEqual(out['normalizer_output_sha256'],hashlib.sha256(canonical(normalized)).hexdigest())
        self.assertTrue(all(v['candidate_status_counts']=={'UNKNOWN':1} for v in out['family_fact_unknowns'].values()))
        self.assertEqual(out['qualified_count'],0);self.assertFalse(out['protocol_activated'])
        self.assertEqual(out['source_observations'][0]['retrieved_utc'],self.report['sources'][0]['retrieved_utc'])
    def test_missing_receipt_not_a_zero_cohort(self):
        self.receipt.unlink();out=self.result();self.assertEqual(out['status'],'UNAVAILABLE');self.assertIsNone(out['counts'])
    def test_changed_latest_not_silently_treated_as_receipt(self):
        self.report['errors']=['new error'];out=self.result();self.assertEqual(out['status'],'UNAVAILABLE')
    def test_future_report_unavailable(self):
        out=summarize_latest(self.root,self.report,'2026-11-16T11:00:00Z');self.assertEqual(out['status'],'UNAVAILABLE')
    def test_changed_snapshot_retained_as_partial_not_success(self):
        self.snapshot.write_bytes(b'{}');out=self.result()
        self.assertEqual(out['status'],'PARTIAL_REHEARSAL');self.assertEqual(out['counts']['source_status_counts'],{'INVALID':1})
        self.assertEqual(out['source_observations'][0]['validation_status'],'INVALID')
    def test_original_access_denial_retained(self):
        self.report['sources'].append({'ticker':'FAIL','error':'HTTP 429 from public source'})
        self.report['errors']=[{'ticker':'FAIL','error':'HTTP 429 from public source'}];self.save()
        out=self.result();self.assertEqual(out['status'],'PARTIAL_REHEARSAL');self.assertEqual(out['scan_errors'],self.report['errors'])
        self.assertEqual(out['counts']['metadata_candidates'],1)
    def test_no_sources_cannot_claim_successful_zero_cohort(self):
        self.report['sources']=[];self.save();self.assertEqual(self.result()['status'],'PARTIAL_REHEARSAL')
    def test_unknown_run_id_is_unavailable(self):
        out=summarize_latest(self.root,{'sources':[]},'2026-11-16T13:00:00Z');self.assertIsNone(out['counts'])
    def test_deterministic_same_bytes_and_anchor(self):self.assertEqual(self.result(),self.result())
    def test_newest_only_no_claim_other_runs_loaded(self):
        old=copy.deepcopy(self.report);old['run_id']='20261116T110000000000Z'
        (self.receipt.parent/f"{old['run_id']}.json").write_text(json.dumps(old))
        out=self.result();self.assertEqual(out['counts']['candidate_observations'],1);self.assertIn('latest retained run only',out['scope'])

if __name__=='__main__':unittest.main()
