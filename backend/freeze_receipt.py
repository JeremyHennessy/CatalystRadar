"""Read-only verifier of a GitHub-server workflow creation receipt.
NOT a push-time oracle: created_at is workflow run creation, bounding existence of
its exact head SHA no later than that time. Never use git author/committer dates.
No CLI, no dispatch or token-writing; not installed in production ADAPTERS.
"""
import base64,hashlib,json,re,os,urllib.request
from datetime import datetime,time,timezone
from zoneinfo import ZoneInfo
from proxy_runner import canonical,digest,instant,valid_hash
from private_prices import NoRedirect
REPO='JeremyHennessy/CatalystRadar-Private'
WORKFLOW='.github/workflows/freeze-receipt.yml'

def api(path):
 if not path.startswith('/repos/'+REPO+'/'):raise ValueError('wrong API scope')
 token=os.environ.get('GITHUB_TOKEN')
 if not token:raise ValueError('missing private read token')
 request=urllib.request.Request('https://api.github.com'+path,headers={'Authorization':'Bearer '+token,'Accept':'application/vnd.github+json','X-GitHub-Api-Version':'2022-11-28'})
 try:
  with urllib.request.build_opener(NoRedirect()).open(request,timeout=30) as response:return json.loads(response.read())
 except Exception:raise ValueError('private GitHub receipt read unavailable') from None

def verify(*,run_id,commit_sha,ledger_path,order_id,freeze_hash,session,expected_workflow_blob_sha,fetch=api,scenario=False):
 if type(run_id)is not int or run_id<=0:raise ValueError('invalid run ID')
 if not re.fullmatch('[a-f0-9]{40}',commit_sha) or not re.fullmatch('[a-f0-9]{40}',expected_workflow_blob_sha):raise ValueError('invalid commit/workflow identity')
 pattern=r'data/scenarios/[a-f0-9]{64}\.json' if scenario is True else r'data/proxy/[0-9]{8}\.json'
 if type(scenario)is not bool or not re.fullmatch(pattern,ledger_path) or not valid_hash(freeze_hash):raise ValueError('invalid immutable ledger reference')
 prefix='/repos/'+REPO
 repo=fetch(prefix+'/')
 if repo.get('full_name')!=REPO or repo.get('private') is not True or repo.get('visibility')!='private':raise ValueError('not verified private repository')
 run=fetch(prefix+'/actions/runs/'+str(run_id))
 if run.get('id')!=run_id or run.get('repository',{}).get('full_name')!=REPO or run.get('head_sha')!=commit_sha or run.get('head_branch')!='main':raise ValueError('run identity mismatch')
 if run.get('event')!='workflow_dispatch' or run.get('path')!=WORKFLOW or run.get('run_attempt')!=1:raise ValueError('not the prescribed first dispatch receipt')
 created=instant(run['created_at']);deadline=datetime.combine(datetime.fromisoformat(session).date(),time(8),ZoneInfo('America/New_York'))
 if created>datetime.now(timezone.utc) or created>deadline:raise ValueError('late or future server receipt')
 # Fetch exact commit content, never mutable main. Verify Git blob hashes locally.
 def file(path):
  f=fetch(prefix+'/contents/'+path+'?ref='+commit_sha)
  if f.get('encoding')!='base64':raise ValueError('unexpected file encoding')
  raw=base64.b64decode(''.join(f['content'].split()),validate=True)
  gitsha=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
  if gitsha!=f.get('sha'):raise ValueError('Git content hash mismatch')
  return raw,gitsha
 _,workflowsha=file(WORKFLOW)
 if workflowsha!=expected_workflow_blob_sha:raise ValueError('unreviewed receipt workflow')
 raw,ledgersha=file(ledger_path);ledger=json.loads(raw)
 if scenario:
  from mechanical_scenario import MODEL
  o=ledger;unhashed={k:v for k,v in o.items() if k!='plan_sha256'}
  if o.get('model')!=MODEL or o.get('entry_session')!=session or o.get('plan_sha256')!=freeze_hash or digest(unhashed)!=freeze_hash or ledger_path!='data/scenarios/'+freeze_hash+'.json':raise ValueError('scenario content mismatch')
 else:
  matches=[o for o in ledger.get('orders',[]) if o.get('id')==order_id]
  if len(matches)!=1:raise ValueError('order not uniquely present')
  o=matches[0];frozen={k:v for k,v in o.items() if k!='freeze_hash'}
  if o.get('state')!='FROZEN' or o.get('session')!=session or o.get('freeze_hash')!=freeze_hash or digest(frozen)!=freeze_hash:raise ValueError('frozen order content mismatch')
 frozen_at=instant(o['freeze_utc'])
 if (not scenario and frozen_at.astimezone(ZoneInfo('America/New_York')).date().isoformat()!=session) or not frozen_at<=created<=deadline:raise ValueError('not prospective server receipt')
 # Entire evidence is private. Hash binds remote run response plus exact blob refs.
 proof={'run':run,'commit_sha':commit_sha,'ledger_blob_sha':ledgersha,'ledger_sha256':hashlib.sha256(raw).hexdigest(),'workflow_blob_sha':workflowsha}
 result={'verified':True,'order_id':order_id,'freeze_hash':freeze_hash,'repository':REPO,'receipt_basis':'TRUSTED_SERVER_RECEIPT','server_received_utc':created.isoformat(),'timestamp_semantics':'WORKFLOW_RUN_CREATED_NOT_GIT_PUSH_TIME','receipt_sha256':digest(proof),'proof':proof}

 if scenario:result['plan_sha256']=freeze_hash
 return result
