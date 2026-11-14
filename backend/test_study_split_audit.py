import unittest
from study_split_audit import audit_partition

class SplitAuditTests(unittest.TestCase):
    def row(self, event='train', group='g', decision='2026-10-01T12:00:00Z', start='2026-10-01T20:00:00Z', end='2026-10-08T20:00:00Z', known='2026-10-09T12:00:00Z'):
        return dict(event_id=event, issuer_id='1', event_group_id=group, decision_utc=decision, window_start_utc=start, window_end_utc=end, outcome=None if known is None else dict(observed_utc=known, excess_total_return=-.1))
    def holdout(self, group='g'):
        return self.row('test', group, '2026-11-16T12:00:00Z', '2026-11-16T21:00:00Z', '2026-11-23T21:00:00Z', '2026-11-24T12:00:00Z')
    def run_audit(self, rows):
        return audit_partition(rows, training_cutoff_utc='2026-10-10T00:00:00Z', holdout_start_utc='2026-11-16T00:00:00Z')
    def test_related_amendment_group_blocked(self):
        r=self.run_audit([self.row(), self.holdout()]); self.assertFalse(r['structural_checks_passed']); self.assertEqual(r['issues'][0]['reason'],'RELATED_EVENT_GROUP_CROSSES_SPLIT')
    def test_distinct_group_not_same_issuer_ban(self):
        r=self.run_audit([self.row(),self.holdout('other')]);self.assertTrue(r['structural_checks_passed']);self.assertFalse(r['trade_eligible']);self.assertIsNone(r['forecast_probability'])
    def test_delayed_label_purged(self):
        r=self.row();r['outcome']['observed_utc']='2026-10-11T00:00:00Z';self.assertEqual(self.run_audit([r])['assignments'][0]['partition'],'purged')
    def test_missing_holdout_preserved(self):
        r=self.holdout();r['outcome']=None;a=self.run_audit([r])['assignments'][0];self.assertEqual(a['partition'],'holdout');self.assertEqual(a['label_status'],'MISSING')
    def test_bad_holdout_timing_rejected(self):
        r=self.holdout();r['outcome']['observed_utc']='2026-11-17T00:00:00Z';self.assertRaises(ValueError,self.run_audit,[r])
    def test_bad_holdout_value_rejected(self):
        for x in (True, float('nan'), float('inf'), '0.1'):
            r=self.holdout();r['outcome']['excess_total_return']=x;self.assertRaises(ValueError,self.run_audit,[r])
    def test_duplicate_identity_rejected(self):
        self.assertRaises(ValueError,self.run_audit,[self.row(),self.row()])
    def test_losses_and_unresolved_preserved(self):
        r=self.row('missing',known=None);a=self.run_audit([self.row(),r]);self.assertEqual({x['partition'] for x in a['assignments']},{'train','unresolved'})
    def test_utc_normalization(self):
        r=self.row();r['decision_utc']='2026-10-01T08:00:00-04:00';self.assertEqual(self.run_audit([r])['assignments'][0]['partition'],'train')
    def test_missing_group_rejected(self):
        r=self.row();r['event_group_id']='';self.assertRaises(ValueError,self.run_audit,[r])
