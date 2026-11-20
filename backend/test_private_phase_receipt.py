import json
import unittest

from private_phase_receipt import COLLECTION, EVALUATION, receipt

P = 'PASSED_REPORTED'
F = 'FAILED_REPORTED'
U = 'UNKNOWN'
W = 'WAITING_REPORTED'
CONTEXT = (('CREDENTIAL_PRESENCE', P), ('WORKFLOW_CONTEXT', P), ('TRIAL_WINDOW', P))
PRE_REQUEST = CONTEXT + (('PRE_REQUEST_PRIVACY', P), ('RETIRED_CONSUMER_CHECK', P))
EVAL_INPUT = (
    ('WORKFLOW_CONTEXT', P), ('PIN_AND_CHECKOUT', P), ('PRE_READ_PRIVACY', P),
    ('TRIAL_WINDOW', P), ('SAFE_PATHS', P),
)


class PrivatePhaseReceiptTest(unittest.TestCase):
    def test_generic_historical_stop_remains_unspecified(self):
        for workflow in (COLLECTION, EVALUATION):
            result = receipt(workflow=workflow)
            self.assertEqual(set(result['phases'].values()), {U})
            self.assertEqual(result['scope'], 'OFFLINE_CALLER_REPORTED_PHASES_NOT_VERIFIED')

    def test_privacy_stop_does_not_infer_request_or_quota(self):
        result = receipt(workflow=COLLECTION, observations=CONTEXT + (('PRE_REQUEST_PRIVACY', F),))
        self.assertEqual(result['phases']['PRE_REQUEST_PRIVACY'], F)
        self.assertEqual(result['phases']['REQUEST_BATCH'], U)
        self.assertFalse(result['provider_request_activity_verified'])
        self.assertFalse(result['provider_quota_usage_verified'])

    def test_passing_budget_guard_is_not_provider_activity(self):
        result = receipt(workflow=COLLECTION, observations=PRE_REQUEST + (('BUDGET_GUARD', P),))
        self.assertEqual(result['phases']['REQUEST_BATCH'], U)
        self.assertFalse(result['provider_request_activity_verified'])
        self.assertFalse(result['provider_quota_usage_verified'])

    def test_partial_batch_definitive_counts_are_not_exposed(self):
        reports = PRE_REQUEST + (('BUDGET_GUARD', P), ('REQUEST_BATCH', F))
        result = receipt(workflow=COLLECTION, observations=reports)
        self.assertEqual(result['phases']['REQUEST_BATCH'], F)
        self.assertEqual(result['phases']['RESPONSE_VALIDATION'], U)
        self.assertEqual(result['phases']['LOCAL_ARCHIVE'], U)
        self.assertFalse(result['provider_request_activity_verified'])
        self.assertFalse(result['collection_success_verified'])

    def test_waiting_is_distinct_from_failed_or_successful(self):
        for status in (W, F, P):
            result = receipt(workflow=EVALUATION, observations=EVAL_INPUT + (('CURRENT_COLLECTION', status),))
            self.assertEqual(result['phases']['CURRENT_COLLECTION'], status)
            self.assertEqual(result['phases']['EVALUATION'], U)
            self.assertNotIn('REQUEST_BATCH', result['phases'])

    def test_full_report_without_promotion_or_authorization(self):
        for workflow in (COLLECTION, EVALUATION):
            reports = tuple((name, P) for name in receipt(workflow=workflow)['phases'])
            result = receipt(workflow=workflow, observations=reports)
            self.assertEqual(set(result['phases'].values()), {P})
            self.assertEqual(result['phases']['REMOTE_RETENTION'], P)
            for field in (
                'provider_request_activity_verified', 'provider_quota_usage_verified',
                'collection_success_verified', 'persistence_verified',
                'publication_verified', 'retry_authorized', 'collection_enabled',
            ):
                self.assertIs(result[field], False)

    def test_invalid_sequences_do_not_ignore_conflicts(self):
        invalid = (
            (('WORKFLOW_CONTEXT', P),),  # skipped first checkpoint
            (('CREDENTIAL_PRESENCE', P), ('CREDENTIAL_PRESENCE', P)),
            (('CREDENTIAL_PRESENCE', F), ('WORKFLOW_CONTEXT', P)),
            (('CREDENTIAL_PRESENCE', U), ('WORKFLOW_CONTEXT', P)),
            (('CREDENTIAL_PRESENCE', W),),
            (('CREDENTIAL_PRESENCE', True),),
            (('CREDENTIAL_PRESENCE', None),),
            (('CREDENTIAL_PRESENCE', P, 'extra'),),
            (['CREDENTIAL_PRESENCE', P],),
            (('CREDENTIAL_PRESENCE', P),) * 50,
            {'CREDENTIAL_PRESENCE': P},
        )
        for reports in invalid:
            with self.subTest(reports=reports), self.assertRaises(ValueError):
                receipt(workflow=COLLECTION, observations=reports)
        with self.assertRaises(ValueError):
            receipt(workflow=EVALUATION, observations=EVAL_INPUT + (
                ('CURRENT_COLLECTION', W), ('PLAN_PROVENANCE', P),
            ))

    def test_out_of_contract_content_never_echoed(self):
        marker = 'synthetic-secret-not-for-output'
        class StrSubclass(str):
            pass
        checks = (
            lambda: receipt(workflow=marker),
            lambda: receipt(workflow=StrSubclass(COLLECTION)),
            lambda: receipt(workflow=COLLECTION, observations=((marker, P),)),
            lambda: receipt(workflow=COLLECTION, observations=(('CREDENTIAL_PRESENCE', marker),)),
            lambda: receipt(workflow=COLLECTION, observations=(('CREDENTIAL_PRESENCE', ValueError(marker)),)),
            lambda: receipt(workflow=COLLECTION, observations=(('CREDENTIAL_PRESENCE', P),), body=marker),
        )
        for check in checks:
            with self.assertRaises((ValueError, TypeError)) as err:
                check()
            self.assertNotIn(marker, str(err.exception))
        self.assertNotIn(marker, json.dumps(receipt(workflow=COLLECTION)))


if __name__ == '__main__':
    unittest.main()
