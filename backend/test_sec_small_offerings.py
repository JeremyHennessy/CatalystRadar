import csv,datetime as dt,io,json,sqlite3,tempfile,unittest,zipfile
from pathlib import Path
import sec_small_offerings as m
class SmallOffersTests(unittest.TestCase):
 def fixtures(self,root,change=None):
  receipts=[]
  for kind in ['cf','rega']:
   acc='0000000001-26-000001';data={n:[] for n in m.SCHEMAS[kind]};sub={k:'' for k in m.SCHEMAS[kind][m.SUB[kind]]};sub['ACCESSION_NUMBER']=acc
   sub.update({'CIK':'1','SUBMISSION_TYPE':'C-W','FILING_DATE':'20260701'} if kind=='cf' else {'ISSUERCIK':'2','SUBMISSIONTYPE':'1-Z','FILING_DATE':'01-JUL-2026'});data[m.SUB[kind]].append(sub)
   if kind=='cf':
    n='2026Q3_cf/FORM_C_COISSUER_INFORMATION.tsv';r={k:'' for k in m.SCHEMAS[kind][n]};r.update(ACCESSION_NUMBER=acc,NAMEOFCOISSUER='Private fixture');data[n].append(r)
   if change:change(kind,data)
   p=root/f'2026q3_{kind}.zip'
   with zipfile.ZipFile(p,'w') as z:
    for n,rs in data.items():
     t=io.StringIO();w=csv.writer(t,delimiter='\t');w.writerow(m.SCHEMAS[kind][n]);w.writerows([[r[k] for k in m.SCHEMAS[kind][n]] for r in rs]);z.writestr(n,t.getvalue())
    for n in set(m.MEMBERS[kind])-set(data):z.writestr(n,'fixture')
   receipts.append(dict(path=p.name,url=m.URLS[kind],byte_count=p.stat().st_size,sha256=m.digest(p),local_verified_utc=dt.datetime.now(dt.timezone.utc).isoformat(),retrieval_method='PUBLIC_BROWSER_LINK_DOWNLOAD_NO_PRIVATE_CONTACT',http_status=None,exact_download_utc=None))
  (root/'browser-receipts.json').write_text(json.dumps(receipts))
 def test_all_tables_persist_and_lifecycle(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);self.fixtures(root);out=root/'out';s=m.ingest(root,out)
   self.assertEqual(len(s['table_rows']),22);self.assertEqual(s['datasets']['cf']['submission_types'],{'C-W':1});self.assertEqual(s['datasets']['rega']['submission_types'],{'1-Z':1});self.assertEqual(s['datasets']['cf']['coissuer_rows_without_cik'],1);self.assertFalse(s['simulation_enabled'])
   self.assertFalse((out/'INCOMPLETE').exists());self.assertNotIn('Private fixture',(out/'summary.json').read_text())
   with sqlite3.connect(out/'offerings.sqlite') as db:
    for table,count in s['table_rows'].items():self.assertEqual(db.execute('SELECT COUNT(*) FROM '+table).fetchone()[0],count)
 def test_failures_do_not_complete(self):
  def orphan(k,d):
   if k=='cf':d['2026Q3_cf/FORM_C_COISSUER_INFORMATION.tsv'][0]['ACCESSION_NUMBER']='0000000002-26-000001'
  def duplicate(k,d):d[m.SUB[k]].append(d[m.SUB[k]][0])
  def future(k,d):d[m.SUB[k]][0]['FILING_DATE']='20261001' if k=='cf' else '01-OCT-2026'
  def unsupported(k,d):d[m.SUB[k]][0]['SUBMISSION_TYPE' if k=='cf' else 'SUBMISSIONTYPE']='PRIVATE TEXT'
  for change in [orphan,duplicate,future,unsupported]:
   with self.subTest(change=change),tempfile.TemporaryDirectory() as td:
    root=Path(td);self.fixtures(root,change)
    with self.assertRaises(ValueError):m.ingest(root,root/'out')
    self.assertFalse((root/'out/summary.json').exists());self.assertTrue((root/'out/INCOMPLETE').exists())
 def test_receipt_inventory_and_duplicates(self):
  for mode in ['duplicate','missing','key']:
   with tempfile.TemporaryDirectory() as d:
    root=Path(d);self.fixtures(root);p=root/'browser-receipts.json';rs=json.loads(p.read_text())
    if mode=='duplicate':p.write_text(json.dumps([rs[0],rs[0]]))
    elif mode=='missing':p.write_text(json.dumps(rs[:1]))
    else:p.write_text(p.read_text().replace('"http_status": null','"http_status": 403,"http_status": null'))
    with self.assertRaises(ValueError):m.ingest(root,root/'out')
    self.assertFalse((root/'out').exists())
 def test_schemas(self):
  for kind in ['cf','rega']:
   name=m.SUB[kind]
   for header in [m.SCHEMAS[kind][name][:-1],m.SCHEMAS[kind][name]+['EXTRA']]:
    raw=io.BytesIO()
    with zipfile.ZipFile(raw,'w') as z:z.writestr(name,'\t'.join(header)+'\n')
    raw.seek(0)
    with zipfile.ZipFile(raw) as z:
     with self.assertRaises(ValueError):list(m.rows(z,kind,name))
     with self.assertRaises(ValueError):m.inventory(z,kind)
