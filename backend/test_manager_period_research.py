import copy,unittest,sqlite3,tempfile,zipfile,subprocess,sys,json
from pathlib import Path
from manager_period_research import project,cik,audit
from financial_pair_candidates import sha

def fixture():
 subs=[];covers=[];summaries=[]
 for n,(ci,period,form,amend,kind) in enumerate([('2','31-MAR-2026','13F-HR','',''),('2','30-JUN-2026','13F-HR/A','Y','RESTATEMENT'),('10','31-MAR-2026','13F-NT','N',''),('10','30-JUN-2026','13F-NT','N','')],1):
  acc=f'0000000001-26-{n:06d}'
  subs.append({'rowid':n,'ACCESSION_NUMBER':acc,'CIK':ci,'FILING_DATE':'01-AUG-2026','PERIODOFREPORT':period,'SUBMISSIONTYPE':form})
  covers.append({'rowid':n,'ACCESSION_NUMBER':acc,'REPORTCALENDARORQUARTER':period,'ISAMENDMENT':amend,'AMENDMENTNO':'1' if amend=='Y' else '','AMENDMENTTYPE':kind,'CONFDENIEDEXPIRED':'','REPORTTYPE':'13F NOTICE' if form=='13F-NT' else '13F HOLDINGS REPORT'})
  if form!='13F-NT':summaries.append({'rowid':n,'ACCESSION_NUMBER':acc,'ISCONFIDENTIALOMITTED':'Y'})
 return subs,covers,summaries
class ManagerResearchTest(unittest.TestCase):
 def test_pinned_readonly_audit_and_cli(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);db=root/'holdings.sqlite';archive=root/'source.zip';conn=sqlite3.connect(db)
   for table,rows in zip(('holdings_submission','holdings_coverpage','holdings_summarypage'),fixture()):
    columns=[k for k in rows[0] if k!='rowid'];conn.execute('CREATE TABLE '+table+' ('+','.join(k+' TEXT' for k in columns)+')')
    conn.executemany('INSERT INTO '+table+' VALUES ('+','.join('?' for _ in columns)+')',[[r[k] for k in columns] for r in rows])
   conn.commit();conn.close()
   with zipfile.ZipFile(archive,'w') as z:z.writestr('synthetic.txt','synthetic fixture only')
   dbhash=sha(db);archivehash=sha(archive);a=audit(db,dbhash,archive,archivehash,manager_cik='2')
   self.assertEqual(a['counts']['selected_filings'],2);self.assertEqual(sha(db),dbhash)
   result=subprocess.run([sys.executable,str(Path(__file__).with_name('manager_period_research.py')),'--database',str(db),'--database-sha',dbhash,'--archive',str(archive),'--archive-sha',archivehash,'--manager-cik','2'],capture_output=True,text=True,check=True,timeout=30)
   self.assertEqual(json.loads(result.stdout),a)
   with self.assertRaises(ValueError):audit(db,'0'*64,archive,archivehash)
 def test_numeric_order_full_history_and_no_flows(self):
  a=project(*fixture(),cohort_limit=1);self.assertEqual(a['managers'][0]['manager_cik'],'0000000002');self.assertEqual(a['counts']['selected_filings'],2);self.assertFalse(a['managers'][0]['positions_assessed']);self.assertFalse(a['training_ready'])
  rows=a['managers'][0]['filings'];self.assertEqual(rows[1]['amendment_type_as_filed'],'RESTATEMENT');self.assertFalse(rows[1]['amendment_reconciled'])
 def test_unknown_is_not_zero_positions_and_notice_context(self):
  a=project(*fixture(),manager_cik='999');self.assertFalse(a['requested_manager_present']);self.assertEqual(a['managers'],[])
  b=project(*fixture(),manager_cik='10');self.assertTrue(b['requested_manager_present']);self.assertIsNone(b['managers'][0]['filings'][0]['confidential_omitted_as_filed']);self.assertFalse(b['managers'][0]['filings'][0]['summary_record_present'])
 def test_conflict_preserved_not_reconciled(self):
  s,c,q=fixture();s[0]['SUBMISSIONTYPE']='13F-HR/A';a=project(s,c,q,manager_cik='2');self.assertTrue(a['managers'][0]['filings'][0]['form_cover_amendment_conflict'])
 def test_duplicate_join_identity_and_date_fail(self):
  original=fixture()
  for mode in ('duplicate','missing','period','date','rowid','category'):
   s,c,q=copy.deepcopy(original)
   if mode=='duplicate':s.append(copy.deepcopy(s[0]))
   elif mode=='missing':c.pop()
   elif mode=='period':c[0]['REPORTCALENDARORQUARTER']='31-DEC-2025'
   elif mode=='date':s[0]['FILING_DATE']='01-SEP-2026'
   elif mode=='rowid':s[0]['rowid']=True
   else:c[0]['REPORTTYPE']='private arbitrary text'
   with self.subTest(mode=mode),self.assertRaises(ValueError):project(s,c,q)
 def test_bounds_and_cik(self):
  for value in ('0','abc','-1','1;drop table',123):
   with self.assertRaises(ValueError):cik(value)
  for n in (0,11,True):
   with self.assertRaises(ValueError):project(*fixture(),cohort_limit=n)
 def test_deterministic_public_fields_no_name_values(self):
  a=project(*fixture());self.assertEqual(a,project(*fixture()));text=str(a)
  for field in ('FILINGMANAGER_NAME','TABLEVALUETOTAL','CUSIP','SSHPRNAMT'):self.assertNotIn("'"+field+"'",text)
if __name__=='__main__':unittest.main()
