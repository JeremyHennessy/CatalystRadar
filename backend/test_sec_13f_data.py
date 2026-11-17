import csv,datetime as dt,hashlib,io,json,sqlite3,tempfile,unittest,zipfile
from pathlib import Path
import sec_13f_data as m
class HoldingsTests(unittest.TestCase):
 def fixture(self,root,change=None):
  acc='0000000001-26-000001';data={n:[] for n in m.ORDER}
  def row(n,**kw):
   d={k:'' for k in m.SCHEMAS[n]};d.update(ACCESSION_NUMBER=acc,**kw);data[n].append(d)
  row('SUBMISSION.tsv',CIK='01',FILING_DATE='01-JUN-2026',SUBMISSIONTYPE='13F-HR',PERIODOFREPORT='31-DEC-2001')
  row('COVERPAGE.tsv',REPORTCALENDARORQUARTER='31-DEC-2001',ISAMENDMENT='Y',AMENDMENTTYPE='NEW HOLDINGS')
  row('SIGNATURE.tsv');row('SUMMARYPAGE.tsv');row('INFOTABLE.tsv',INFOTABLE_SK='1',NAMEOFISSUER='Fixture',CUSIP='123456789',VALUE='1234567890123456',SSHPRNAMT='1',VOTING_AUTH_SOLE='1',VOTING_AUTH_SHARED='0',VOTING_AUTH_NONE='0')
  if change:change(data)
  with zipfile.ZipFile(root/m.ARCHIVE,'w') as z:
   for n,rs in data.items():
    stream=io.StringIO();w=csv.writer(stream,delimiter='\t');w.writerow(m.SCHEMAS[n]);w.writerows([[r[k] for k in m.SCHEMAS[n]] for r in rs]);z.writestr(n,stream.getvalue())
   z.writestr('FORM13F_metadata.json','{}');z.writestr('FORM13F_readme.htm','fixture')
  p=root/m.ARCHIVE;r=dict(path=m.ARCHIVE,url=m.URL,byte_count=p.stat().st_size,sha256=m.digest(p),local_verified_utc=dt.datetime.now(dt.timezone.utc).isoformat(),retrieval_method='PUBLIC_BROWSER_LINK_DOWNLOAD_NO_PRIVATE_CONTACT',http_status=None,exact_download_utc=None);(root/'browser-receipt.json').write_text(json.dumps(r))
 def test_full_persist_reopen_and_context(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);self.fixture(root);out=root/'out';s=m.ingest(root,out)
   self.assertEqual(s['filing_manager_ciks'],1);self.assertEqual(s['report_period_min'],'2001-12-31');self.assertEqual(s['amendment_form_cover_conflicts'],1)
   self.assertFalse((out/'INCOMPLETE').exists());self.assertFalse(s['simulation_enabled']);self.assertEqual(s['orders_created'],0)
   with sqlite3.connect('file:'+str(out/'holdings.sqlite')+'?mode=ro',uri=True) as db:
    for table,count in s['table_rows'].items():self.assertEqual(db.execute('SELECT COUNT(*) FROM '+table).fetchone()[0],count)
    self.assertEqual(db.execute('SELECT VALUE FROM holdings_infotable').fetchone()[0],'1234567890123456')
   self.assertNotIn('Fixture',(out/'summary.json').read_text())
 def test_invalid_cases_fail_without_completion(self):
  cases=[lambda d:d['COVERPAGE.tsv'][0].update(AMENDMENTTYPE='unexpected private text'),lambda d:d['SUBMISSION.tsv'].append(d['SUBMISSION.tsv'][0]),lambda d:d['INFOTABLE.tsv'][0].update(ACCESSION_NUMBER='0000000002-26-000001'),lambda d:d['COVERPAGE.tsv'][0].update(REPORTCALENDARORQUARTER='30-JUN-2026'),lambda d:d['SUBMISSION.tsv'][0].update(FILING_DATE='01-SEP-2026'),lambda d:d['SIGNATURE.tsv'].clear()]
  for case in cases:
   with self.subTest(case=case),tempfile.TemporaryDirectory() as td:
    root=Path(td);self.fixture(root,case)
    with self.assertRaises(ValueError):m.ingest(root,root/'out')
    self.assertFalse((root/'out/summary.json').exists());self.assertTrue((root/'out/INCOMPLETE').exists())
 def test_schema_and_inventory(self):
  for header in [m.SCHEMAS['INFOTABLE.tsv'][:-1],m.SCHEMAS['INFOTABLE.tsv']+['EXTRA']]:
   stream=io.BytesIO()
   with zipfile.ZipFile(stream,'w') as z:z.writestr('INFOTABLE.tsv','\t'.join(header)+'\n')
   stream.seek(0)
   with zipfile.ZipFile(stream) as z:
    with self.assertRaises(ValueError):list(m.rows(z,'INFOTABLE.tsv'))
    with self.assertRaises(ValueError):m.inventory(z)
 def test_duplicate_receipt_and_bad_hash(self):
  for duplicate in [True,False]:
   with tempfile.TemporaryDirectory() as d:
    root=Path(d);self.fixture(root);p=root/'browser-receipt.json';s=p.read_text()
    if duplicate:s=s[:-1]+',"http_status":200}'
    else:s=s.replace(m.digest(root/m.ARCHIVE),'0'*64)
    p.write_text(s)
    with self.assertRaises(ValueError):m.ingest(root,root/'out')
    self.assertFalse((root/'out').exists())
