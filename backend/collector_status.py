"""Offline operations projection. Never calls a provider or authorizes collection.

Only allowlisted receipt metadata is emitted. A retained successful receipt is not
proof of the latest workflow attempt. Configured slots are not promised runs.
"""
import argparse
import datetime as dt
import hashlib
import json
import re
from pathlib import Path
from private_prices import unique_object

UTC = dt.timezone.utc
SEC_TRIAL_EXPIRY = '2026-11-21T00:00:00+00:00'
SEC_TRIAL_CRON = '17,47 11-23 16-20 11 *'
# Admit only the reviewed scheduled workflow and the exact schedule-only removal.
SEC_TRIAL_SCHEDULED_SHA = '118290b70cf5394b1631b5deb23e598f139ec8b7902f04ca018c7ef366b4d375'
SEC_TRIAL_RETIRED_SHA = 'fc59de2b940a3dd18ecaebc6274433418616b5bb0176f41b217684b9928ec1dd'

def instant(value):
    if not isinstance(value, str): raise ValueError('missing timestamp')
    result = dt.datetime.fromisoformat(value.replace('Z', '+00:00'))
    if result.tzinfo is None or result.utcoffset() != dt.timedelta(0): raise ValueError('UTC required')
    return result

def load(path):
    raw = Path(path).read_bytes()
    if len(raw) > 4_000_000: raise ValueError('oversized input')
    return json.loads(raw, object_pairs_hook=unique_object), hashlib.sha256(raw).hexdigest()

def next_slot(now, source):
    days, hours, minutes = ((range(16,21), range(11,24), (17,47)) if source == 'sec' else (range(16,22), (12,), (10,)))
    return next((stamp.isoformat() for day in days for hour in hours for minute in minutes
                 if (stamp := dt.datetime(2026,11,day,hour,minute,tzinfo=UTC)) > now), None)

def row(identifier, now, expiry, mode, storage):
    return {'id': identifier, 'mode': mode, 'storage': storage,
            'last_attempt': None, 'last_attempt_status': 'UNVERIFIED_ACTIONS_HISTORY',
            'last_successful_observation': None, 'last_verified_complete_run': None,
            'accepted_records': None, 'rejected_records': None, 'held_records': None,
            'missing_periods': None, 'missing_periods_status': 'NOT_AUDITED',
            'workflow_failure': None, 'workflow_failure_status': 'UNVERIFIED_ACTIONS_HISTORY',
            'expiry_utc': expiry, 'policy_state': ('EXPIRED' if now >= instant(expiry) else 'BOUNDED_TRIAL') if expiry else 'MANUAL_ONLY',
            'next_configured_slot': None, 'next_run_guaranteed': False,
            'source_status': 'NO_VERIFIED_RECEIPT', 'evidence': [], 'blockers': []}

def build(root, as_of):
    root = Path(root); now = instant(as_of)
    if now < instant('2026-11-18T01:08:00+00:00'): raise ValueError('as-of precedes policy audit')
    result = {'schema_version': 1, 'as_of': now.isoformat(), 'collection_enabled_by_this_index': False,
              'execution_ready': False, 'scope': 'Saved evidence only; Refresh does not collect data',
              'history_completeness': 'LATEST_ACTIONS_ATTEMPTS_NOT_VERIFIED', 'collectors': []}
    workflow_path = '.github/workflows/sec-observations.yml'
    workflow_digest = hashlib.sha256((root / workflow_path).read_bytes()).hexdigest()
    if workflow_digest not in (SEC_TRIAL_SCHEDULED_SHA, SEC_TRIAL_RETIRED_SHA):
        raise ValueError('SEC workflow changed; re-audit policy')
    retired = workflow_digest == SEC_TRIAL_RETIRED_SHA
    if retired and now < instant(SEC_TRIAL_EXPIRY):
        raise ValueError('retired SEC workflow cannot represent an in-trial status')
    sec = row('sec_watchlist', now, SEC_TRIAL_EXPIRY,
              'SCHEDULE_RETIRED' if retired else 'SCHEDULED_BOUNDED', 'PUBLIC_METADATA')
    sec['configured_cron'] = None if retired else SEC_TRIAL_CRON
    sec['evidence'].append({'path': workflow_path, 'sha256': workflow_digest})
    gate = (root / 'backend/trial_gate.py').read_text()
    if 'date(2026,11,16)<=et.date()<=date(2026,11,20)' not in gate or 'time(6)<=et.time()<=time(18,59,59)' not in gate: raise ValueError('SEC runtime gate changed; re-audit')
    sec['next_configured_slot'] = None if retired else next_slot(now, 'sec')
    sec['quota_status'] = 'BOUNDED_10_ISSUER_SCOPE_NOT_PROVIDER_ENTITLEMENT'
    sec['rights_status'] = 'PUBLIC_METADATA_ONLY_NO_EXTENSION_APPROVED'
    sec['blockers'] = ['Trial expires; continuation requires reviewed bounded policy.', 'Unresolved reservation or failed latest scan blocks automatic collection.', 'Latest Actions attempt and missing slots are not established by retained receipts.']
    path = root / 'data/latest_scan.json'
    if path.exists():
        receipt, digest = load(path)
        finished = instant(receipt['finished_at']); started = instant(receipt['started_at'])
        if not started <= finished <= now: raise ValueError('invalid/future SEC receipt')
        total, good = receipt['configured_issuers'], receipt['successful_issuers']
        if type(total) is not int or type(good) is not int or total != 10 or not 0 <= good <= total: raise ValueError('invalid issuer counts')
        if not isinstance(receipt['errors'], list): raise ValueError('invalid error list')
        complete = receipt.get('metadata_window_complete') is True and good == total and not receipt['errors']
        sec.update(source_status='COMPLETE_RETAINED_METADATA' if complete else 'INCOMPLETE_RETAINED_RECEIPT', configured_issuers=total, successful_issuers=good)
        sec['evidence'].append({'path': 'data/latest_scan.json', 'sha256': digest})
        if complete:
            sources = receipt.get('sources')
            if not isinstance(sources, list) or len(sources) != total:
                raise ValueError('complete SEC receipt requires all source evidence')
            expected_ciks = {'0000820318':'COHR','0000012659':'HRB','0000020286':'CINF','0000025743':'TXMD','0000031791':'RVTY','0000032604':'EMR','0000042582':'GT','0000091576':'KEY','0000108516':'WOR','0001770450':'XRX'}
            seen = set()
            for source in sources:
                if not isinstance(source, dict): raise ValueError('invalid SEC source')
                url = source.get('url')
                if not isinstance(url, str) or not re.fullmatch(r'https://data.sec.gov/submissions/CIK[0-9]{10}\.json', url) or url in seen:
                    raise ValueError('invalid or duplicate SEC issuer source')
                cik = url.rsplit('CIK',1)[1][:-5]
                if cik not in expected_ciks: raise ValueError('SEC issuer scope changed; re-audit')
                if source.get('ticker') != expected_ciks[cik]: raise ValueError('SEC receipt ticker/CIK mismatch')
                seen.add(url)
                digest = source.get('sha256')
                if not isinstance(digest, str) or not re.fullmatch(r'[0-9a-f]{64}', digest): raise ValueError('invalid SEC source hash')
                expected_path = f'data/sec-snapshots/{digest}.json'
                if source.get('archive_path') != expected_path: raise ValueError('invalid SEC archive path')
                raw = (root / expected_path).read_bytes()
                if len(raw) > 4_000_000: raise ValueError('oversized SEC archive')
                document = json.loads(raw, object_pairs_hook=unique_object)
                if not isinstance(document, dict) or str(document.get('cik')).zfill(10) != cik:
                    raise ValueError('SEC archive issuer mismatch')
                if type(source.get('byte_count')) is not int or len(raw) != source['byte_count'] or hashlib.sha256(raw).hexdigest() != digest:
                    raise ValueError('SEC retained source integrity failed')
                if type(source.get('status')) is not int or source['status'] != 200 or source.get('validation_status') != 'METADATA_WINDOW_VALIDATED':
                    raise ValueError('SEC source not validated')
                if not started <= instant(source.get('request_utc')) <= instant(source.get('retrieved_utc')) <= finished:
                    raise ValueError('invalid SEC source clocks')
            sec['last_successful_observation'] = finished.isoformat()
            run_url = receipt.get('github_run_url', '')
            sec['last_verified_complete_run'] = run_url if isinstance(run_url,str) and re.fullmatch(r'https://github.com/JeremyHennessy/CatalystRadar/actions/runs/[1-9][0-9]{0,19}',run_url) else None
        sec['observation_age_seconds'] = int((now-finished).total_seconds())
    reservations = []
    for path in sorted((root/'data/sec-control/attempts').glob('*.json')):
        if len(reservations) >= 2000: raise ValueError('reservation history oversized')
        reservation, digest = load(path)
        reserved = instant(reservation['reserved_at'])
        if reserved > now: raise ValueError('future reservation')
        run_id = reservation.get('run_id')
        if not isinstance(run_id,str) or not re.fullmatch(r'[1-9][0-9]{0,19}',run_id): raise ValueError('invalid reservation run')
        reservations.append((reserved,run_id,reservation.get('event')))
    sec['last_retained_reservation'] = None
    if reservations:
        reserved, run_id, event = max(reservations)
        sec['last_retained_reservation'] = {'reserved_at': reserved.isoformat(), 'run_id': run_id, 'trigger': event if event in ('schedule','push','workflow_dispatch') else 'UNKNOWN'}
        sec['reservation_warning'] = 'Reservation proves admission intent, not successful requests or latest Actions attempt.'
    result['collectors'].append(sec)
    av = row('private_daily_prices', now, '2026-11-22T00:00:00+00:00', 'SCHEDULED_BOUNDED', 'PRIVATE_OWNER_ONLY')
    av.update(configured_cron='10 12 16-21 11 *', next_configured_slot=next_slot(now,'av'),
              policy_verified_at='2026-11-18T01:08:00+00:00', policy_basis_private_commit='9a9225f76201e86f83c61f1a4c7bec104f226ffa',
              policy_basis_workflow_blob='094a279366d11bfb3972b24d36535df8ff08f35c', collector_pin='2cc42023deddf3ad275848d6631e59b21ca80680',
              quota_status='11_CALL_RUN_RESERVATION_MAX_22_ROLLING_24H_EXTERNAL_KEY_USE_UNKNOWN', rights_status='PRIVATE_PERSONAL_RESEARCH_NO_PUBLIC_PRICES_OR_RETURNS',
              blockers=['Runtime gate expires Nov22 UTC; no continuation activated.', 'External consumers of the same key and private Actions cost allowance are unverified.', 'Run-history budget fails closed at 100 combined rows; indefinite operation needs reviewed accounting.', 'Failure reasons are sanitized but not yet classified; latest success does not establish latest attempt.'])
    path = root / 'data/price_feed_status.json'
    if path.exists():
        status, digest = load(path); receipt = status.get('latest_collection')
        av['evidence'].append({'path': 'data/price_feed_status.json', 'sha256': digest})
        if receipt:
            observed = instant(receipt['observed_at'])
            if observed > now: raise ValueError('future private metadata receipt')
            if receipt.get('saved_snapshots') != 11 or receipt.get('rows_per_symbol') != 100: raise ValueError('private scope changed; re-audit')
            audit = receipt.get('coverage_audit')
            if receipt.get('scheduled_run_verified') is not True or not isinstance(audit, dict) or audit.get('hashes_and_symbols_verified') is not True:
                raise ValueError('private receipt verification incomplete')
            if not observed <= instant(audit.get('verified_at')) <= now:
                raise ValueError('invalid private verification clock')
            av.update(last_successful_observation=observed.isoformat(), source_status='PUBLIC_METADATA_OF_PRIVATE_COMPLETE_RECEIPT', saved_snapshots=11, rows_per_snapshot=100, observation_age_seconds=int((now-observed).total_seconds()))
    result['collectors'].append(av)
    manual = row('prepared_and_reference_imports', now, None, 'MANUAL_OFFLINE_IMPORTS', 'SOURCE_SPECIFIC_PUBLIC_SUMMARIES_PRIVATE_RETAINED_DATA')
    manual.update(source_status='NO_SCHEDULED_COLLECTOR_IN_AUDITED_REPOSITORIES', quota_status='NO_REQUESTS_FROM_THIS_INDEX', rights_status='SOURCE_SPECIFIC_REVIEW_REQUIRED', blockers=['Financial, insider, 13F, notes and reference imports are not ongoing scheduled collection.', 'Select analytically useful window and verify permissions, storage and integrity before importing.', 'This grouped row does not certify every source receipt; inspect individual source manifests.'])
    result['collectors'].append(manual)
    return result

if __name__ == '__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('--root', default='.'); parser.add_argument('--as-of', required=True); parser.add_argument('--output', required=True)
    args=parser.parse_args(); value=build(args.root,args.as_of)
    Path(args.output).write_text(json.dumps(value,indent=2)+'\n')
