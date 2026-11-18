import copy,csv,io,json,sqlite3,tempfile,unittest,zipfile
from pathlib import Path
from unittest.mock import patch
import company_going_concern as m
ROOT=Path(__file__).resolve().parents[1]
ACC='0000000001-26-000001';TAG='SubstantialDoubtAboutGoingConcernWithinOneYear'
def fixture():
 x=dict.fromkeys(m.SCHEMAS['txt.tsv'],'');x.update(adsh=ACC,tag=TAG,version='us-gaap/2026',ddate='20260630',qtrs='2',dimh='0x00000000',dimn='0',context='From2026-01-01to2026-06-30',lang='en-US',escaped='0',value='false')
 s=dict.fromkeys(m.SCHEMAS['sub.tsv'],'');s.update(adsh=ACC,cik='1',name='Synthetic issuer',form='10-Q',filed='20261028')
 t=dict.fromkeys(m.SCHEMAS['tag.tsv'],'');t.update(tag=TAG,version='us-gaap/2026',datatype='boolean',custom='0',abstract='0')
 d={'dimhash':'0x00000000','segments':'','segt':'0'}
 return {k:[m.row(v,1)] for k,v in [('txt',x),('sub',s),('tag',t),('dim',d)]}
class GoingConcernTests(unittest.TestCase):
 def test_false_source_value_not_no_risk_and_dates_distinct(self):
  companies,n,private=m.project(['0000000001','0000000002'],fixture());r=companies[0]['records'][0]
  self.assertEqual(r['status'],'FALSE_AS_REPORTED');self.assertIs(r['boolean_value_as_reported'],False);self.assertIsNone(r['risk_conclusion']);self.assertIsNone(r['event_date']);self.assertEqual(r['context']['ddate'],'20260630');self.assertEqual(r['filing_date_as_reported'],'2026-10-28');self.assertEqual(n['cohort_ciks_without_selected_contexts'],1)
 def test_taxonomy_identity_and_duplicate_fail_closed(self):
  for key,field,value in [('tag','custom','1'),('tag','abstract','1'),('tag','datatype','textBlock'),('txt','version','custom/2026'),('txt','adsh','wrong'),('sub','cik','2')]:
   d=fixture();d[key][0]['fields'][field]=value
   with self.assertRaises(ValueError):m.project(['0000000001'],d)
  for key in ['sub','tag','dim','txt']:
   d=fixture();d[key]+=copy.deepcopy(d[key])
   with self.assertRaises(ValueError):m.project(['0000000001'],d)
 def test_boolean_lexical_validation_not_truthiness(self):
  for val,expected in [('false',False),('0',False),('true',True),('1',True)]:
   d=fixture();d['txt'][0]['fields']['value']=val;self.assertIs(m.project(['0000000001'],d)[0][0]['records'][0]['boolean_value_as_reported'],expected)
  for val in ['FALSE',' false ','not true','unknown','']:
   d=fixture();d['txt'][0]['fields']['value']=val
   with self.assertRaises(ValueError):m.project(['0000000001'],d)
 def test_dimensions_preserved_without_member_text(self):
  d=fixture();d['txt'][0]['fields']['dimn']='1';d['dim'][0]['fields']['segments']='SensitiveMember=PrivateLabel;';d['dim'][0]['fields']['segt']='1'
  c,_,p=m.project(['0000000001'],d);r=c[0]['records'][0];self.assertEqual(r['context']['dimn'],'1');self.assertEqual(r['dimension_metadata']['segt_as_reported'],'1');self.assertIs(r['dimension_metadata']['raw_dim_segments_published'],False);self.assertNotIn('dimension_member_labels_published',r['dimension_metadata']);self.assertNotIn('PrivateLabel',json.dumps(c));self.assertIn('PrivateLabel',json.dumps(p))
  d['txt'][0]['fields']['dimn']='0'
  with self.assertRaises(ValueError):m.project(['0000000001'],d)
 def test_narrative_and_strings_stay_private(self):
  for tag,typ,status in [('SubstantialDoubtAboutGoingConcernTextBlock','textBlock','UNINTERPRETED_DISCLOSURE'),('SubstantialDoubtAboutGoingConcernConditionsOrEvents','string','UNINTERPRETED_SPECIFIC_STRING_DISCLOSURE')]:
   d=fixture();d['txt'][0]['fields'].update(tag=tag,value='Secret narrative person and amount');d['tag'][0]['fields'].update(tag=tag,datatype=typ)
   c,_,p=m.project(['0000000001'],d);self.assertEqual(c[0]['records'][0]['status'],status);self.assertNotIn('Secret narrative',json.dumps(c));self.assertIn('Secret narrative',json.dumps(p))
 def test_context_and_join_privacy_bounds(self):
  for key,field,value in [('txt','context','<script>'),('txt','coreg','private person'),('txt','lang','bad\x00'),('txt','dimh','../../path'),('txt','escaped','2'),('dim','segt','unknown'),('sub','name','private\x00'),('sub','filed','20261101')]:
   d=fixture();d[key][0]['fields'][field]=value
   with self.assertRaises(ValueError):m.project(['0000000001'],d)
  d=fixture();d['dim']=[]
  with self.assertRaises(ValueError):m.project(['0000000001'],d)
 def test_full_zip_db_reconstruction_and_mismatch(self):
  from sec_notes_data import MEMBERS
  with tempfile.TemporaryDirectory() as td:
   a=Path(td)/'a.zip';dbpath=Path(td)/'db';fixture_data=fixture()
   with sqlite3.connect(dbpath) as db,zipfile.ZipFile(a,'w') as z:
    for member in MEMBERS:
     label=member.split('.')[0]
     if label not in fixture_data:z.writestr(member,b'');continue
     fields=m.SCHEMAS[member];v=[fixture_data[label][0]['fields'][k] for k in fields];buf=io.StringIO();w=csv.writer(buf,delimiter='\t',lineterminator='\n');w.writerow(fields);w.writerow(v);z.writestr(member,buf.getvalue());db.execute('create table notes_'+label+' ('+','.join('"'+k+'" TEXT' for k in fields)+')');db.execute('insert into notes_'+label+' values ('+','.join('?' for k in fields)+')',v)
   with patch.object(m,'ZIP_BYTES',a.stat().st_size),patch.object(m,'ZIP_SHA',m.sha(a)),patch.object(m,'DB_SHA',m.sha(dbpath)),patch.object(m,'TOTALS',dict.fromkeys(m.TOTALS,1)):
    data,pins,excluded=m.verify(a,dbpath);self.assertEqual(data,fixture_data);self.assertEqual(excluded,0)
   with sqlite3.connect(dbpath) as db:db.execute("update notes_txt set value='true'")
   with patch.object(m,'ZIP_BYTES',a.stat().st_size),patch.object(m,'ZIP_SHA',m.sha(a)),patch.object(m,'DB_SHA',m.sha(dbpath)),patch.object(m,'TOTALS',dict.fromkeys(m.TOTALS,1)):
    with self.assertRaisesRegex(ValueError,'correspondence'):m.verify(a,dbpath)
 def test_failed_source_pin_and_completion(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/'bad';p.write_bytes(b'bad')
   with self.assertRaises(ValueError):m.verify(p,p)
   out=Path(td)/'failed'
   with self.assertRaises(ValueError):m.save(ROOT,p,p,p,out)
   self.assertTrue((out/'INCOMPLETE').exists());self.assertFalse((out/'contexts.json').exists());self.assertFalse((out/'COMPLETE.json').exists())
   out=Path(td)/'success'
   with patch.object(m,'build',return_value=({'safe':True},[])):m.save(ROOT,p,p,p,out)
   self.assertEqual(out.stat().st_mode&511,448);self.assertEqual((out/'contexts.json').stat().st_mode&511,384);self.assertFalse((out/'INCOMPLETE').exists())
 def test_actual_public_census_and_allowlist(self):
  d=json.loads((ROOT/'web/company-findings/going-concern-contexts.json').read_bytes());self.assertEqual(d['counts']['selected_contexts'],123);self.assertEqual(d['counts']['selected_filings'],108);self.assertEqual(d['counts']['selected_ciks'],97);self.assertEqual(d['counts']['status_counts'],{'FALSE_AS_REPORTED':2,'UNINTERPRETED_DISCLOSURE':119,'UNINTERPRETED_SPECIFIC_STRING_DISCLOSURE':2})
  records=[r for c in d['companies'] for r in c['records']]
  for c in d['companies']:
   for r in c['records']:
    self.assertEqual(r['issuer_cik'],c['issuer_cik']);self.assertIn(r['issuer_cik'],d['cohort_ciks']);self.assertEqual(set(r),{'id','issuer_cik','issuer_name_as_filed','accession','form_as_filed','filing_date_as_reported','concept','taxonomy_version','datatype','status','boolean_value_as_reported','qualification','context','dimension_metadata','value_utf8_sha256','source_rows','event_date','first_public_utc','risk_conclusion','sec_accession_lookup_url','lookup_status'})
  self.assertEqual({r['issuer_cik'] for r in records if r['status']=='FALSE_AS_REPORTED'},{'0001513761','0001318742'})
if __name__=='__main__':unittest.main()
