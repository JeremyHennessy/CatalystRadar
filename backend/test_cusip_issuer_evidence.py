import tempfile,sqlite3,unittest
from pathlib import Path
from unittest.mock import patch
import cusip_issuer_evidence as m
class EvidenceTests(unittest.TestCase):
 def fixture(self,p):
  f=p/'ftd.sqlite';h=p/'hold.sqlite'
  with sqlite3.connect(f) as d:
   d.execute('create table ftd (settlement_date,cusip,symbol,quantity,description,previous_day_price)')
   for date in ['20261016','20261019','20261021','20261026']:d.execute('insert into ftd values(?,?,?,?,?,?)',(date,m.CUSIP,'EXAMPLE','123','Example depositary class','9.00'))
  with sqlite3.connect(h) as d:
   d.execute('create table holdings_infotable (accession,sk,name,class,CUSIP,figi,value,shares)')
   d.execute('create table holdings_submission (ACCESSION_NUMBER,date,form,cik,period)')
   for i,cl in enumerate(['PUBLIC','Common Stock']):
    d.execute('insert into holdings_infotable values(?,?,?,?,?,?,?,?)',(str(i),'id','Example',cl,m.CUSIP,'','999','888'))
    d.execute('insert into holdings_submission values(?,?,?,?,?)',(str(i),'07-AUG-2026','13F-HR','999','30-JUN-2026'))
  return f,h
 def test_projection_omits_values_and_manager(self):
  with tempfile.TemporaryDirectory() as t:
   f,h=self.fixture(Path(t));a,b=m.selected_rows(f,h)
   self.assertEqual((len(a),len(b)),(4,2));self.assertEqual(b[1]['class_as_reported'],'Common Stock')
   self.assertNotIn('quantity',a[0]);self.assertNotIn('previous_day_price',a[0]);self.assertNotIn('shares',b[0]);self.assertNotIn('manager_cik',b[0])
 def test_wrong_cusip_not_ticker_join(self):
  with tempfile.TemporaryDirectory() as t:
   f,h=self.fixture(Path(t))
   with sqlite3.connect(f) as d:d.execute("update ftd set cusip='000000000'")
   with self.assertRaises(ValueError):m.selected_rows(f,h)
 def test_duplicate_submission_fails(self):
  with tempfile.TemporaryDirectory() as t:
   f,h=self.fixture(Path(t))
   with sqlite3.connect(h) as d:d.execute('insert into holdings_submission select * from holdings_submission limit 1')
   with self.assertRaises(ValueError):m.selected_rows(f,h)
 def test_source_pin_and_failed_completion(self):
  with self.assertRaises(ValueError):m.source_evidence(b'CUSIP 493267702')
  with tempfile.TemporaryDirectory() as t:
   out=Path(t)/'result'
   with patch.object(m,'build',side_effect=ValueError('wrong pin')):
    with self.assertRaises(ValueError):m.save('bad','bad','bad',out)
   self.assertTrue((out/'INCOMPLETE').exists());self.assertFalse((out/'COMPLETE.json').exists())
 def test_hash_binds_omitted_private_fields(self):
  self.assertNotEqual(m.rowhash(['a','1']),m.rowhash(['a','2']))
if __name__=='__main__':unittest.main()
