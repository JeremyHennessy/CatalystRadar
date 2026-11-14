"""One bounded receipt dispatch after private immutable scenario commit.
No vendor calls/trades. No CLI until the exact workflow and code pin are reviewed.
"""
import os,json,re,time,urllib.request,subprocess,base64,hashlib
from pathlib import Path
from datetime import datetime,timezone
from collect import privacy,api,REPO
from private_prices import HTTP
from private_scenario import gate
from freeze_receipt import verify
from mechanical_scenario import DEADLINE
from proxy_runner import canonical

def checked_runs(response):
 if not isinstance(response,dict) or not isinstance(response.get('workflow_runs'),list):raise ValueError('invalid workflow history shape')
 runs=response['workflow_runs'];total=response.get('total_count')
 if type(total)is not int or total<0 or total!=len(runs) or len(runs)>=100 or any(not isinstance(r,dict) for r in runs):raise ValueError('truncated or invalid workflow history')
 return runs

def dispatch_once():
 req=urllib.request.Request('https://api.github.com/repos/'+REPO+'/actions/workflows/freeze-receipt.yml/dispatches',data=b'{"ref":"main"}',method='POST',headers={'Authorization':'Bearer '+os.environ['GITHUB_TOKEN'],'Accept':'application/vnd.github+json','Content-Type':'application/json'})
 with HTTP.open(req,timeout=30) as response:
  if response.status!=204:raise ValueError('receipt dispatch not accepted')

def record_receipt():
 root,_=gate();privacy()
 if datetime.now(timezone.utc)>DEADLINE:raise ValueError('missed prospective receipt deadline')
 commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()
 if not re.fullmatch('[a-f0-9]{40}',commit):raise ValueError('invalid private commit')
 head=api('repos/'+REPO+'/git/ref/heads/main')
 if head.get('object',{}).get('sha')!=commit:raise ValueError('private main differs from frozen commit')
 plans=list((root/'data/scenarios').glob('*.json'))
 if len(plans)!=1:raise ValueError('exactly one immutable plan required')
 plan=json.loads(plans[0].read_text());workflow_sha=os.environ.get('EXPECTED_RECEIPT_WORKFLOW_BLOB_SHA','')
 if not re.fullmatch('[a-f0-9]{40}',workflow_sha):raise ValueError('reviewed receipt workflow missing')
 dest=root/'data/scenario-receipts'
 if dest.is_symlink() or (root/'data').is_symlink():raise ValueError('symlink receipt destination')
 if dest.exists() and list(dest.glob('*.json')):raise ValueError('receipt already exists; no repeat dispatch')
 # Precheck authoritative exact committed bytes/workflow before any dispatch.
 workflow=api('repos/'+REPO+'/contents/.github/workflows/freeze-receipt.yml?ref='+commit)
 if workflow.get('sha')!=workflow_sha:raise ValueError('unreviewed receipt workflow')
 remote=api('repos/'+REPO+'/contents/data/scenarios/'+plan['plan_sha256']+'.json?ref='+commit)
 if remote.get('encoding')!='base64':raise ValueError('invalid plan encoding')
 raw=base64.b64decode(''.join(remote['content'].split()),validate=True)
 if hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()!=remote.get('sha') or json.loads(raw)!=plan:raise ValueError('committed plan mismatch')
 runpath='repos/'+REPO+'/actions/workflows/freeze-receipt.yml/runs?event=workflow_dispatch&head_sha='+commit+'&per_page=100'
 previous=checked_runs(api(runpath))
 if previous:raise ValueError('existing receipt attempt; no repeat dispatch')
 if datetime.now(timezone.utc)>DEADLINE:raise ValueError('pre-dispatch deadline missed')
 dispatch_once() # Never retry this POST, even after ambiguous timeout/cancellation.
 receipt=None
 for attempt in range(12):
  if datetime.now(timezone.utc)>DEADLINE:raise ValueError('missed receipt deadline; no valid prospective scenario')
  runs=checked_runs(api('repos/'+REPO+'/actions/workflows/freeze-receipt.yml/runs?event=workflow_dispatch&head_sha='+commit+'&per_page=100'))
  if len(runs)>=100:raise ValueError('receipt history truncated')
  candidates=[r for r in runs if r.get('head_sha')==commit and r.get('event')=='workflow_dispatch' and r.get('run_attempt')==1]
  if len(candidates)>1:raise ValueError('ambiguous duplicate receipts')
  if candidates:
   receipt=verify(run_id=candidates[0]['id'],commit_sha=commit,ledger_path='data/scenarios/'+plan['plan_sha256']+'.json',order_id=None,freeze_hash=plan['plan_sha256'],session=plan['entry_session'],expected_workflow_blob_sha=workflow_sha,scenario=True);break
  if attempt<11:time.sleep(5)
 if not isinstance(receipt,dict) or receipt.get('verified') is not True or receipt.get('plan_sha256')!=plan['plan_sha256']:raise ValueError('no trusted server receipt observed; do not redispatch automatically')
 privacy();dest.mkdir(parents=True,exist_ok=True)
 fd=os.open(dest/(plan['plan_sha256']+'.json'),os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
 with os.fdopen(fd,'wb') as out:out.write(canonical(receipt));out.flush();os.fsync(out.fileno())
 return {'trusted_receipt_obtained':True,'plan_sha256':plan['plan_sha256'],'run_id':candidates[0]['id'],'primary_book_changed':False}
