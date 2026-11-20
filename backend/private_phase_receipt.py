"""Offline prototype for fixed-code companion workflow diagnostics.

This module is not wired to either workflow. It serializes a caller's reports,
not a plan, run replay, or independent verification. The checkpoints describe
batch-level milestones, not a per-request ledger or proof of intermediate
side effects. In collection, request/validation/archive operations interleave;
failure at any batch milestone cannot rule out earlier requests or writes.
"""

COLLECTION = 'PRIVATE_COLLECTION'
EVALUATION = 'PRIVATE_SCENARIO_EVALUATION'
_PHASES = {
    COLLECTION: (
        'CREDENTIAL_PRESENCE', 'WORKFLOW_CONTEXT', 'TRIAL_WINDOW',
        'PRE_REQUEST_PRIVACY', 'RETIRED_CONSUMER_CHECK', 'BUDGET_GUARD',
        'REQUEST_BATCH', 'RESPONSE_VALIDATION', 'LOCAL_ARCHIVE',
        'PRE_RETENTION_PRIVACY', 'LOCAL_CHECKPOINT', 'REMOTE_RETENTION',
    ),
    EVALUATION: (
        'WORKFLOW_CONTEXT', 'PIN_AND_CHECKOUT', 'PRE_READ_PRIVACY',
        'TRIAL_WINDOW', 'SAFE_PATHS', 'CURRENT_COLLECTION', 'PLAN_PROVENANCE',
        'EVALUATION', 'PRE_RETENTION_PRIVACY', 'LOCAL_REPORT', 'REMOTE_RETENTION',
    ),
}
_STATUS = frozenset(('PASSED_REPORTED', 'FAILED_REPORTED', 'UNKNOWN'))
_WAITING = 'WAITING_REPORTED'


def receipt(*, workflow, observations=()):
    """Validate an ordered, bounded prefix of explicit (phase, status) codes.

    Omitted, unknown and unreached phases all project as UNKNOWN, never as
    proof of nonexecution. WAITING is reserved for the evaluator's collection
    check; it reports absence of qualifying same-day input, not a failure.
    Raw context, prose, bodies, paths, and exception objects are not accepted.
    """
    if type(workflow) is not str or workflow not in _PHASES:
        raise ValueError('unsupported diagnostic workflow')
    phases = _PHASES[workflow]
    if type(observations) is not tuple or len(observations) > len(phases):
        raise ValueError('invalid diagnostic observations')
    statuses = dict.fromkeys(phases, 'UNKNOWN')
    open_prefix = True
    for expected, observed in zip(phases, observations):
        if not open_prefix or type(observed) is not tuple or len(observed) != 2:
            raise ValueError('invalid diagnostic sequence')
        phase, status = observed
        if type(phase) is not str or phase != expected or type(status) is not str:
            raise ValueError('invalid diagnostic checkpoint')
        if status not in _STATUS and not (
            workflow == EVALUATION and phase == 'CURRENT_COLLECTION' and status == _WAITING
        ):
            raise ValueError('unsupported diagnostic status')
        statuses[expected] = status
        open_prefix = status == 'PASSED_REPORTED'
    return {
        'schema_version': 1,
        'scope': 'OFFLINE_CALLER_REPORTED_PHASES_NOT_VERIFIED',
        'workflow': workflow,
        'phases': statuses,
        'provider_request_activity_verified': False,
        'provider_quota_usage_verified': False,
        'collection_success_verified': False,
        'persistence_verified': False,
        'publication_verified': False,
        'retry_authorized': False,
        'collection_enabled': False,
    }
