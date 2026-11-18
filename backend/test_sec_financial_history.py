import csv,datetime as dt,io,json,sqlite3,tempfile,unittest,zipfile
from pathlib import Path
import sec_financial_history as m
class FinancialHistoryTests(unittest.TestCase):
 def fixture(self,root,change=None):
  acc='0000000001-26-000001';data={n:[] for n in m.ORDER}
  def row(n,**kw):
   d={k:'' for k in m.SCHEMAS[n]};d.update(**kw);data[n].append(d)
  row('sub.txt',adsh=acc,cik='1',filed='20260401',fp='Q1',fy='2026')
  row('tag.txt',tag='FixtureRevenue',version='2026',custom='1')
  row('pre.txt',adsh=acc,tag='FixtureRevenue',version='2026')
  row('num.txt',adsh=acc,tag='FixtureRevenue',version='2026',value='12345678901234567890.123',uom='USD',ddate='20260331',qtrs='1',segments='segment=fixture',coreg='Subsidiary fixture',footnote='Private footnote')
  if change:change(data)
  p=root/m.ARCHIVE
  with zipfile.ZipFile(p,'w') as z:
   for n,rs in data.items():
    stream=io.StringIO();w=csv.writer(stream,delimiter='\t');w.writerow(m.SCHEMAS[n]);w.writerows([[r[k] for k in m.SCHEMAS[n]] for r in rs]);z.writestr(n,stream.getvalue())
   z.writestr('readme.htm','fixture')
  r=dict(path=p.name,url=m.URL,byte_count=p.stat().st_size,sha256=m.digest(p),local_verified_utc=dt.datetime.now(dt.timezone.utc).isoformat(),retrieval_method='PUBLIC_BROWSER_LINK_DOWNLOAD_NO_PRIVATE_CONTACT',http_status=None,exact_download_utc=None);(root/'browser-receipt.json').write_text(json.dumps(r))
 def test_exact_context_persisted(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);self.fixture(root);out=root/'out';s=m.ingest(root,out);self.assertTrue(s['taxonomy_joins_complete']);self.assertFalse(s['simulation_enabled']);self.assertFalse((out/'INCOMPLETE').exists())
   with sqlite3.connect(out/'financial.sqlite') as db:
    for t,n in s['table_rows'].items():self.assertEqual(db.execute('SELECT COUNT(*) FROM '+t).fetchone()[0],n)
    self.assertEqual(db.execute('SELECT value,uom,ddate,qtrs,segments,coreg FROM financial_num').fetchone(),('12345678901234567890.123','USD','20260331','1','segment=fixture','Subsidiary fixture'))
   self.assertNotIn('Private footnote',(out/'summary.json').read_text())
 def test_missing_taxonomy_preserved(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);self.fixture(root,lambda d:d['tag.txt'].clear());s=m.ingest(root,root/'out');self.assertFalse(s['taxonomy_joins_complete']);self.assertEqual(s['rows_missing_tag_definitions'],2);self.assertEqual(s['missing_tag_definition_keys'],1);self.assertEqual(s['table_rows']['financial_num'],1)
 def test_fail_closed(self):
  cases=[lambda d:d['sub.txt'].append(d['sub.txt'][0]),lambda d:d['num.txt'][0].update(adsh='0000000002-26-000001'),lambda d:d['sub.txt'][0].update(filed='20260701'),lambda d:d['tag.txt'].append(d['tag.txt'][0]),lambda d:d['num.txt'][0].update(value='NaN')]
  for change in cases:
   with self.subTest(change=change),tempfile.TemporaryDirectory() as td:
    root=Path(td);self.fixture(root,change)
    with self.assertRaises(ValueError):m.ingest(root,root/'out')
    self.assertFalse((root/'out/summary.json').exists());self.assertTrue((root/'out/INCOMPLETE').exists())
 def test_receipt_integrity(self):
  for mode in ['duplicate','hash']:
   with tempfile.TemporaryDirectory() as td:
    root=Path(td);self.fixture(root);p=root/'browser-receipt.json';raw=p.read_text();raw=raw[:-1]+',"http_status":200}' if mode=='duplicate' else raw.replace(m.digest(root/m.ARCHIVE),'0'*64);p.write_text(raw)
    with self.assertRaises(ValueError):m.ingest(root,root/'out')
    self.assertFalse((root/'out').exists())

 def q1_fixture(self,root,filed='20260101'):
  self.fixture(root,lambda d:d['sub.txt'][0].update(filed=filed))
  old=root/m.ARCHIVE;new=root/'2026q1.zip';old.rename(new)
  p=root/'browser-receipt.json';r=json.loads(p.read_text());r.update(path=new.name,url=m.URL.replace('2026q2','2026q1'));p.write_text(json.dumps(r))
 def test_explicit_q1_and_retained_fiscal_context(self):
  for filed in ['20260101','20260331']:
   with tempfile.TemporaryDirectory() as d:
    root=Path(d);self.q1_fixture(root,filed);s=m.ingest(root,root/'out','2026q1')
    self.assertEqual(s['filing_date_min'],filed[:4]+'-'+filed[4:6]+'-'+filed[6:])
    self.assertEqual(s['status'],'HISTORICAL_FINANCIAL_Q1_NOT_COMPARABLE_FACTS')
    with sqlite3.connect(root/'out/financial.sqlite') as db:
     self.assertEqual(db.execute('SELECT ddate,segments,coreg FROM financial_num').fetchone(),('20260331','segment=fixture','Subsidiary fixture'))
 def test_q1_outside_quarter_rejected(self):
  for filed in ['20251231','20260401']:
   with tempfile.TemporaryDirectory() as d:
    root=Path(d);self.q1_fixture(root,filed)
    with self.assertRaises(ValueError):m.ingest(root,root/'out','2026q1')
    self.assertFalse((root/'out/summary.json').exists())
 def test_quarter_receipt_mismatch_and_unknown_rejected(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);self.q1_fixture(root)
   for q in ['2026q2','2025q1','2026q3','2026Q1']:
    with self.assertRaises(ValueError):m.ingest(root,root/'out',q)
    self.assertFalse((root/'out').exists())

 def q4_fixture(self,root,filed):
  self.fixture(root,lambda d:d['sub.txt'][0].update(filed=filed))
  (root/m.ARCHIVE).rename(root/'2025q4.zip');p=root/'browser-receipt.json';r=json.loads(p.read_text());r.update(path='2025q4.zip',url=m.URL.replace('2026q2','2025q4'));p.write_text(json.dumps(r))
 def test_q4_boundaries_and_year_label(self):
  for filed in ['20251001','20251231']:
   with tempfile.TemporaryDirectory() as d:
    root=Path(d);self.q4_fixture(root,filed);s=m.ingest(root,root/'out','2025q4')
    self.assertEqual(s['status'],'HISTORICAL_FINANCIAL_Q4_NOT_COMPARABLE_FACTS')
    self.assertTrue(s['limitations'][0].startswith('Q4 2025 filing-date batch'))
    self.assertEqual(s['table_rows']['financial_num'],1)
 def test_q4_outside_boundaries_and_wrong_receipt(self):
  for filed in ['20250930','20260101']:
   with tempfile.TemporaryDirectory() as d:
    root=Path(d);self.q4_fixture(root,filed)
    with self.assertRaises(ValueError):m.ingest(root,root/'out','2025q4')
    self.assertFalse((root/'out/summary.json').exists())
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);self.fixture(root)
   with self.assertRaises(ValueError):m.ingest(root,root/'out','2025q4')
   self.assertFalse((root/'out').exists())
