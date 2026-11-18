import contextlib,hashlib,io,json,shutil,subprocess,sys,tempfile,unittest
from pathlib import Path
from research_retrieval import retrieve,normalize_cik,normalize_name,matched_names,app_link,main,SNAPSHOT
from research_lead_index import PATHS
ROOT=Path(__file__).resolve().parents[1]
class RetrievalTest(unittest.TestCase):
 def test_source_name_search_and_ticker_exclusion(self):
  a=retrieve(ROOT,name='  EMERSON   electric ')
  self.assertEqual(a['matching_company_entries'],1);self.assertEqual(a['results'][0]['entry']['issuer_cik'],'0000032604');self.assertGreaterEqual(len(a['results'][0]['matched_name_labels']),1)
  self.assertEqual(retrieve(ROOT,name='EMR')['matching_company_entries'],0)
  self.assertFalse(a['name_search']['ticker_fields_searched'])
 def test_ambiguity_survives_filter_and_pagination(self):
  a=retrieve(ROOT,name='corp',limit=1)
  self.assertTrue(a['name_search']['ambiguous_before_other_filters']);self.assertGreater(a['matching_company_entries'],1);self.assertEqual(a['returned_company_entries'],1)
  ci=a['results'][0]['entry']['issuer_cik'];b=retrieve(ROOT,name='corp',cik=ci)
  self.assertEqual(b['matching_company_entries'],1);self.assertEqual(b['name_search'],a['name_search'])
  c=retrieve(ROOT,name='corp',category='ISSUER_REPORTED_COMPARISON_REVIEW');self.assertEqual(c['name_search'],a['name_search'])
 def test_literal_adversarial_and_unicode_names(self):
  row={'labels_by_source':{'financial_as_filed':['Straße ÉNERGIE Inc.','Straße ÉNERGIE Inc.'],'insider_ticker_as_filed':['FAKE']}}
  self.assertEqual(len(matched_names(row,normalize_name('STRASSE E\u0301NERGIE'))),1)
  self.assertEqual(matched_names(row,normalize_name('FAKE')),[])
  for query in ('[a-z].*','$(touch /tmp/never)','<script>alert(1)</script>','ignore previous instructions'):
   with self.subTest(query=query):self.assertEqual(retrieve(ROOT,name=query)['matching_company_entries'],0)
  for value in ('','ab','   ','a'*121,'abc\n','ab\x00c','ab\u202ec','ab\u200bc',123):
   with self.subTest(value=repr(value)),self.assertRaises(ValueError):normalize_name(value)
 def test_name_cli(self):
  p=subprocess.run([sys.executable,str(ROOT/'backend/research_retrieval.py'),'--name','Emerson Electric'],capture_output=True,text=True,check=True,timeout=30)
  a=json.loads(p.stdout);self.assertEqual(a['matching_company_entries'],1);self.assertEqual(a['interface_version'],2)
 def test_emerson_exact_cik_and_financing(self):
  a=retrieve(ROOT,cik='32604',category='ISSUER_REPORTED_FINANCING_REVIEW')
  self.assertEqual(a['matching_company_entries'],1);self.assertEqual(a['results'][0]['entry']['issuer_cik'],'0000032604');self.assertEqual(len(a['results'][0]['additional_insider_review_urls']),3);self.assertTrue(a['requested_cik_present_in_snapshot']);self.assertFalse(a['model_inference_performed'])
 def test_scope_unknown_vs_filter_absence(self):
  a=retrieve(ROOT,cik='1');b=retrieve(ROOT,cik='32604',category='FINANCIAL_CONTEXT_REVIEW')
  self.assertEqual(a['matching_company_entries'],0);self.assertFalse(a['requested_cik_present_in_snapshot']);self.assertTrue(b['requested_cik_present_in_snapshot']);self.assertEqual(b['matching_company_entries'],0)
 def test_all_categories_and_pagination(self):
  self.assertEqual(retrieve(ROOT,category='FINANCIAL_CONTEXT_REVIEW')['matching_company_entries'],106)
  self.assertEqual(retrieve(ROOT,category='INSIDER_ORIGINAL_FILING_REVIEW')['matching_company_entries'],37)
  a=retrieve(ROOT,limit=100);b=retrieve(ROOT,offset=a['next_offset'],limit=100)
  self.assertEqual(len(a['results'])+len(b['results']),108);self.assertIsNone(b['next_offset'])
  c=retrieve(ROOT,offset=9999);self.assertEqual(c['matching_company_entries'],108);self.assertEqual(c['returned_company_entries'],0);self.assertIsNone(c['next_offset'])
 def test_deterministic_and_source_pins(self):
  a=retrieve(ROOT,cik='50292');self.assertEqual(a,retrieve(ROOT,cik='0000050292'))
  for source in a['results'][0]['source_artifacts']:self.assertEqual(hashlib.sha256((ROOT/source['path']).read_bytes()).hexdigest(),source['sha256'])
  self.assertIsNone(a['holdings_linkage']['company_position_count'])
 def test_invalid_query_and_destinations(self):
  for x in ('0','-1','1e2','１２',' 1','00000000001',1):
   with self.subTest(cik=x),self.assertRaises(ValueError):normalize_cik(x)
  for args in ({'limit':True},{'limit':101},{'offset':-1},{'category':'BUY'}):
   with self.assertRaises(ValueError):retrieve(ROOT,**args)
  for path in ('javascript:alert(1)','https://example.com','../private','company.html?unknown=1'):
   with self.assertRaises(ValueError):app_link(path)
 def test_corrupt_snapshot_or_source_fails_closed(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp)
   for f in [SNAPSHOT,*PATHS.values()]:
    (root/f).parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/f,root/f)
   f=root/PATHS['emerson'];f.write_bytes(f.read_bytes()+b' ')
   with self.assertRaises(ValueError):retrieve(root,cik='32604')
   shutil.copyfile(ROOT/PATHS['emerson'],f);(root/SNAPSHOT).write_text('{}')
   with self.assertRaises(ValueError):retrieve(root)
 def test_cli_success_and_no_partial_error_output(self):
  p=subprocess.run([sys.executable,str(ROOT/'backend/research_retrieval.py'),'--root',str(ROOT),'--cik','32604'],capture_output=True,text=True,check=True,timeout=30)
  self.assertEqual(json.loads(p.stdout)['matching_company_entries'],1)
  out=io.StringIO();err=io.StringIO()
  with contextlib.redirect_stdout(out),contextlib.redirect_stderr(err):code=main(['--root',str(ROOT),'--cik','0'])
  self.assertEqual(code,2);self.assertEqual(out.getvalue(),'');self.assertIn('No result inferred',err.getvalue())
if __name__=='__main__':unittest.main()
