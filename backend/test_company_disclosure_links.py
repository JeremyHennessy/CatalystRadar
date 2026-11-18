import copy,hashlib,json,tempfile,unittest
from pathlib import Path
from company_disclosure_links import build,project,PATHS
ROOT=Path(__file__).resolve().parents[1]
class DisclosureLinksTest(unittest.TestCase):
 def setUp(self):
  self.data={k:json.loads((ROOT/v).read_bytes()) for k,v in PATHS.items()}
 def run_project(self):return project(self.data['financial'],self.data['catalog'],self.data['manifest'])
 def test_actual_full_cohort_and_exact_matches(self):
  r=self.run_project();self.assertEqual(r['counts'],{'financial_issuers':106,'financial_contexts':605,'issuers_with_selected_disclosures':5,'issuers_without_selected_disclosures':101,'selected_filings':5,'selected_disclosure_records':8})
  self.assertEqual(len({c['issuer_cik'] for c in r['companies']}),106)
  for c in r['companies']:
   expected=[x['accession'] for x in self.data['catalog'] if x['issuer_cik']==c['issuer_cik']]
   self.assertEqual(c['disclosure_accessions'],sorted(expected));self.assertIsNone(c['confirmed_deal']);self.assertFalse(c['same_event_verified'])
 def test_reject_catalog_corruption(self):
  original=copy.deepcopy(self.data)
  changes=[('sec_filing_index_url','javascript:alert(1)'),('issuer_cik','0000000000'),('disclosure_records',True),('records_with_dimensions',999),('filing_date','2026-11-01')]
  for key,value in changes:
   self.data=copy.deepcopy(original);self.data['catalog'][0][key]=value
   with self.subTest(key=key),self.assertRaises(ValueError):self.run_project()
 def test_duplicate_and_private_fields(self):
  self.data['catalog'].append(copy.deepcopy(self.data['catalog'][0]))
  with self.assertRaises(ValueError):self.run_project()
  self.data['catalog'].pop();self.data['catalog'][0]['raw_narrative']='private'
  with self.assertRaises(ValueError):self.run_project()
 def test_manifest_count_and_qualification(self):
  self.data['manifest']['filings']+=1
  with self.assertRaises(ValueError):self.run_project()
  self.data['manifest']['filings']-=1;self.data['manifest']['training_ready']=True
  with self.assertRaises(ValueError):self.run_project()
 def test_pinned_build_and_manifest_binding(self):
  pins={k:hashlib.sha256((ROOT/v).read_bytes()).hexdigest() for k,v in PATHS.items()}
  result=build(ROOT,pins);self.assertEqual(result['counts']['selected_filings'],5)
  pins['catalog']='0'*64
  with self.assertRaises(ValueError):build(ROOT,pins)
 def test_manifest_private_selection_and_date_corruption(self):
  original=copy.deepcopy(self.data)
  for key,value in [('selection',{'private':'extra'}),('source_url','https://example.invalid'),('filing_date_min','2020-01-01'),('filings',True)]:
   self.data=copy.deepcopy(original);self.data['manifest'][key]=value
   with self.subTest(key=key),self.assertRaises(ValueError):self.run_project()
 def test_name_is_not_join_key(self):
  for r in self.data['catalog']:r['issuer_name_as_filed']='identical arbitrary as-filed name'
  self.assertEqual(self.run_project()['counts']['selected_filings'],5)
if __name__=='__main__':unittest.main()
