from datetime import datetime, date
import unittest
from private_session_context import inspect, session_close

class PrivateSessionContextTests(unittest.TestCase):
    def check(self,now,expected):
        r=inspect(datetime.fromisoformat(now))
        self.assertEqual(r['latest_closed_core_session'],expected)
        self.assertFalse(r['collection_enabled']);self.assertFalse(r['receipt_qualified']);self.assertFalse(r['trade_eligible'])
        self.assertEqual(r['provider_availability'],'UNVERIFIED');return r
    def test_trial_morning(self): self.check('2026-11-18T12:10:00+00:00','2026-11-17')
    def test_regular_boundary(self):
        self.check('2026-11-25T20:59:59.999999+00:00','2026-11-24')
        self.check('2026-11-25T21:00:00+00:00','2026-11-25')
    def test_holiday_all_day(self):
        self.check('2026-11-26T12:10:00+00:00','2026-11-25')
        r=self.check('2026-11-26T22:00:00+00:00','2026-11-25');self.assertTrue(r['legacy_calendar_differs'])
        self.assertIsNone(session_close(date(2026,11,26)))
    def test_early_boundary(self):
        self.check('2026-11-27T17:59:59.999999+00:00','2026-11-25')
        r=self.check('2026-11-27T18:00:00+00:00','2026-11-27');self.assertTrue(r['legacy_calendar_differs'])
    def test_early_morning_skips_holiday(self):self.check('2026-11-27T12:10:00+00:00','2026-11-25')
    def test_weekend_and_monday(self):
        self.check('2026-11-28T12:00:00+00:00','2026-11-27')
        self.check('2026-11-30T12:10:00+00:00','2026-11-27')
    def test_timezone_equivalence(self):
        self.assertEqual(inspect(datetime.fromisoformat('2026-11-27T13:00:00-05:00')),inspect(datetime.fromisoformat('2026-11-27T18:00:00+00:00')))
    def test_invalid_clocks(self):
        for v in [datetime(2026,11,18),datetime.fromisoformat('2026-11-13T22:00:00+00:00'),datetime.fromisoformat('2026-12-01T12:00:00+00:00'),'secret']:
            with self.assertRaises(ValueError):inspect(v)
    def test_reported_reference_states(self):
        now=datetime.fromisoformat('2026-11-27T18:00:00+00:00')
        for day,expected in [('2026-11-27','MATCHES_LATEST_CLOSED_CORE_SESSION_ONLY'),('2026-11-25','EARLIER_THAN_LATEST_CLOSED_CORE_SESSION'),('2026-11-26','NON_SESSION_IN_REFERENCE_CALENDAR'),('2026-11-30','CORE_SESSION_NOT_CLOSED_AT_OBSERVATION'),('2026-10-01','OUTSIDE_REVIEWED_CALENDAR')]:
            self.assertEqual(inspect(now,day)['reported_session_relation'],expected)
    def test_no_raw_input_echo(self):
        for v in ['private@example.test',{},True]:
            with self.assertRaises(ValueError):inspect(datetime.fromisoformat('2026-11-27T18:00:00+00:00'),v)
    def test_calendar_boundaries(self):
        for d in [date(2026,12,1),date(2026,11,12),datetime(2026,11,18)]:
            with self.assertRaises(ValueError):session_close(d)
    def test_retained_observation_clock(self):
        r=inspect(datetime.fromisoformat('2026-11-17T20:49:18.653849+00:00'),'2026-11-16')
        self.assertEqual(r['latest_closed_core_session'],'2026-11-16')
        self.assertFalse(r['legacy_calendar_differs'])
        self.assertFalse(r['receipt_qualified'])
