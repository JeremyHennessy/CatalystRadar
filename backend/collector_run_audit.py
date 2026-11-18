"""Offline projection of an explicitly time-bounded, manually verified Actions audit.
No collection, scheduling or live-history inference. Receipt claims remain reported
metadata, not independent source-byte revalidation or provider authenticity proofs.
"""
import hashlib
import json
import re
from datetime import datetime
from pathlib import Path

INPUT = 'data/operational-audits/collector-runs-20261118.json'

def bounded(path, size=200_000):
    with path.open('rb') as f: raw=f.read(size+1)
    if len(raw)>size: raise ValueError('Input exceeds bound')
    return raw

def integer(value, low=0, high=10**15):
    if type(value) is not int or not low <= value <= high: raise ValueError('Invalid integer')
    return value

def clock(value, end=None):
    if not isinstance(value,str) or not re.fullmatch(r'2026-11-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?(?:Z|\+00:00)',value):
        raise ValueError('Invalid UTC clock')
    date=datetime.fromisoformat(value.replace('Z','+00:00'))
    if end is not None and date>end: raise ValueError('Clock after audit')
    return date

def build(root):
    root = Path(root)
    raw = bounded(root / INPUT)
    audit = json.loads(raw)
    asof=clock(audit['audit_as_of'])
    if audit['schema_version'] != 1: raise ValueError('Unsupported schema')
    public = audit['public_history']
    if public['source'] != 'GITHUB_WORKFLOW_RUNS_API' or audit['private_history']['source'] != 'SIGNED_IN_WORKFLOW_LIST_AND_JOB_STEPS': raise ValueError('Unknown history source')
    if public['pagination_next'] is not None or public['total_count'] != len(public['runs']):
        raise ValueError('Incomplete named workflow listing')
    integer(public['total_count'],1,100)
    integer(audit['private_history']['listed_count'],1,100)
    private_receipt=audit['private_history']['latest_receipt']
    integer(private_receipt['saved_snapshots'],0,100)
    integer(private_receipt['sessions_per_snapshot'],0,10000)
    clock(private_receipt['observed_utc'],asof)
    if not isinstance(private_receipt['blob'],str) or not re.fullmatch('[0-9a-f]{40}',private_receipt['blob']): raise ValueError('Invalid private blob')
    if audit['private_history']['listed_count'] != len(audit['private_history']['runs']):
        raise ValueError('Private listing count mismatch')
    unlinked=audit['unlinked_sec_receipts']
    if not isinstance(unlinked,list) or len(unlinked)>100 or len(set(unlinked))!=len(unlinked): raise ValueError('Invalid unlinked inventory')
    for path in unlinked:
        if not path.startswith('data/sec-observations/') or '..' in path or json.loads(bounded(root/path,2_000_000)).get('github_run_url'):
            raise ValueError('Invalid unlinked receipt')
    output = []
    for family, history, repo in [('sec', public, 'CatalystRadar'), ('private_prices', audit['private_history'], 'CatalystRadar-Private')]:
        if not isinstance(history['runs'],list) or not 1 <= len(history['runs']) <= 100: raise ValueError('Invalid run list')
        rows = []
        seen = set()
        for item in history['runs']:
            run_id = integer(item['run_id'],1)
            if item['created_at'] is not None: clock(item['created_at'],asof)
            elif family=='sec' or run_id==44172913902: raise ValueError('Missing latest/public clock')
            if run_id in seen or item['job']['run_id'] != run_id:
                raise ValueError('Duplicate or mismatched run')
            seen.add(run_id)
            job = item['job']
            integer(job['id'],1); integer(job['run_id'],1)
            if job['conclusion'] not in ('success','failure','cancelled','skipped','timed_out','neutral','action_required') or job['status'] != 'completed': raise ValueError('Invalid job status')
            if not isinstance(job['steps'],list) or not 1 <= len(job['steps']) <= 100: raise ValueError('Invalid steps')
            steps={}
            for step in job['steps']:
                n=integer(step['number'],1,100)
                if n in steps or step['conclusion'] not in ('success','failure','cancelled','skipped','timed_out','neutral') or step['status']!='completed': raise ValueError('Invalid/duplicate step')
                steps[n]=step['conclusion']
            row = dict(run_id=run_id, url=f'https://github.com/JeremyHennessy/{repo}/actions/runs/{run_id}', created_at=item['created_at'], job_conclusion=job['conclusion'], admission='UNVERIFIED', source_response='UNVERIFIED', persistence='UNVERIFIED', publication='UNVERIFIED', source_observed_at=None, successful_issuers=None, configured_issuers=None, receipt_path=None, receipt_sha256=None)
            if family == 'sec':
                path = item['receipt_path']
                gate = item['gate_evidence']
                if gate:
                    if path or gate not in ('OUTSIDE_TRIAL_WINDOW', 'WINDOW_GATE_OUTPUT_FALSE') or any(steps.get(n) != 'skipped' for n in (4,5,6)):
                        raise ValueError('Contradictory skip evidence')
                    row.update(admission='SKIPPED_OUTSIDE_WINDOW', source_response='NOT_REQUESTED', persistence='SKIPPED', publication='SKIPPED', gate_evidence=gate)
                elif path:
                    if not path.startswith('data/sec-observations/') or '..' in path:
                        raise ValueError('Invalid receipt path')
                    data = bounded(root/path,2_000_000); receipt = json.loads(data)
                    started=clock(receipt['started_at'],asof); finished=clock(receipt['finished_at'],asof)
                    if finished<started or started<clock(item['created_at']): raise ValueError('Contradictory receipt clocks')
                    integer(receipt['successful_issuers'],0,10); integer(receipt['configured_issuers'],0,10)
                    if receipt.get('github_run_url') != row['url']:
                        raise ValueError('Receipt/run mismatch')
                    statuses = [s.get('validation_status') for s in receipt['sources']]
                    denied = any(s.get('error') == 'HTTP 403 from public source' for s in receipt['sources'])
                    complete = receipt.get('metadata_window_complete') is True and receipt.get('successful_issuers') == receipt.get('configured_issuers') == 10 and len(statuses) == 10 and not denied and all(status=='METADATA_WINDOW_VALIDATED' for status in statuses) and not receipt.get('errors')
                    response = 'REPORTED_COMPLETE_METADATA' if complete else 'SOURCE_DENIED_403' if denied else 'INCOMPLETE_RETAINED_RECEIPT'
                    row.update(admission='ADMITTED', source_response=response, source_observed_at=receipt['finished_at'], successful_issuers=receipt['successful_issuers'], configured_issuers=receipt['configured_issuers'], receipt_path=path, receipt_sha256=hashlib.sha256(data).hexdigest(), persistence='RECEIPT_PERSISTED' if steps.get(5)=='success' else 'UNVERIFIED', publication='PUBLICATION_STEP_SUCCEEDED' if steps.get(6)=='success' else 'UNVERIFIED')
            else:
                if steps.get(4)=='success':
                    row.update(admission='COLLECTION_STEP_SUCCEEDED', source_response='UNVERIFIED_PER_RUN')
                if steps.get(5)=='success':
                    row.update(persistence='PRIVATE_RETENTION_STEP_SUCCEEDED', publication='NOT_PUBLICLY_PUBLISHED')
                if run_id == 44172913902:
                    if steps.get(4) != 'success' or steps.get(5) != 'success':
                        raise ValueError('Private retained receipt conflicts with job stages')
                    receipt = history['latest_receipt']
                    row.update(source_response='PRIVATE_SNAPSHOTS_RETAINED', source_observed_at=receipt['observed_utc'], saved_snapshots=receipt['saved_snapshots'], sessions_per_snapshot=receipt['sessions_per_snapshot'], private_receipt_blob=receipt['blob'])
            rows.append(row)
        if family=='sec':
            rows.sort(key=lambda row:clock(row['created_at']),reverse=True)
            latest=rows[0]
        else:
            matches=[row for row in rows if row['run_id']==44172913902]
            if len(matches)!=1: raise ValueError('Missing observed latest private run')
            latest=matches[0]
            if clock(latest['source_observed_at'])<clock(latest['created_at']): raise ValueError('Private receipt precedes run')
        output.append(dict(id=family, history_source=history['source'], listed_run_count=len(rows), latest_workflow_execution=latest, runs=rows))
    return dict(schema_version=1, audit_as_of=audit['audit_as_of'], collection_enabled=False, scope='NAMED_WORKFLOW_HISTORY_SNAPSHOT_NOT_LIVE', input_path=INPUT, input_sha256=hashlib.sha256(raw).hexdigest(), collectors=output, unlinked_sec_receipt_count=len(audit['unlinked_sec_receipts']), limitations=['Workflow success is not source success. Publication step success is not independent deployed-content verification.', 'Latest receipt freshness and latest workflow execution are separate clocks.', 'Private source rows and quotes are not public; older per-run response details remain unverified.', 'Named workflow list snapshots are not global consumer or provider history and do not promise future execution.', 'Unlinked retained SEC receipts have no workflow URL; no workflow execution is inferred for them.'])

if __name__ == '__main__':
    print(json.dumps(build(Path(__file__).resolve().parent.parent), indent=2, sort_keys=True))
