"""Offline policy-annex tests; no actual vault or balance operations."""
import hashlib
import json
import unittest

import paper_account_v2_policy as policy


class PaperAccountV2PolicyTests(unittest.TestCase):
    def setUp(self):
        self.digest = hashlib.sha256(b"synthetic immutable genesis for policy test only").hexdigest()
        self.raw = policy.build(self.digest)

    def test_exact_deterministic_and_inclusive_limits_no_execution(self):
        self.assertEqual(policy.build(self.digest), self.raw)
        self.assertTrue(self.raw.endswith(b"\n"))
        expected = policy.validate(self.raw, expected_genesis_sha256=self.digest)
        self.assertEqual(expected, {
            "schema_version": 1, "policy_id": "PAPER_V2_OPENING_LIMITS_V1",
            "account": "PAPER_V2", "genesis_sha256": self.digest, "currency": "USD",
            "max_positions_inclusive": 5, "max_per_position_cents_inclusive": 10_000,
            "per_position_cap_includes_fees_and_reserves": True,
            "margin_allowed": False, "leverage_allowed": False,
            "short_selling_allowed": False, "fractional_shares_allowed": False,
            "unqualified_fills_allowed": False, "historical_backdating_allowed": False,
            "real_money_execution_allowed": False, "brokerage_allowed": False,
            "execution_enabled": False,
        })
        self.assertEqual(json.loads(self.raw), expected)

    def test_different_genesis_and_malformed_pin_fail(self):
        other = "f" * 64
        with self.assertRaises(ValueError):
            policy.validate(self.raw, expected_genesis_sha256=other)
        for bad in (None, self.digest.upper(), self.digest[:-1], self.digest + "\n"):
            with self.assertRaises(ValueError):
                policy.build(bad)
            with self.assertRaises(ValueError):
                policy.validate(self.raw, expected_genesis_sha256=bad)

    def test_every_limit_and_capability_is_immutable(self):
        for old, new in (
            (b'"max_positions_inclusive":5', b'"max_positions_inclusive":6'),
            (b'"max_per_position_cents_inclusive":10000', b'"max_per_position_cents_inclusive":10001'),
            (b'"per_position_cap_includes_fees_and_reserves":true',
             b'"per_position_cap_includes_fees_and_reserves":false'),
            *[(f'"{key}":false'.encode(), f'"{key}":true'.encode()) for key in
              ("margin_allowed", "leverage_allowed", "short_selling_allowed",
               "fractional_shares_allowed", "unqualified_fills_allowed",
               "historical_backdating_allowed", "real_money_execution_allowed",
               "brokerage_allowed", "execution_enabled")],
        ):
            changed = self.raw.replace(old, new)
            self.assertNotEqual(changed, self.raw)
            with self.assertRaises(ValueError):
                policy.validate(changed, expected_genesis_sha256=self.digest)

    def test_canonical_bytes_only(self):
        for malformed in (bytearray(self.raw), self.raw[:-1], self.raw + b"\n",
                          b'{"x":0,' + self.raw[1:],
                          self.raw.replace(b'"margin_allowed":false',
                                           b'"margin_allowed":true,"margin_allowed":false'),
                          self.raw.replace(b'"margin_allowed":false', b'"margin_allowed":0'),
                          b"x" * 2049):
            with self.assertRaises(ValueError):
                policy.validate(malformed, expected_genesis_sha256=self.digest)
