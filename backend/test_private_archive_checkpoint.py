import copy
import json
from pathlib import Path
import tempfile
import unittest
from archive_reviewed_filings import run
from private_archive_checkpoint import create,read_checkpoint
from test_archive_reviewed_filings import document,review

class CheckpointTests(unittest.TestCase):
    def setUp(self):
        self.t=tempfile.TemporaryDirectory();self.addCleanup(self.t.cleanup)
        self.root=Path(self.t.name);self.reviews=self.root/'reviews.json'
        self.reviews.write_text(json.dumps({'records':[review()]}))
        self.archive=self.root/'archive'
        run([review()],self.archive,get=lambda _:document(),clock=lambda:'2026-11-14T10:00:00Z',sleep=lambda _:None)
        self.check=create(self.reviews,self.archive,'2026-11-14T11:00:00Z')
    def read(self,c=None,raw=None):
        return read_checkpoint(c or self.check,raw or self.reviews.read_bytes(),'2026-11-14T12:00:00Z')
    def test_real_bytes_verified_then_whitelisted(self):
        self.assertEqual(len(self.read()),1)
        encoded=json.dumps(self.check)
        self.assertNotIn(str(self.archive),encoded);self.assertNotIn('archive_file',encoded)
        self.assertNotIn('SEC-DOCUMENT',encoded)
    def test_tampered_raw_fails_creation(self):
        next(self.archive.glob('*.txt')).write_text('changed')
        with self.assertRaises(ValueError):create(self.reviews,self.archive)
    def test_changed_reviews_fail_consumption(self):
        with self.assertRaises(ValueError):self.read(raw=self.reviews.read_bytes()+b' ')
    def test_private_extra_field_rejected(self):
        c=copy.deepcopy(self.check);c['records'][0]['library_id']='private'
        with self.assertRaises(ValueError):self.read(c)
    def test_unknown_accession_rejected(self):
        c=copy.deepcopy(self.check);c['records'][0]['accession']='unknown'
        with self.assertRaises(ValueError):self.read(c)
    def test_future_checkpoint_rejected(self):
        c=copy.deepcopy(self.check);c['verified_at']='2027-01-01T00:00:00Z'
        with self.assertRaises(ValueError):self.read(c)
    def test_wrong_match_claim_rejected(self):
        c=copy.deepcopy(self.check);c['records'][0]['prior_hash_matches']=False
        with self.assertRaises(ValueError):self.read(c)
    def test_declared_checkpoint_is_not_byte_verification(self):
        # Structural reader intentionally cannot prove that private bytes exist.
        next(self.archive.glob('*.txt')).unlink()
        self.assertEqual(len(self.read()),1)
        with self.assertRaises(FileNotFoundError):create(self.reviews,self.archive)

if __name__=='__main__':unittest.main()
