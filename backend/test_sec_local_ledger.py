import copy,multiprocessing,os,tempfile,unittest
from pathlib import Path
from sec_request_accounting import propose,GENESIS
from sec_local_ledger import initialize,inspect,append

NOW='2026-11-23T11:00:00Z'
def intent(run='1'):
 return propose([],GENESIS,NOW,'RESERVE',run_id=run,consumer='sec_metadata_watchlist_v1',issuer_cik='0000820318',request_id=run+':0000820318',url='https://data.sec.gov/submissions/CIK0000820318.json')['event']
def race(root,event,queue):
 try:append(root,GENESIS,event,NOW);queue.put('persisted')
 except ValueError:queue.put('rejected')
def fifo_probe(root,queue):
 try:inspect(root,NOW);queue.put('unexpected success')
 except (ValueError,OSError):queue.put('rejected')

def crash(root,point):
 append(root,GENESIS,intent(),NOW,_test_fault=lambda stage:os._exit(17) if stage==point else None)

class LocalLedger(unittest.TestCase):
 def setUp(self):self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)/'ledger';initialize(self.root)
 def tearDown(self):self.temp.cleanup()
 def test_roundtrip_and_stale_cas(self):
  out=append(self.root,GENESIS,intent(),NOW);self.assertTrue(out['persisted_locally']);self.assertFalse(out['collection_enabled']);self.assertFalse(out['remote_persistence_verified'])
  with self.assertRaises(ValueError):append(self.root,GENESIS,intent('2'),NOW)
  self.assertEqual(inspect(self.root,NOW)['state']['reserved_requests'],1)
 def test_real_competing_processes_only_one_wins(self):
  context=multiprocessing.get_context('fork');q=context.Queue();workers=[context.Process(target=race,args=(self.root,intent(str(i+1)),q)) for i in range(2)]
  for p in workers:p.start()
  for p in workers:p.join(10);self.assertFalse(p.is_alive());self.assertEqual(p.exitcode,0)
  self.assertEqual(sorted([q.get(timeout=2),q.get(timeout=2)]),['persisted','rejected'])
  self.assertEqual(len(inspect(self.root,NOW)['events']),1);q.close()
 def test_crash_before_replace_old_snapshot_survives(self):
  p=multiprocessing.get_context('fork').Process(target=crash,args=(self.root,'after_file_fsync'));p.start();p.join(10);self.assertEqual(p.exitcode,17)
  self.assertEqual(inspect(self.root,NOW)['state']['tip_sha256'],GENESIS)
  self.assertTrue(list(self.root.glob('.pending-*')))
 def test_crash_after_replace_and_after_sync_new_intent_stops_retry(self):
  for point in ('after_replace','after_directory_fsync'):
   with tempfile.TemporaryDirectory() as t:
    root=Path(t)/'ledger';initialize(root);p=multiprocessing.get_context('fork').Process(target=crash,args=(root,point));p.start();p.join(10);self.assertEqual(p.exitcode,17)
    state=inspect(root,NOW)['state'];self.assertIsNotNone(state['pending_request_id'])
    with self.assertRaises(ValueError):append(root,GENESIS,intent('2'),NOW)
 def test_invalid_append_cannot_change_snapshot(self):
  before=(self.root/'ledger.json').read_bytes();event=intent();event['url']='https://other.invalid/'
  with self.assertRaises(ValueError):append(self.root,GENESIS,event,NOW)
  self.assertEqual((self.root/'ledger.json').read_bytes(),before)
 def test_uninitialized_and_reinitialize_rejected(self):
  with self.assertRaises(FileExistsError):initialize(self.root)
  (self.root/'ledger.json').unlink()
  with self.assertRaises(FileNotFoundError):inspect(self.root,NOW)
 def test_symlink_and_permissions_fail_closed(self):
  ledger=self.root/'ledger.json';original=ledger.read_bytes();ledger.unlink();ledger.symlink_to('/etc/passwd')
  with self.assertRaises(OSError):inspect(self.root,NOW)
  ledger.unlink();ledger.write_bytes(original);ledger.chmod(0o644)
  with self.assertRaises(ValueError):inspect(self.root,NOW)
 def test_duplicate_json_and_corruption_rejected(self):
  (self.root/'ledger.json').write_text('[{"a":1,"a":2}]')
  with self.assertRaises(ValueError):inspect(self.root,NOW)
 def test_file_and_directory_permissions(self):
  self.assertEqual(self.root.stat().st_mode&0o777,0o700)
  for name in ('ledger.json','lock'):self.assertEqual((self.root/name).stat().st_mode&0o777,0o600)
 def test_directory_sync_failure_never_acknowledges_success(self):
  from unittest.mock import patch
  real=os.fsync;calls=[]
  def fail_second(fd):
   calls.append(fd)
   if len(calls)==2:raise OSError('simulated directory sync failure')
   return real(fd)
  with patch('sec_local_ledger.os.fsync',side_effect=fail_second):
   with self.assertRaises(OSError):append(self.root,GENESIS,intent(),NOW)
  self.assertIsNotNone(inspect(self.root,NOW)['state']['pending_request_id'])
 def test_lock_symlink_rejected(self):
  (self.root/'lock').unlink();(self.root/'lock').symlink_to('/etc/passwd')
  with self.assertRaises(OSError):inspect(self.root,NOW)

 def test_fifo_ledger_and_lock_rejected_without_hanging(self):
  for name in ('ledger.json','lock'):
   with tempfile.TemporaryDirectory() as t:
    root=Path(t)/'ledger';initialize(root);(root/name).unlink();os.mkfifo(root/name,0o600)
    context=multiprocessing.get_context('fork');queue=context.Queue();worker=context.Process(target=fifo_probe,args=(root,queue));worker.start();worker.join(3)
    if worker.is_alive():worker.terminate();worker.join(3);self.fail('FIFO blocked ledger operation')
    self.assertEqual(worker.exitcode,0);self.assertEqual(queue.get(timeout=2),'rejected');queue.close()
 def test_hardlinked_ledger_and_lock_rejected(self):
  for name in ('ledger.json','lock'):
   with tempfile.TemporaryDirectory() as t:
    root=Path(t)/'ledger';initialize(root);os.link(root/name,Path(t)/'alias')
    with self.assertRaises(ValueError):inspect(root,NOW)
