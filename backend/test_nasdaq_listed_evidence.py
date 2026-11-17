"""Synthetic directory fixtures; not real market evidence."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from nasdaq_listed_evidence import parse,audit,URL,HEADER,LIMIT

def data(rows=None,footer='File Creation Time: 1116202618:01|||||||'):
    return ('|'.join(HEADER)+'\n'+'\n'.join(rows or ['ABC|Example Common Stock|Q|N|N|100|N|N'])+'\n'+footer+'\n').encode()
def sha(b): return hashlib.sha256(b).hexdigest()
class Tests(unittest.TestCase):
    def test_retains_test_and_flags(self):
        rows,clock,_=parse(data(['ZXYZ.A|Test|Q|Y|N|100|N|N','ABC|ETF |G|N|H|40|Y|N']))
        self.assertEqual(rows[0]['source_line_number'],2);self.assertEqual(rows[1]['fields']['ETF'],'Y');self.assertEqual(clock,'1116202618:01');self.assertEqual(rows[1]['fields']['Security Name'],'ETF ')
    def test_duplicate_symbol_rejected(self):
        with self.assertRaises(ValueError):parse(data(['ABC|One|Q|N|N|100|N|N','ABC|Two|Q|N|N|100|N|N']))
    def test_schema_footer_and_bounds(self):
        for raw in [data().replace(b'Security Name',b'Name'),data()+b'\n',data(footer='File Creation Time: 1132202618:01|||||||'),data(footer='File Creation Time: 1116202618:01|extra||||||'),b'x'*(LIMIT+1),data().replace(b'Example',b'Ex\x00ample')]:
            with self.subTest(raw=raw[:30]),self.assertRaises(ValueError):parse(raw)
    def test_unknown_flags_and_invalid_lots(self):
        for row in ['ABC|X|Z|N|N|100|N|N','ABC|X|Q|N|X|100|N|N','ABC|X|Q|N|N|0|N|N','ABC|X|Q|N|N|100|?|N','ABC.A|X|Q|N|N|100|N|N','ABC||Q|N|N|100|N|N','ABC|X|Q|N|N|100|N|N|extra']:
            with self.subTest(row=row),self.assertRaises(ValueError):parse(data([row]))
    def fixture(self,p):
        raw=data();receipt={'url':URL,'requested_at':'2026-11-16T23:00:00+00:00','finished_at':'2026-11-16T23:00:01+00:00','status':200,'bytes':len(raw),'sha256':sha(raw),'maximum_bytes':LIMIT,'maximum_attempts':1}
        (p/'source').write_bytes(raw);(p/'receipt').write_text(json.dumps(receipt));(p/'watchlist').write_text(json.dumps([{'ticker':'ABC','cik':'1'},{'ticker':'OTHER','cik':'2'}]))
        return receipt
    def run_audit(self,p):
        return audit(p/'source',sha((p/'source').read_bytes()),p/'receipt',sha((p/'receipt').read_bytes()),p/'watchlist',sha((p/'watchlist').read_bytes()))
    def test_end_to_end_source_pinned_no_identity_inference(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);self.fixture(p);summary,evidence=self.run_audit(p)
            self.assertEqual(summary['record_count'],1);self.assertEqual(summary['watchlist_symbol_matches'],1)
            self.assertIsNone(summary['source_creation_utc']);self.assertFalse(summary['training_ready'])
            self.assertFalse(summary['watchlist_comparison'][0]['issuer_cik_link_verified'])
            self.assertEqual(summary['watchlist_comparison'][1]['disposition'],'NOT_IN_THIS_NASDAQ_FILE')
            self.assertEqual(evidence['rows'][0]['fields']['Security Name'],'Example Common Stock')
    def test_receipt_hash_and_identity_failures(self):
        for key,value in [('url',URL+'?other'),('status',403),('bytes',0),('sha256','0'*64),('maximum_attempts',2),('finished_at','2026-11-15T23:00:00+00:00')]:
            with self.subTest(key=key),tempfile.TemporaryDirectory() as d:
                p=Path(d);r=self.fixture(p);r[key]=value;(p/'receipt').write_text(json.dumps(r))
                with self.assertRaises(ValueError):self.run_audit(p)
    def test_duplicate_json_and_nonfinite(self):
        for tail in [',"status":200',',"extra":NaN']:
            with tempfile.TemporaryDirectory() as d:
                p=Path(d);self.fixture(p);f=p/'receipt';f.write_text(f.read_text()[:-1]+tail+'}')
                with self.assertRaises(ValueError):self.run_audit(p)
    def test_future_footer_date_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);r=self.fixture(p);raw=data(footer='File Creation Time: 1120202618:01|||||||');(p/'source').write_bytes(raw);r['sha256']=sha(raw);r['bytes']=len(raw);(p/'receipt').write_text(json.dumps(r))
            with self.assertRaises(ValueError):self.run_audit(p)
    def test_pinned_source_mismatch(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);self.fixture(p)
            with self.assertRaises(ValueError):audit(p/'source','0'*64,p/'receipt',sha((p/'receipt').read_bytes()),p/'watchlist',sha((p/'watchlist').read_bytes()))
if __name__=='__main__':unittest.main()
