import datetime as dt,hashlib,json,sqlite3,tempfile,unittest,zipfile
from pathlib import Path
from unittest.mock import patch
import sec_insider_history as m
from sec_prepared_data import MEMBERS
class History(unittest.TestCase):
 def fixture(self,root,change=None):
  acc='0000000001-26-000001';rows={n:[] for n in m.ORDER}
  for n in m.ORDER:
   d={c:'' for c in m.SCHEMAS[n]};d['ACCESSION_NUMBER']=acc
   for c in d:
    if c.endswith('_SK'):d[c]='1'
   if n=='SUBMISSION.tsv':d.update(FILING_DATE='01-Apr-2026',ISSUERCIK='0000000001',ISSUERNAME='Fixture',DOCUMENT_TYPE='4',AFF10B5ONE='false')
   if n=='FOOTNOTES.tsv':d.update(FOOTNOTE_ID='F1',FOOTNOTE_TXT='Private text')
   if n=='NONDERIV_TRANS.tsv':d.update(TRANS_CODE='P',TRANS_ACQUIRED_DISP_CD='D')
   rows[n].append(d)
  if change:change(rows)
  with zipfile.ZipFile(root/m.ARCHIVE,'w') as z:
   for n in MEMBERS['insider']:
    if n in rows:
     h=m.SCHEMAS[n];z.writestr(n,'\t'.join(h)+'\n'+''.join('\t'.join(d[c] for c in h)+'\n' for d in rows[n]))
    else:z.writestr(n,'fixture')
  p=root/m.ARCHIVE;r=dict(path=m.ARCHIVE,url=m.URL,byte_count=p.stat().st_size,sha256=m.digest(p),local_verified_utc=dt.datetime.now(dt.timezone.utc).isoformat(),retrieval_method='PUBLIC_BROWSER_LINK_DOWNLOAD_NO_PRIVATE_CONTACT',http_status=None,exact_download_utc=None)
  (root/'browser-receipt.json').write_text(json.dumps(r));return r
 def test_persist_all_fields_and_private_completion(self):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t);self.fixture(root);out=root/'out';s=m.ingest(root,out)
   with sqlite3.connect(out/'insider.sqlite') as db:
    for table,n in s['table_rows'].items():self.assertEqual(db.execute('SELECT COUNT(*) FROM '+table).fetchone()[0],1)
    self.assertEqual(db.execute('SELECT FOOTNOTE_TXT FROM insider_footnotes').fetchone()[0],'Private text')
   self.assertFalse((out/'INCOMPLETE').exists());self.assertEqual(s['nonderivative_code_direction'],{'P:D':1})
   for p in out.iterdir():self.assertEqual(p.stat().st_mode&0o777,0o600)
   self.assertNotIn('Private text',json.dumps(s));self.assertTrue((out/'COMPLETE.json').exists())
 def test_invalid_source_rows_leave_incomplete(self):
  for mutate in [lambda r:r['SUBMISSION.tsv'][0].update(FILING_DATE='01-Jul-2026'),lambda r:r['FOOTNOTES.tsv'].append(r['FOOTNOTES.tsv'][0]),lambda r:r['REPORTINGOWNER.tsv'][0].update(ACCESSION_NUMBER='0000000002-26-000001')]:
   with self.subTest(mutate=mutate),tempfile.TemporaryDirectory() as t:
    root=Path(t);self.fixture(root,mutate);out=root/'out'
    with self.assertRaises(ValueError):m.ingest(root,out)
    self.assertTrue((out/'INCOMPLETE').exists());self.assertFalse((out/'COMPLETE.json').exists())
 def test_hash_receipt_and_schema_rejections(self):
  for mode in ['hash','duplicate','nonfinite','schema']:
   with self.subTest(mode=mode),tempfile.TemporaryDirectory() as t:
    root=Path(t);r=self.fixture(root);p=root/'browser-receipt.json'
    if mode=='hash':r['sha256']='0'*64;p.write_text(json.dumps(r))
    elif mode=='duplicate':p.write_text(p.read_text()[:-1]+',"path":"bad"}')
    elif mode=='nonfinite':p.write_text(p.read_text()[:-1]+',"unused":NaN}')
    else:r['url']='https://invalid.example';p.write_text(json.dumps(r))
    with self.assertRaises(ValueError):m.ingest(root,root/'out')
 def test_missing_header_and_existing_output_reject(self):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t);r=self.fixture(root);archive=root/m.ARCHIVE
   with zipfile.ZipFile(archive) as z:members={n:z.read(n) for n in z.namelist()}
   members['SUBMISSION.tsv']=members['SUBMISSION.tsv'].replace(b'ISSUERCIK',b'UNKNOWN_CIK')
   with zipfile.ZipFile(archive,'w') as z:
    for n,b in members.items():z.writestr(n,b)
   r.update(byte_count=archive.stat().st_size,sha256=m.digest(archive));(root/'browser-receipt.json').write_text(json.dumps(r))
   out=root/'out'
   with self.assertRaises(ValueError):m.ingest(root,out)
   self.assertTrue((out/'INCOMPLETE').exists())
   with self.assertRaises(ValueError):m.ingest(root,out)
 def test_oversized_receipt_rejects_before_output(self):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t);self.fixture(root);(root/'browser-receipt.json').write_bytes(b' '*100_001)
   with self.assertRaises(ValueError):m.ingest(root,root/'out')
   self.assertFalse((root/'out').exists())
 def test_unknown_categories_do_not_leak_source_strings(self):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t)
   def change(rows):
    rows['SUBMISSION.tsv'][0]['DOCUMENT_TYPE']='private@example.invalid'
    rows['NONDERIV_TRANS.tsv'][0].update(TRANS_CODE='private@example.invalid',TRANS_ACQUIRED_DISP_CD='private@example.invalid')
   self.fixture(root,change);out=root/'out';s=m.ingest(root,out)
   self.assertNotIn('private@example.invalid',json.dumps(s));self.assertEqual(s['submission_forms'],{'UNKNOWN':1});self.assertEqual(s['nonderivative_code_direction'],{'UNKNOWN:UNKNOWN':1})
   with sqlite3.connect(out/'insider.sqlite') as db:self.assertEqual(db.execute('SELECT DOCUMENT_TYPE FROM insider_submission').fetchone()[0],'private@example.invalid')
 def test_summary_write_failure_remains_incomplete(self):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t);self.fixture(root);out=root/'out'
   with patch.object(m,'save',side_effect=OSError('injected')):
    with self.assertRaises(OSError):m.ingest(root,out)
   self.assertTrue((out/'INCOMPLETE').exists());self.assertFalse((out/'COMPLETE.json').exists())
if __name__=='__main__':unittest.main()
