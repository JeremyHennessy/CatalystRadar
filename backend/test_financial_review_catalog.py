import copy,json,unittest
from pathlib import Path
from financial_review_catalog import project,build,PIN
class ReviewTest(unittest.TestCase):
 def setUp(self):
  obs=lambda acc,val,batch:{'issuer_cik_as_filed':'123','accession':acc,'batch':batch,'value_as_filed':val,'filed_as_filed':'20260513','source_rowid':1,'database_sha256':'a'*64,'source_archive_sha256':'b'*64}
  self.r={'context_id':'f'*64,'context':{'issuer_cik':'123','tag':'Revenues','version':'us-gaap/2026','qtrs':'1','segments':'','coreg':'','uom':'USD','ddate':'20250331'},'category':'multiple_accession_context','cross_batch':True,'observations':[obs('0001437749-26-016543','1','q2_2026_filing_batch'),obs('0001437749-26-026366','2','q3_2026_filing_batch')],'numeric_relation':'different_reported_numbers','restatement_verified':False,'comparability_verified':False,'event_group_verified':False,'training_ready':False}
 def test_projection(self):
  d=project([self.r]);text=json.dumps(d);self.assertNotIn('value_as_filed',text);self.assertNotIn('accepted_as_filed',text);self.assertEqual(d['records'][0]['issuer_cik'],'0000000123');self.assertIsNone(d['records'][0]['first_observed_utc'])
 def test_reject_mutations(self):
  for key,val in [('numeric_relation','numerically_equal'),('comparability_verified',True),('cross_batch',False),('context_id','bad')]:
   r=copy.deepcopy(self.r);r[key]=val
   with self.assertRaises(ValueError):project([r])
 def test_eps_unit_preserved(self):
  self.r['context']['tag']='EarningsPerShareDiluted'
  r=project([self.r])['records'][0];self.assertEqual(r['reported_unit'],'USD');self.assertEqual(r['unit_status'],'EPS_UNIT_REQUIRES_REVIEW')
 def test_duplicates(self):
  with self.assertRaises(ValueError):project([self.r,self.r])
 def test_identity(self):
  self.r['observations'][0]['issuer_cik_as_filed']='987'
  with self.assertRaises(ValueError):project([self.r])
 def test_private_fields_removed(self):
  self.r['owner_name']='private';self.r['observations'][0]['address']='private';self.assertNotIn('private',json.dumps(project([self.r])))
 def test_public_counts(self):
  d=json.loads((Path(__file__).parent.parent/'web/company-findings/financial-review.json').read_text());self.assertEqual(len(d['records']),605);self.assertEqual(sum(r['numeric_relation']=='different_reported_numbers' for r in d['records']),90);self.assertEqual(d['source_candidate_sha256'],PIN)
if __name__=='__main__':unittest.main()
