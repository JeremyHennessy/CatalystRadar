import copy,json,tempfile,unittest
from pathlib import Path
import financial_context_overlap as m
from financial_pair_candidates import publish,write_private,sha

class OverlapTests(unittest.TestCase):
    def pair(self,adsh='A',db='a'*64,cik='00123',prior='1.0',current='2',version='us-gaap/2026'):
        base=dict(adsh=adsh,tag='Revenues',version=version,qtrs='1',uom='USD',segments='',coreg='')
        return dict(issuer_cik_as_filed=cik,accession=adsh,database_sha256=db,source_archive_sha256='b'*64,filing_date_as_filed='20260501',accepted_as_filed='2026-05-01 16:00:00.0',training_ready=False,comparability_verified=False,decision_utc=None,outcome=None,current=dict(base,rowid=1,ddate='20260331',value=current),prior=dict(base,rowid=2,ddate='20250331',value=prior))
    def test_exact_decimal_equal_different_and_cik_normalization(self):
        a=self.pair();b=self.pair('B','c'*64,'123',prior='1',current='3')
        summary,groups=m.contexts({'q2':[a],'q3':[b]})
        self.assertEqual(summary['fact_observations'],4);self.assertEqual(summary['exact_context_keys'],2)
        self.assertEqual(summary['overlap_counts']['cross_batch_numerically_equal'],1)
        self.assertEqual(summary['overlap_counts']['cross_batch_different_reported_numbers'],1)
        self.assertTrue(all(not g['restatement_verified'] for g in groups))
    def test_no_decimal_context_rounding(self):
        a=self.pair(current='1234567890123456789012345678901');b=self.pair('B','c'*64,current='1234567890123456789012345678902')
        summary,_=m.contexts({'a':[a],'b':[b]})
        self.assertEqual(summary['overlap_counts']['different_reported_numbers'],1)
    def test_duplicate_source_reference_rejected(self):
        with self.assertRaisesRegex(ValueError,'duplicate source'):m.contexts({'a':[self.pair()],'b':[self.pair()]})
    def test_taxonomy_versions_not_merged(self):
        summary,groups=m.contexts({'a':[self.pair()],'b':[self.pair('B','c'*64,version='us-gaap/2025')]})
        self.assertEqual(groups,[]);self.assertEqual(summary['version_different_near_contexts_unassessed'],2)
    def test_same_accession_not_distinct_event(self):
        summary,groups=m.contexts({'a':[self.pair()],'b':[self.pair(db='c'*64)]})
        self.assertEqual(summary['overlap_counts']['same_accession_multiple_sources'],2)
        self.assertEqual(summary['unique_accessions'],1)
    def test_missing_invalid_or_qualified_input_rejected(self):
        for field,value in [('issuer_cik_as_filed','0'),('training_ready',True),('decision_utc','2026-05-01')]:
            p=self.pair();p[field]=value
            with self.assertRaises(ValueError):m.contexts({'a':[p]})
        for value in ['', 'NaN','Infinity']:
            p=self.pair(current=value)
            with self.assertRaises(ValueError):m.contexts({'a':[p]})
    def test_completed_input_binding_and_failures(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);p=root/'batch';p.mkdir();write_private(p/'INCOMPLETE',{})
            summary=dict(candidate_pairs=1,database_sha256='a'*64,source_archive_sha256='b'*64)
            publish(p,summary,[self.pair()]);checkpoint=root/'checkpoint.json'
            checkpoint.write_text(json.dumps({'batches':{'q2':dict(summary,private_candidates_sha256=sha(p/'candidate-pairs.json'))}}))
            result,_=m.audit(checkpoint,{'q2':p});self.assertEqual(result['fact_observations'],2)
            (p/'INCOMPLETE').write_text('failed')
            with self.assertRaisesRegex(ValueError,'incomplete'):m.audit(checkpoint,{'q2':p})
            (p/'INCOMPLETE').unlink();(p/'candidate-pairs.json').write_text('[]')
            with self.assertRaisesRegex(ValueError,'hash mismatch'):m.audit(checkpoint,{'q2':p})
    def test_strict_json(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'bad.json'
            for value in ['{"x":1,"x":2}','{"x":NaN}']:
                p.write_text(value)
                with self.assertRaises(ValueError):m.read(p)

if __name__=='__main__':unittest.main()
