import json
from pathlib import Path
import tempfile
import unittest
from frozen_financial_cohort import select, build, digest, STRATA

class FrozenCohortTests(unittest.TestCase):
    def setUp(self):
        self.plan = {'strata':list(STRATA),'per_stratum':2}
        self.groups = [{'context_id':f'{s}-{i}', 'category':'multiple_accession_context',
            'cross_batch':s!=2,'numeric_relation':'different_reported_numbers' if s==1 else 'numerically_equal',
            'context':{'issuer_cik':'123','tag':'Revenues','ddate':'20250331','qtrs':'1'},
            'observations':[{'accession':'0000000123-26-000001','source_rowid':1,'database_sha256':'a'*64}]}
            for s in range(3) for i in range(3)]
    def test_order_invariant(self):
        self.assertEqual(select(self.plan,self.groups),select(self.plan,list(reversed(self.groups))))
    def test_no_availability_or_value_selection(self):
        before=[g['context_id'] for _,g in select(self.plan,self.groups)]
        for g in self.groups:g['value']='9999';g['original_available']=True
        self.assertEqual(before,[g['context_id'] for _,g in select(self.plan,self.groups)])
    def test_fail_policy_changes(self):
        self.plan['per_stratum']=1
        with self.assertRaises(ValueError):select(self.plan,self.groups)
    def test_fail_insufficient(self):
        with self.assertRaises(ValueError):select(self.plan,self.groups[:4])
    def test_fail_duplicates(self):
        with self.assertRaises(ValueError):select(self.plan,self.groups+self.groups[:1])
    def fixture(self, folder):
        raw=json.dumps(self.groups).encode();self.plan['input_groups_sha256']=digest(raw)
        plan=json.dumps(self.plan).encode();selection={'plan_sha256':digest(plan),'cases':[{'stratum':s,'context_id':g['context_id']} for s,g in select(self.plan,self.groups)]}
        paths=[folder/'plan',folder/'selection',folder/'groups']
        for p,b in zip(paths,[plan,json.dumps(selection).encode(),raw]):p.write_bytes(b)
        return paths
    def test_abstains_without_originals(self):
        with tempfile.TemporaryDirectory() as t:
            p=self.fixture(Path(t));r=build(*p,[])
            self.assertEqual(len(r['cases']),6);self.assertEqual(r['qualified_cases'],0)
            self.assertTrue(all(not c['qualified'] and c['growth'] is None for c in r['cases']))
            self.assertTrue(all(c['observations'][0]['original_status']=='NOT_IN_CHECKED_INVENTORY' for c in r['cases']))
    def test_changed_groups_rejected(self):
        with tempfile.TemporaryDirectory() as t:
            p=self.fixture(Path(t));p[2].write_text('[]')
            with self.assertRaises(ValueError):build(*p,[])
    def test_changed_frozen_selection_rejected(self):
        with tempfile.TemporaryDirectory() as t:
            p=self.fixture(Path(t));s=json.loads(p[1].read_text());s['cases'].reverse();p[1].write_text(json.dumps(s))
            with self.assertRaises(ValueError):build(*p,[])
    def test_receipt_hash_rejected(self):
        with tempfile.TemporaryDirectory() as t:
            folder=Path(t);p=self.fixture(folder);receipt=folder/'receipt';receipt.write_text('{}')
            with self.assertRaises(ValueError):build(*p,[{'receipt':str(receipt),'receipt_sha256':'0'*64}])
    def original(self, folder, mutation=None):
        import zipfile
        from test_inline_context_evidence import InlineEvidenceTests
        raw=InlineEvidenceTests().xml();package=folder/'source.zip'
        with zipfile.ZipFile(package,'w') as z:z.writestr('primary.htm',raw)
        r={'accession':'0000000123-26-000001','issuer_cik_verified':'123',
           'zip_sha256':digest(package.read_bytes()),'zip_byte_count':package.stat().st_size,
           'primary_member':'primary.htm','primary_member_sha256':digest(raw)}
        if mutation:mutation(r,package)
        receipt=folder/'receipt';receipt.write_text(json.dumps(r))
        return {'receipt':str(receipt),'receipt_sha256':digest(receipt.read_bytes()),'package':str(package)}
    def test_positive_original_is_candidate_not_qualified(self):
        with tempfile.TemporaryDirectory() as t:
            folder=Path(t);p=self.fixture(folder);r=build(*p,[self.original(folder)])
            o=r['cases'][0]['observations'][0]
            self.assertEqual(o['original_status'],'RETAINED_REQUIRES_CONTEXT_REVIEW')
            self.assertEqual(o['same_issuer_concept_candidates'][0]['fact_id'],'f1')
            self.assertFalse(o['exact_archive_to_original_match_verified']);self.assertEqual(r['qualified_cases'],0)
    def test_bad_original_binding(self):
        mutations=[lambda r,p:r.update(zip_sha256='0'*64),lambda r,p:r.update(zip_byte_count=1),
                   lambda r,p:r.update(primary_member='absent'),lambda r,p:r.update(primary_member_sha256='0'*64),
                   lambda r,p:r.update(issuer_cik_verified='999')]
        for mutation in mutations:
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as t:
                folder=Path(t);p=self.fixture(folder)
                with self.assertRaises(ValueError):build(*p,[self.original(folder,mutation)])
    def test_duplicate_original_rejected(self):
        with tempfile.TemporaryDirectory() as t:
            folder=Path(t);p=self.fixture(folder);o=self.original(folder)
            with self.assertRaises(ValueError):build(*p,[o,o])
    def test_bounds(self):
        from frozen_financial_cohort import bounded_read
        with tempfile.TemporaryDirectory() as t:
            folder=Path(t);p=self.fixture(folder)
            with self.assertRaises(ValueError):bounded_read(p[0],1)
            with self.assertRaises(ValueError):build(*p,[{}]*101)
    def test_selection_digest_uses_validated_snapshot(self):
        from unittest.mock import patch
        from frozen_financial_cohort import parse as real_parse
        with tempfile.TemporaryDirectory() as t:
            folder=Path(t);p=self.fixture(folder);o=self.original(folder)
            expected=digest(p[1].read_bytes())
            def mutate(raw,sha):
                p[1].write_text('changed after validation')
                return real_parse(raw,sha)
            with patch('frozen_financial_cohort.parse',side_effect=mutate):r=build(*p,[o])
            self.assertEqual(r['selection_sha256'],expected)
