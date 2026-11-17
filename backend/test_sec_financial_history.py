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
