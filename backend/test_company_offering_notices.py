import copy,csv,io,json,sqlite3,tempfile,unittest,zipfile
from pathlib import Path
from unittest.mock import patch
import company_offering_notices as m
ROOT=Path(__file__).resolve().parents[1]
A='0000000001-26-000001';B='0000000001-26-000002'
def row(d,n=1):return {'rowid':n,'fields':d,'canonical_row_sha256':m.digest(m.canonical(d))}
def fixture():
 s={'ACCESSIONNUMBER':A,'SUBMISSIONTYPE':'D','TESTORLIVE':'LIVE','FILING_DATE':'01-JUL-2026'}
 i={'ACCESSIONNUMBER':A,'CIK':'1','ENTITYNAME':'Synthetic issuer <not markup>','IS_PRIMARYISSUER_FLAG':'YES','ISSUER_SEQ_KEY':'1'}
 o={'ACCESSIONNUMBER':A,'PREVIOUSACCESSIONNUMBER':'','ISAMENDMENT':'false',**dict.fromkeys(m.FLAGS,'')}
 return {'FORMDSUBMISSION':[row(s)],'ISSUERS':[row(i)],'OFFERING':[row(o)]}
class NoticeTests(unittest.TestCase):
 def test_exact_cik_conservation_and_safe_scope(self):
  x,n,p=m.project(['0000000001','0000000002'],fixture());self.assertEqual(n['selected_distinct_submissions'],1);self.assertEqual(n['cohort_ciks_without_selected_notices'],1);self.assertEqual(x[0]['records'][0]['filing_date_as_reported'],'2026-07-01');self.assertIsNone(x[0]['records'][0]['previous_accession']);self.assertEqual(x[0]['records'][0]['issuer_name_as_filed'],'Synthetic issuer <not markup>')
  x,n,p=m.project(['0000000002'],fixture());self.assertEqual(x,[]);self.assertEqual(n['issuer_rows_outside_cohort'],1)
 def test_duplicates_and_identity_orphans_fail(self):
  for family in ['FORMDSUBMISSION','ISSUERS','OFFERING']:
   t=fixture();t[family]+=copy.deepcopy(t[family])
   with self.assertRaises(ValueError):m.project(['0000000001'],t)
  for field,val in [('CIK','not-cik'),('IS_PRIMARYISSUER_FLAG','UNKNOWN'),('ACCESSIONNUMBER',B)]:
   t=fixture();t['ISSUERS'][0]['fields'][field]=val
   with self.assertRaises(ValueError):m.project(['0000000001'],t)
  with self.assertRaises(ValueError):m.project(['0000000001']*2,fixture())
 def test_unsafe_names_dates_forms_fail(self):
  for family,field,value in [('ISSUERS','ENTITYNAME','bad\x00name'),('FORMDSUBMISSION','FILING_DATE','31-JUN-2026'),('FORMDSUBMISSION','FILING_DATE','01-JUL-2025'),('FORMDSUBMISSION','SUBMISSIONTYPE','private text'),('FORMDSUBMISSION','TESTORLIVE','TEST')]:
   t=fixture();t[family][0]['fields'][field]=value
   with self.assertRaises(ValueError):m.project(['0000000001'],t)
 def test_previous_status_flags_and_conflicts_no_raw_unknown(self):
  t=fixture();o=t['OFFERING'][0]['fields'];o['PREVIOUSACCESSIONNUMBER']='unsafe private text';o['ISEQUITYTYPE']='private text';o['ISAMENDMENT']='true'
  x,_,_=m.project(['0000000001'],t);r=x[0]['records'][0];self.assertEqual(r['previous_accession_status'],'INVALID_REDACTED');self.assertIsNone(r['previous_accession']);self.assertTrue(r['form_amendment_conflict']);self.assertNotIn('private text',json.dumps(x));self.assertEqual(r['security_type_flags_as_reported']['ISEQUITYTYPE'],'UNKNOWN_REDACTED')
  o['PREVIOUSACCESSIONNUMBER']=B;x,_,_=m.project(['0000000001'],t);self.assertEqual(x[0]['records'][0]['previous_accession_status'],'OUTSIDE_RETAINED_BATCH')
 def test_self_cycle_and_same_issuer_reference_are_diagnostics(self):
  t=fixture();t['OFFERING'][0]['fields']['PREVIOUSACCESSIONNUMBER']=A
  x,n,_=m.project(['0000000001'],t);self.assertTrue(x[0]['records'][0]['self_reference']);self.assertTrue(x[0]['records'][0]['declared_predecessor_same_cik_and_role']);self.assertEqual(n['cycle_associations'],1)
  for family in t:
   r=copy.deepcopy(t[family][0]);r['rowid']=2;r['fields']['ACCESSIONNUMBER']=B;t[family].append(r)
  t['OFFERING'][0]['fields']['PREVIOUSACCESSIONNUMBER']=B;t['OFFERING'][1]['fields']['PREVIOUSACCESSIONNUMBER']=A
  x,n,_=m.project(['0000000001'],t);self.assertEqual(n['cycle_associations'],2)
 def test_hash_duplicate_json_and_read_bounds(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/'x';p.write_bytes(b'{"x":1,"x":2}')
   with self.assertRaises(ValueError):m.pinned_json(p,m.sha(p),100)
   p.write_bytes(b'{}')
   with self.assertRaises(ValueError):m.pinned_json(p,'0'*64,100)
   with self.assertRaises(ValueError):m.pinned_json(p,m.sha(p),1)
   with self.assertRaises(ValueError):m.verified_tables(p,p)
 def test_receipt_cannot_invent_download_clock(self):
  s={'source':{'path':'2026q3_d.zip','url':m.URL,'sha256':m.ZIP_SHA,'byte_count':3652689,'local_verified_utc':'2026-11-17T20:22:01.440157+00:00','http_status':None,'exact_download_utc':None,'retrieval_method':'PUBLIC_BROWSER_LINK_DOWNLOAD_NO_PRIVATE_CONTACT'}}
  self.assertIsNone(m.receipt(s)['http_status'])
  for k,v in [('http_status',200),('exact_download_utc','2026-11-17T20:22:01Z'),('url','https://example.com'),('byte_count',True),('local_verified_utc','2026-11-17T20:22:01')]:
   t=copy.deepcopy(s);t['source'][k]=v
   with self.assertRaises(ValueError):m.receipt(t)
 def test_completion_and_failure(self):
  with tempfile.TemporaryDirectory() as td:
   out=Path(td)/'done'
   with patch.object(m,'build',return_value=({'safe':True},[])):m.save(ROOT,'a','d','s',out)
   self.assertFalse((out/'INCOMPLETE').exists());self.assertEqual(out.stat().st_mode&511,448);self.assertEqual((out/'notices.json').stat().st_mode&511,384)
   fail=Path(td)/'fail'
   with patch.object(m,'build',side_effect=ValueError('mismatch')):
    with self.assertRaises(ValueError):m.save(ROOT,'a','d','s',fail)
   self.assertTrue((fail/'INCOMPLETE').exists());self.assertFalse((fail/'COMPLETE.json').exists());self.assertFalse((fail/'notices.json').exists())
 def test_full_zip_to_database_correspondence_and_changed_row(self):
  from sec_formd_data import MEMBERS
  with tempfile.TemporaryDirectory() as td:
   zpath=Path(td)/'source.zip';dbpath=Path(td)/'source.sqlite'
   with sqlite3.connect(dbpath) as db,zipfile.ZipFile(zpath,'w') as z:
    for member in MEMBERS:
     label=member.split('/')[-1].split('.')[0]
     if label not in m.TABLES:z.writestr(member,b'');continue
     fields=m.SCHEMAS[member];values=['synthetic-'+str(n) for n in range(len(fields))]
     buf=io.StringIO();w=csv.writer(buf,delimiter='\t',lineterminator='\n');w.writerow(fields);w.writerow(values);z.writestr(member,buf.getvalue())
     table='formd_'+label.lower();db.execute('CREATE TABLE '+table+' ('+','.join('"'+f+'" TEXT' for f in fields)+')');db.execute('INSERT INTO '+table+' VALUES ('+','.join('?' for f in fields)+')',values)
   with patch.object(m,'ZIP_SHA',m.sha(zpath)),patch.object(m,'DB_SHA',m.sha(dbpath)),patch.object(m,'TABLES',dict.fromkeys(m.TABLES,1)):
    data,pins=m.verified_tables(zpath,dbpath);self.assertEqual(len(data),3);self.assertEqual(data['ISSUERS'][0]['rowid'],1)
   with sqlite3.connect(dbpath) as db:db.execute("UPDATE formd_issuers SET CIK='changed'")
   with patch.object(m,'ZIP_SHA',m.sha(zpath)),patch.object(m,'DB_SHA',m.sha(dbpath)),patch.object(m,'TABLES',dict.fromkeys(m.TABLES,1)):
    with self.assertRaisesRegex(ValueError,'correspondence'):m.verified_tables(zpath,dbpath)
 def test_public_census_lookup_and_allowlist(self):
  d=json.loads((ROOT/'web/company-findings/formd-notice-history.json').read_bytes());self.assertEqual(len(d['cohort_ciks']),8035);self.assertEqual(len(set(d['cohort_ciks'])),8035);self.assertEqual(len(d['companies']),187)
  rr=[r for c in d['companies'] for r in c['records']];self.assertEqual(len(rr),223);self.assertEqual(sum(r['declared_predecessor_same_cik_and_role'] is True for r in rr),3)
  for c in d['companies']:
   self.assertIn(c['issuer_cik'],d['cohort_ciks'])
   for r in c['records']:
    self.assertEqual(set(r),{'issuer_cik','issuer_name_as_filed','accession','form_as_filed','filing_date_as_reported','primary_issuer_as_reported','amendment_flag','form_amendment_conflict','previous_accession','previous_accession_status','declared_predecessor_same_cik_and_role','self_reference','retained_reference_cycle','security_type_flags_as_reported','source_rows','sec_accession_lookup_url','lookup_status','event_date','first_public_utc','financing_completion_verified','security_identity_verified'});self.assertEqual(r['issuer_cik'],c['issuer_cik']);self.assertEqual(r['sec_accession_lookup_url'],'https://www.sec.gov/edgar/search/#/q='+r['accession']);self.assertIsNone(r['event_date']);self.assertFalse(r['financing_completion_verified']);self.assertEqual(set(r['security_type_flags_as_reported']),set(m.FLAGS))
  self.assertEqual(d['counts']['selected_issuer_associations']+d['counts']['issuer_rows_outside_cohort'],16160)
if __name__=='__main__':unittest.main()
