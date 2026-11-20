"""Offline Paper V2 policy declaration; no order enforcement or state access.

Use the externally verified SHA-256 of the complete immutable genesis file,
not its internal status digest. This module neither reads nor writes that
file. A different genesis digest requires a different annex. Digest matching
does not prove who opened an account, validate a market, or enable execution.
"""
import json
import re

_POLICY_JSON_LIMIT = 2048


def _manifest(genesis_sha256):
    if type(genesis_sha256) is not str or re.fullmatch(r"[a-f0-9]{64}", genesis_sha256) is None:
        raise ValueError("expected SHA-256 of exact V2 genesis bytes")
    return {
        "schema_version": 1,
        "policy_id": "PAPER_V2_OPENING_LIMITS_V1",
        "account": "PAPER_V2",
        "genesis_sha256": genesis_sha256,
        "currency": "USD",
        "max_positions_inclusive": 5,
        "max_per_position_cents_inclusive": 10_000,
        "per_position_cap_includes_fees_and_reserves": True,
        "margin_allowed": False,
        "leverage_allowed": False,
        "short_selling_allowed": False,
        "fractional_shares_allowed": False,
        "unqualified_fills_allowed": False,
        "historical_backdating_allowed": False,
        "real_money_execution_allowed": False,
        "brokerage_allowed": False,
        "execution_enabled": False,
    }


def _encoded(manifest):
    return (json.dumps(manifest, sort_keys=True, separators=(",", ":"),
                       ensure_ascii=True, allow_nan=False) + "\n").encode("utf-8")


def build(genesis_sha256):
    """Return canonical annex bytes; caller is responsible for storing them."""
    return _encoded(_manifest(genesis_sha256))


def validate(raw, *, expected_genesis_sha256):
    """Return the exact policy or reject noncanonical/changed/foreign bytes.

    Exact byte comparison to a regenerated allowlist rejects altered limits,
    duplicate or extra keys, and type substitutions without parsing raw input.
    """
    expected = _manifest(expected_genesis_sha256)
    if type(raw) is not bytes or len(raw) > _POLICY_JSON_LIMIT or raw != _encoded(expected):
        raise ValueError("unrecognized Paper V2 opening policy")
    return expected
