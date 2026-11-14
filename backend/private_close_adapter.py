"""Read-only local adapter for approved private raw-daily snapshot archive.
Does not prove corporate-action/halt completeness and is NOT auto-registered.
The returned quote and any derived prices must remain private.
"""
import json
from pathlib import Path
from datetime import datetime,timezone
from close_proxy import read_envelope,instant,MissingSessionError

def clock():return datetime.now(timezone.utc)

def lookup(root,symbol,session,*,first_observed=False):
 now=clock();root=Path(root)
 if root.is_symlink():raise ValueError('symlink archive not allowed')
 candidates=[]
 for p in root.glob('*.json'):
  if p.is_symlink():raise ValueError('symlink snapshot not allowed')
  e=json.loads(p.read_text())
  if e.get('symbol')!=symbol:continue
  observed=instant(e['observed_utc'])
  if observed>now:continue
  if first_observed:
   from datetime import time,date
   from zoneinfo import ZoneInfo
   if observed<datetime.combine(date.fromisoformat(session),time(16),ZoneInfo('America/New_York')):continue
  # Validate every eligible same-symbol snapshot: corrupted evidence is not silently skipped.
  try:q=read_envelope(p,symbol=symbol,session=session,now=now)
  except MissingSessionError:continue
  candidates.append((observed,e['response_sha256'],p.name,q))
 if not candidates:raise ValueError('no observed private daily close for requested session')
 # Latest known vintage, saved with exact evidence in the frozen order. Never
 # rewrite a frozen order using a later revision. Symbol/date ties deterministic.
 selector=min if first_observed else max
 observed,sha,name,q=selector(candidates,key=lambda x:(x[0],x[1]))
 return {**q,'private_snapshot_name':name,'adapter':'ALPHA_VANTAGE_RAW_DAILY_PRIVATE_V1','selected_as_of_utc':now.isoformat(),'vintage_policy':'FIRST_OBSERVED' if first_observed else 'LATEST_OBSERVED'}
