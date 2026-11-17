"""Synthetic mutation tests; no provider requests or permissions granted."""
import copy
import datetime as dt
import json
from pathlib import Path
import tempfile
import unittest
import source_registry as s

ROOT=Path(__file__).resolve().parents[1]
class RegistryTests(unittest.TestCase):
    def setUp(self): self.data=s.load(ROOT/'docs/research/source-registry.json')
    def check(self,d):return s.validate(d,today=dt.date(2026,11,17))
    def test_actual_catalog_and_generated_document(self):
        self.check(self.data)
        self.assertEqual(s.render(self.data),(ROOT/'docs/research/source-registry.md').read_text())
        self.assertEqual(len(self.data['records']),25)
    def test_expansion_remains_research_only(self):
        ids={'openfigi_mapping','gleif_lei','nasdaq_symbol_events','openfda_drugs',
             'openfda_drug_recalls','clinicaltrials_v2','usaspending_awards',
             'sam_public_opportunities','gdelt_project','globenewswire_rss'}
        records={r['id']:r for r in self.data['records']}
        self.assertTrue(ids <= records.keys())
        for key in ids:
            r=records[key]
            self.assertEqual(r['verified_access']['status'],'UNVERIFIED')
            self.assertEqual(r['verified_access']['downloaded_records'],0)
            self.assertEqual(r['current_operational_access']['status'],'UNVERIFIED')
            self.assertIs(r['training_ready'],False)
        for key in ['clinicaltrials_v2','sam_public_opportunities','globenewswire_rss']:
            self.assertEqual(records[key]['rights']['model_training']['status'],'UNVERIFIED')
        self.assertEqual(records['nasdaq_symbol_events']['rights']['storage']['status'],'PARTIAL')
        for key in ['openfda_drugs','openfda_drug_recalls']:
            self.assertEqual(records[key]['rights']['storage']['status'],'PARTIAL')

    def test_source_ids_unique(self):
        self.data['records'].append(copy.deepcopy(self.data['records'][0]))
        with self.assertRaises(ValueError):self.check(self.data)
    def test_no_activation_or_training_admission(self):
        for key,value in [('collection_enabled',True),('collection_enabled',0)]:
            d=copy.deepcopy(self.data);d[key]=value
            with self.assertRaises(ValueError):self.check(d)
        self.data['records'][0]['training_ready']=True
        with self.assertRaises(ValueError):self.check(self.data)
    def test_rights_separate_and_cited(self):
        for mutate in [lambda r:r['rights'].pop('storage'),lambda r:r['rights']['model_training'].update(status='ALLOWED'),lambda r:r['rights']['storage'].update(evidence_urls=['https://example.invalid/'])]:
            d=copy.deepcopy(self.data);mutate(d['records'][0])
            with self.assertRaises(ValueError):self.check(d)
    def test_no_future_evidence(self):
        for mutate in [lambda d:d.update(verified_on='2026-11-18'),lambda d:d['records'][0].update(verified_on='2026-11-18'),lambda d:d['records'][0]['evidence'][0].update(checked_date='2026-11-18')]:
            d=copy.deepcopy(self.data);mutate(d)
            with self.assertRaises(ValueError):self.check(d)
    def test_access_not_inferred_from_docs(self):
        r=next(r for r in self.data['records'] if r['id']=='alpaca_basic_equities')
        r['verified_access']['downloaded_records']=100
        with self.assertRaises(ValueError):self.check(self.data)
    def test_current_access_not_historical_receipt(self):
        self.data['records'][0]['current_operational_access']['status']='VERIFIED'
        with self.assertRaises(ValueError):self.check(self.data)
    def test_bad_url_and_storage_count(self):
        d=copy.deepcopy(self.data);d['records'][0]['evidence'][0]['url']='https://user:secret@example.invalid/'
        with self.assertRaises(ValueError):self.check(d)
        self.data['records'][0]['storage_estimate']['bytes']=True
        with self.assertRaises(ValueError):self.check(self.data)
    def test_decoder_rejects_duplicates_constants_and_oversize(self):
        for raw in ['{"a":1,"a":2}','{"unused":NaN}','{"unused":Infinity}','{"unused":-Infinity}',' '*1_000_001]:
            with tempfile.TemporaryDirectory() as td:
                p=Path(td)/'registry.json';p.write_text(raw)
                with self.assertRaises(ValueError):s.load(p)
    def test_restricted_routes_remain_distinct(self):
        records={r['id']:r for r in self.data['records']}
        for key in ['fred_alfred','massive_basic_stocks','finra_website']:
            self.assertEqual(records[key]['rights']['model_training']['status'],'BLOCKED')
        self.assertEqual(records['finra_equity_api']['rights']['model_training']['status'],'UNVERIFIED')
        for r in records.values():self.assertIs(r['training_ready'],False)

if __name__=='__main__':unittest.main()
