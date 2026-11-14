"""Private-only mechanical-plan wrapper, not scheduled or activated.
A reviewed private workflow must pin EXPECTED_PUBLIC_CODE_SHA and checkout .collector
at exactly that commit. No raw prices or derived values are printed/publicized.
"""
from pathlib import Path
import os,re,subprocess,json,fcntl
from collect import privacy
from private_close_adapter import lookup
from mechanical_scenario import freeze
from proxy_runner import canonical,digest

def gate():
 if os.environ.get('GITHUB_REPOSITORY')!='JeremyHennessy/CatalystRadar-Private' or os.environ.get('GITHUB_ACTIONS')!='true' or os.environ.get('GITHUB_RUN_ATTEMPT')!='1':raise ValueError('approved private Actions context required')
 expected=os.environ.get('EXPECTED_PUBLIC_CODE_SHA','')
 if not re.fullmatch('[0-9a-f]{40}',expected):raise ValueError('reviewed code pin missing')
 root=Path(os.environ['GITHUB_WORKSPACE'])
 if not root.is_absolute() or root.is_symlink():raise ValueError('invalid private workspace')
 root=root.resolve();code=Path(__file__).resolve().parent.parent
 if code!=root/'.collector':raise ValueError('code must be separate pinned checkout')
 head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=code,text=True).strip()
 if head!=expected:raise ValueError('code pin mismatch')
 if subprocess.check_output(['git','status','--porcelain','--untracked-files=all'],cwd=code,text=True).strip():raise ValueError('modified collector checkout')
 privacy() # authenticated official GitHub metadata and owner-only collaborator check
 return root,expected

def prepare():
 root,pin=gate();data=root/'data';dest=data/'scenarios';prices=data/'prices'
 for path in (data,dest,prices):
  if path.is_symlink():raise ValueError('symlink private data path forbidden')
 if not prices.is_dir():raise ValueError('private prices unavailable')
 dest.mkdir(parents=True,exist_ok=True)
 with (dest/'.lock').open('a') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX)
  # A second run must not silently replace selection, timing or protocol.
  existing=list(dest.glob('*.json'))
  if existing:raise ValueError('scenario already exists; explicit restatement review required')
  plan=freeze(lambda symbol,session:lookup(prices,symbol,session))
  plan['reviewed_public_code_sha']=pin;plan.pop('plan_sha256');plan['plan_sha256']=digest(plan)
  privacy() # No write if visibility/access has changed during source reads.
  target=dest/(plan['plan_sha256']+'.json');fd=os.open(target,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
  with os.fdopen(fd,'wb') as out:out.write(canonical(plan));out.flush();os.fsync(out.fileno())
 return {'mode':'CONDITIONAL_MECHANICAL_ILLUSTRATION','plan_sha256':plan['plan_sha256'],'universe_count':len(plan['records']),'selected_count':sum(r['state']=='SELECTED' for r in plan['records']),'trusted_receipt_obtained':False,'primary_book_changed':False,'prices_public':False}

# No CLI until exact public pin, private workflow and receipt dispatch are reviewed.
