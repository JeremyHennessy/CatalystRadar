import copy
import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
import company_evidence_retrieval as m

ROOT=Path(__file__).resolve().parents[1]
class Retrieval(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.index=m.load(ROOT)
 def test_complete_directory(self):
  rows=[]
  for offset in range(0,8035,20):rows.extend(x['company'] for x in m.search(self.index,offset=offset)['records'])
  self.assertEqual(rows,self.index['directory'])
  for section,key in [('prepared','prepared_batches'),('insider','insider_filings'),('disclosure','disclosure_filings'),('scanner','scanner_records')]:
   self.assertEqual(m.search(self.index,section=section)['total_records'],sum(r['source_counts'][key]>0 for r in rows))
 def test_all_evidence_membership(self):
  cache={}
  original=m.pinned
  def cached(root,pin):
   key=(pin['path'],pin['sha256'])
   if key not in cache:cache[key]=original(root,pin)
   return cache[key]
  counts={s:0 for s in m.SECTIONS}
  with patch.object(m,'pinned',side_effect=cached):
   for entry in self.index['directory']:
    ci=entry['issuer_cik'];pin=next(p for p in self.index['detail_shards'] if p['bucket']==entry['detail_bucket'])
    company=next(r for r in cached(ROOT,pin)['companies'] if r['issuer_cik']==ci)
    for section in m.SECTIONS:
     if section=='insider':
      ref=company[section]['record'];expected=[]
      if ref:
       p=ref['filing_detail_shard'];obj=cached(ROOT,{'path':p['path'],'bytes':p['byte_count'],'sha256':p['sha256']})
       expected=next(r['filings'] for r in obj['issuers'] if r['issuer_cik']==ci)
     else:expected=[r['source_record'] for r in company[section]['records']]
     actual=[]
     for offset in range(0,max(1,len(expected)),5):
      page=m.evidence(ROOT,self.index,ci,section,offset=offset)
      self.assertEqual(page['total_records'],len(expected));m.output_bytes(page)
      actual.extend(r['source_record'] for r in page['records'])
     self.assertEqual(actual,expected);counts[section]+=len(actual)
  self.assertEqual(counts,{'prepared':12977,'insider':26827,'disclosure':466,'scanner':907})
 def test_name_literal_and_ambiguity(self):
  x=m.search(self.index,name=' corp ');self.assertTrue(x['name_ambiguous'])
  ci=x['records'][0]['company']['issuer_cik']
  self.assertEqual(m.search(self.index,name='CORP',cik=ci)['global_name_matching_ciks'],x['global_name_matching_ciks'])
  self.assertEqual(m.search(self.index,name='.*')['total_records'],0)
  self.assertEqual(m.normalize_name('E\u0301  A'),m.normalize_name('É A'))
  self.assertNotEqual(m.normalize_name('АMD'),m.normalize_name('AMD')) # Cyrillic A is not Latin.
 def test_invalid_queries(self):
  for s in ['', 'x'*121,'a\x00b','a\u200bb']:
   with self.assertRaises(ValueError):m.normalize_name(s)
  for s in ['０１２','0','1.0','+1','1 '*3]:
   with self.assertRaises(ValueError):m.exact_cik(s)
  for n,o in [(21,0),(True,0),(1,-1),(1,100001)]:
   with self.assertRaises(ValueError):m.search(self.index,limit=n,offset=o)
 def test_records_all_sections(self):
  for section in m.SECTIONS:
   key={'prepared':'prepared_batches','insider':'insider_filings','disclosure':'disclosure_filings','scanner':'scanner_records'}[section]
   ci=next(r['issuer_cik'] for r in self.index['directory'] if r['source_counts'][key])
   a=m.evidence(ROOT,self.index,ci,section)
   self.assertGreater(a['total_records'],0);self.assertLessEqual(a['returned_records'],5)
   self.assertLessEqual(len(m.output_bytes(a)),m.MAX_OUTPUT)
   self.assertEqual(m.evidence(ROOT,self.index,ci,section,offset=100000)['records'],[])
 def test_absence_and_outside(self):
  a=m.evidence(ROOT,self.index,'9999999999','insider');self.assertIsNone(a['total_records'])
  a=m.evidence(ROOT,self.index,'108772','prepared');self.assertEqual(a['total_records'],0)
  self.assertEqual(a['coverage'],'NO_ENTRY_IN_FIXED_PREPARED_INDEX')
 def test_pin_failure_and_output_cap(self):
  with patch.object(m,'INDEX',dict(m.INDEX,sha256='0'*64)):
   with self.assertRaises(ValueError):m.load(ROOT)
  with self.assertRaises(ValueError):m.output_bytes({'x':'a'*m.MAX_OUTPUT})
 def test_wrong_shard_and_duplicate_identity(self):
  ci='0000108772';entry=next(r for r in self.index['directory'] if r['issuer_cik']==ci)
  p=next(p for p in self.index['detail_shards'] if p['bucket']==entry['detail_bucket'])
  obj=m.pinned(ROOT,p)
  bad=copy.deepcopy(obj);bad['companies'].append(bad['companies'][0])
  with patch.object(m,'pinned',return_value=bad):
   with self.assertRaises(ValueError):m.evidence(ROOT,self.index,ci,'scanner')
  bad=copy.deepcopy(obj);r=next(x for x in bad['companies'] if x['issuer_cik']==ci)['scanner']['records'][0]
  r['source_record']['issuer_associations']=[]
  with patch.object(m,'pinned',return_value=bad):
   with self.assertRaises(ValueError):m.evidence(ROOT,self.index,ci,'scanner')
 def test_insider_duplicate_and_cross_cik(self):
  ci='0000032604'
  entry=next(r for r in self.index['directory'] if r['issuer_cik']==ci)
  pin=next(p for p in self.index['detail_shards'] if p['bucket']==entry['detail_bucket'])
  company=m.pinned(ROOT,pin)
  ref=next(r for r in company['companies'] if r['issuer_cik']==ci)['insider']['record']['filing_detail_shard']
  insider=m.pinned(ROOT,{'path':ref['path'],'bytes':ref['byte_count'],'sha256':ref['sha256']})
  for duplicate in (True,False):
   bad=copy.deepcopy(insider);filings=next(r['filings'] for r in bad['issuers'] if r['issuer_cik']==ci)
   if duplicate:filings.append(filings[0])
   else:filings[0]['issuer_cik']='0000000001'
   with patch.object(m,'pinned',side_effect=[company,bad]):
    with self.assertRaises(ValueError):m.evidence(ROOT,self.index,ci,'insider')
 def test_cli_no_partial_output(self):
  p=subprocess.run([sys.executable,str(ROOT/'backend/company_evidence_retrieval.py'),'evidence','--cik','0','--section','scanner'],capture_output=True)
  self.assertEqual(p.returncode,2);self.assertEqual(p.stdout,b'');self.assertIn(b'failed validation',p.stderr)
if __name__=='__main__':unittest.main()
