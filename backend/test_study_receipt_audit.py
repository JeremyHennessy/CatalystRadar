import copy
import hashlib
import json
import unittest
from unittest.mock import patch
import test_study_archive_audit
from study_receipt_audit import audit_receipted_study


class ReceiptAuditTests(unittest.TestCase):
    def setUp(self):
        self.row = test_study_archive_audit.ArchiveAuditTests().row()
        self.archives = test_study_archive_audit.ArchiveAuditTests().archives()
        self.source = self.row['features'][0]['sources'][0]
        self.receipt = dict(version=1, source_ref=self.source['source_ref'],
                            sha256=self.source['sha256'], observed_utc=self.source['observed_utc'])
        self.bind(self.receipt)

    def bind(self, receipt):
        raw = receipt if isinstance(receipt, bytes) else json.dumps(receipt).encode()
        key = hashlib.sha256(raw).hexdigest()
        self.source['observation_receipt_sha256'] = key
        self.receipts = {key: raw}

    def audit(self):
        return audit_receipted_study([self.row], archives=self.archives, receipts=self.receipts,
            required_features=['growth'], training_cutoff_utc='2026-10-10T00:00:00Z',
            holdout_start_utc='2026-11-16T00:00:00Z')

    def test_binding_does_not_authenticate_or_activate(self):
        before = copy.deepcopy(self.row)
        r = self.audit()
        self.assertTrue(r['all_receipt_integrity_checks_passed'])
        for field in ('observation_receipts_verified','trusted_clock_verified','source_authenticity_verified','feature_values_recomputed','trade_eligible'):
            self.assertFalse(r[field])
        self.assertIsNone(r['forecast_probability'])
        self.assertEqual(self.row, before)
        self.assertNotIn('private evidence', json.dumps(r))

    def test_receipt_cannot_backdate_source(self):
        self.receipt['observed_utc']='2026-10-04T00:00:00Z';self.bind(self.receipt)
        r=self.audit()
        self.assertTrue(r['all_integrity_checks_passed'])
        self.assertFalse(r['all_receipt_integrity_checks_passed'])
        self.assertEqual(r['receipt_checks'][0]['status'],'RECEIPT_TIME_MISMATCH')

    def test_equal_instants_with_different_offsets(self):
        self.receipt['observed_utc']='2026-10-01T06:00:00-04:00';self.bind(self.receipt)
        self.assertTrue(self.audit()['receipt_bindings_verified'])

    def test_missing_reference_receipt_and_altered_bytes(self):
        key=self.source.pop('observation_receipt_sha256')
        self.assertEqual(self.audit()['receipt_checks'][0]['status'],'MISSING_RECEIPT_REFERENCE')
        self.source['observation_receipt_sha256']=key;self.receipts={}
        self.assertEqual(self.audit()['receipt_checks'][0]['status'],'MISSING_RECEIPT')
        self.receipts={key:b'changed'}
        self.assertEqual(self.audit()['receipt_checks'][0]['status'],'RECEIPT_HASH_MISMATCH')

    def test_wrong_source_or_revision(self):
        for field,value in [('source_ref','synthetic://other'),('sha256','b'*64)]:
            receipt={**self.receipt,field:value};self.bind(receipt)
            self.assertEqual(self.audit()['receipt_checks'][0]['status'],'RECEIPT_SOURCE_MISMATCH')

    def test_malformed_receipts_fail_closed(self):
        for raw in (b'{}',b'null',b'[]',b'{"version":1,"version":1}',b'\xff',
                    json.dumps({**self.receipt,'version':True}).encode(),
                    json.dumps({**self.receipt,'observed_utc':'2026-10-01'}).encode()):
            self.bind(raw)
            self.assertEqual(self.audit()['receipt_checks'][0]['status'],'MALFORMED_RECEIPT')

    def test_bound_receipt_does_not_override_late_computation_or_missing_bytes(self):
        self.row['features'][0]['computed_utc']='2026-10-02T00:00:00Z'
        self.assertTrue(self.audit()['receipt_bindings_verified'])
        self.assertFalse(self.audit()['all_receipt_integrity_checks_passed'])
        self.archives={}
        self.assertFalse(self.audit()['all_receipt_integrity_checks_passed'])

    def test_bounds_and_invalid_reference(self):
        for name in ('MAX_RECEIPTS','MAX_RECEIPT_BYTES','MAX_TOTAL_BYTES'):
            with patch('study_receipt_audit.'+name,0):
                with self.assertRaises(ValueError):self.audit()
        self.source['observation_receipt_sha256']='bad'
        with self.assertRaises(ValueError):self.audit()

    def test_missing_feature_and_holdout_not_filtered_away(self):
        self.row.update(decision_utc='2026-11-16T12:00:00Z',window_start_utc='2026-11-16T21:00:00Z',window_end_utc='2026-11-17T21:00:00Z',outcome=None)
        self.receipts={}
        r=self.audit()
        self.assertEqual(r['assignments'][0]['partition'],'holdout')
        self.assertFalse(r['all_receipt_integrity_checks_passed'])
        self.row['features']=[]
        self.assertFalse(self.audit()['receipt_bindings_verified'])
