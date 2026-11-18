import tempfile,unittest
from pathlib import Path
from observed_outcome_coverage import candidate_dates,summarize,read,build
class ObservedCoverageTests(unittest.TestCase):
    def test_before_at_after_close(self):
        self.assertEqual(candidate_dates('2026-11-16T20:59:59+00:00'),['2026-11-16','2026-11-17'])
        for t in ['21:00:00','21:00:01']:
            self.assertEqual(candidate_dates('2026-11-16T'+t+'+00:00'),['2026-11-17','2026-11-18'])
    def test_weekend_holiday_and_early_close(self):
        self.assertEqual(candidate_dates('2026-11-14T23:33:00+00:00'),['2026-11-16','2026-11-17'])
        self.assertEqual(candidate_dates('2026-11-26T12:00:00+00:00'),['2026-11-27','2026-11-30'])
        self.assertEqual(candidate_dates('2026-11-27T18:00:00+00:00'),['2026-11-30','2026-12-01'])
    def test_timezone_required(self):
        with self.assertRaises(ValueError):candidate_dates('2026-11-16T12:00:00')
    def records(self):
        return [{'issuer_cik':'0000000123','accession':'a','observed_utc':x,'kind':'METADATA_OBSERVED','sec_accepted_utc':'2026-01-01T00:00:00Z'} for x in ['2026-11-17T14:00:00Z','2026-11-14T23:00:00Z']]
    def test_no_backdating_or_return_and_conflict_retained(self):
        records=self.records();records.append(dict(records[1],issuer_cik='0000000456'))
        out=summarize(records,{'2026-11-16'})
        self.assertEqual(out['issuer_accession_pairs'],2);self.assertEqual(out['unique_accessions'],1)
        for r in out['events']:
            self.assertTrue(r['accession_issuer_conflict']);self.assertEqual(r['candidate_scheduled_start'],'2026-11-16')
            self.assertEqual(r['missing_from_all_retained_series'],['2026-11-17']);self.assertIsNone(r['return_value'])
    def test_sufficient_dates_never_admit_identity_or_outcomes(self):
        out=summarize(self.records(),{'2026-11-16','2026-11-17'})
        self.assertEqual(out['coverage_bound_passes'],1);self.assertEqual(out['qualified_outcomes'],0)
        self.assertFalse(out['events'][0]['qualified'])
    def test_wrong_pin_and_changed_receipt_inventory(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'bad';p.write_bytes(b'x')
            with self.assertRaises(ValueError):read(p,'0'*64,1)
            with self.assertRaisesRegex(ValueError,'inventory'):build(t,p,t)
