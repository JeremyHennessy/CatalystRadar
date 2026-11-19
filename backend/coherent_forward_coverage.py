"""Read-only single-case coverage exclusion; does not fetch, price, or trade."""
import argparse
import json
from pathlib import Path

from observed_outcome_coverage import candidate_dates, read, stamp
from research_priority_successor import ORIGINAL_COHR_SHA

CIK, ACCESSION = "0000820318", "0001193125-26-467737"
# Internal protocol cutoff, not EDGAR dissemination or timestamp authentication.
CUTOFF_UTC = "2026-11-19T21:11:52Z"
ORIGINAL_SIZE = 29_296
RANK_SHA = "28e8b1d7b80a34de480ad03e9bdf7a5d18b65fdf5816239968f2f2fd52e6196a"
PUSH_SHA = "10b3c74b4949b1d23d850a9c822f052343dac979fa1112f3723c37fda81100bc"
REPEAT_SHA = "be97f6b0e9ee936072bab704619bdebd2b2d962f0929590422153ed6969bfadc"
AUDIT_SHA = "711b3697bbc2766ce04ccd7dfa020823a962677d16a596a579cda4bad0cbfccf"


def _load(root, path, pin):
    return json.loads(read(root / path, pin, 1_000_000))


def _event(root, name, pin):
    receipt = _load(root, "data/sec-observations/" + name, pin)
    rows = [r for r in receipt["events"] if (r["issuer_cik"], r["accession"]) == (CIK, ACCESSION)]
    if len(rows) != 1:
        raise ValueError("exact issuer/accession not unique")
    event = rows[0]
    if (event["form"] != "8-K" or event["items_raw"] != "7.01" or
            event["first_public_utc"] is not None or event["eligible"] is not False):
        raise ValueError("metadata boundary")
    return event


def build(root, original):
    root = Path(root)
    rank = _load(root, f"web/trade-ideas/v1/snapshots/{RANK_SHA}.json", RANK_SHA)
    matches = [r for r in rank["ideas"] if r["id"] == "research-88f4fe3fecb3853d4c6596aa"]
    if (len(matches) != 1 or matches[0]["source_records"][0]["source_accessions"] != [ACCESSION]
            or matches[0]["issuer_associations"][0]["issuer_cik"] != CIK):
        raise ValueError("ranking case mismatch")
    first = _event(root, "20261119T114159492631Z.json", PUSH_SHA)
    repeat = _event(root, "20261119T193148867794Z.json", REPEAT_SHA)
    if (first["source_metadata_sha256"] != repeat["source_metadata_sha256"]
            or first["sec_accepted_utc"] != repeat["sec_accepted_utc"]
            or not stamp(first["sec_accepted_utc"]) < stamp(first["observed_utc"])
            < stamp(repeat["observed_utc"]) < stamp(rank["cutoff_utc"]) < stamp(CUTOFF_UTC)):
        raise ValueError("observation ordering or revision")
    metadata = _load(root, f"data/sec-snapshots/{first['source_metadata_sha256']}.json",
                     first["source_metadata_sha256"])
    if str(metadata["cik"]).zfill(10) != CIK or ACCESSION not in metadata["filings"]["recent"]["accessionNumber"]:
        raise ValueError("metadata identity")
    raw = read(original, ORIGINAL_COHR_SHA, ORIGINAL_SIZE)
    if len(raw) != ORIGINAL_SIZE or not all(term in raw for term in (CIK.encode(), ACCESSION.encode(),
            b'Common Stock, no par value', b'>COHR<', b'>New York Stock Exchange<')):
        raise ValueError("source cover identity")
    audit = _load(root, "docs/research/price-session-audit-2026-11-17.json", AUDIT_SHA)
    bound = audit["window_end"]
    sessions = candidate_dates(CUTOFF_UTC)
    missing = [day for day in sessions if day > bound]
    if (audit["status"] != "SCHEDULED_SESSION_DATE_COMPARISON_ONLY" or
            audit["symbols_checked"] != 11 or audit["symbols_matching_date_set"] != 11 or
            len(missing) != 2):
        raise ValueError("coverage exclusion no longer follows")
    return {
        "issuer_cik": CIK, "accession": ACCESSION, "snapshot_sha256": RANK_SHA,
        "protocol_cutoff_utc": CUTOFF_UTC, "historical_rank_cutoff_utc": rank["cutoff_utc"],
        "cutoff_status": "INTERNAL_PROTOCOL_NOT_AUTHENTICATED_PUBLIC_CLOCK",
        "sec_acceptance_utc": first["sec_accepted_utc"],
        "first_retained_metadata_observation_utc": first["observed_utc"],
        "scheduled_repeat_observation_utc": repeat["observed_utc"],
        "first_public_utc": None,
        "issuer_reported_class_and_venue": "COHR / common stock, no par value / NYSE",
        "provider_security_join": "UNVERIFIED",
        "earlier_metadata_clock_descriptive_dates_only": candidate_dates(first["observed_utc"]),
        "protocol_candidate_scheduled_dates": sessions,
        "audited_data_through": bound,
        "candidate_dates_beyond_all_audited_series": missing,
        "actual_trading_and_halts": "NOT_VERIFIED",
        "corporate_action_continuity": "NOT_VERIFIED",
        "publication_rights": "NO_VERIFIED_PUBLIC_RAW_OR_DERIVED_DATA_RIGHTS",
        "exclusion": "NO_REQUIRED_PRICE_ENDPOINTS_IN_AUDITED_RETENTION",
        "return": None, "qualified_outcome": False, "execution_ready": False,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    parser.add_argument("original", type=Path)
    args = parser.parse_args()
    print(json.dumps(build(args.root, args.original), indent=2))
