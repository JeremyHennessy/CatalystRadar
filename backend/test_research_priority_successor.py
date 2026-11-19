import json
from pathlib import Path
import unittest
from unittest.mock import patch

import research_priority as v1
import research_priority_successor as v2
from research_scanner import pointer, digest


ROOT = Path(__file__).resolve().parents[1]


class SuccessorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files = v2.build(ROOT)
        cls.snapshot_path, cls.snapshot_raw = next((k,v) for k,v in cls.files.items() if '/snapshots/' in k)
        cls.result = json.loads(cls.snapshot_raw)
        cls.records = [r for idea in cls.result['ideas'] for r in idea['source_records']]

    def test_canonical_bytes_and_original_preservation(self):
        self.assertEqual(self.files,v2.build(ROOT))
        self.assertEqual(len(self.files),3)
        for path, data in self.files.items():
            self.assertEqual((ROOT/path).read_bytes(),data)
            self.assertEqual(Path(path).stem,v1.sha(data))
        basename = v1.BASE+'latest.json'
        self.assertNotIn(basename,self.files)
        self.assertEqual(v1.sha((ROOT/basename).read_bytes()),'8c70e86caeddcb8a8b9c254f1eaa8ba8eb53175c73eace8d1a492e8f34d3d8b7')
        for path, raw in v1.build(ROOT).items():
            self.assertEqual((ROOT/path).read_bytes(),raw)
            self.assertNotIn(path,self.files)

    def test_source_pins_and_object_refs(self):
        for key,(path,size,expected) in v2.PINS.items():
            raw=(ROOT/path).read_bytes()
            self.assertEqual((len(raw),v1.sha(raw)),(size,expected))
            self.assertEqual(self.result['source_pins'][key],v1.pin(path,raw))
        for row in self.records:
            ref=row['source_ref']
            if ref['key'] in v2.PINS:
                self.assertEqual(digest(pointer(v2._input(ROOT,ref['key']),ref['json_pointer'])),ref['object_sha256'])

    def test_repeat_record_does_not_create_new_event_or_timing(self):
        records,excludes=v2.extensions(ROOT)
        cohr,txmd,wor=records
        self.assertEqual(cohr['source_accessions'],[v2.COHR[1]])
        self.assertEqual(txmd['source_accessions'],[v2.TXMD[1]])
        self.assertEqual(wor['source_accessions'],[v2.WOR[1]])
        self.assertEqual(excludes,{wor['id']:'EARLIER_DISCLOSURE_CONTROL_NO_NEW_QUALIFIED_FACT'})
        self.assertEqual({c['meaning']:c['value_as_reported'] for c in cohr['clocks']}['metadata_observation_utc_as_recorded'],
                         '2026-11-19T11:41:59.642713+00:00')
        self.assertTrue(all(row['first_public_utc'] is None for row in records))
        cohort_sources={r['id'] for r in self.records}
        self.assertIn(cohr['id'],cohort_sources)
        self.assertIn(txmd['id'],cohort_sources)
        self.assertNotIn(wor['id'],cohort_sources)

    def test_no_downgrade_or_upgrade_of_market_gates(self):
        d=self.result
        self.assertEqual(d['counts'],{'actionable_trades':0,'consolidated_theses':7,'eligible_source_records':8,
            'evaluated':908,'excluded':900,'paper_trades_placed':0,'returned':7})
        self.assertEqual([x['rank'] for x in d['ideas']],list(range(1,8)))
        self.assertEqual([x['research_priority_score'] for x in d['ideas']],[80,80,80,80,60,60,60])
        self.assertFalse(d['execution_ready'] or d['training_ready'] or d['provider_requests_made'])
        for x in d['ideas']:
            self.assertEqual((x['status'],x['actionability']),('WATCH','UNPRICED_NOT_ACTIONABLE'))
            self.assertTrue(all(x['coverage'][k] is None for k in ('current_price','security_mapping','first_public_verified','return_outcome')))
            if x['category'] in {'REPORTED_REPURCHASE_AUTHORIZATION','REPORTED_LICENSE_MILESTONE_CONTEXT'}:
                factors={f['id']:f for f in x['factors']}
                self.assertEqual(factors['source_review']['points'],40)
                self.assertEqual(factors['accession_citation']['points'],20)
                self.assertIsNone(factors['exact_period_context']['points'])
                self.assertEqual(factors['declared_filing_age']['points'],20)

    def test_bad_scheduled_observation_rejected(self):
        original=v2._input
        def change(root,key):
            value=original(root,key)
            if key=='sec_repeat':
                value['events'][1]['source_metadata_sha256']='f'*64
            return value
        with patch.object(v2,'_input',side_effect=change):
            with self.assertRaisesRegex(ValueError,'re-observation'):
                v2.extensions(ROOT)


if __name__ == '__main__':
    unittest.main()
