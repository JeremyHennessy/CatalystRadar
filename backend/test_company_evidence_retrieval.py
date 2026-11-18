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

class ReviewedLayers(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.index=m.load(ROOT)
  cls.layers={s:m.load_layer(ROOT,cls.index,s) for s in m.LAYER_SECTIONS}
 def test_all_company_memberships_and_original_objects(self):
  expected_counts={'redemption_calls':(1,1),'offerings':(187,223),'going_concern':(97,123),'assertions':(12,12)}
  for section,(obj,groups) in self.layers.items():
   count=0;selected=0
   with patch.object(m,'load_layer',return_value=(obj,groups)):
    for company in self.index['directory']:
     ci=company['issuer_cik'];expected=groups.get(ci,[]);actual=[]
     for offset in range(0,max(1,len(expected)),5):
      page=m.layer_evidence(ROOT,self.index,ci,section,offset=offset)
      self.assertEqual(page['total_records'],len(expected) if section not in ('assertions','redemption_calls') or ci in groups else None)
      actual+=page['records']
      if expected:m.output_bytes(page)
     self.assertEqual(actual,expected);selected+=bool(expected);count+=len(actual)
    self.assertEqual(m.layer_search(ROOT,self.index,section=section)['total_records'],len(groups))
   self.assertEqual((selected,count),expected_counts[section])
   originals=[]
   if section=='redemption_calls':originals=[(obj['issuer_cik'],'',obj)]
   elif section=='assertions':
    originals=[(f['cik'],f'/packages/{i}',r) for i,r in enumerate(obj['packages']) for f in r['filers_as_reported']]
   else:originals=[(c['issuer_cik'],f'/companies/{i}/records/{j}',r) for i,c in enumerate(obj['companies']) for j,r in enumerate(c['records'])]
   for ci,pointer,record in originals:
    found=[r for r in groups[ci] if r['source_ref']['json_pointer']==pointer]
    self.assertEqual(len(found),1);self.assertEqual(found[0]['source_record'],record)
 def test_old_outputs_byte_identical(self):
  hashes={'prepared':'04a56a273da4b93e997e1252fceb53d45893ff04f083d42a47f93418673313ee','insider':'0756dec534f5d24072ec917b1e797dc6c220de56a7418be0532cbfe9a786c46b','disclosure':'437eb81c222ca018398ebd0a797f9e21d95bf60f6bac155b4a6491e085b2d54a','scanner':'0c720ad9cb100b25eb887fcec2cb9ec5d1eaf17e8a8b5d9288602cb2c6f3155d'}
  import hashlib
  for s,h in hashes.items():self.assertEqual(hashlib.sha256(m.output_bytes(m.evidence(ROOT,self.index,'32604',s))).hexdigest(),h)
  self.assertEqual(hashlib.sha256(m.output_bytes(m.search(self.index,name='Emerson'))).hexdigest(),'6a3aee13b9a91db29c2e2f2826607ec9fd5ca4196ab66bb50778fa2420a8bb21')
 def test_layer_bad_identity_duplicates_status_counts(self):
  for section,(obj,_) in self.layers.items():
   if section=='redemption_calls':
    for key,value in [('issuer_cik','9999999999'),('status','COMPLETED'),('currency_iso','USD'),('redemption_completion_verified',True),('first_public_utc','2026-11-13')]:
     bad=copy.deepcopy(obj);bad[key]=value
     with self.assertRaises(ValueError):m.validate_layer(self.index,section,bad)
    continue
   for mode in ('identity','duplicate','status','counts'):
    bad=copy.deepcopy(obj)
    if section=='assertions':
     if mode=='identity':bad['packages'][0]['filers_as_reported'][0]['cik']='9999999999'
     if mode=='duplicate':bad['packages'].append(bad['packages'][0])
     if mode=='status':bad['packages'][0]['status']='NO_RISK'
     if mode=='counts':bad['counts']['metric_pairs']=8
    else:
     if mode=='identity':bad['companies'][0]['records'][0]['issuer_cik']='9999999999'
     if mode=='duplicate':bad['companies'].append(bad['companies'][0])
     if mode=='status':bad['companies'][0]['records'][0]['amendment_flag' if section=='offerings' else 'status']='NO_RISK'
     if mode=='counts':bad['counts']['selected_ciks']+=1
    with self.assertRaises(ValueError):m.validate_layer(self.index,section,bad)
 def test_boolean_not_numeric_and_cohort_pin(self):
  obj=copy.deepcopy(self.layers['going_concern'][0])
  r=next(r for c in obj['companies'] for r in c['records'] if r['datatype']=='boolean')
  r['boolean_value_as_reported']=0
  with self.assertRaises(ValueError):m.validate_layer(self.index,'going_concern',obj)
  obj=copy.deepcopy(self.layers['offerings'][0]);obj['sources']['cohort']['sha256']='0'*64
  with self.assertRaises(ValueError):m.validate_layer(self.index,'offerings',obj)
 def test_tampered_pin_and_related_identity(self):
  for section in m.LAYER_SECTIONS:
   with patch.dict(m.LAYER_PINS,{section:dict(m.LAYER_PINS[section],sha256='0'*64)}):
    with self.assertRaises(ValueError):m.load_layer(ROOT,self.index,section)
  original=m.pinned
  def wrong(root,pin):
   value=copy.deepcopy(original(root,pin))
   if pin['path'].endswith('ieh-reported-revenue.json'):value['issuer']['cik']='0000012659'
   return value
  with patch.object(m,'pinned',side_effect=wrong):
   with self.assertRaises(ValueError):m.load_layer(ROOT,self.index,'assertions')
 def test_scopes_precision_and_ambiguity(self):
  for section in m.LAYER_SECTIONS:
   outside=m.layer_evidence(ROOT,self.index,'9999999999',section)
   self.assertIsNone(outside['total_records'])
   with self.assertRaises(ValueError):m.layer_evidence(ROOT,self.index,'32604',section,limit=6)
  self.assertIsNone(m.layer_evidence(ROOT,self.index,'2488','assertions')['total_records'])
  x=m.layer_evidence(ROOT,self.index,'108772','assertions')
  self.assertEqual(x['records'][0]['source_record']['status'],'NOT_SUPPORTED_GRAMMAR')
  self.assertEqual(len(x['records'][0]['source_record']['filers_as_reported']),2)
  obj,groups=self.layers['going_concern']
  false=[r['source_record'] for rows in groups.values() for r in rows if r['source_record']['status']=='FALSE_AS_REPORTED']
  self.assertEqual(len(false),2);self.assertTrue(all(r['risk_conclusion'] is None for r in false))
  x=m.layer_search(ROOT,self.index,name='corp',section='offerings')
  self.assertEqual(x['global_name_matching_ciks'],m.search(self.index,name='corp')['global_name_matching_ciks'])
  self.assertEqual(m.layer_search(ROOT,self.index,name='.*',section='offerings')['total_records'],0)
 def test_cli_new_section(self):
  p=subprocess.run([sys.executable,str(ROOT/'backend/company_evidence_retrieval.py'),'evidence','--cik','25743','--section','assertions'],capture_output=True)
  self.assertEqual(p.returncode,0,p.stderr)
  import json
  x=json.loads(p.stdout);self.assertEqual(x['total_records'],1)
  self.assertEqual(x['records'][0]['source_record'],self.layers['assertions'][1]['0000025743'][0]['source_record'])

if __name__=='__main__':unittest.main()
