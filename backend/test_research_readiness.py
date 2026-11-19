import copy
import json
from pathlib import Path
import tempfile
import unittest

import research_readiness as mod

ROOT = Path(__file__).resolve().parents[1]


class ReadinessTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.artifacts = mod.build(ROOT)
        cls.rows = [json.loads(x) for x in cls.artifacts.values()]
        cls.snapshot = json.loads((ROOT / cls.rows[1]['snapshot']['path']).read_bytes())

    def test_byte_reproducible_and_bound_to_distinct_snapshots(self):
        self.assertEqual(self.artifacts, mod.build(ROOT))
        self.assertEqual(len(self.artifacts), 2)
        for path, raw in self.artifacts.items():
            self.assertEqual((ROOT / path).read_bytes(), raw)
            self.assertEqual(Path(path).stem, mod.sha(raw))
        self.assertEqual([len(x['assessments']) for x in self.rows], [5, 7])
        for d, (path, size, sha) in zip(self.rows, mod.SNAPSHOTS):
            self.assertEqual(d['assessment_id'], mod.ASSESSMENT_ID)
            manifest = mod._read_pin(ROOT, path, size, sha)
            self.assertEqual(d['snapshot'], manifest['snapshot'])
            snap = json.loads((ROOT / d['snapshot']['path']).read_bytes())
            self.assertEqual(d['cutoff_utc'], snap['cutoff_utc'])
            self.assertEqual([x['id'] for x in d['assessments']], [x['id'] for x in snap['ideas']])

    def test_independent_evidence_count_and_gate_precedence(self):
        for d in self.rows:
            for row in d['assessments']:
                ev = row['evidence']
                states = {x['id']: x['state'] for x in ev['checks']}
                self.assertEqual((ev['verified'], ev['total']), (2, 10))
                self.assertEqual({k for k,v in states.items() if v == 'VERIFIED'}, {'source_identity', 'event_content'})
                self.assertEqual(states['event_availability'], 'UNKNOWN')
                self.assertEqual(states['financial_comparability'], 'NOT_ASSESSED')
                self.assertEqual(states['outcome_evidence'], 'NOT_ASSESSED')
                self.assertEqual(row['readiness']['state'], 'NEEDS_EVENT_VERIFICATION')
                self.assertEqual(row['readiness']['first_blocker']['id'], 'event_availability')
                self.assertEqual([b['id'] for b in row['readiness']['blockers']], [id_ for id_,_ in mod.GATES])

    def test_no_synthetic_promotion_via_score_or_filing_date(self):
        evidence = copy.deepcopy(self.snapshot)
        evidence['ideas'][0]['research_priority_score'] = 100
        evidence['ideas'][0]['declared_filing_date'] = '2026-11-19'
        self.assertEqual(mod._build_snapshot(evidence, self.rows[1]['snapshot']), self.rows[1])

    def test_rejects_new_or_altered_qualification_inputs(self):
        cases = [
            lambda d: d.update(execution_ready=True),
            lambda d: d['counts'].update(paper_trades_placed=1),
            lambda d: d['ideas'][0]['coverage'].update(first_public_verified=False),
            lambda d: d['ideas'][0]['coverage'].update(current_price=0),
            lambda d: d['ideas'][0]['source_records'][0].update(evidence_state='ORIGINAL_REVIEW_REQUIRED'),
            lambda d: d['ideas'][0]['source_records'][0]['source_ref'].update(key='not_pinned'),
            lambda d: d['ideas'].append(d['ideas'][0]),
        ]
        for mutate in cases:
            with self.subTest(mutate=mutate):
                evidence = copy.deepcopy(self.snapshot)
                mutate(evidence)
                with self.assertRaises(ValueError):
                    mod._build_snapshot(evidence, self.rows[1]['snapshot'])

    def test_file_pin_rejects_unchanged_length_mutation(self):
        with tempfile.TemporaryDirectory() as dirname:
            root = Path(dirname)
            for path, _, _ in mod.SNAPSHOTS:
                target = root / path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes((ROOT / path).read_bytes())
            pin = self.rows[0]['snapshot']
            target = root / pin['path']
            target.parent.mkdir(parents=True)
            exact = (ROOT / pin['path']).read_bytes()
            target.write_bytes(exact.replace(b'"WATCH"', b'"watch"', 1))
            self.assertEqual(target.stat().st_size, len(exact))
            with self.assertRaisesRegex(ValueError, 'Evidence bytes do not match the pin'):
                mod.build(root)


if __name__ == '__main__':
    unittest.main()
