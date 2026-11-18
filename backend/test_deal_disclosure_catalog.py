import copy,json,sqlite3,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import deal_disclosure_catalog as m
import deal_disclosure_evidence as evidence
import test_deal_disclosure_evidence as fixtures

class Tests(unittest.TestCase):
 def fixture(self):
  db=fixtures.Tests().fixture();rows,counts=evidence.scan(db)
  s={'status':'ACQUISITION_DISPOSAL_DISCLOSURES_UNADJUDICATED','verified_events':0,'training_ready':False,'execution_ready':False,'counts':counts,'source_url':'https://www.sec.gov/files/synthetic.zip','source_archive_sha256':'0'*64,'database_sha256':'1'*64,'selection':{'tags':list(m.TAGS),'taxonomy_versions':list(m.VERSIONS),'custom':'0','abstract':'0','datatype':'textBlock'}}
  return s,rows
 def test_public_allowlist_and_url(self):
  s,r=self.fixture();raw,manifest=m.catalog(s,r);row=json.loads(raw)[0]
  self.assertEqual(set(row),m.PUBLIC_FIELDS);self.assertNotIn('script',raw.decode());self.assertNotIn('did not acquire',raw.decode());self.assertEqual(row['issuer_cik'],'0000000001');self.assertEqual(row['sec_filing_index_url'],'https://www.sec.gov/Archives/edgar/data/1/000000000126000001/0000000001-26-000001-index.html');self.assertEqual(manifest['verified_events'],0)
 def test_repeated_disclosure_group_not_new_filing(self):
  s,r=self.fixture();r.append(copy.deepcopy(r[0]));r[1]['raw']['rowid']=2;s['counts']['disclosure_records']=2;s['counts']['by_concept'][m.TAGS[0]]=2;s['counts']['by_taxonomy_version'][m.VERSIONS[1]]=2
  raw,manifest=m.catalog(s,r);row=json.loads(raw)[0];self.assertEqual(row['disclosure_records'],2);self.assertEqual(row['concepts'][0]['records'],2);self.assertEqual(manifest['filings'],1)
 def test_duplicate_row_conflicting_submission_and_tamper(self):
  for kind in ('duplicate','identity','hash'):
   s,r=self.fixture()
   if kind=='duplicate':r.append(copy.deepcopy(r[0]));s['counts']['disclosure_records']=2
   if kind=='identity':r[0]['submission']['adsh']='0000000002-26-000001'
   if kind=='hash':r[0]['raw']['value']='changed'
   with self.assertRaises(ValueError):m.catalog(s,r)
 def test_adjudicated_or_count_mismatch_rejected(self):
  for kind in ('event','status','count','ciks','dimensions','concepts','selection'):
   s,r=self.fixture()
   if kind=='event':r[0]['event_date']='2020-01-01'
   if kind=='status':s['verified_events']=1
   if kind=='count':s['counts']['filings']=2
   if kind=='ciks':s['counts']['issuer_ciks']=2
   if kind=='dimensions':s['counts']['records_with_dimensions']=1
   if kind=='concepts':s['counts']['by_concept']={}
   if kind=='selection':s['selection']['custom']='1'
   with self.assertRaises(ValueError):m.catalog(s,r)
 def test_source_labels_not_html_and_unsupported_form(self):
  s,r=self.fixture();r[0]['submission']['name']='<b>Issuer</b>';raw,_=m.catalog(s,r);self.assertEqual(json.loads(raw)[0]['issuer_name_as_filed'],'<b>Issuer</b>')
  r[0]['submission']['form']='contact@example.invalid'
  with self.assertRaises(ValueError):m.catalog(s,r)
 def test_persist_and_fail_closed(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);s,r=self.fixture()
   with patch.object(m,'audit',return_value=(s,r)):m.save('db','h','zip','z',p/'out')
   self.assertFalse((p/'out/INCOMPLETE').exists());c=json.loads((p/'out/COMPLETE.json').read_text());self.assertEqual(c['filings_sha256'],m.sha(p/'out/filings.json'));self.assertEqual((p/'out/filings.json').stat().st_mode&0o777,0o600)
   with patch.object(m,'audit',side_effect=ValueError('failure')):
    with self.assertRaises(ValueError):m.save('db','h','zip','z',p/'failed')
   self.assertTrue((p/'failed/INCOMPLETE').exists());self.assertFalse((p/'failed/COMPLETE.json').exists())
if __name__=='__main__':unittest.main()
