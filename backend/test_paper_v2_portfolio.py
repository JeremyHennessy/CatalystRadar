import hashlib
from pathlib import Path
import tempfile
import unittest

from paper_account_v2 import open_account
from paper_v2_portfolio import render


class PortfolioTest(unittest.TestCase):
    def test_failed_read_creates_nothing(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            with self.assertRaises(FileNotFoundError):
                render(root)
            self.assertFalse(list(root.iterdir()))

    def test_exact_cash_and_no_execution_or_network(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            initial = open_account(root)
            before = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                      for p in root.iterdir() if p.is_file()}
            page = render(root)
            self.assertIn(initial["opened_utc"], page)
            for text in ["US$500.00", "AWAITING_MARKET_DATA", "Real capital at risk",
                         "Automatic processing", "Off.", "No qualified market mark",
                         "default-src 'none'"]:
                self.assertIn(text, page)
            self.assertNotIn("<script", page)
            self.assertNotIn("http://", page)
            self.assertNotIn("https://", page)
            after = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                     for p in root.iterdir() if p.is_file()}
            self.assertEqual(before, after)
