import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from normalize_candidates import normalize
from fact_admission import CONTRACTS,admit_facts,classify_family
from unittest.mock import patch

class CandidateTests(unittest.TestCase):
    def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
    def tearDown(self):self.tmp.cleanup()
    def sample(self,rid='run1',accepted='2020-01-01T12:00:00Z',form='8-K'):
        rr={'accessionNumber':['0000000001-20-000001'],'acceptanceDateTime':[accepted],
            'form':[form],'filingDate':['2020-01-01'],'primaryDocument':['x.htm']}
        raw=json.dumps({'cik':'1','tickers':['NOW'],'filings':{'recent':rr}}).encode()
        sha=hashlib.sha256(raw).hexdigest();path=self.root/'data/sec-snapshots'/f'{sha}.json';path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
        return {'run_id':rid,'started_at':'2026-11-16T12:00:00Z','finished_at':'2026-11-16T12:00:05Z','errors':[],
                'sources':[{'ticker':'NOW','url':'https://data.sec.gov/submissions/CIK0000000001.json','sha256':sha,
                            'retrieved_utc':'2026-11-16T12:00:02Z','archive_path':str(path.relative_to(self.root)),'byte_count':len(raw)}]}
    def test_old_filing_retained_not_fresh_or_eligible(self):
        r=normalize([self.sample()],self.root);c=r['candidates'][0]
        self.assertTrue(c['observations'][0]['older_than_96h_at_observation'])
        self.assertIsNone(c['first_public_utc']);self.assertFalse(c['qualified'])
        self.assertEqual(c['first_retained_observation_utc'],'2026-11-16T12:00:02+00:00')
        self.assertTrue(all(v['status']=='UNKNOWN' for v in c['family_admission'].values()))
    def test_amendments_conflicts_and_duplicates_preserved(self):
        a=self.sample();b=self.sample('run2',form='8-K/A')
        r=normalize([a,b],self.root);c=r['candidates'][0]
        self.assertEqual(len(c['observations']),2);self.assertTrue(c['metadata_revision_conflict'])
        self.assertIsNone(c['event_group'])
    def test_repeat_observation_not_independent_event(self):
        a=self.sample();b=copy.deepcopy(a);b['run_id']='run2'
        r=normalize([a,b],self.root)
        self.assertEqual((r['candidate_count'],r['candidate_observation_count']),(1,2))
        self.assertFalse(r['candidates'][0]['metadata_revision_conflict'])
    def test_missing_source_and_errors_stay_visible(self):
        a=self.sample();a['sources']=[{'ticker':'NOW'}];a['errors']=[{'ticker':'NOW','error':'HTTP 429 from public source'}]
        r=normalize([a],self.root)
        self.assertEqual(r['candidate_count'],0);self.assertEqual(r['source_results'][0]['status'],'UNAVAILABLE')
        self.assertEqual(r['report_errors'][0]['errors'],a['errors'])
    def test_tamper_or_wrong_cik_or_clock_held(self):
        for kind in ('hash','cik','clock'):
            a=self.sample()
            if kind=='hash':(self.root/a['sources'][0]['archive_path']).write_bytes(b'{}')
            elif kind=='cik':a['sources'][0]['url']='https://data.sec.gov/submissions/CIK0000000002.json'
            else:a['sources'][0]['retrieved_utc']='2026-11-16T11:00:00Z'
            r=normalize([a],self.root);self.assertEqual(r['candidate_count'],0);self.assertEqual(r['source_results'][0]['status'],'INVALID')
    def test_future_or_missing_acceptance_retained_held(self):
        for t in ('2027-01-01T00:00:00Z',None):
            r=normalize([self.sample(accepted=t)],self.root);self.assertEqual(r['candidate_count'],1)
            self.assertEqual(r['candidates'][0]['status'],'HELD_METADATA_CONFLICT_OR_INVALID')
    def test_malformed_source_does_not_drop_next_valid_source(self):
        for bad_clock in (None,12):
            a=self.sample();good=copy.deepcopy(a['sources'][0]);a['sources'][0]['retrieved_utc']=bad_clock;a['sources'].append(good)
            result=normalize([a],self.root)
            self.assertEqual(result['candidate_count'],1)
            self.assertEqual([s['status'] for s in result['source_results']],['INVALID','HASH_AND_METADATA_VALIDATED'])
    def test_string_submission_columns_rejected_without_aborting(self):
        a=self.sample();good=copy.deepcopy(a['sources'][0]);bad=copy.deepcopy(good)
        raw=json.dumps({'cik':'1','filings':{'recent':{k:'x' for k in ('accessionNumber','filingDate','acceptanceDateTime','form','primaryDocument')}}}).encode()
        sha=hashlib.sha256(raw).hexdigest();path=self.root/'data/sec-snapshots'/f'{sha}.json';path.write_bytes(raw)
        bad.update(sha256=sha,archive_path=str(path.relative_to(self.root)),byte_count=len(raw));a['sources']=[bad,good]
        result=normalize([a],self.root)
        self.assertEqual(result['candidate_count'],1)
        self.assertEqual([s['status'] for s in result['source_results']],['INVALID','HASH_AND_METADATA_VALIDATED'])
    def test_duplicate_report_ids_rejected(self):
        a=self.sample()
        with self.assertRaises(ValueError):normalize([a,a],self.root)
    def test_non_target_form_not_in_candidate_cohort(self):
        self.assertEqual(normalize([self.sample(form='10-Q')],self.root)['candidate_count'],0)
    def test_report_order_deterministic(self):
        a=self.sample('b');b=self.sample('a',form='8-K/A')
        self.assertEqual(normalize([a,b],self.root),normalize([b,a],self.root))

class FactTests(unittest.TestCase):
    def facts(self,family):
        s=CONTRACTS[family];return {**{x:True for x in s['bool']},**{x:1 for x in s['number']}}
    def test_every_required_missing_operand_is_unknown(self):
        for family,spec in CONTRACTS.items():
            f=self.facts(family)
            for field in f:
                x=f.copy();del x[field];r=admit_facts(family,x)
                self.assertEqual(r['status'],'UNKNOWN');self.assertIn(field,r['missing_fields'])
    def test_every_required_null_operand_is_unknown(self):
        for family in CONTRACTS:
            f=self.facts(family)
            for field in f:
                x=f.copy();x[field]=None;self.assertEqual(admit_facts(family,x)['status'],'UNKNOWN')
    def test_falsy_values_present_not_inferred_or_positive(self):
        for family,s in CONTRACTS.items():
            f={**{x:False for x in s['bool']},**{x:0 for x in s['number']}}
            r=admit_facts(family,f);self.assertEqual(r['status'],'COMPLETE_FACT_TYPES_ONLY');self.assertIsNone(r['signal']);self.assertFalse(r['qualified'])
    def test_invalid_types_and_nonfinite(self):
        for family,spec in CONTRACTS.items():
            for name in spec['number']:
                for bad in (True,'1',float('nan'),float('inf'),10**1000):
                    f=self.facts(family);f[name]=bad;self.assertEqual(admit_facts(family,f)['status'],'UNKNOWN')
            for name in spec['bool']:
                f=self.facts(family);f[name]='false';self.assertEqual(admit_facts(family,f)['status'],'UNKNOWN')
    def test_guidance_only_existing_earnings_branch(self):
        self.assertEqual(admit_facts('GUIDANCE_RAISE',self.facts('GUIDANCE_RAISE'))['required_event_type'],'EARNINGS')
    def test_missing_families_do_not_become_negative_signals(self):
        self.assertTrue(all(admit_facts(f,{})['status']=='UNKNOWN' for f in CONTRACTS))
    def test_wrapper_does_not_call_classifier_for_missing_facts(self):
        with patch('radar.classify') as classifier:
            r=classify_family('EARNINGS_GROWTH',{'event_type':'EARNINGS','facts':{}},'unused','unused')
            self.assertEqual(r['status'],'UNKNOWN');classifier.assert_not_called()
    def test_wrapper_preserves_common_gate_failure(self):
        e={'event_type':'EARNINGS','facts':self.facts('EARNINGS_GROWTH')}
        with patch('radar.classify',return_value={'status':'BLOCKED','signals':[],'reasons':['missing source']}) as classifier:
            r=classify_family('EARNINGS_GROWTH',e,'cutoff','root','session')
            self.assertEqual(r['status'],'BLOCKED');self.assertFalse(r['qualified']);classifier.assert_called_once()
    def test_wrapper_does_not_return_other_family_signal(self):
        e={'event_type':'EARNINGS','facts':self.facts('EARNINGS_GROWTH')}
        with patch('radar.classify',return_value={'status':'OBSERVE','signals':['GUIDANCE_RAISE'],'reasons':[]}):
            r=classify_family('EARNINGS_GROWTH',e,'cutoff','root')
            self.assertEqual(r['status'],'NO_RULE_MATCH');self.assertIsNone(r['signal'])
    def test_wrapper_keeps_guidance_mapping_explicit(self):
        e={'event_type':'GUIDANCE','facts':self.facts('GUIDANCE_RAISE')}
        with patch('radar.classify') as classifier:
            self.assertEqual(classify_family('GUIDANCE_RAISE',e,'x','x')['reason'],'EVENT_TYPE_MAPPING_UNRESOLVED');classifier.assert_not_called()
    def test_unknown_rule_rejected(self):
        with self.assertRaises(ValueError):admit_facts('new-rule',{})

if __name__=='__main__':unittest.main()
