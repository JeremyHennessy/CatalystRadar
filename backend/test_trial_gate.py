import unittest
from datetime import datetime
from trial_gate import allowed
class Tests(unittest.TestCase):
 def test_monday(self):self.assertTrue(allowed(datetime.fromisoformat('2026-11-16T11:17:00+00:00')))
 def test_friday(self):self.assertTrue(allowed(datetime.fromisoformat('2026-11-20T23:47:00+00:00')))
 def test_next_year(self):self.assertFalse(allowed(datetime.fromisoformat('2027-11-16T11:17:00+00:00')))
 def test_weekend(self):self.assertFalse(allowed(datetime.fromisoformat('2026-11-21T12:00:00+00:00')))
 def test_now(self):self.assertFalse(allowed(datetime.fromisoformat('2026-11-14T17:00:00+00:00')))
if __name__=='__main__':unittest.main()
