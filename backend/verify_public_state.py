"""Release tripwires: public prototype must not pretend to trade or have prices."""
from pathlib import Path
import json,hashlib
from paper import APPROVED_PROVIDERS
ROOT=Path(__file__).resolve().parent.parent

def verify(root=ROOT):
 book=json.loads((root/'data/paper_ledger.json').read_text());app=json.loads((root/'web/app-data.json').read_text())
 assert book['initial_cash']==500 and book['cash']==500 and app['portfolio']['initial_cash']==500 and app['portfolio']['cash']==500,'paper starting cash mismatch'
 assert book['benchmark']['initial_cash']==500 and book['benchmark']['type']=='ZERO_INTEREST_CASH_COMPARATOR'
 assert book['simulation_enabled'] is False and APPROVED_PROVIDERS=={},'production simulation must remain disabled'
 assert book['positions']==[] and book['orders']==[] and book['fills']==[],'unexpected paper transactions'
 assert app['portfolio']['trades']==[] and app['discovery']['eligible_signals']==0,'dashboard contradicts blocked state'
 for row in app['signals']:
  assert row['eligible'] is False
  assert row['source_url'].startswith('https://www.sec.gov/Archives/')
 for source in json.loads((root/'data/provenance.json').read_text())['sources']:
  assert source['url'].startswith(('https://www.sec.gov/','https://data.sec.gov/','https://ir.therapeuticsmd.com/'))
 scanpath=root/'data/latest_scan.json'
 if scanpath.exists():
  for src in json.loads(scanpath.read_text())['sources']:
   if src.get('archive_path'):
    p=(root/src['archive_path']).resolve();assert (root/'data/sec-snapshots').resolve() in p.parents
    assert hashlib.sha256(p.read_bytes()).hexdigest()==src['sha256']
 return True
if __name__=='__main__':verify();print('Public state verified: no prices/trades/eligible claims; available snapshot hashes match.')
