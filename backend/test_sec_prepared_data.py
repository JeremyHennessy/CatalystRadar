import io,zipfile,unittest
from unittest.mock import patch
import sec_prepared_data as p

def archive(items):
 b=io.BytesIO()
 with zipfile.ZipFile(b,'w',zipfile.ZIP_DEFLATED) as z:
  for name,data in items:z.writestr(name,data)
 b.seek(0);return zipfile.ZipFile(b)

class PreparedTests(unittest.TestCase):
 def ftd(self,row='20261015|123456789|EX|10|EXAMPLE|.',trail='Trailer record count 1\nTrailer total quantity of shares 10\n'):
  return archive([('cnsfails202610b.txt','SETTLEMENT DATE|CUSIP|SYMBOL|QUANTITY (FAILS)|DESCRIPTION|PRICE\n'+row+'\n'+trail)])
 def test_ftd_valid_missing_price_and_day15(self):
  with self.ftd() as z:
   rows,total=p.ftd_rows(z);self.assertEqual(len(rows),1);self.assertEqual(total,10);self.assertEqual(rows[0][-1],'.')
 def test_source_missing_or_long_symbol_preserved(self):
  for symbol in ['', 'C847PAIROFF']:
   with self.ftd(row=f'20261015|123456789|{symbol}|10|EXAMPLE|.') as z:
    rows,total=p.ftd_rows(z);self.assertEqual(rows[0][2],symbol)
 def test_ftd_trailer_mismatch(self):
  with self.ftd(trail='Trailer record count 2\nTrailer total quantity of shares 10\n') as z:
   with self.assertRaises(ValueError):p.ftd_rows(z)
 def test_ftd_duplicate_and_bad_date(self):
  for row in ['20261101|123456789|EX|10|EXAMPLE|.','20261015|123456789|EX|10|EXAMPLE|.\n20261015|123456789|EX|10|EXAMPLE|.']:
   with self.ftd(row=row) as z:
    with self.assertRaises(ValueError):p.ftd_rows(z)
 def test_ftd_nonfinite(self):
  with self.ftd(row='20261015|123456789|EX|10|EXAMPLE|NaN') as z:
   with self.assertRaises(ValueError):p.ftd_rows(z)
 def test_tsv_quoted_tab_and_quotes_preserved(self):
  with patch.dict(p.SCHEMAS,{'num.txt':['adsh','value','footnote']}),archive([('num.txt','adsh\tvalue\tfootnote\n0000000001-26-000001\t2\t"Quoted\ttab and ""words"""\n')]) as z:
   rows=list(p.tab_rows(z,'num.txt'));self.assertEqual(rows[1][-1],'Quoted\ttab and "words"')
 def test_tsv_bad_width_and_duplicate_header(self):
  for data in ['a\ta\n1\t2\n','a\tb\n1\n','a\tb\n1\t"unclosed\n']:
   with patch.dict(p.SCHEMAS,{'x.tsv':['a','b']}),archive([('x.tsv',data)]) as z:
    with self.assertRaises((ValueError,p.csv.Error)):list(p.tab_rows(z,'x.tsv'))
 def test_inventory_rejects_extra_and_path(self):
  for name in ['../cnsfails202610b.txt','extra.txt']:
   with archive([('cnsfails202610b.txt','x'),(name,'y')]) as z:
    with self.assertRaises(ValueError):p.inventory(z,'ftd')
 def test_inventory_bound(self):
  with archive([('cnsfails202610b.txt','x')]) as z:
   z.infolist()[0].file_size=1_200_000_001
   with self.assertRaises(ValueError):p.inventory(z,'ftd')
 def test_finite_text_no_rounding(self):
  p.finite_number('12345678901234567890123456789.12345')
  for value in ['NaN','Infinity','invalid','1'*101]:
   with self.assertRaises(ValueError):p.finite_number(value)


class FullIngestTests(unittest.TestCase):
 def fixture(self,root,omit_segments=False):
  import datetime,hashlib,json,csv
  records=[]
  for filename,(kind,url) in p.SOURCES.items():
   with zipfile.ZipFile(root/filename,'w',zipfile.ZIP_DEFLATED) as z:
    for name in p.MEMBERS[kind]:
     if kind=='ftd':
      data='SETTLEMENT DATE|CUSIP|SYMBOL|QUANTITY (FAILS)|DESCRIPTION|PRICE\n20261015|123456789|EX|10|EXAMPLE|.\nTrailer record count 1\nTrailer total quantity of shares 10\n'
     elif name.endswith(('.txt','.tsv')):
      header=p.SCHEMAS[name].copy()
      if name=='num.txt' and omit_segments:header.remove('segments')
      values={'adsh':'0000000001-26-000001','ACCESSION_NUMBER':'0000000001-26-000002','cik':'1','ISSUERCIK':'1','name':'EXAMPLE','ISSUERNAME':'EXAMPLE','ISSUERTRADINGSYMBOL':'EX','form':'10-Q','DOCUMENT_TYPE':'4','filed':'20260805','FILING_DATE':'31-JUL-2026','value':'12.00','uom':'USD','segments':'Segment=A;','RPTOWNERNAME':'PRIVATE_OWNER','OWNERSIGNATURENAME':'PRIVATE_SIGNATURE'}
      out=io.StringIO();w=csv.writer(out,delimiter='\t');w.writerow(header);w.writerow([values.get(k,'') for k in header]);data=out.getvalue()
     else:data='documentation'
     z.writestr(name,data)
   raw=(root/filename).read_bytes();records.append({'path':filename,'url':url,'byte_count':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'local_verified_utc':(datetime.datetime.now(datetime.timezone.utc)-datetime.timedelta(seconds=1)).isoformat(),'retrieval_method':'PUBLIC_BROWSER_LINK_DOWNLOAD_NO_PRIVATE_CONTACT','http_status':None,'exact_download_utc':None})
  (root/'browser-receipts.json').write_text(json.dumps(records))
 def test_full_ingest_persists_every_table_and_allows_only_issuer_metadata(self):
  import tempfile,sqlite3,json
  from pathlib import Path
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);self.fixture(root);out=root/'out';s=p.ingest(root,out)
   self.assertFalse((out/'INCOMPLETE').exists())
   with sqlite3.connect('file:'+str(out/'prepared.sqlite')+'?mode=ro',uri=True) as db:
    for table,count in s['table_rows'].items():self.assertEqual(db.execute('SELECT COUNT(*) FROM '+table).fetchone()[0],count)
    self.assertEqual(db.execute('SELECT COUNT(*) FROM ftd').fetchone()[0],1)
    self.assertEqual(db.execute('SELECT segments,uom,value FROM financial_num').fetchone(),('Segment=A;','USD','12.00'))
   public=(out/'summary.json').read_text()+(out/'issuers.json').read_text()
   self.assertNotIn('PRIVATE_OWNER',public);self.assertNotIn('PRIVATE_SIGNATURE',public)
   self.assertEqual(s['issuer_counts']['union'],1)
 def test_missing_semantic_column_marks_incomplete(self):
  import tempfile
  from pathlib import Path
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);self.fixture(root,omit_segments=True);out=root/'out'
   with self.assertRaises(ValueError):p.ingest(root,out)
   self.assertTrue((out/'INCOMPLETE').exists());self.assertFalse((out/'summary.json').exists())

if __name__=='__main__':unittest.main()
