import copy
import json
from pathlib import Path
import tempfile
import unittest
from historical_outcome_audit import audit_rows,build,read_pinned
ROOT=Path(__file__).resolve().parents[1]
class OutcomeAuditTests(unittest.TestCase):
    def setUp(self):
        self.rows=json.loads((ROOT/'data/filing_feature_rows.json').read_bytes())['rows']
        self.ready=json.loads((ROOT/'docs/research/horizon-readiness-2026-11-17.json').read_bytes())
    def test_real_scope(self):
        r=build(ROOT);self.assertEqual(r['universe_count'],10);self.assertEqual(r['selection_count'],1)
        self.assertEqual(len(r['excluded_by_selection']),9);self.assertEqual(r['qualified_outcomes'],0)
        self.assertEqual(r['selected'][0]['event_id'],'0001213900-26-119681')
        self.assertEqual(r['selected'][0]['first_missing_dependency'],'VERIFIED_EVENT_FIRST_PUBLIC_TIME')
    def test_order_independent(self):
        self.assertEqual(audit_rows(self.rows,self.ready),audit_rows(list(reversed(self.rows)),self.ready))
    def test_declarations_do_not_admit(self):
        for row in self.rows:row.update(first_public_utc='2026-11-01T00:00:00Z',decision_utc='2026-11-02T00:00:00Z',eligible=True,outcome={'return':100})
        r=audit_rows(self.rows,self.ready);self.assertEqual(r['qualified_outcomes'],0)
        self.assertIsNone(r['selected'][0]['return_value'])
    def test_no_price_or_ticker_selection(self):
        self.ready['retained_price_evidence']['symbols']=0
        self.assertEqual(audit_rows(self.rows,self.ready)['selection_count'],1)
    def test_invalid_feature_and_duplicate(self):
        with self.assertRaises(ValueError):audit_rows(self.rows+self.rows[:1],self.ready)
        self.rows[0]['features'].append(self.rows[0]['features'][0])
        with self.assertRaises(ValueError):audit_rows(self.rows,self.ready)
    def test_missing_selection_feature(self):
        self.rows[0]['features']=[]
        with self.assertRaises(ValueError):audit_rows(self.rows,self.ready)
    def test_changed_snapshot_rejected(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'source';p.write_text('{}')
            with self.assertRaises(ValueError):read_pinned(p,'0'*64)
    def test_no_values_output(self):
        r=json.dumps(build(ROOT));self.assertNotIn('open_price',r);self.assertNotIn('close_price',r)
