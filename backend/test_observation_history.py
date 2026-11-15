"""Public metadata receipt regression tests; no network calls."""
import copy
import json
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch
import hashlib
import scan_watchlist as scanner

RUN='20261116T120000000000Z'

def report(run=RUN):
    return {'run_id':run,'started_at':'2026-11-16T12:00:00+00:00',
            'events':[{'accession':'0000000001-26-000001','first_public_utc':None,
                       'observed_utc':'2026-11-16T12:00:02Z','eligible':False}],
            'errors':[],'orders_created':0}

class HistoryTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
    def tearDown(self):self.tmp.cleanup()
    def test_idempotent_exact_report(self):
        first=scanner.persist_observation(report(),self.root)
        old=first.read_bytes()
        self.assertEqual(scanner.persist_observation(report(),self.root),first)
        self.assertEqual(first.read_bytes(),old)
        self.assertEqual(list(first.parent.iterdir()),[first])
    def test_conflict_preserves_original(self):
        first=scanner.persist_observation(report(),self.root);old=first.read_bytes()
        changed=report();changed['events']=[]
        with self.assertRaisesRegex(ValueError,'conflicting'):
            scanner.persist_observation(changed,self.root)
        self.assertEqual(first.read_bytes(),old)
    def test_concurrent_identical_and_conflicting_runs(self):
        with ThreadPoolExecutor(4) as pool:
            results=list(pool.map(lambda _:scanner.persist_observation(report(),self.root),range(8)))
        self.assertEqual(len(set(results)),1)
        self.assertEqual(json.loads(results[0].read_text()),report())
        other=report();other['errors']=['source unavailable']
        with self.assertRaises(ValueError):scanner.persist_observation(other,self.root)
    def test_revisions_and_absence_do_not_replace_previous_observations(self):
        first=scanner.persist_observation(report(),self.root)
        second=report('20261116T123000000000Z');second['events']=[]
        second['errors']=['HTTP 429 from public source']
        scanner.persist_observation(second,self.root)
        self.assertEqual(json.loads(first.read_text()),report())
        self.assertEqual(len(list(first.parent.glob('*.json'))),2)
    def test_bad_ids_nonfinite_and_size_rejected(self):
        for bad in ('../bad','20261116','20261116T120000000000Z/evil'):
            with self.assertRaises(ValueError):scanner.persist_observation(report(bad),self.root)
        row=report();row['value']=float('nan')
        with self.assertRaises(ValueError):scanner.persist_observation(row,self.root)
        row=report();row['large']='x'*(4*1024*1024)
        with self.assertRaisesRegex(ValueError,'4 MiB'):scanner.persist_observation(row,self.root)
    def test_failed_atomic_publication_keeps_no_final_file(self):
        with patch.object(scanner.os,'link',side_effect=OSError('disk error')):
            with self.assertRaises(OSError):scanner.persist_observation(report(),self.root)
        self.assertEqual(list((self.root/'data/sec-observations').iterdir()),[])
    def test_scan_retains_partial_success_and_sanitized_denial(self):
        (self.root/'data').mkdir()
        (self.root/'data/watchlist.json').write_text(json.dumps([
            {'ticker':'ONE','cik':'1'},{'ticker':'TWO','cik':'2'},{'ticker':'THREE','cik':'3'}]))
        class Clock(datetime):
            @classmethod
            def now(cls,tz=None):return cls(2026,11,16,12,0,tzinfo=timezone.utc)
        recent={'accessionNumber':['0000000001-26-000001','0000000001-26-000000'],
                'acceptanceDateTime':['2026-11-16T10:00:00Z','2026-11-01T10:00:00Z'],
                'filingDate':['2026-11-16','2026-11-01'],'primaryDocument':['one.htm','old.htm'],
                'form':['8-K','10-Q'],'items':['2.02','']}
        raw=json.dumps({'name':'One','tickers':['ONE'],'filings':{'recent':recent}}).encode()
        def get(arc,url,label):
            if '0000000001' in url:
                return raw,{'url':url,'retrieved_utc':'2026-11-16T12:00:02Z',
                            'sha256':hashlib.sha256(raw).hexdigest(),'status':200}
            return None,{'url':url,'error':'HTTP Error 429 private diagnostic path','status':429}
        with patch.object(scanner,'datetime',Clock),patch.object(scanner.Archive,'get',get),patch.object(scanner,'stamp',return_value='2026-11-16T12:00:05Z'):
            result=scanner.scan(self.root)
        saved=json.loads(next((self.root/'data/sec-observations').glob('*.json')).read_text())
        self.assertEqual(saved,result)
        self.assertEqual(len(saved['events']),1)
        self.assertEqual(len(saved['errors']),2)
        self.assertNotIn('private diagnostic',json.dumps(saved))
        self.assertIsNone(saved['events'][0]['first_public_utc'])
        self.assertFalse(saved['metadata_window_complete'])
        self.assertEqual(saved['orders_created'],0)
        self.assertEqual(json.loads((self.root/'data/latest_scan.json').read_text()),saved)
    def test_workflow_stages_only_complete_receipts(self):
        workflow=(Path(__file__).resolve().parents[1]/'.github/workflows/sec-observations.yml').read_text()
        self.assertIn('git add -- data/sec-observations/*.json',workflow)
        self.assertNotIn('git add -- .data',workflow)

if __name__=='__main__':unittest.main()
