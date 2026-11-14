import copy
import hashlib
import json
import unittest
from unittest.mock import patch
from study_archive_audit import audit_archived_study


class ArchiveAuditTests(unittest.TestCase):
    def row(self):
        return dict(event_id='event', issuer_id='issuer', event_group_id='group',
            decision_utc='2026-10-01T12:00:00Z', window_start_utc='2026-10-01T20:00:00Z',
            window_end_utc='2026-10-02T20:00:00Z',
            outcome=dict(observed_utc='2026-10-03T00:00:00Z', excess_total_return=-.1),
            features=[dict(name='growth',value=-.2,computed_utc='2026-10-01T11:00:00Z',
                sources=[dict(source_ref='synthetic://vintage',sha256=hashlib.sha256(b'private evidence').hexdigest(),
                              observed_utc='2026-10-01T10:00:00Z')])])

    def archives(self):
        s=self.row()['features'][0]['sources'][0]
        return {(s['source_ref'],s['sha256']):b'private evidence'}

    def audit(self, rows=None, archives=None):
        return audit_archived_study([self.row()] if rows is None else rows,
            archives=self.archives() if archives is None else archives, required_features=['growth'],
            training_cutoff_utc='2026-10-10T00:00:00Z', holdout_start_utc='2026-11-16T00:00:00Z')

    def test_matching_bytes_are_not_authenticity_or_forecast(self):
        r=self.audit(); self.assertTrue(r['all_integrity_checks_passed'])
        for field in ('source_truth_verified','source_authenticity_verified','observation_receipts_verified',
                      'feature_values_recomputed','trade_eligible'):
            self.assertFalse(r[field])
        self.assertIsNone(r['forecast_probability'])
        self.assertNotIn('private evidence',json.dumps(r))

    def test_missing_and_changed_bytes_fail_without_dropping_losses(self):
        for archives, status in [({},'MISSING_ARCHIVE'),
                ({next(iter(self.archives())):b'altered'},'HASH_MISMATCH')]:
            r=self.audit(archives=archives)
            self.assertFalse(r['all_integrity_checks_passed'])
            self.assertEqual(r['archive_checks'][0]['status'],status)
            self.assertEqual(r['assignments'][0]['partition'],'train')

    def test_same_hash_wrong_reference_cannot_substitute(self):
        s=self.row()['features'][0]['sources'][0]
        r=self.audit(archives={('synthetic://other',s['sha256']):b'private evidence'})
        self.assertEqual(r['archive_checks'][0]['status'],'MISSING_ARCHIVE')
        self.assertEqual(r['unreferenced_archive_count'],1)

    def test_revision_does_not_overwrite_original(self):
        a=self.row(); b=copy.deepcopy(a); b['event_id']='revision'
        s=b['features'][0]['sources'][0]; s['sha256']=hashlib.sha256(b'revision').hexdigest()
        archives=self.archives();archives[(s['source_ref'],s['sha256'])]=b'revision'
        self.assertTrue(self.audit([a,b],archives)['feature_source_bytes_verified'])
        del archives[next(iter(self.archives()))]
        self.assertFalse(self.audit([a,b],archives)['feature_source_bytes_verified'])

    def test_bytes_cannot_override_late_observation(self):
        a=self.row(); f=a['features'][0]
        f['sources'][0]['observed_utc']='2026-10-02T00:00:00Z'; f['computed_utc']='2026-10-02T01:00:00Z'
        r=self.audit([a]);self.assertTrue(r['feature_source_bytes_verified'])
        self.assertFalse(r['all_integrity_checks_passed'])

    def test_empty_or_missing_features_not_verified(self):
        self.assertFalse(self.audit([])['feature_source_bytes_verified'])
        a=self.row();a['features']=[]
        self.assertFalse(self.audit([a])['feature_source_bytes_verified'])

    def test_holdout_missing_outcome_and_archive_retained(self):
        a=self.row();a.update(decision_utc='2026-11-16T12:00:00Z',window_start_utc='2026-11-16T21:00:00Z',
            window_end_utc='2026-11-17T21:00:00Z',outcome=None)
        r=self.audit([a],{})
        self.assertEqual(r['assignments'][0]['partition'],'holdout')
        self.assertEqual(r['assignments'][0]['label_status'],'MISSING')
        self.assertFalse(r['all_integrity_checks_passed'])

    def test_only_bounded_raw_bytes_and_valid_keys(self):
        key=next(iter(self.archives()))
        for value in ('/path/to/private/file',bytearray(b'x'),None):
            self.assertRaises(ValueError,self.audit,archives={key:value})
        for badkey in ('path',('ref','bad'),('',key[1])):
            self.assertRaises(ValueError,self.audit,archives={badkey:b'x'})
        for constant in ('MAX_ARCHIVES','MAX_ARCHIVE_BYTES','MAX_TOTAL_BYTES'):
            with patch('study_archive_audit.'+constant,0):
                self.assertRaises(ValueError,self.audit)

    def test_inputs_not_mutated_and_repeated_references_retained(self):
        a=self.row();b=copy.deepcopy(a);b['event_id']='other'
        rows=[a,b]; before=copy.deepcopy(rows);archives=self.archives()
        r=self.audit(rows,archives)
        self.assertEqual(rows,before);self.assertEqual(archives,self.archives())
        self.assertEqual(len(r['archive_checks']),2)

if __name__ == '__main__': unittest.main()
