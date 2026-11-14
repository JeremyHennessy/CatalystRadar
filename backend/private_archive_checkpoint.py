"""Produce sanitized evidence checkpoint after actually verifying private bytes.
Public readers validate bindings, not the inaccessible bytes or receipt truth.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from archive_reviewed_filings import identity, validate, MAX_BYTES
from study_split_audit import instant

MODE='PRIVATE_ORIGINAL_BYTE_CHECKPOINT_NOT_HISTORICAL_AVAILABILITY'
KEYS={'mode','verified_at','reviews_sha256','manifest_sha256','records'}
ROW_KEYS={'accession','issuer_cik','sha256','retrieved_utc','prior_hash_matches'}

def digest(raw):return hashlib.sha256(raw).hexdigest()

def create(reviews_path, archive_dir, verified_at=None):
    reviewed=Path(reviews_path).read_bytes();reviews=json.loads(reviewed)['records']
    archive_dir=Path(archive_dir).resolve();manifest=(archive_dir/'manifest.jsonl').read_bytes()
    receipts=[json.loads(x)for x in manifest.splitlines()]
    if not 1<=len(reviews)<=10 or len(receipts)!=len(reviews):raise ValueError('bounded complete recovery required')
    by_id={x['accession']:x for x in receipts}
    if len(by_id)!=len(receipts):raise ValueError('duplicate receipt')
    verified_at=verified_at or datetime.now(timezone.utc).isoformat();now=instant(verified_at)
    records=[]
    for review in reviews:
        cik,acc,url=identity(review);r=by_id[acc]
        if r['status']!='ARCHIVED_IDENTITY_VERIFIED' or r['issuer_cik']!=cik or r['url']!=url:raise ValueError('receipt identity/status mismatch')
        if r['prior_recorded_sha256']!=review['source_sha256']:raise ValueError('review changed')
        observed=instant(r['retrieved_utc']);requested=instant(r['request_utc'])
        if not requested<=observed<=now:raise ValueError('invalid receipt clocks')
        if r['archive_file']!=r['sha256']+'.txt':raise ValueError('content addressed filename required')
        path=(archive_dir/r['archive_file']).resolve()
        if path.parent!=archive_dir:raise ValueError('archive path escape')
        raw=path.read_bytes()
        if len(raw)>MAX_BYTES or len(raw)!=r['byte_count'] or digest(raw)!=r['sha256']:raise ValueError('archive bytes differ')
        validate(raw,cik,acc)
        records.append({'accession':acc,'issuer_cik':cik,'sha256':r['sha256'],
            'retrieved_utc':r['retrieved_utc'],'prior_hash_matches':r['sha256']==review['source_sha256']})
    return {'mode':MODE,'verified_at':verified_at,'reviews_sha256':digest(reviewed),
            'manifest_sha256':digest(manifest),'records':sorted(records,key=lambda x:x['accession'])}

def read_checkpoint(checkpoint, reviews_raw, as_of):
    """Structural binding only. Never upgrades recorded claims to live verification."""
    import re
    if not isinstance(checkpoint,dict) or set(checkpoint)!=KEYS or checkpoint['mode']!=MODE:raise ValueError('unknown checkpoint schema')
    if checkpoint['reviews_sha256']!=digest(reviews_raw):raise ValueError('checkpoint review inputs stale')
    if not re.fullmatch('[a-f0-9]{64}',checkpoint['manifest_sha256']):raise ValueError('manifest hash required')
    verified=instant(checkpoint['verified_at'])
    if verified>instant(as_of):raise ValueError('checkpoint is from future')
    rows=checkpoint['records'];reviews=json.loads(reviews_raw)['records']
    if not isinstance(rows,list)or len(rows)>10 or len(rows)!=len(reviews):raise ValueError('complete bounded checkpoint required')
    expected={r['accession']:r for r in reviews};seen=set()
    for row in rows:
        if not isinstance(row,dict)or set(row)!=ROW_KEYS:raise ValueError('checkpoint fields not whitelisted')
        acc=row['accession']
        if acc in seen or acc not in expected:raise ValueError('unknown/duplicate checkpoint record')
        seen.add(acc);r=expected[acc]
        if row['issuer_cik']!=str(int(r['issuer_cik'])) or not re.fullmatch('[a-f0-9]{64}',row['sha256']):raise ValueError('checkpoint identity mismatch')
        if type(row['prior_hash_matches'])is not bool or row['prior_hash_matches']!=(row['sha256']==r['source_sha256']):raise ValueError('hash comparison mismatch')
        if instant(row['retrieved_utc'])>verified:raise ValueError('invalid recorded clock')
    return {r['accession']:r for r in rows}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--reviews',required=True);p.add_argument('--archive-dir',required=True);p.add_argument('--output',required=True);a=p.parse_args()
    result=create(a.reviews,a.archive_dir)
    # Exclusive output protects an earlier checkpoint from silent replacement.
    with Path(a.output).open('x')as f:f.write(json.dumps(result,indent=2)+'\n')
    print('Sanitized checkpoint saved; raw bytes and storage identifiers excluded.')
