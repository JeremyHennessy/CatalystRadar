import copy,json,tempfile,unittest,sqlite3,zipfile
from pathlib import Path
from unittest.mock import patch
import revenue_instance_references as m
import test_revenue_review_sample as fixtures
class InstanceReferenceTests(unittest.TestCase):
 def setUp(self):
  self.packet={'issuer_cik':'0000002488','accession':'0000002488-26-000123','issuer_name_as_filed':'TEST','source_sub_rowid':1,'source_sub_row_sha256':'a'*64,'source_url':'https://www.sec.gov/Archives/edgar/data/2488/000000248826000123/0000002488-26-000123-index.html'}
  self.sub={'cik':'2488','adsh':self.packet['accession'],'name':'TEST','instance':'amd-20260627_htm.xml'}
 def test_literal_filename_no_date_inference(self):
  x=m.reference(self.packet,self.sub);self.assertTrue(x['constructed_instance_lookup_url'].endswith('/amd-20260627_htm.xml'));self.assertIsNone(x['period_dates_inferred_from_filename']);self.assertIsNone(x['http_status']);self.assertFalse(x['availability_verified']);self.assertFalse(x['comparability_verified'])
 def test_unsafe_filename_and_identity(self):
  for name in ('../x.xml','x/abc.xml','x%2Fabc.xml','x.xml?query=1','https://example.invalid/x.xml','x\\a.xml','x..xml','x.xml\n','x.html','x'*80+'.xml'):
   with self.assertRaises(ValueError):m.reference(self.packet,dict(self.sub,instance=name))
  for field,value in [('cik','2489'),('cik','２４８８'),('adsh','0000002488-26-000124'),('name','OTHER')]:
   with self.assertRaises(ValueError):m.reference(self.packet,dict(self.sub,**{field:value}))
  with self.assertRaises(ValueError):m.reference(dict(self.packet,source_url='https://example.invalid'),self.sub)
 def test_full_correspondence_and_changed_hash(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);db,archive,_,_=fixtures.RevenueReviewSampleTests().fixture(root)
   conn=sqlite3.connect(db);conn.row_factory=sqlite3.Row
   conn.execute("UPDATE financial_sub SET instance='example-20260630_htm.xml'");conn.commit();rows=[dict(r) for r in conn.execute('SELECT rowid,* FROM financial_sub')];conn.close()
   with zipfile.ZipFile(archive) as z:contents={n:z.read(n) for n in z.namelist()}
   fields=m.SCHEMAS['sub.txt'];contents['sub.txt']=('\t'.join(fields)+'\n'+''.join('\t'.join(r[k] for k in fields)+'\n' for r in rows)).encode()
   with zipfile.ZipFile(archive,'w') as z:
    for n,raw in contents.items():z.writestr(n,raw)
   packets=[]
   for r in rows:
    packets.append({'issuer_cik':r['cik'].zfill(10),'accession':r['adsh'],'issuer_name_as_filed':r['name'],'source_sub_rowid':r['rowid'],'source_sub_row_sha256':m.digest(m.encoded({k:r[k] for k in fields})),'source_url':f"https://www.sec.gov/Archives/edgar/data/{int(r['cik'])}/{r['adsh'].replace('-','')}/{r['adsh']}-index.html",'database_sha256':m.sha(db),'source_archive_sha256':m.sha(archive)})
   with patch.object(m,'read_pinned',return_value=({'packets':packets},m.PACKET_BYTES)):
    result=m.build(root,db,archive);self.assertEqual(5,len(result['records']));self.assertNotIn('PRIVATE ADDRESS',json.dumps(result));self.assertFalse(result['provider_requests_made'])
    dest=root/'done';m.run(dest,root=root,database=db,archive=archive);self.assertFalse((dest/'INCOMPLETE').exists());self.assertEqual(m.sha(dest/'references.json'),json.loads((dest/'COMPLETE.json').read_text())['references_sha256'])
    packets[0]['source_sub_row_sha256']='0'*64
    with self.assertRaisesRegex(ValueError,'correspondence'):m.build(root,db,archive)
 def test_failure_marker(self):
  with tempfile.TemporaryDirectory() as td,patch.object(m,'build',side_effect=ValueError('bad input')):
   out=Path(td)/'failure'
   with self.assertRaises(ValueError):m.run(out)
   self.assertTrue((out/'INCOMPLETE').exists());self.assertFalse((out/'COMPLETE.json').exists())
if __name__=='__main__':unittest.main()
