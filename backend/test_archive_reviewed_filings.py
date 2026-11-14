import hashlib
from pathlib import Path
import tempfile
import unittest
import urllib.error
from archive_reviewed_filings import run, identity, validate, MAX_BYTES, NoRedirect, ResponseTooLarge

ACC='0000000123-26-000001'
def document(acc=ACC,cik='123'):
    return f'<SEC-DOCUMENT>file\n<SEC-HEADER>\nACCESSION NUMBER: {acc}\nCENTRAL INDEX KEY: {cik}\n</SEC-HEADER>\ntext'.encode()
def review(acc=ACC):
    return {'issuer_cik':'123','accession':acc,'source_sha256':hashlib.sha256(document(acc)).hexdigest(),'source_url':'https://attacker.invalid/ignore'}

class ArchiveTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.dest=Path(self.temp.name)/'new'
    def execute(self, reviews=None,get=None):
        return run(reviews or [review()], self.dest, get=get or (lambda u:document()),clock=lambda:'2026-11-14T23:30:00Z',sleep=lambda s:None)
    def test_archives_exact_bytes_new_clock_not_first_public(self):
        r=self.execute();x=r['records'][0]
        self.assertEqual((self.dest/x['archive_file']).read_bytes(),document())
        self.assertIsNone(x['first_public_utc']);self.assertTrue(x['prior_hash_matches'])
        self.assertFalse(r['durable_remote_storage_verified'])
    def test_url_derived_not_trusted(self):
        self.assertEqual(identity(review())[2],f'https://www.sec.gov/Archives/edgar/data/123/{ACC.replace("-","")}/{ACC}.txt')
    def test_wrong_accession_rejected(self):
        self.assertEqual(self.execute(get=lambda _:document('0000000123-26-000999'))['archived_count'],0)
    def test_wrong_cik_rejected(self):
        self.assertEqual(self.execute(get=lambda _:document(cik='9'))['archived_count'],0)
    def test_block_page_rejected(self):
        self.assertEqual(self.execute(get=lambda _:b'HTTP200 blocked')['archived_count'],0)
    def test_403_stops_remaining_no_retry(self):
        calls=[]
        def denied(url):
            calls.append(url);raise urllib.error.HTTPError(url,403,'denied',{},None)
        r=self.execute([review(),review('0000000123-26-000002')],denied)
        self.assertEqual(len(calls),1);self.assertEqual(r['records'][1]['status'],'NOT_ATTEMPTED_AFTER_STOP')
    def test_429_stops(self):
        def denied(url):raise urllib.error.HTTPError(url,429,'limit',{},None)
        self.assertEqual(self.execute([review(),review('0000000123-26-000002')],denied)['records'][1]['status'],'NOT_ATTEMPTED_AFTER_STOP')
    def test_existing_directory_not_reused(self):
        self.dest.mkdir()
        with self.assertRaises(FileExistsError):self.execute()
    def test_conflicting_prior_hash_retained_not_overwritten(self):
        r=review();r['source_sha256']='0'*64
        result=self.execute([r]);self.assertFalse(result['records'][0]['prior_hash_matches'])
        self.assertEqual(result['records'][0]['prior_recorded_sha256'],'0'*64)
    def test_duplicate_and_oversized_requests_preflight(self):
        with self.assertRaises(ValueError):self.execute([review(),review()])
        self.assertFalse(self.dest.exists())
        with self.assertRaises(ValueError):self.execute([review()]*11)
    def test_header_must_end_before_document(self):
        malformed=document().replace(b'</SEC-HEADER>',b'<DOCUMENT>')
        self.assertEqual(self.execute(get=lambda _:malformed)['archived_count'],0)
    def test_identity_in_exhibit_not_header_rejected(self):
        raw=b'<SEC-DOCUMENT>x\n<SEC-HEADER>empty</SEC-HEADER><DOCUMENT>'+document()
        self.assertEqual(self.execute(get=lambda _:raw)['archived_count'],0)
    def test_oversize_stops_all_further_requests(self):
        calls=[]
        def too_large(url):calls.append(url);raise ResponseTooLarge()
        r=self.execute([review(),review('0000000123-26-000002')],too_large)
        self.assertEqual(len(calls),1)
        self.assertEqual(r['records'][0]['status'],'RESPONSE_SIZE_LIMIT_STOP')
        self.assertEqual(len((self.dest/'manifest.jsonl').read_text().splitlines()),2)
    def test_redirect_handler_denies(self):
        self.assertIsNone(NoRedirect().redirect_request(None,None,302,'',{},'https://elsewhere.invalid'))

if __name__=='__main__':unittest.main()
