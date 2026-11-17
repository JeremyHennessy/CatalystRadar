import csv,datetime as dt,io,json,sqlite3,tempfile,unittest,zipfile
from pathlib import Path
import sec_formd_data as m
class FormDTests(unittest.TestCase):
 def fixture(self,root,change=None):
  acc='0000000001-26-000001';data={n:[] for n in m.ORDER}
  def row(label,**kw):
   n=m.PREFIX+label+'.tsv';d={k:'' for k in m.SCHEMAS[n]};d.update(ACCESSIONNUMBER=acc,**kw);data[n].append(d)
  row('FORMDSUBMISSION',FILING_DATE='01-JUL-2026',SUBMISSIONTYPE='D',TESTORLIVE='LIVE')
  row('ISSUERS',CIK='1',IS_PRIMARYISSUER_FLAG='YES',ENTITYNAME='Private fixture')
  row('OFFERING',ISAMENDMENT='false',TOTALOFFERINGAMOUNT='Indefinite',TOTALAMOUNTSOLD='12345678901234567890')
  if change:change(data)
  with zipfile.ZipFile(root/m.ARCHIVE,'w') as z:
   for n,rs in data.items():
    t=io.StringIO();w=csv.writer(t,delimiter='\t');w.writerow(m.SCHEMAS[n]);w.writerows([[r[k] for k in m.SCHEMAS[n]] for r in rs]);z.writestr(n,t.getvalue())
   for n in m.MEMBERS-set(m.ORDER):z.writestr(n,'fixture')
  p=root/m.ARCHIVE;r=dict(path=m.ARCHIVE,url=m.URL,byte_count=p.stat().st_size,sha256=m.digest(p),local_verified_utc=dt.datetime.now(dt.timezone.utc).isoformat(),retrieval_method='PUBLIC_BROWSER_LINK_DOWNLOAD_NO_PRIVATE_CONTACT',http_status=None,exact_download_utc=None);(root/'browser-receipt.json').write_text(json.dumps(r))
 def test_persist_all_tables_and_indefinite(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);self.fixture(root);out=root/'out';s=m.ingest(root,out)
   self.assertEqual(s['issuer_ciks_in_batch'],1);self.assertEqual(s['indefinite_total_offering_amount_rows'],1);self.assertFalse(s['simulation_enabled']);self.assertFalse((out/'INCOMPLETE').exists())
   with sqlite3.connect(out/'offerings.sqlite') as db:
    for table,count in s['table_rows'].items():self.assertEqual(db.execute('SELECT COUNT(*) FROM '+table).fetchone()[0],count)
    self.assertEqual(db.execute('SELECT TOTALAMOUNTSOLD FROM formd_offering').fetchone()[0],'12345678901234567890')
   self.assertNotIn('Private fixture',(out/'summary.json').read_text())
 def test_amendment_conflict_retained(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);self.fixture(root,lambda d:d[m.PREFIX+'OFFERING.tsv'][0].update(ISAMENDMENT='true'));s=m.ingest(root,root/'out');self.assertEqual(s['amendment_form_conflicts'],1);self.assertEqual(s['table_rows']['formd_offering'],1)
 def test_fail_closed(self):
  cases=[lambda d:d[m.PREFIX+'FORMDSUBMISSION.tsv'].append(d[m.PREFIX+'FORMDSUBMISSION.tsv'][0]),lambda d:d[m.PREFIX+'OFFERING.tsv'].clear(),lambda d:d[m.PREFIX+'ISSUERS.tsv'][0].update(IS_PRIMARYISSUER_FLAG='NO'),lambda d:d[m.PREFIX+'OFFERING.tsv'][0].update(ACCESSIONNUMBER='0000000002-26-000001'),lambda d:d[m.PREFIX+'FORMDSUBMISSION.tsv'][0].update(FILING_DATE='01-OCT-2026')]
  for case in cases:
   with self.subTest(case=case),tempfile.TemporaryDirectory() as td:
    root=Path(td);self.fixture(root,case)
    with self.assertRaises(ValueError):m.ingest(root,root/'out')
    self.assertFalse((root/'out/summary.json').exists());self.assertTrue((root/'out/INCOMPLETE').exists())
 def test_duplicate_receipt(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);self.fixture(root);p=root/'browser-receipt.json';p.write_text(p.read_text()[:-1]+',"http_status":200}')
   with self.assertRaises(ValueError):m.ingest(root,root/'out')
   self.assertFalse((root/'out').exists())
 def test_schema(self):
  name=m.PREFIX+'OFFERING.tsv'
  for h in [m.SCHEMAS[name][:-1],m.SCHEMAS[name]+['EXTRA']]:
   raw=io.BytesIO()
   with zipfile.ZipFile(raw,'w') as z:z.writestr(name,'\t'.join(h)+'\n')
   raw.seek(0)
   with zipfile.ZipFile(raw) as z:
    with self.assertRaises(ValueError):list(m.rows(z,name))
    with self.assertRaises(ValueError):m.inventory(z)
