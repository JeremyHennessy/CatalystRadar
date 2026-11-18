import copy,json,subprocess,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import research_dossier as m
ROOT=Path(__file__).resolve().parents[1]
class DossierTests(unittest.TestCase):
 def test_cross_source_company_and_exact_public_object(self):
  r=m.dossier(ROOT,'1130310','disclosure');self.assertEqual({k:v['total_source_records'] for k,v in r['section_overview'].items()},{'financial':6,'insider':1,'disclosure':1,'reported':None})
  original=json.loads((ROOT/'web/disclosure-catalog/filings.json').read_text());expected=next(x for x in original if x['accession']=='0001130310-26-000048');self.assertEqual(r['selected_section']['records'],[expected]);self.assertFalse(r['execution_ready'])
 def test_standalone_findings_not_financial_cohort(self):
  for ci,key in [('50292','ieh'),('32604','emerson')]:
   r=m.dossier(ROOT,ci,'reported');self.assertIsNone(r['section_overview']['financial']['total_source_records']);self.assertIsNone(r['section_overview']['disclosure']['total_source_records']);self.assertEqual(r['selected_section']['source_key'],key);self.assertEqual(r['selected_section']['total_source_records'],1)
  r=m.dossier(ROOT,'32604','insider');self.assertEqual(r['selected_section']['total_source_records'],3);self.assertEqual(r['selected_section']['source_key'],'watchlist_insider')
 def test_scoped_absence_outside_and_empty_page(self):
  r=m.dossier(ROOT,'1001907','disclosure');self.assertEqual(r['selected_section']['total_source_records'],0)
  r=m.dossier(ROOT,'12659');self.assertEqual(r['status'],'CIK_OUTSIDE_REVIEWED_SNAPSHOT');self.assertIsNone(r['selected_section']['total_source_records'])
  r=m.dossier(ROOT,'1130310','financial',limit=2,offset=999);self.assertEqual(r['selected_section']['total_source_records'],6);self.assertEqual(r['selected_section']['records'],[]);self.assertIsNone(r['selected_section']['next_offset'])
 def test_pagination_is_exact_partition(self):
  a=m.dossier(ROOT,'1130310','financial',limit=25)['selected_section']['records'];b=[]
  for offset in (0,2,4):b+=m.dossier(ROOT,'1130310','financial',limit=2,offset=offset)['selected_section']['records']
  self.assertEqual(a,b)
 def test_reference_identity_rejection(self):
  rows=[{'id':'a','issuer_cik':'0000000001'}]
  for records,refs,ci in [(rows+rows,['a'],'0000000001'),(rows,['a','a'],'0000000001'),(rows,['b'],'0000000001'),(rows,['a'],'0000000002')]:
   with self.assertRaises(ValueError):m.resolve(records,refs,ci,lambda r:r['id'])
 def test_changed_snapshot_and_query_bounds(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t)/m.SNAPSHOT;p.parent.mkdir(parents=True);p.write_text('{}')
   with self.assertRaises(ValueError):m.dossier(t,'1130310')
  for kwargs in [{'cik':None},{'cik':'EMR'},{'cik':'１２３'},{'cik':'1','section':'prices'},{'cik':'1','limit':True},{'cik':'1','limit':26},{'cik':'1','offset':-1}]:
   with self.assertRaises(ValueError):m.dossier(ROOT,**kwargs)
 def test_output_bound_and_cli(self):
  with patch.object(m,'MAX_OUTPUT',100):
   with self.assertRaises(ValueError):m.dossier(ROOT,'1130310')
  r=subprocess.run([sys.executable,str(ROOT/'backend/research_dossier.py'),'--root',str(ROOT),'--cik','32604','--section','reported'],capture_output=True,text=True,timeout=30);self.assertEqual(r.returncode,0,r.stderr);j=json.loads(r.stdout);self.assertEqual(j['selected_section']['records'][0]['id'],'emerson-reported-note-completion');self.assertFalse(j['provider_requests_made'])
if __name__=='__main__':unittest.main()
