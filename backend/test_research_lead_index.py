import copy,hashlib,json,unittest,subprocess,sys,tempfile
from pathlib import Path
from research_lead_index import PATHS,build,index
ROOT=Path(__file__).resolve().parents[1]
class LeadIndexTest(unittest.TestCase):
 def setUp(self):
  self.data={k:json.loads((ROOT/v).read_bytes()) for k,v in PATHS.items()};self.pins={k:hashlib.sha256((ROOT/v).read_bytes()).hexdigest() for k,v in PATHS.items()}
 def test_deterministic_complete_index(self):
  a=build(ROOT,self.pins);self.assertEqual(a,build(ROOT,self.pins));self.assertEqual(a['counts'],{'company_entries':108,'financial_review_issuers':106,'reported_comparison_only_issuers':1,'reported_financing_only_issuers':1,'financial_contexts':605,'with_selected_insider_filings':37,'with_selected_disclosure_filings':5})
  rows=a['records'];self.assertEqual(len({r['issuer_cik'] for r in rows}),108);self.assertEqual([r['issuer_cik'] for r in rows],sorted(r['issuer_cik'] for r in rows))
  for r in rows:self.assertFalse(r['training_ready']);self.assertFalse(r['execution_ready']);self.assertIsNone(r['first_public_utc']);self.assertNotIn('score',r)
 def test_documented_cli_reproduces(self):
  with tempfile.TemporaryDirectory() as tmp:
   out=Path(tmp)/'index.json';args=[sys.executable,str(ROOT/'backend/research_lead_index.py'),'--root',str(ROOT),'--out',str(out)]
   for key,value in self.pins.items():args+=['--'+key.replace('_','-')+'-sha',value]
   subprocess.run(args,check=True,capture_output=True,timeout=30)
   self.assertEqual(json.loads(out.read_bytes()),build(ROOT,self.pins))
 def test_emerson_identity_and_separate_source_links(self):
  a=build(ROOT,self.pins);r=next(r for r in a['records'] if r['issuer_cik']=='0000032604')
  self.assertEqual(len(r['insider_filing_refs']),3);self.assertEqual(r['financial_case_ids'],[]);self.assertEqual(r['evidence_url'],'company.html#debt-offering');self.assertEqual(r['financial_coverage'],'NOT_IN_EXISTING_FINANCIAL_REVIEW_COHORT')
 def test_old_entries_preserved(self):
  old=json.loads((ROOT/'web/company-findings/research-lead-index-v2.json').read_bytes());new=build(ROOT,self.pins)
  self.assertEqual(old['records'],[r for r in new['records'] if r['issuer_cik']!='0000032604'])
 def test_emerson_changed_facts_identity_and_duplicate_reject(self):
  original=copy.deepcopy(self.data)
  for kind in ('cik','debt','refs','qualification'):
   self.data=copy.deepcopy(original)
   if kind=='cik':self.data['emerson']['issuer']['cik']='0000000001'
   elif kind=='debt':self.data['emerson']['facts']['previously_announced']=False
   elif kind=='qualification':next(r for r in self.data['watchlist_insider']['filings'] if r['issuer_cik']=='0000032604')['original_reviewed']=True
   else:self.data['watchlist_insider']['filings'].append(copy.deepcopy(self.data['watchlist_insider']['filings'][0]))
   with self.subTest(kind=kind),self.assertRaises(ValueError):index(self.data,self.pins)
 def test_holdings_unknown_not_zero_positions(self):
  a=index(self.data,self.pins)
  self.assertFalse(a['holdings_linkage']['company_holdings_assessed']);self.assertIsNone(a['holdings_linkage']['company_position_count'])
  self.assertEqual(a['holdings_linkage']['existing_identifier_correspondences'],1507)
  for r in a['records']:
   self.assertEqual(r['holdings_coverage'],'NOT_ASSESSED_MISSING_VERIFIED_ISSUER_SECURITY_MAPPING');self.assertNotIn('holdings',r)
 def test_holdings_provenance_or_qualification_change_rejects(self):
  original=copy.deepcopy(self.data)
  for kind in ('hash','issuer','history','count','positions'):
   self.data=copy.deepcopy(original)
   if kind=='hash':self.data['holdings']['mapping_response_sha256']='0'*64
   elif kind=='issuer':self.data['mapping']['mappings'][0]['issuer_cik_link_verified']=True
   elif kind=='history':self.data['holdings']['historical_security_link_verified']=True
   elif kind=='positions':self.data['mapping']['mappings'][0]['request_position']=1
   else:self.data['holdings']['census']['holding_rows']+=1
   with self.subTest(kind=kind),self.assertRaises(ValueError):index(self.data,self.pins)
 def test_ieh_not_evaluated_is_not_absence(self):
  r=next(r for r in index(self.data,self.pins)['records'] if r['issuer_cik']=='0000050292')
  self.assertEqual(r['insider_coverage'],'NOT_EVALUATED_IN_THIS_FINANCIAL_COHORT');self.assertEqual(r['evidence_url'],'company-ieh.html')
 def test_changed_source_version(self):
  self.data['insider']['financial_source']['sha256']='0'*64
  with self.assertRaises(ValueError):index(self.data,self.pins)
 def test_duplicate_and_missing_references(self):
  original=copy.deepcopy(self.data)
  for mode in ('filing','company','reference','case'):
   self.data=copy.deepcopy(original)
   if mode=='filing':self.data['insider']['insider_filings'].append(copy.deepcopy(self.data['insider']['insider_filings'][0]))
   elif mode=='company':self.data['insider']['companies'][0]=copy.deepcopy(self.data['insider']['companies'][1])
   elif mode=='reference':next(c for c in self.data['insider']['companies'] if c['insider_filing_refs'])['insider_filing_refs'].pop()
   else:self.data['insider']['companies'][0]['financial_cases'].append(copy.deepcopy(self.data['insider']['companies'][0]['financial_cases'][0]))
   with self.subTest(mode=mode),self.assertRaises(ValueError):index(self.data,self.pins)
 def test_updated_reported_facts_require_review(self):
  self.data['ieh']['comparison']['current_value']='0'
  with self.assertRaises(ValueError):index(self.data,self.pins)
 def test_pin_failure(self):
  self.pins['ieh']='0'*64
  with self.assertRaises(ValueError):build(ROOT,self.pins)
 def test_no_source_numeric_values_or_narratives_copied(self):
  a=index(self.data,self.pins)
  for r in a['records']:
   self.assertFalse({'current_value','prior_value','raw','owner','price','quantity','narrative','probability','return_estimate'} & set(r))
if __name__=='__main__':unittest.main()
