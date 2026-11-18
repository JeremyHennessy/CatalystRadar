import copy,json,unittest
from pathlib import Path
from financial_review_names import attach
class NameJoinTest(unittest.TestCase):
 def setUp(self):
  self.record={'issuer_cik':'0000000123','observations':[{'filing_batch':'q1_2026_filing_batch','accession':'0000000123-26-000001','filing_date_as_filed':'2026-01-01'},{'filing_batch':'q2_2026_filing_batch','accession':'0000000123-26-000002','filing_date_as_filed':'2026-04-01'}]}
  self.rows=[{'rowid':1,'cik':'123','adsh':'0000000123-26-000001','filed':'20260101','name':'OLD NAME','address':'NOT PUBLIC'},{'rowid':2,'cik':'123','adsh':'0000000123-26-000002','filed':'20260401','name':'NEW NAME'}]
 def lookup(self,batch,acc):return [x for x in self.rows if x['adsh']==acc]
 def test_exact_join_variants_private_exclusion(self):
  result=attach(self.record,self.lookup);self.assertEqual(result['issuer_names_as_filed'],['NEW NAME','OLD NAME']);self.assertEqual(result['observations'][0]['issuer_name_as_filed'],'OLD NAME');self.assertNotIn('NOT PUBLIC',json.dumps(result));self.assertNotIn('issuer_names_as_filed',self.record)
 def test_missing_duplicate(self):
  for rows in ([],self.rows+[self.rows[0]]):
   self.rows=rows
   with self.assertRaises(ValueError):attach(self.record,self.lookup)
 def test_conflicts(self):
  for key,value in [('cik','999'),('filed','20260102'),('name',''),('name','a\nb')]:
   saved=copy.deepcopy(self.rows);self.rows[0][key]=value
   with self.assertRaises(ValueError):attach(self.record,self.lookup)
   self.rows=saved
 def test_public_label_counts(self):
  d=json.loads((Path(__file__).parent.parent/'web/company-findings/financial-review.json').read_text());self.assertEqual(d['version'],2);self.assertEqual(len({n for r in d['records'] for n in r['issuer_names_as_filed']}),108);self.assertEqual(len({r['issuer_cik'] for r in d['records']}),106)
if __name__=='__main__':unittest.main()
