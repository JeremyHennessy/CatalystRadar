"""Synthetic fixtures for the fixed source-reported abstention case."""
import copy,datetime as dt,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import company_revenue_finding as m

class Tests(unittest.TestCase):
 def fixture(self):
  summary={'accession_from_pinned_manifest':m.ACCESSION,'comparability_verified':False,'training_ready':False,'execution_ready':False,'archive_sha256':'a'*64,'raw_member_sha256':'b'*64,'identity_manifest_sha256':'c'*64,'prepared_archive_sha256':'d'*64,'prepared_database_sha256':'e'*64}
  receipt={'accession':m.ACCESSION,'issuer_cik_verified':m.CIK,'zip_sha256':'a'*64,'primary_member_sha256':'b'*64,'primary_member':'vsbc_10q.htm','source_url':f'https://www.sec.gov/Archives/edgar/data/{m.CIK}/{m.ACCESSION.replace("-","")}/{m.ACCESSION}-xbrl.zip','local_verified_utc':'2026-11-17T00:00:00+00:00'}
  results=[]
  for i,(fid,(start,end)) in enumerate(m.FACTS.items()):
   f={'fact_id':fid,'concept':{'namespace':'http://fasb.org/us-gaap/2025','local_name':'Revenues'},'period':{'kind':'duration','startDate':start,'endDate':end},'unit':{'kind':'simple','measures':[m.USD]},'dimension_or_scenario_present':False,'numeric_conversion_verified':True,'numeric_value':'0','issuer_identifier_as_filed':'0001697884','issuer_identifier_scheme':'http://www.sec.gov/CIK','raw_member_sha256':'b'*64,'text_untransformed':'-','format':{'namespace':'http://www.xbrl.org/inlineXBRL/transformation/2015-02-26','local_name':'zerodash'},'decimals_as_filed':'0','context_ref':'context'+str(i),'context_serialization_sha256':'f'*64}
   sub={'adsh':m.ACCESSION,'cik':m.CIK,'period':'20250731','filed':'20260617','form':'10-Q','name':'Synthetic Case Label','fy':'2026','fp':'Q2','rowid':1,'bas1':'PRIVATE ADDRESS SHOULD NOT APPEAR','baph':'PRIVATE CONTACT'}
   num={'adsh':m.ACCESSION,'tag':'Revenues','version':'us-gaap/2025','ddate':end.replace('-',''),'qtrs':'1','uom':'USD','segments':'','coreg':'','footnote':'','value':'0.0000','rowid':i+10}
   results.append({'disposition':'candidate_numeric_equal','candidate':{'numeric_equal':True,'source_group':{'occurrences':[f]},'prepared_submission':sub,'prepared_num':num}})
  return summary,results,receipt
 def test_historical_zero_abstention_and_privacy(self):
  s,r,p=self.fixture();c=m.build(s,r,p);self.assertIsNone(c['calculation']['value']);self.assertEqual(c['calculation']['reason'],'ZERO_COMPARISON_BASE');self.assertEqual([f['period_end'] for f in c['facts']],['2025-07-31','2024-07-31']);self.assertEqual(c['filing']['filing_date_as_reported'],'2026-06-17');self.assertFalse(c['training_ready']);self.assertIsNone(c['probability']);self.assertNotIn('PRIVATE',json.dumps(c));self.assertEqual(c['filing']['fiscal_year_as_filed'],'2026')
 def test_nonzero_missing_and_ambiguous_cases_fail_closed(self):
  for case in ('value','missing','duplicate','unequal'):
   s,r,p=self.fixture()
   if case=='value':r[0]['candidate']['source_group']['occurrences'][0]['numeric_value']='1'
   if case=='missing':r.pop()
   if case=='duplicate':r.append(copy.deepcopy(r[0]))
   if case=='unequal':r[0]['candidate']['numeric_equal']=False
   with self.assertRaises(ValueError):m.build(s,r,p)
 def test_wrong_concept_currency_duration_or_dimensions(self):
  for key,value in [('concept',{'namespace':'http://fasb.org/us-gaap/2025','local_name':'NetIncomeLoss'}),('unit',{'kind':'simple','measures':[]}),('period',{'kind':'duration','startDate':'2025-02-01','endDate':'2025-07-31'}),('dimension_or_scenario_present',True),('format',{'namespace':'unknown','local_name':'zerodash'})]:
   s,r,p=self.fixture();r[0]['candidate']['source_group']['occurrences'][0][key]=value
   with self.assertRaises(ValueError):m.build(s,r,p)
 def test_identity_scope_sourceclock_and_prepared_context(self):
  for case in ('issuer','url','clock','segment','date','admission'):
   s,r,p=self.fixture()
   if case=='issuer':p['issuer_cik_verified']='2'
   if case=='url':p['source_url']='https://example.invalid/data'
   if case=='clock':p['local_verified_utc']='2026-11-17T00:00:00'
   if case=='segment':r[0]['candidate']['prepared_num']['segments']='segment'
   if case=='date':r[0]['candidate']['prepared_submission']['filed']='20261117'
   if case=='admission':s['training_ready']=True
   with self.assertRaises(ValueError):m.build(s,r,p)
 def test_private_completion_and_failure(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);s,r,receipt=self.fixture();config={'manifest':'synthetic','manifest_sha':'a'*64}
   with patch.object(m,'correspondence',return_value=(s,r)),patch.object(m,'read_pinned',return_value=(receipt,b'')):
    c=m.save(config,p/'out')
   self.assertFalse((p/'out/INCOMPLETE').exists());self.assertEqual(json.loads((p/'out/COMPLETE.json').read_text())['finding_sha256'],m.sha(p/'out/finding.json'));self.assertEqual((p/'out/finding.json').stat().st_mode&0o777,0o600)
   with patch.object(m,'correspondence',side_effect=ValueError('failure')):
    with self.assertRaises(ValueError):m.save(config,p/'failed')
   self.assertTrue((p/'failed/INCOMPLETE').exists())
if __name__=='__main__':unittest.main()
