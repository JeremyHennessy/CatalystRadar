import unittest,tempfile,json
from pathlib import Path
from datetime import datetime
from unittest.mock import patch
import private_close_adapter as a
class TestAdapter(unittest.TestCase):
 def setUp(self):
  self.t=tempfile.TemporaryDirectory();self.root=Path(self.t.name)
  self.clock=patch.object(a,'clock',return_value=datetime.fromisoformat('2026-11-16T12:00:00+00:00'));self.clock.start()
 def tearDown(self):self.clock.stop();self.t.cleanup()
 def put(self,name,observed,symbol='TEST'):
  (self.root/name).write_text(json.dumps({'symbol':symbol,'observed_utc':observed,'response_sha256':name}))
 def reader(self,p,**kw):return {'symbol':kw['symbol'],'session':kw['session'],'source_sha256':json.loads(p.read_text())['response_sha256'],'close':'20'}
 def test_latest_observed_only(self):
  self.put('old.json','2026-11-14T12:00:00Z');self.put('new.json','2026-11-15T12:00:00Z');self.put('future.json','2026-11-17T12:00:00Z')
  with patch.object(a,'read_envelope',side_effect=self.reader):
   q=a.lookup(self.root,'TEST','2026-11-13');self.assertEqual(q['private_snapshot_name'],'new.json')
 def test_future_only_unavailable(self):
  self.put('future.json','2026-11-17T12:00:00Z');self.assertRaises(ValueError,a.lookup,self.root,'TEST','2026-11-13')
 def test_corrupt_fails_closed(self):
  self.put('old.json','2026-11-14T12:00:00Z')
  with patch.object(a,'read_envelope',side_effect=ValueError('bad hash')):self.assertRaises(ValueError,a.lookup,self.root,'TEST','2026-11-13')
 def test_no_symbol(self):self.assertRaises(ValueError,a.lookup,self.root,'TEST','2026-11-13')

 def test_valid_older_archive_without_session_skipped(self):
  self.put('old.json','2026-11-14T12:00:00Z');self.put('new.json','2026-11-15T12:00:00Z')
  def reader(p,**kw):
   if p.name=='old.json':raise a.MissingSessionError('missing')
   return self.reader(p,**kw)
  with patch.object(a,'read_envelope',side_effect=reader):self.assertEqual(a.lookup(self.root,'TEST','2026-11-13')['private_snapshot_name'],'new.json')

 def test_first_vintage_survives_later_revision(self):
  self.put('old.json','2026-11-14T12:00:00Z');self.put('new.json','2026-11-15T12:00:00Z')
  with patch.object(a,'read_envelope',side_effect=self.reader):
   q=a.lookup(self.root,'TEST','2026-11-13',first_observed=True);self.assertEqual(q['private_snapshot_name'],'old.json');self.assertEqual(q['vintage_policy'],'FIRST_OBSERVED')
