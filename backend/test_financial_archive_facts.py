import copy,io,json,unittest,zipfile
from pathlib import Path
from financial_archive_facts import qualify,read_source_rows
from sec_prepared_data import SCHEMAS
class ArchiveFactsTest(unittest.TestCase):
 def setUp(self):
  self.r={'metric':'NetIncomeLoss','taxonomy':'us-gaap/2026','reported_end_date':'2025-03-31','issuer_cik':'0000000123'}
  self.o={'accession':'0000000123-26-000001','issuer_name_as_filed':'TEST','filing_date_as_filed':'2026-05-01','source_url':'https://example.invalid','source_archive_sha256':'a'*64,'database_sha256':'b'*64,'source_rowid':1,'prepared_sub_rowid':2}
  self.n={'adsh':self.o['accession'],'tag':'NetIncomeLoss','version':'us-gaap/2026','ddate':'20250331','qtrs':'1','uom':'USD','segments':'','coreg':'','footnote':'','value':'-100.0000'}
  self.s={'cik':'123','adsh':self.n['adsh'],'name':'TEST','filed':'20260501','form':'10-Q','address':'PRIVATE'}
  self.t={'tag':self.n['tag'],'version':self.n['version'],'datatype':'monetary','custom':'0','abstract':'0','iord':'D'}
 def test_exact_value_unknown_period_and_private_exclusion(self):
  x=qualify(self.r,self.o,self.n,self.s,self.t);self.assertEqual(x['value_as_reported'],'-100.0000');self.assertIsNone(x['period_start']);self.assertFalse(x['consolidated_scope_verified']);self.assertFalse(x['original_filing_text_checked']);self.assertNotIn('PRIVATE',json.dumps(x))
 def test_reject_context_number_taxonomy_identity(self):
  for target,key,value in [('n','value',''),('n','value','NaN'),('n','uom','EUR'),('n','qtrs','4'),('n','segments','segment'),('n','footnote','review required'),('n','ddate','20250330'),('s','cik','999'),('s','filed','20260502'),('t','datatype','perShare'),('t','custom','1'),('r','metric','EarningsPerShareDiluted')]:
   r,o,n,s,t=map(copy.deepcopy,(self.r,self.o,self.n,self.s,self.t));{'r':r,'n':n,'s':s,'t':t}[target][key]=value
   with self.assertRaises(ValueError):qualify(r,o,n,s,t)
 def test_amendment_preserved(self):
  self.s['form']='10-Q/A';self.assertTrue(qualify(self.r,self.o,self.n,self.s,self.t)['amendment_as_filed'])
 def test_raw_row_correspondence_and_missing_row(self):
  stream=io.BytesIO()
  with zipfile.ZipFile(stream,'w') as z:z.writestr('num.txt','\t'.join(SCHEMAS['num.txt'])+'\n'+'\t'.join(self.n[k] for k in SCHEMAS['num.txt'])+'\n')
  stream.seek(0)
  with zipfile.ZipFile(stream) as z:
   self.assertEqual(read_source_rows(z,'num.txt',{1})[1],self.n)
   with self.assertRaises(ValueError):read_source_rows(z,'num.txt',{2})
 def test_published_scope(self):
  x=json.loads((Path(__file__).parent.parent/'web/company-findings/financial-archive-facts.json').read_text());self.assertEqual(len(x['contexts']),395);self.assertEqual(sum(len(c['facts']) for c in x['contexts']),802);self.assertEqual(len({c['issuer_cik'] for c in x['contexts']}),103);self.assertEqual(x['excluded_eps_contexts'],210)
if __name__=='__main__':unittest.main()
