import csv,datetime,hashlib,io,json,sqlite3,tempfile,unittest,zipfile
from pathlib import Path
import sec_notes_data as p

class NotesTests(unittest.TestCase):
 def fixture(self,root,missing_tag=False,bad_dim=False,bad_date=False,missing_column=False,orphan=False):
  with zipfile.ZipFile(root/p.ARCHIVE,'w',zipfile.ZIP_DEFLATED) as z:
   for name in p.MEMBERS:
    if name in p.SCHEMAS:
     header=p.SCHEMAS[name].copy()
     if missing_column and name=='txt.tsv':header.remove('context')
     v={'adsh':'0000000001-26-000001','cik':'1','name':'EXAMPLE','form':'10-Q','filed':'20261030','tag':'ExampleTag','version':'example/2026','dimhash':'0x00000000','dimh':'0x00000000','ptag':'ExampleTag','pversion':'example/2026','ctag':'ExampleTag','cversion':'example/2026','value':'12.50','segments':'Segment=Example;','uom':'USD','context':'As filed context','lang':'en'}
     if name=='txt.tsv':v['value']='<script>untrusted text never rendered</script>'
     if missing_tag and name=='num.tsv':v['tag']='MissingTag'
     if bad_dim and name=='num.tsv':v['dimh']='missing'
     if bad_date and name=='sub.tsv':v['filed']='20261101'
     if orphan and name=='num.tsv':v['adsh']='0000000001-26-000002'
     b=io.StringIO();w=csv.writer(b,delimiter='\t');w.writerow(header);w.writerow([v.get(k,'') for k in header]);data=b.getvalue()
    else:data='source documentation'
    z.writestr(name,data)
  raw=(root/p.ARCHIVE).read_bytes();r={'path':p.ARCHIVE,'url':p.URL,'byte_count':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'local_verified_utc':(datetime.datetime.now(datetime.timezone.utc)-datetime.timedelta(seconds=1)).isoformat(),'retrieval_method':'PUBLIC_BROWSER_LINK_DOWNLOAD_NO_PRIVATE_CONTACT','http_status':None,'exact_download_utc':None};(root/'browser-receipt.json').write_text(json.dumps(r))
 def test_complete_persistence_context_and_public_allowlist(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);self.fixture(root);out=root/'out';s=p.ingest(root,out)
   self.assertFalse((out/'INCOMPLETE').exists());self.assertTrue(s['taxonomy_joins_complete'])
   with sqlite3.connect('file:'+str(out/'notes.sqlite')+'?mode=ro',uri=True) as db:
    for table,count in s['table_rows'].items():self.assertEqual(db.execute('SELECT COUNT(*) FROM '+table).fetchone()[0],count)
    self.assertEqual(db.execute('SELECT value,context,lang FROM notes_txt').fetchone(),('<script>untrusted text never rendered</script>','As filed context','en'))
    self.assertEqual(db.execute('SELECT segments FROM notes_dim').fetchone()[0],'Segment=Example;')
   self.assertNotIn('<script>',(out/'summary.json').read_text()+(out/'issuers.json').read_text())
 def test_missing_taxonomy_preserved_and_flagged(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);self.fixture(root,missing_tag=True);out=root/'out';s=p.ingest(root,out)
   self.assertFalse(s['taxonomy_joins_complete']);self.assertEqual(s['numeric_rows_missing_tag_definitions'],1);self.assertEqual(s['missing_tag_definition_keys'],1)
   with sqlite3.connect(out/'notes.sqlite') as db:
    self.assertEqual(db.execute('SELECT count(*) FROM notes_num').fetchone()[0],1);self.assertEqual(db.execute('SELECT reason FROM notes_validation_gaps').fetchone()[0],'MISSING_SOURCE_TAG_DEFINITION_NOT_QUALIFIED')
 def test_unacceptable_missing_context_identity_or_time_fails_closed(self):
  for flag in ['bad_dim','bad_date','missing_column','orphan']:
   with self.subTest(flag=flag),tempfile.TemporaryDirectory() as d:
    root=Path(d);self.fixture(root,**{flag:True});out=root/'out'
    with self.assertRaises(ValueError):p.ingest(root,out)
    self.assertTrue((out/'INCOMPLETE').exists());self.assertFalse((out/'summary.json').exists())
 def test_source_tamper(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);self.fixture(root);(root/p.ARCHIVE).write_bytes(b'changed')
   with self.assertRaises(ValueError):p.ingest(root,root/'out')
   self.assertFalse((root/'out').exists())
 def test_unknown_receipt_and_duplicate_keys(self):
  for extra in [',"private_header":"withheld"',',"http_status":200']:
   with tempfile.TemporaryDirectory() as d:
    root=Path(d);self.fixture(root);f=root/'browser-receipt.json';f.write_text(f.read_text()[:-1]+extra+'}')
    with self.assertRaises(ValueError):p.ingest(root,root/'out')
    self.assertFalse((root/'out').exists())
if __name__=='__main__':unittest.main()
