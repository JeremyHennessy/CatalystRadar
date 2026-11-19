"""Static saved-case control, not a verification of unretained original pages."""
import datetime as dt
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
RECEIPT='data/sec-observations/20261118T192626511660Z.json'
PIN='6ebebfb3fafa156857d5c2685352c3fb15332e564ce45f5f65bc7213df3a29d5'
CIK='0000108516'; ACC='0001193125-26-464853'
ORIGINAL='https://www.sec.gov/Archives/edgar/data/108516/000119312526464853/wor-20261112.htm'
CALENDAR='https://ir.worthingtonenterprises.com/news/news-details/2026/Worthington-Enterprises-Participating-in-Baird-Global-Industrial-Conference-Following-Investor-and-Analyst-Day/default.aspx'

class Detail(HTMLParser):
    def __init__(self):
        super().__init__();self.depth=0;self.fields={};self.text=[];self.links=[];self.tags=[]
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=='details' and a.get('id')=='worthington-saved-chronology':self.depth=1
        elif self.depth and tag=='details':self.depth+=1
        if self.depth:
            self.tags.append(tag)
            for k,v in attrs:
                if k.startswith('data-wor-'):self.fields.setdefault(k,[]).append(v)
                if k.startswith('on'):raise AssertionError('Static detail cannot execute an action')
            if tag=='a':self.links.append(a['href'])
    def handle_endtag(self,tag):
        if self.depth and tag=='details':self.depth-=1
    def handle_data(self,s):
        if self.depth:self.text.append(s)

class WorthingtonSavedChronologyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw=(ROOT/RECEIPT).read_bytes();cls.receipt=json.loads(cls.raw)
        cls.html=(ROOT/'web/collectors.html').read_text();cls.p=Detail();cls.p.feed(cls.html)
        cls.text=' '.join(cls.p.text)
        cls.doc=(ROOT/'docs/research/worthington-saved-observation-chronology.md').read_text()

    def test_exact_receipt_and_metadata_membership(self):
        self.assertEqual(len(self.raw),6637);self.assertEqual(hashlib.sha256(self.raw).hexdigest(),PIN)
        self.assertEqual(len(self.receipt['events']),1);e=self.receipt['events'][0]
        self.assertEqual((e['issuer_cik'],e['accession'],e['form']),(CIK,ACC,'8-K'))
        source=[s for s in self.receipt['sources'] if s['sha256']==e['source_metadata_sha256']]
        self.assertEqual(len(source),1);source=source[0];raw=(ROOT/source['archive_path']).read_bytes()
        self.assertEqual(len(raw),source['byte_count']);self.assertEqual(hashlib.sha256(raw).hexdigest(),source['sha256'])
        d=json.loads(raw);self.assertEqual(str(d['cik']).zfill(10),CIK)
        r=d['filings']['recent'];self.assertEqual(r['accessionNumber'].count(ACC),1);i=r['accessionNumber'].index(ACC)
        self.assertEqual(r['acceptanceDateTime'][i],e['sec_accepted_utc'])
        self.assertEqual(r['primaryDocument'][i],'wor-20261112.htm');self.assertEqual(r['reportDate'][i],'2026-11-12')
        self.assertEqual(source['retrieved_utc'],e['observed_utc'])
        self.assertFalse(e['eligible']);self.assertIsNone(e['first_public_utc'])
        self.assertEqual(e['status'],'METADATA_DISCOVERY_NOT_ELIGIBLE')
        self.assertEqual((self.receipt['eligible_count'],self.receipt['orders_created']),(0,0))

    def test_clocks_are_separate_not_substituted(self):
        e=self.receipt['events'][0]
        expected={'cik':CIK,'accession':ACC,'occurrence':'2026-11-12','schedule':'2026-11-12 1:35 ET','accepted':e['sec_accepted_utc'],'observed':e['observed_utc']}
        self.assertEqual(self.p.fields,{'data-wor-'+k:[v] for k,v in expected.items()})
        occurrence=dt.date.fromisoformat(expected['occurrence'])
        accepted=dt.datetime.fromisoformat(e['sec_accepted_utc'].replace('Z','+00:00'))
        observed=dt.datetime.fromisoformat(e['observed_utc'])
        self.assertLess(occurrence,accepted.date());self.assertLess(accepted,observed)
        # No conversion of the schedule to an actual event instant or first-public clock.
        for s in ['as scheduled','No UTC conversion','November 10 Investor Day is a distinct event','actual start instant is not established','Neither SEC acceptance nor collector discovery should be substituted']:
            self.assertIn(s,self.text)

    def test_objects_and_unverified_source_provenance(self):
        for s in ['deck had already been posted before the conference','transcript is separately furnished as Exhibit 99.2','does not establish when the transcript first became public','that every fact was already public','Precise first-public time and information-level novelty remain unknown','not a live status check','or a claim that this receipt remains latest','no additional retrieval','Original-page bytes, HTTP status and page hashes are not certified','receipt hash binds metadata only','opening this static detail does not fetch the originals']:
            self.assertIn(s,self.text)
        for s in [ORIGINAL,CALENDAR,'../'+RECEIPT,'../docs/research/worthington-saved-observation-chronology.md']:
            self.assertIn(s,self.p.links)
        for s in [PIN,ORIGINAL,CALENDAR,'not an independent refetch','No original-page HTTP bytes','not a general novelty verdict']:
            self.assertIn(s,self.doc)
        self.assertIn(PIN,self.text)

    def test_additive_static_hook_preserves_existing_controls(self):
        self.assertEqual(self.html.count('id="worthington-saved-chronology"'),1)
        for tag in ['script','button','form','input','iframe']:self.assertNotIn(tag,self.p.tags)
        for id_ in ['collector-published-sec','run-audit-refresh','collector-refresh','collector-list']:
            self.assertEqual(self.html.count('id="'+id_+'"'),1)
        for phrase in ['No price join, outcome, collector action, provider request or paper decision','First-public time remains null','saved event remains not eligible']:
            self.assertIn(phrase,self.text)

if __name__=='__main__':unittest.main()
