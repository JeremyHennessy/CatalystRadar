import unittest
from pathlib import Path
from sec_continuation_candidate import inspect, slots

class ContinuationCandidateTests(unittest.TestCase):
    root=Path(__file__).resolve().parent.parent
    def test_exact_capacity_and_nonoperational(self):
        result=inspect(self.root,'2026-11-23T11:00:00Z',complete_history_verified=True)
        self.assertEqual(len(set(slots())),130)
        self.assertEqual(result['max_source_requests'],1300)
        self.assertFalse(result['can_collect']);self.assertFalse(result['collection_enabled'])
        self.assertIn('ACTIVATION_AND_WORKFLOW_REVIEW_REQUIRED',result['blockers'])
        self.assertIn('PRODUCTION_POLICY_CHANGED_REAUDIT_REQUIRED',result['blockers'])
    def test_weekend_gap_and_expiry(self):
        before=inspect(self.root,'2026-11-21T00:00:00Z')
        self.assertEqual(before['next_candidate_slot'],'2026-11-23T11:17:00+00:00')
        self.assertIn('CONTINUATION_WINDOW_NOT_STARTED',before['blockers'])
        after=inspect(self.root,'2026-11-28T00:00:00Z')
        self.assertIsNone(after['next_candidate_slot'])
        self.assertIn('CONTINUATION_WINDOW_EXPIRED',after['blockers'])
    def test_unknown_history_fails_closed(self):
        self.assertIn('COMPLETE_ACTIONS_AND_RESERVATION_HISTORY_NOT_VERIFIED',inspect(self.root,'2026-11-23T12:00:00Z')['blockers'])
    def test_unresolved_previous_trial_blocks(self):
        rows=[{'run_id':'1','reserved_at':'2026-11-20T12:00:00Z','resolved_complete':False}]
        self.assertIn('UNRESOLVED_OR_FAILED_RESERVATION',inspect(self.root,'2026-11-23T12:00:00Z',rows)['blockers'])
    def test_recent_reservation_blocks(self):
        rows=[{'run_id':'1','reserved_at':'2026-11-23T11:47:00Z','resolved_complete':True}]
        self.assertIn('RECENT_RESERVATION',inspect(self.root,'2026-11-23T12:00:00Z',rows)['blockers'])
    def test_future_and_duplicate_fail(self):
        row={'run_id':'1','reserved_at':'2026-11-23T11:47:00Z','resolved_complete':True}
        with self.assertRaises(ValueError):inspect(self.root,'2026-11-23T11:00:00Z',[row])
        with self.assertRaises(ValueError):inspect(self.root,'2026-11-23T12:00:00Z',[row,row])
    def test_run_ceiling(self):
        rows=[{'run_id':str(i+1),'reserved_at':stamp.isoformat(),'resolved_complete':True} for i,stamp in enumerate(slots())]
        result=inspect(self.root,'2026-11-27T23:59:00Z',rows)
        self.assertIn('WINDOW_RUN_CEILING_REACHED',result['blockers'])
        self.assertIn('DAILY_RUN_CEILING_REACHED',result['blockers'])

    def test_daily_window_boundaries(self):
        for clock in ('2026-11-24T00:00:00Z','2026-11-24T10:59:59Z'):
            self.assertIn('DAILY_WINDOW_CLOSED',inspect(self.root,clock)['blockers'])
        for clock in ('2026-11-24T11:00:00Z','2026-11-24T23:59:59Z'):
            self.assertNotIn('DAILY_WINDOW_CLOSED',inspect(self.root,clock)['blockers'])
        self.assertEqual(inspect(self.root,'2026-11-24T12:00:00Z')['ceiling_status'],'PROPOSED_REQUIRES_NEW_RUNNER_ENFORCEMENT')
