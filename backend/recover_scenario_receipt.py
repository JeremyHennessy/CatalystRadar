"""Verify already-created receipt; NEVER dispatch, regenerate plan or call vendor."""
from pathlib import Path
import os,json,re
from private_scenario import gate
from collect import privacy
from freeze_receipt import verify
from proxy_runner import canonical

def recover():
 root,_=gate();privacy()
 run_id=os.environ.get('EXISTING_RECEIPT_RUN_ID','');commit=os.environ.get('FROZEN_PLAN_COMMIT','');plan_hash=os.environ.get('FROZEN_PLAN_SHA256','');workflow=os.environ.get('EXPECTED_RECEIPT_WORKFLOW_BLOB_SHA','')
 if not run_id.isdigit() or not re.fullmatch('[a-f0-9]{40}',commit) or not re.fullmatch('[a-f0-9]{64}',plan_hash):raise ValueError('fixed existing receipt identity required')
 receipt=verify(run_id=int(run_id),commit_sha=commit,ledger_path='data/scenarios/'+plan_hash+'.json',order_id=None,freeze_hash=plan_hash,session='2026-11-16',expected_workflow_blob_sha=workflow,scenario=True)
 if receipt.get('verified')is not True or receipt.get('plan_sha256')!=plan_hash:raise ValueError('existing receipt not verified')
 dest=root/'data/scenario-receipts'
 if (root/'data').is_symlink() or dest.is_symlink():raise ValueError('unsafe private receipt path')
 privacy();dest.mkdir(parents=True,exist_ok=True);target=dest/(plan_hash+'.json');payload=canonical(receipt)
 if target.exists():
  if target.is_symlink()or target.read_bytes()!=payload:raise ValueError('receipt differs; preserve existing record')
 else:
  fd=os.open(target,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
  with os.fdopen(fd,'wb')as out:out.write(payload);out.flush();os.fsync(out.fileno())
 return {'existing_receipt_verified':True,'run_id':int(run_id),'plan_sha256':plan_hash,'new_dispatches':0,'primary_book_changed':False}
