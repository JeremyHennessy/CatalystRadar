import hashlib,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import insider_issuer_extension as m
import test_sec_insider_history as fixture
from sec_insider_history import ingest
class Extension(unittest.TestCase):
 def test_association_keeps_names_placeholders_and_dates(self):
  rows=[('0000000001-26-000001','1','A <text>','NONE','01-Apr-2026'),('0000000001-26-000002','0000000001','Other name','N/A','30-Jun-2026')]
  x=m.build(rows)[0];self.assertEqual(x['cik'],'0000000001');s=x['sources'][0];self.assertEqual(s['names'],['A <text>','Other name']);self.assertEqual(s['reported_tickers'],['N/A','NONE']);self.assertEqual(s['submissions'],2)
 def test_invalid_identity_date_duplicate_control_text(self):
  row=('0000000001-26-000001','1','Name','X','01-Apr-2026')
  for rows in [[row,row],[row[:1]+('0',)+row[2:]],[row[:4]+('01-Jul-2026',)],[row[:2]+('bad\nname',)+row[3:]],[]]:
   with self.assertRaises(ValueError):m.build(rows)
 def test_end_to_end_and_failure_markers(self):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t);fixture.History().fixture(root);dbdir=root/'db';s=ingest(root,dbdir)
   c={'database':str(dbdir/'insider.sqlite'),'database_sha256':s['database_sha256'],'archive':str(root/m.ARCHIVE),'archive_sha256':s['source']['sha256'],'baseline':'unused','completed_ingest':str(dbdir)}
   with patch.object(m,'baseline',return_value={'0000000002'}):
    out=root/'out';v=m.run(c,out);self.assertEqual(v['combined_issuer_ciks'],2);self.assertEqual(v['added_issuer_coverage'],1);self.assertFalse((out/'INCOMPLETE').exists());self.assertTrue((out/'COMPLETE.json').exists());self.assertNotIn('Private text',(out/'issuers.json').read_text())
    (dbdir/'INCOMPLETE').write_text('fail')
    with self.assertRaises(ValueError):m.run(c,root/'fail')
    self.assertTrue((root/'fail'/'INCOMPLETE').exists());self.assertFalse((root/'fail'/'COMPLETE.json').exists())
 def test_pinned_baseline_rejects_changed_bytes(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t)/'base';p.write_text('[]')
   with self.assertRaises(ValueError):m.baseline(p)
 def test_strict_json(self):
  for raw in ['{"a":1,"a":2}','{"a":NaN}']:
   with tempfile.TemporaryDirectory() as t:
    p=Path(t)/'j';p.write_text(raw)
    with self.assertRaises(ValueError):m.read_json(p,100)
if __name__=='__main__':unittest.main()
