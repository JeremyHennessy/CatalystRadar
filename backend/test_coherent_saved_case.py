"""Static source-reviewed interpretation, not historical availability evidence."""
import datetime as dt
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
RECEIPT='data/sec-observations/20261119T114159492631Z.json'
PIN='10b3c74b4949b1d23d850a9c822f052343dac979fa1112f3723c37fda81100bc'
CIK='0000820318';ACC='0001193125-26-467737'
class Detail(HTMLParser):
 def __init__(self):super().__init__();self.active=False;self.fields={};self.text=[];self.links=[];self.tags=[]
 def handle_starttag(self,t,attrs):
  a=dict(attrs)
  if a.get('id')=='coherent-saved-case':self.active=True
  if not self.active:return
  self.tags.append(t)
  for k,v in attrs:
   if k.startswith('data-cohr-'):self.fields[k]=v
   if k.startswith('on'):raise AssertionError('No actions permitted')
  if t=='a':self.links.append(a['href'])
 def handle_endtag(self,t):
  if t=='details':self.active=False
 def handle_data(self,s):
  if self.active:self.text.append(s)
class CoherentSavedCaseTests(unittest.TestCase):
 @classmethod
 def setUpClass(c):
  c.raw=(ROOT/RECEIPT).read_bytes();c.r=json.loads(c.raw);c.html=(ROOT/'web/collectors.html').read_text();c.p=Detail();c.p.feed(c.html);c.text=' '.join(c.p.text);c.doc=(ROOT/'docs/research/coherent-saved-repurchase-authorization.md').read_text()
 def test_exact_receipt_and_source_identity(self):
  self.assertEqual(len(self.raw),7373);self.assertEqual(hashlib.sha256(self.raw).hexdigest(),PIN);self.assertEqual(len(self.r['events']),2)
  matches=[e for e in self.r['events'] if e['issuer_cik']==CIK and e['accession']==ACC];self.assertEqual(len(matches),1);e=matches[0]
  self.assertFalse(e['eligible']);self.assertIsNone(e['first_public_utc']);self.assertEqual(e['status'],'METADATA_DISCOVERY_NOT_ELIGIBLE');self.assertEqual(self.r['github_event_name'],'push');self.assertEqual((self.r['orders_created'],self.r['eligible_count']),(0,0))
  sources=[s for s in self.r['sources'] if s['sha256']==e['source_metadata_sha256']];self.assertEqual(len(sources),1);source=sources[0];self.assertEqual(source['sha256'],'c0f3a419d2d23b0966097f86fc70ae90bdceeb911620a4674c07e60937591d52');b=(ROOT/source['archive_path']).read_bytes();self.assertEqual(len(b),159944);self.assertEqual(hashlib.sha256(b).hexdigest(),source['sha256']);d=json.loads(b);self.assertEqual(str(d['cik']).zfill(10),CIK)
  f=d['filings']['recent'];self.assertEqual(f['accessionNumber'].count(ACC),1);i=f['accessionNumber'].index(ACC);self.assertEqual(f['acceptanceDateTime'][i],e['sec_accepted_utc']);self.assertEqual(f['items'][i],'7.01');self.assertEqual(f['primaryDocument'][i],'d867801d8k.htm');self.assertEqual(f['reportDate'][i],'2026-11-18');self.assertEqual(f['form'][i],'8-K');self.assertEqual(source['retrieved_utc'],e['observed_utc'])
 def test_clocks_and_authorization_not_execution(self):
  e=next(e for e in self.r['events'] if e['issuer_cik']==CIK)
  self.assertEqual(self.p.fields,{'data-cohr-cik':CIK,'data-cohr-accession':ACC,'data-cohr-board-date':'2026-11-18','data-cohr-cap':'2000000000','data-cohr-accepted':e['sec_accepted_utc'],'data-cohr-observed':e['observed_utc']})
  gap=dt.datetime.fromisoformat(e['observed_utc'])-dt.datetime.fromisoformat(e['sec_accepted_utc'].replace('Z','+00:00'));self.assertEqual(gap,dt.timedelta(seconds=713,microseconds=642713))
  for s in ['request-triggered fallback','GitHub trigger: push','not evidence of a scheduled collection success','excluding fees, commissions','authorization cap','not an expenditure','no expiration date','no specific number of shares','suspended or discontinued','does not disclose completed purchases','not proof that no purchases occurred','not executive transactions or a strategic investment','not an availability lag','First-public remains null','not eligible']:
   self.assertIn(s,self.text)
 def test_static_provenance_and_old_controls(self):
  for u in ['https://ir.coherent.com/node/18481/html','../'+RECEIPT,'../docs/research/coherent-saved-repurchase-authorization.md']:self.assertIn(u,self.p.links)
  for s in [PIN,'aef701901dc28af1cdd0b0b543e01a74fccd77fa45fa274be81090383798d983','29,296','not EDGAR bytes','raw issuer page is not added','713.642713','two-event membership']:self.assertIn(s,self.doc)
  for s in ['not EDGAR response bytes','historical dissemination clock','No price, return, order or paper decision','Expanding this static detail does not fetch it']:self.assertIn(s,self.text)
  for tag in ['script','button','form','iframe','input']:self.assertNotIn(tag,self.p.tags)
  for id_ in ['coherent-saved-case','worthington-saved-chronology','worthington-earlier-claims','collector-published-sec','collector-refresh','run-audit-refresh','collector-list']:self.assertEqual(self.html.count('id="'+id_+'"'),1)
if __name__=='__main__':unittest.main()
