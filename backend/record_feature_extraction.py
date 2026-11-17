"""Local-only append-only source and extraction capture. Never a trade activation.

Retains exact existing collector bytes; does not fetch or reconstruct observations.
The local runtime clock is recorded, not independently authenticated.
"""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import stat
from filing_feature_rows import build
from study_split_audit import instant

CODE_ROOT = Path(__file__).resolve().parent.parent
MAX_TOTAL_BYTES = 64 * 1024 * 1024
MAX_MANIFEST_BYTES = 1024 * 1024


def clock():
    return datetime.now(timezone.utc)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def write_new(path, raw):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, 'wb') as out:
        out.write(raw)
        out.flush()
        os.fsync(out.fileno())


def encode(value):
    return (json.dumps(value, sort_keys=True, indent=2) + '\n').encode()


def record(reviews_path, archive_dir, destination):
    started = clock()
    if started.tzinfo is None:
        raise ValueError('timezone-aware runtime clock required')
    reviews_path, archive_dir, destination = map(Path, (reviews_path, archive_dir, destination))
    if not destination.is_absolute() or destination.resolve() != destination or destination == CODE_ROOT or CODE_ROOT in destination.parents:
        raise ValueError('private output outside the public checkout required')
    if reviews_path.is_symlink() or archive_dir.is_symlink():
        raise ValueError('symlink inputs forbidden')
    manifest_path = archive_dir / 'manifest.jsonl'
    if manifest_path.is_symlink() or manifest_path.stat().st_size > MAX_MANIFEST_BYTES:
        raise ValueError('invalid manifest')
    manifest = manifest_path.read_bytes()
    receipts = [json.loads(line) for line in manifest.splitlines()]
    if not 1 <= len(receipts) <= 10 or len({r['accession'] for r in receipts}) != len(receipts):
        raise ValueError('bounded unique collector receipts required')
    if reviews_path.stat().st_size > MAX_MANIFEST_BYTES:
        raise ValueError('oversized reviews')
    reviews = reviews_path.read_bytes()
    retained, total = {}, len(manifest) + len(reviews)
    for receipt in receipts:
        sha = receipt['sha256']
        if not isinstance(sha, str) or not re.fullmatch('[a-f0-9]{64}', sha) or receipt['archive_file'] != sha + '.txt':
            raise ValueError('invalid source identity')
        if receipt['status'] != 'ARCHIVED_IDENTITY_VERIFIED' or not instant(receipt['request_utc']) <= instant(receipt['retrieved_utc']) <= started:
            raise ValueError('unverified source or future observation')
        path = archive_dir / receipt['archive_file']
        if path.is_symlink() or path.stat().st_size > MAX_TOTAL_BYTES - total:
            raise ValueError('invalid or oversized source')
        raw = path.read_bytes()
        if digest(raw) != sha or len(raw) != receipt['byte_count']:
            raise ValueError('source bytes changed')
        if path.name in retained:
            raise ValueError('duplicate source file')
        retained[path.name] = raw
        total += len(raw)
    destination.mkdir(mode=0o700, exist_ok=True)
    if stat.S_IMODE(destination.stat().st_mode) & 0o077:
        raise ValueError('private destination permissions required')
    run = destination / started.astimezone(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    run.mkdir(mode=0o700)  # Existing runs are never overwritten.
    sources = run / 'sources'
    sources.mkdir(mode=0o700)
    write_new(sources / 'manifest.jsonl', manifest)
    write_new(run / 'reviews.json', reviews)
    for name, raw in retained.items():
        write_new(sources / name, raw)
    features = build(run / 'reviews.json', sources, computed_at=started.isoformat())
    finished = clock()
    if finished.tzinfo is None or finished < started:
        raise ValueError('runtime clock moved backwards')
    # Availability is no earlier than completion, never caller-supplied.
    features['computed_at'] = finished.isoformat()
    for row in features['rows']:
        row['computed_utc'] = finished.isoformat()
        for feature in row['features']:
            feature['computed_utc'] = finished.isoformat()
    feature_bytes = encode(features)
    write_new(run / 'features.json', feature_bytes)
    receipt = dict(mode='LOCAL_EXTRACTION_CAPTURE_NOT_TRUSTED_TIMESTAMP',
        started_utc=started.isoformat(), finished_utc=finished.isoformat(),
        manifest_sha256=digest(manifest), reviews_sha256=digest(reviews),
        features_sha256=digest(feature_bytes), source_count=len(retained),
        structural_feature_rows=features['structural_feature_rows'],
        implementation_sha256={name: digest((Path(__file__).parent / name).read_bytes())
            for name in ('record_feature_extraction.py', 'filing_feature_rows.py', 'archive_reviewed_filings.py')},
        trusted_clock_verified=False, historical_availability_verified=False,
        trade_eligible=False, orders_created=0)
    write_new(run / 'complete.json', encode(receipt))  # Only complete runs have this marker.
    return run, receipt


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reviews', required=True)
    parser.add_argument('--archive', required=True)
    parser.add_argument('--private-destination', required=True)
    args = parser.parse_args()
    _, result = record(args.reviews, args.archive, args.private_destination)
    print(json.dumps({k: result[k] for k in ('mode','started_utc','finished_utc','source_count','structural_feature_rows','trade_eligible','orders_created')}))
