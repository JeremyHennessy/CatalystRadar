import copy,json,sqlite3,tempfile,unittest,zipfile
from pathlib import Path
from unittest.mock import patch
import ftd_balance_series as f
from financial_pair_candidates import sha

def rows():return [['20261015','000000002','B','12','SECOND','1'],['20261016','000000001','A','0','FIRST','2'],['20261015','000000001','A','999999999999999999999999999999','FIRST','2']]
class FTDBalanceSeriesTest(unittest.TestCase):
 def test_sorted_cusip_full_dates_preserved_not_summed(self):
  r=f.project(rows());self.assertEqual([x['cusip_as_reported'] for x in r['series']],['000000001','000000002']);a,b=r['series'];self.assertEqual(a['observations'][0]['outstanding_fail_shares_as_reported'],'999999999999999999999999999999');self.assertEqual(a['observations'][1]['outstanding_fail_shares_as_reported'],'0');self.assertEqual(b['observations'][1]['status'],'NO_SOURCE_ROW');self.assertIsNone(b['observations'][1]['outstanding_fail_shares_as_reported']);self.assertIsNone(r['cross_date_balance_sum']);self.assertFalse(r['execution_ready'])
 def test_source_specific_labels_and_rowhash_not_ticker_join(self):
  r=rows();r[2][2]='CHANGED';p=f.project(r);a=p['series'][0];self.assertEqual([x['symbol_as_reported'] for x in a['observations']],['CHANGED','A']);s=a['observations'][0]['source_row'];self.assertEqual(s['sqlite_rowid'],3);self.assertEqual(s['archive_line_1based'],4);self.assertEqual(s['full_six_field_canonical_sha256'],f.digest(f.canonical(r[2])));self.assertIsNone(a['issuer_cik'])
 def test_fixed_first_five_not_highest_balances(self):
  r=[['20261015',str(i).zfill(9),'S',str(i),'SECURITY','.'] for i in range(7,0,-1)];p=f.project(r);self.assertEqual([x['cusip_as_reported'] for x in p['series']],[str(i).zfill(9) for i in range(1,6)])
 def test_duplicates_invalid_dates_and_labels(self):
  for mutation in ('duplicate','date','quantity','cusip','control','shape'):
   r=copy.deepcopy(rows())
   if mutation=='duplicate':r.append(copy.deepcopy(r[0]))
   elif mutation=='date':r[0][0]='20261101'
   elif mutation=='quantity':r[0][3]='1.5'
   elif mutation=='cusip':r[0][1]='BAD'
   elif mutation=='control':r[0][2]='A\x00'
   else:r[0].pop()
   with self.subTest(mutation=mutation),self.assertRaises(ValueError):f.project(r)
 def test_no_prices_or_synthetic_missing_evidence(self):
  p=f.project(rows());text=json.dumps(p)
  self.assertNotIn('previous_day_price',text)
  for s in p['series']:
   for o in s['observations']:
    if o['status']=='NO_SOURCE_ROW':self.assertIsNone(o['source_row']);self.assertIsNone(o['symbol_as_reported'])
 def test_full_zip_db_pipeline_and_completion(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);db=root/'source.sqlite';archive=root/'source.zip';source=[['20261015',str(i).zfill(9),'X','1','SYNTHETIC','.'] for i in range(1,63158)]
   conn=sqlite3.connect(db);conn.execute('create table ftd ('+','.join(k+' TEXT' for k in f.FIELDS)+')');conn.executemany('insert into ftd values (?,?,?,?,?,?)',source);conn.commit();conn.close()
   body='SETTLEMENT DATE|CUSIP|SYMBOL|QUANTITY (FAILS)|DESCRIPTION|PRICE\n'+'\n'.join('|'.join(r) for r in source)+'\nTrailer record count 63157\nTrailer total quantity of shares 63157\n'
   with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED) as z:z.writestr('cnsfails202610b.txt',body)
   with patch.object(f,'ZIP_SHA',sha(archive)),patch.object(f,'DB_SHA',sha(db)):
    result=f.save(archive,db,root/'output');self.assertEqual(result['counts']['source_rows'],63157);self.assertEqual(result['counts']['selected_cusips'],5);self.assertFalse((root/'output/INCOMPLETE').exists());self.assertEqual(json.loads((root/'output/COMPLETE.json').read_text())['series_sha256'],sha(root/'output/series.json'))
   conn=sqlite3.connect(db);conn.execute("update ftd set previous_day_price='123' where rowid=1");conn.commit();conn.close()
   with patch.object(f,'ZIP_SHA',sha(archive)),patch.object(f,'DB_SHA',sha(db)):
    with self.assertRaises(ValueError):f.save(archive,db,root/'bad')
   self.assertTrue((root/'bad/INCOMPLETE').exists());self.assertFalse((root/'bad/COMPLETE.json').exists())
if __name__=='__main__':unittest.main()
