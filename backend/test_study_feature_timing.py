import copy
import unittest
from study_split_audit import audit_study


class FeatureTimingTests(unittest.TestCase):
    def row(self):
        return dict(event_id='a', issuer_id='1', event_group_id='g',
                    decision_utc='2026-10-01T12:00:00Z',
                    window_start_utc='2026-10-01T20:00:00Z',
                    window_end_utc='2026-10-02T20:00:00Z',
                    outcome=dict(observed_utc='2026-10-03T00:00:00Z', excess_total_return=-.1),
                    features=[dict(name='growth', value=-.2, computed_utc='2026-10-01T11:00:00Z',
                                   sources=[dict(source_ref='synthetic://filing-v1', sha256='a'*64,
                                                 observed_utc='2026-10-01T10:00:00Z')])])

    def audit(self, rows, features=('growth',)):
        return audit_study(rows, required_features=features,
                           training_cutoff_utc='2026-10-10T00:00:00Z',
                           holdout_start_utc='2026-11-16T00:00:00Z')

    def test_valid_clocks_do_not_verify_sources_or_forecasts(self):
        r=self.audit([self.row()])
        self.assertTrue(r['all_declared_checks_passed'])
        self.assertFalse(r['source_truth_verified'])
        self.assertFalse(r['feature_source_bytes_verified'])
        self.assertFalse(r['trade_eligible'])
        self.assertIsNone(r['forecast_probability'])

    def test_later_retrieval_not_backdated_by_earlier_filing_date(self):
        row=self.row(); f=row['features'][0]
        f['computed_utc']='2026-10-05T12:00:00Z'
        f['sources'][0].update(observed_utc='2026-10-04T12:00:00Z', filing_date='2026-09-01')
        r=self.audit([row]); self.assertFalse(r['all_declared_checks_passed'])
        self.assertEqual(r['assignments'][0]['partition'],'train')
        self.assertEqual({x['reason'] for x in r['feature_checks'][0]['reasons']},
                         {'SOURCE_OBSERVED_AFTER_DECISION','FEATURE_COMPUTED_AFTER_DECISION'})

    def test_missing_features_retained_not_filled_with_zero(self):
        row=self.row(); del row['features']
        r=self.audit([row]); self.assertFalse(r['declared_timing_checks_passed'])
        self.assertEqual(r['feature_checks'][0]['reasons'][0]['reason'],'REQUIRED_FEATURE_MISSING')

    def test_later_calculation_is_not_earlier_knowledge(self):
        row=self.row(); row['features'][0]['computed_utc']='2026-10-02T00:00:00Z'
        self.assertFalse(self.audit([row])['all_declared_checks_passed'])

    def test_impossible_calculation_order_rejected(self):
        row=self.row(); row['features'][0]['computed_utc']='2026-10-01T09:00:00Z'
        self.assertRaises(ValueError,self.audit,[row])

    def test_invalid_values_and_source_identity_rejected(self):
        for value in (True, None, float('nan'), float('inf'), '1'):
            row=self.row(); row['features'][0]['value']=value
            self.assertRaises(ValueError,self.audit,[row])
        for field, value in [('sha256','x'*64),('source_ref','')]:
            row=self.row(); row['features'][0]['sources'][0][field]=value
            self.assertRaises(ValueError,self.audit,[row])

    def test_holdout_and_missing_outcome_still_checked(self):
        row=self.row(); row.update(decision_utc='2026-11-16T12:00:00Z',
            window_start_utc='2026-11-16T21:00:00Z',window_end_utc='2026-11-17T21:00:00Z',outcome=None)
        row['features'][0]['computed_utc']='2026-11-18T00:00:00Z'
        r=self.audit([row]); self.assertEqual(r['assignments'][0]['label_status'],'MISSING')
        self.assertEqual(r['assignments'][0]['partition'],'holdout')
        self.assertFalse(r['all_declared_checks_passed'])

    def test_invalid_holdout_outcome_never_bypasses_audit(self):
        row=self.row(); row.update(decision_utc='2026-11-16T12:00:00Z',
            window_start_utc='2026-11-16T21:00:00Z',window_end_utc='2026-11-17T21:00:00Z')
        row['outcome'].update(observed_utc='2026-11-18T00:00:00Z',excess_total_return=float('nan'))
        self.assertRaises(ValueError,self.audit,[row])

    def test_names_sources_and_timestamps_are_strict(self):
        for mutation in ('duplicate_feature','undeclared','duplicate_source','naive'):
            row=self.row(); f=row['features'][0]
            if mutation=='duplicate_feature': row['features'].append(copy.deepcopy(f))
            elif mutation=='undeclared': f['name']='unplanned'
            elif mutation=='duplicate_source': f['sources'].append(copy.deepcopy(f['sources'][0]))
            else: f['computed_utc']='2026-10-01T11:00:00'
            self.assertRaises(ValueError,self.audit,[row])
        for features in ([],['growth','growth'],['']):
            self.assertRaises(ValueError,self.audit,[self.row()],features)

    def test_empty_cohort_not_pass_and_inputs_unchanged(self):
        self.assertFalse(self.audit([])['all_declared_checks_passed'])
        row=self.row(); before=copy.deepcopy(row);self.audit([row]);self.assertEqual(row,before)

    def test_timezone_and_exact_deadline(self):
        row=self.row(); row['features'][0]['computed_utc']='2026-10-01T08:00:00-04:00'
        self.assertTrue(self.audit([row])['all_declared_checks_passed'])

    def test_related_event_split_failure_remains_failure(self):
        a=self.row(); b=copy.deepcopy(a);b.update(event_id='b',decision_utc='2026-11-16T12:00:00Z',
            window_start_utc='2026-11-16T21:00:00Z',window_end_utc='2026-11-17T21:00:00Z',outcome=None)
        r=self.audit([a,b]);self.assertTrue(r['declared_timing_checks_passed']);self.assertFalse(r['all_declared_checks_passed'])
