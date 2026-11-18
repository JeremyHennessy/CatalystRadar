"""Offline local POSIX CAS persistence. NOT remote/global collection admission.

Cooperating processes must use this adapter and a trusted owner-only local
filesystem with working flock, atomic replace and fsync. No network operations.
"""
from contextlib import contextmanager
import fcntl
import json
import os
from pathlib import Path
import stat
import uuid
from sec_request_accounting import GENESIS, replay

MAX_BYTES=4_000_000

def unique(pairs):
 result={}
 for key,value in pairs:
  if key in result:raise ValueError('duplicate ledger field')
  result[key]=value
 return result

def encode(events):
 raw=(json.dumps(events,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode()
 if len(raw)>MAX_BYTES:raise ValueError('ledger byte bound exceeded')
 return raw

def check_owner(st,directory=False):
 if st.st_uid!=os.geteuid() or stat.S_IMODE(st.st_mode)!=(0o700 if directory else 0o600):raise ValueError('owner-only ledger required')
 if not (stat.S_ISDIR(st.st_mode) if directory else stat.S_ISREG(st.st_mode)):raise ValueError('wrong ledger object type')
 if not directory and st.st_nlink!=1:raise ValueError('linked ledger file rejected')

@contextmanager
def directory(root):
 fd=os.open(root,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
 try:check_owner(os.fstat(fd),True);yield fd
 finally:os.close(fd)

def open_file(fd,name,flags):
 handle=os.open(name,flags|os.O_NOFOLLOW|os.O_NONBLOCK,0o600,dir_fd=fd)
 try:check_owner(os.fstat(handle))
 except BaseException:os.close(handle);raise
 return handle

def initialize(root):
 """Explicitly create a NEW local ledger; never overwrite or repair existing one."""
 root=Path(root);root.mkdir(mode=0o700,parents=False,exist_ok=False)
 with directory(root) as fd:
  for name,raw in [('lock',b''),('ledger.json',encode([]))]:
   handle=open_file(fd,name,os.O_WRONLY|os.O_CREAT|os.O_EXCL)
   with os.fdopen(handle,'wb') as out:out.write(raw);out.flush();os.fsync(out.fileno())
  os.fsync(fd)
 # Persist creation of the root directory itself on the trusted parent.
 with directory_parent(root.parent) as parent:os.fsync(parent)

@contextmanager
def directory_parent(root):
 fd=os.open(root,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
 try:yield fd
 finally:os.close(fd)

@contextmanager
def locked(root):
 with directory(root) as fd:
  lock=open_file(fd,'lock',os.O_RDWR)
  try:
   fcntl.flock(lock,fcntl.LOCK_EX)
   yield fd
  finally:
   fcntl.flock(lock,fcntl.LOCK_UN);os.close(lock)

def read_locked(fd,as_of):
 handle=open_file(fd,'ledger.json',os.O_RDONLY)
 with os.fdopen(handle,'rb') as source:raw=source.read(MAX_BYTES+1)
 if len(raw)>MAX_BYTES:raise ValueError('ledger byte bound exceeded')
 events=json.loads(raw,object_pairs_hook=unique,parse_constant=lambda _:(_ for _ in ()).throw(ValueError('nonfinite JSON')))
 return events,replay(events,as_of)

def inspect(root,as_of):
 with locked(root) as fd:
  events,state=read_locked(fd,as_of)
  return {'events':events,'state':state,'persistence_scope':'LOCAL_POSIX_ONLY','collection_enabled':False}

def append(root,expected_tip,event,as_of,_test_fault=None):
 """Persist exactly one validated event by local CAS; never authorize retrieval.

A failure/lost acknowledgment may leave OLD or NEW ledger. Caller must reread;
never blindly retry a provider request. `_test_fault` is fault injection only.
"""
 def fault(point):
  if _test_fault is not None:_test_fault(point)
 with locked(root) as fd:
  events,state=read_locked(fd,as_of)
  if state['tip_sha256']!=expected_tip:raise ValueError('stale local CAS expectation')
  new_events=events+[event];new_state=replay(new_events,as_of);raw=encode(new_events)
  temporary='.pending-'+uuid.uuid4().hex
  handle=open_file(fd,temporary,os.O_WRONLY|os.O_CREAT|os.O_EXCL)
  with os.fdopen(handle,'wb') as out:
   out.write(raw);out.flush();os.fsync(out.fileno())
  fault('after_file_fsync')
  os.replace(temporary,'ledger.json',src_dir_fd=fd,dst_dir_fd=fd)
  fault('after_replace')
  os.fsync(fd)
  fault('after_directory_fsync')
  saved,verified=read_locked(fd,as_of)
  if saved!=new_events or verified['tip_sha256']!=new_state['tip_sha256']:raise ValueError('local readback mismatch')
  return {'persisted_locally':True,'tip_sha256':verified['tip_sha256'],
          'remote_persistence_verified':False,'collection_enabled':False,
          'scope':'COOPERATING_PROCESSES_ON_TRUSTED_LOCAL_POSIX_FILESYSTEM_ONLY'}
