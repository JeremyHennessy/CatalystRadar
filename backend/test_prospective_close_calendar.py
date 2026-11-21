from datetime import date, datetime, time, timezone
import unittest

from prospective_close_calendar import next_two_core_closes


def clock(s):
    return datetime.fromisoformat(s)


def rows(**values):
    return {date.fromisoformat(key.replace("_", "-")): value for key, value in values.items()}


FULL, EARLY = time(16), time(13)
# Fixture dates: https://www.nyse.com/trade/hours-calendars . No production calendar.
DEC = rows(**{
    "2026_12_22": FULL, "2026_12_23": FULL, "2026_12_24": EARLY,
    "2026_12_25": None, "2026_12_26": None, "2026_12_27": None,
    "2026_12_28": FULL, "2026_12_29": FULL, "2026_12_30": FULL,
    "2026_12_31": FULL, "2027_01_01": None, "2027_01_02": None,
    "2027_01_03": None, "2027_01_04": FULL, "2027_01_05": FULL,
})


class ProspectiveCalendarTest(unittest.TestCase):
    def assert_pair(self, observed, calendar, first, second):
        self.assertEqual(next_two_core_closes(clock(observed), calendar), (clock(first), clock(second)))

    def test_december_22_does_not_require_unused_days(self):
        self.assert_pair("2026-12-22T17:00:00Z", dict(list(DEC.items())[:2]),
                         "2026-12-22T21:00:00Z", "2026-12-23T21:00:00Z")

    def test_early_close_before_and_exact(self):
        self.assert_pair("2026-12-24T17:59:59.999999Z", DEC,
                         "2026-12-24T18:00:00Z", "2026-12-28T21:00:00Z")
        self.assert_pair("2026-12-24T13:00:00-05:00", DEC,
                         "2026-12-28T21:00:00Z", "2026-12-29T21:00:00Z")

    def test_turn_of_year_with_reviewed_coverage_only(self):
        self.assert_pair("2026-12-31T20:59:59Z", DEC,
                         "2026-12-31T21:00:00Z", "2027-01-04T21:00:00Z")
        self.assert_pair("2026-12-31T21:00:00Z", DEC,
                         "2027-01-04T21:00:00Z", "2027-01-05T21:00:00Z")
        for covered in [dict(list(DEC.items())[:10]), dict(list(DEC.items())[:-1])]:
            with self.assertRaisesRegex(ValueError, "coverage"):
                next_two_core_closes(clock("2026-12-31T21:00:00Z"), covered)

    def test_reviewed_closed_not_same_as_unknown(self):
        missing = dict(DEC)
        del missing[date(2026, 12, 25)]
        with self.assertRaisesRegex(ValueError, "coverage"):
            next_two_core_closes(clock("2026-12-24T17:59:59Z"), missing)

    def test_venue_date_and_daylight_time(self):
        july = rows(**{"2026_07_02": FULL, "2026_07_03": None, "2026_07_04": None,
                        "2026_07_05": None, "2026_07_06": FULL, "2026_07_07": FULL})
        self.assert_pair("2026-07-03T00:30:00Z", july,
                         "2026-07-06T20:00:00Z", "2026-07-07T20:00:00Z")

    def test_rejects_naive_clock_and_non_core_times(self):
        with self.assertRaisesRegex(ValueError, "timezone"):
            next_two_core_closes(clock("2026-12-22T17:00:00"), DEC)
        for bad in (True, time(13, 15), time(13, tzinfo=timezone.utc)):
            calendar = {**DEC, date(2026, 12, 22): bad}
            with self.assertRaisesRegex(ValueError, "unsupported"):
                next_two_core_closes(clock("2026-12-22T17:00:00Z"), calendar)
