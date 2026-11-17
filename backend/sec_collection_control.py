"""Fail-closed admission for bounded SEC workflow collection, never trade admission.

Reservations are durable Git records, not immutable or independent-clock evidence.
No network in plan(); only run() commits a reservation before calling the scanner.
"""
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo
import hashlib
import json
import os
import re
import subprocess

from trial_gate import allowed

REPO = 'JeremyHennessy/CatalystRadar'
REQUEST = 'data/sec-control/request.json'
ET = ZoneInfo('America/New_York')
MAX_RECORDS = 2000


def instant(value):
    if not isinstance(value, str):
        raise ValueError('invalid control timestamp')
    result = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if result.tzinfo is None or result.utcoffset().total_seconds() != 0:
        raise ValueError('UTC control timestamp required')
    return result


def unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('duplicate control field')
        result[key] = value
    return result


def decode(raw):
    if len(raw) > 4 * 1024 * 1024:
        raise ValueError('control record too large')
    return json.loads(raw, object_pairs_hook=unique)


def plan(*, now, event, actor, run_id, attempt, request, receipts, reservations):
    """Return reason plus reservation, or fail closed on ambiguous prior state."""
    if event not in ('schedule', 'workflow_dispatch', 'push') or actor != 'JeremyHennessy':
        raise ValueError('unapproved workflow context')
    if attempt != '1' or not re.fullmatch(r'[1-9][0-9]{0,19}', run_id):
        raise ValueError('retries or invalid run identity prohibited')
    if not allowed(now):
        return 'OUTSIDE_TRIAL_WINDOW', None
    day = now.astimezone(ET).date().isoformat()
    request_hash = None
    if event == 'push':
        if not isinstance(request, dict) or set(request) != {'version', 'purpose', 'requested_at', 'expires_at', 'session'}:
            raise ValueError('invalid fallback request schema')
        if type(request['version']) is not int or request['version'] != 1 or request['purpose'] != 'PUBLIC_SEC_OBSERVATION_ONLY':
            raise ValueError('invalid fallback purpose')
        requested, expires = instant(request['requested_at']), instant(request['expires_at'])
        if not requested <= now <= expires or not timedelta(0) < expires-requested <= timedelta(minutes=15):
            raise ValueError('expired or future fallback request')
        if request['session'] != day or requested.astimezone(ET).date().isoformat() != day or not allowed(requested) or not allowed(expires):
            raise ValueError('fallback outside trial session')
        request_hash = hashlib.sha256(json.dumps(request, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    if len(receipts) > MAX_RECORDS or len(reservations) > MAX_RECORDS:
        raise ValueError('control history bound exceeded')
    completed = {}
    ordered = []
    for receipt in receipts:
        finished = instant(receipt['finished_at'])
        if instant(receipt['started_at']) > finished or finished > now:
            raise ValueError('future receipt')
        total, success = receipt['configured_issuers'], receipt['successful_issuers']
        if type(total) is not int or type(success) is not int or not 0 <= success <= total <= 20 or total == 0 or not isinstance(receipt['errors'], list):
            raise ValueError('invalid receipt counts')
        complete = success == total and receipt['metadata_window_complete'] is True and receipt['errors'] == []
        ordered.append((finished, complete))
        url = receipt.get('github_run_url')
        if url:
            match = re.fullmatch(r'https://github.com/JeremyHennessy/CatalystRadar/actions/runs/([1-9][0-9]{0,19})', url)
            if not match or match[1] in completed:
                raise ValueError('ambiguous receipt run identity')
            completed[match[1]] = receipt
    seen = set()
    fallback_today = False
    for reservation in reservations:
        if set(reservation) != {'version', 'run_id', 'event', 'reserved_at', 'session', 'request_sha256'} or type(reservation['version']) is not int or reservation['version'] != 1:
            raise ValueError('invalid reservation')
        identity = reservation['run_id']
        if not isinstance(identity, str) or not re.fullmatch(r'[1-9][0-9]{0,19}', identity) or identity in seen:
            raise ValueError('duplicate reservation')
        seen.add(identity)
        reserved = instant(reservation['reserved_at'])
        if reserved > now or reservation['session'] != reserved.astimezone(ET).date().isoformat() or reservation['event'] not in ('push', 'schedule', 'workflow_dispatch'):
            raise ValueError('invalid reservation timing')
        request_digest = reservation['request_sha256']
        if (reservation['event'] == 'push' and (not isinstance(request_digest, str) or not re.fullmatch(r'[0-9a-f]{64}', request_digest))) or (reservation['event'] != 'push' and request_digest is not None):
            raise ValueError('invalid reservation request binding')
        if identity not in completed:
            raise ValueError('unresolved prior reservation; inspect before retry')
        receipt = completed[identity]
        if instant(receipt['started_at']) < reserved or receipt.get('github_event_name') != reservation['event']:
            raise ValueError('receipt does not resolve reservation')
        if reservation['event'] == 'push' and reservation['session'] == day:
            fallback_today = True
    if run_id in seen or run_id in completed:
        raise ValueError('run already reserved')
    if event == 'push' and fallback_today:
        return 'FALLBACK_ALREADY_RESERVED_TODAY', None
    if ordered:
        latest = max(stamp for stamp, _ in ordered)
        complete = all(ok for stamp, ok in ordered if stamp == latest)
        # Any failed latest scan, including403/429, requires explicit investigation.
        if not complete:
            raise ValueError('latest source scan incomplete; no automated retry')
        if now-latest < timedelta(minutes=30):
            return 'RECENT_COMPLETE_OBSERVATION', None
    return 'RESERVE_BEFORE_COLLECTION', {'version': 1, 'run_id': run_id, 'event': event,
        'reserved_at': now.isoformat(), 'session': day, 'request_sha256': request_hash}


def records(directory):
    paths = sorted(directory.glob('*.json'))
    if len(paths) > MAX_RECORDS:
        raise ValueError('too many records')
    return [decode(path.read_bytes()) for path in paths]


def git(*args):
    return subprocess.check_output(['git', *args], text=True, stderr=subprocess.DEVNULL).strip()


def run(root, environ, clock=lambda: datetime.now(timezone.utc)):
    if environ.get('GITHUB_ACTIONS') != 'true' or environ.get('GITHUB_REPOSITORY') != REPO or environ.get('GITHUB_REF') != 'refs/heads/main':
        raise ValueError('approved main workflow required')
    event = environ.get('GITHUB_EVENT_NAME')
    request = decode((root / REQUEST).read_bytes()) if event == 'push' else None
    if git('status', '--porcelain'):
        raise ValueError('clean checkout required for isolated reservation')
    head = git('rev-parse', 'HEAD')
    if event == 'push':
        if head != environ.get('GITHUB_SHA') or len(git('rev-list', '--parents', '-n', '1', 'HEAD').split()) != 2:
            raise ValueError('fallback request commit superseded or not single-parent')
        if git('diff-tree', '--no-commit-id', '--name-only', '-r', 'HEAD').splitlines() != [REQUEST]:
            raise ValueError('fallback commit must change only exact request file')
    args = dict(event=event, actor=environ.get('GITHUB_ACTOR'), run_id=environ.get('GITHUB_RUN_ID', ''),
        attempt=environ.get('GITHUB_RUN_ATTEMPT'), request=request,
        receipts=records(root / 'data/sec-observations'), reservations=records(root / 'data/sec-control/attempts'))
    reason, reservation = plan(now=clock(), **args)
    if reservation is None:
        return reason, False
    # Check private identity before reserving; never print it.
    from sec_identity import contact_email
    contact_email()
    directory = root / 'data/sec-control/attempts'
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / (reservation['run_id'] + '.json')
    with path.open('x') as out:
        json.dump(reservation, out, sort_keys=True, indent=2)
        out.write('\n')
    git('config', 'user.name', 'github-actions[bot]')
    git('config', 'user.email', '41898282+github-actions[bot]@users.noreply.github.com')
    git('add', '--', str(path.relative_to(root)))
    git('commit', '-m', 'Reserve bounded SEC collection attempt')
    git('push', 'origin', 'HEAD:main')  # No force/retry; failure means no source request.
    if git('ls-remote', 'origin', 'refs/heads/main').split()[0] != git('rev-parse', 'HEAD'):
        raise ValueError('reservation superseded before collection')
    # Recheck deadline/freshness after persistence; failure leaves visible reservation.
    reason, confirmed = plan(now=clock(), **args)
    if confirmed is None:
        raise ValueError('collection window changed after reservation')
    from scan_watchlist import scan
    scan(root)
    return 'COLLECTION_RECORDED', True


if __name__ == '__main__':
    try:
        root = Path(__file__).resolve().parent.parent
        status, collected = run(root, os.environ)
        with open(os.environ['GITHUB_OUTPUT'], 'a') as out:
            out.write('collected=' + str(collected).lower() + '\n')
        print(status)
    except Exception:
        print('SEC workflow stopped safely; inspect reservation/source state before retry. No details disclosed.')
        raise SystemExit(1)
