import copy,json,sqlite3,tempfile,unittest,zipfile
from pathlib import Path
import insider_transaction_evidence as m
from sec_prepared_data import SCHEMAS
class InsiderEvidenceTests(unittest.TestCase):
 def row(self,**kw):
  r={k:'' for k in SCHEMAS['NONDERIV_TRANS.tsv']};r.update(ACCESSION_NUMBER='0000000001-26-000001',NONDERIV_TRANS_SK='1',TRANS_DATE='01-JUL-2026',TRANS_FORM_TYPE='4',TRANS_CODE='P',EQUITY_SWAP_INVOLVED='0',TRANS_SHARES='1.25',TRANS_PRICEPERSHARE='2.50',TRANS_ACQUIRED_DISP_CD='A');r.update(kw);return r
 def sub(self,**kw):
  s={k:'' for k in SCHEMAS['SUBMISSION.tsv']};s.update(ACCESSION_NUMBER='0000000001-26-000001',FILING_DATE='03-JUL-2026',DOCUMENT_TYPE='4',ISSUERCIK='1',AFF10B5ONE='false');s.update(kw);return s
 def test_code_scope_and_no_admission(self):
  for code,ad in [('P','A'),('S','D')]:
   v=m.classify(self.row(TRANS_CODE=code,TRANS_ACQUIRED_DISP_CD=ad),self.sub(),{})
   self.assertIn('or_private',v['reported_code_category']);self.assertFalse(v['open_market_trade_verified']);self.assertFalse(v['training_ready']);self.assertEqual(v['calendar_days_transaction_to_filing'],2)
 def test_contradictions_preserved(self):
  for code,ad in [('P','D'),('S','A')]:
   r=self.row(TRANS_CODE=code,TRANS_ACQUIRED_DISP_CD=ad);before=copy.deepcopy(r);v=m.classify(r,self.sub(),{});self.assertIn('PURCHASE_SALE_DIRECTION_CONTRADICTION',v['diagnostic_flags']);self.assertEqual(r,before)
 def test_amendment_plan_form_and_date(self):
  v=m.classify(self.row(TRANS_DATE='04-JUL-2026',TRANS_FORM_TYPE='5'),self.sub(DOCUMENT_TYPE='4/A',AFF10B5ONE='true'),{})
  self.assertEqual(v['calendar_days_transaction_to_filing'],-1);self.assertEqual(v['submission_plan_flag_status'],'REPORTED_TRUE')
  for f in ['AMENDMENT_NOT_RECONCILED','TRANSACTION_SUBMISSION_FORM_DIFFERENCE','TRANSACTION_DATE_AFTER_FILING_DATE']:self.assertIn(f,v['diagnostic_flags'])
 def test_footnotes_multi_missing_duplicate_ambiguous(self):
  acc=self.row()['ACCESSION_NUMBER'];notes={(acc,'F2'):[{'rowid':1,'source_row_sha256':'a'*64}],(acc,'F1'):[{'rowid':2},{'rowid':3}]}
  v=m.classify(self.row(TRANS_PRICEPERSHARE_FN='F2, F1, F3'),self.sub(),notes)
  self.assertEqual([x['id'] for x in v['footnote_links']],['F2','F1','F3']);self.assertEqual([x['status'] for x in v['footnote_links']],['RESOLVED','AMBIGUOUS','MISSING'])
  for f in ['FOOTNOTE_CONTEXT_REQUIRED','FOOTNOTE_AMBIGUOUS','FOOTNOTE_MISSING']:self.assertIn(f,v['diagnostic_flags'])
  for text in ['F1;F2','F1,F1','x','']:
   w=m.classify(self.row(TRANS_PRICEPERSHARE_FN=text),self.sub(),{})
   self.assertEqual('UNSUPPORTED_FOOTNOTE_REFERENCE' in w['diagnostic_flags'],bool(text))
 def test_numeric_zero_blank_invalid_and_exact(self):
  for val,status in [('', 'MISSING'),('0','ZERO'),('-2','NEGATIVE'),('NaN','INVALID'),('Infinity','INVALID'),('1,000','INVALID'),('123456789012345678901234567890.123','POSITIVE')]:self.assertEqual(m.numeric_status(val),status)
  v=m.classify(self.row(TRANS_SHARES='',TRANS_PRICEPERSHARE='0'),self.sub(),{});self.assertIn('TRANS_SHARES_MISSING',v['diagnostic_flags']);self.assertIn('TRANS_PRICEPERSHARE_ZERO',v['diagnostic_flags'])
 def test_date_strict_and_unknowns(self):
  for s in ['', '31-FEB-2026','1-JUL-2026','01-Jul-2026']:self.assertIsNone(m.date(s))
  v=m.classify(self.row(TRANS_CODE='?',TRANS_DATE='',EQUITY_SWAP_INVOLVED='',TRANS_ACQUIRED_DISP_CD=''),self.sub(AFF10B5ONE='?'),{})
  self.assertIsNone(v['calendar_days_transaction_to_filing']);self.assertEqual(v['reported_code_category'],'unknown');self.assertIn('UNKNOWN_SUBMISSION_PLAN_FLAG',v['diagnostic_flags'])
 def fixture(self,root,mutate=None):
  dbp=root/'fixture.sqlite';c=sqlite3.connect(dbp)
  for file in ['SUBMISSION.tsv','NONDERIV_TRANS.tsv','FOOTNOTES.tsv']:
   table='insider_'+file[:-4].lower();c.execute('CREATE TABLE '+table+' ('+','.join('"'+k+'" TEXT' for k in SCHEMAS[file])+')')
  s=self.sub();r=self.row(TRANS_PRICEPERSHARE_FN='F1');f={'ACCESSION_NUMBER':r['ACCESSION_NUMBER'],'FOOTNOTE_ID':'F1','FOOTNOTE_TXT':'Private owner context'}
  if mutate:mutate(s,r,f)
  for file,values in [('SUBMISSION.tsv',s),('NONDERIV_TRANS.tsv',r),('FOOTNOTES.tsv',f)]:c.execute('INSERT INTO insider_'+file[:-4].lower()+' VALUES ('+','.join('?' for _ in SCHEMAS[file])+')',[values[k] for k in SCHEMAS[file]])
  c.commit();c.close();zp=root/'fixture.zip'
  # Inventory guards test structural member set; source-to-DB derivation is separately audited.
  from sec_prepared_data import MEMBERS
  with zipfile.ZipFile(zp,'w') as z:
   for n in MEMBERS['insider']:z.writestr(n,'synthetic fixture')
  return dbp,zp
 def test_end_to_end_private_lineage_public_allowlist(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);db,z=self.fixture(root);s,rows=m.audit(db,m.sha(db),z,m.sha(z));self.assertEqual(s['counts']['transaction_rows'],1);self.assertEqual(s['reported_code_counts'],{'P':1});self.assertEqual(rows[0]['footnote_links'][0]['status'],'RESOLVED');self.assertNotIn('Private owner',json.dumps(rows));self.assertNotIn('2.50',json.dumps(s));self.assertNotIn('ISSUERCIK',json.dumps(s))
   out=root/'out';out.mkdir(mode=0o700);m.write_private(out/'INCOMPLETE',{});m.publish(out,s,rows);self.assertTrue((out/'COMPLETE.json').exists());self.assertFalse((out/'INCOMPLETE').exists())
 def test_hash_and_orphan_fail_closed(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);db,z=self.fixture(root)
   with self.assertRaises(ValueError):m.audit(db,'0'*64,z,m.sha(z))
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);db,z=self.fixture(root,lambda s,r,f:r.update(ACCESSION_NUMBER='0000000002-26-000002'))
   with self.assertRaises(ValueError):m.audit(db,m.sha(db),z,m.sha(z))
 def test_empty_duplicate_and_bad_schema_fail_closed(self):
  for mode in ['empty','duplicate','bad_schema','bad_key']:
   with self.subTest(mode=mode),tempfile.TemporaryDirectory() as td:
    root=Path(td);db,z=self.fixture(root);c=sqlite3.connect(db)
    if mode=='empty':c.execute('DELETE FROM insider_nonderiv_trans')
    elif mode=='duplicate':c.execute('INSERT INTO insider_nonderiv_trans SELECT * FROM insider_nonderiv_trans')
    elif mode=='bad_schema':c.execute('ALTER TABLE insider_nonderiv_trans ADD COLUMN unexpected TEXT')
    else:c.execute("UPDATE insider_nonderiv_trans SET NONDERIV_TRANS_SK=''")
    c.commit();c.close()
    with self.assertRaises(ValueError):m.audit(db,m.sha(db),z,m.sha(z))
 def test_plan_flag_does_not_change_code_or_infer_legal_lateness(self):
  for flag in ['1','true','0','false','']:
   v=m.classify(self.row(TRANS_DATE='03-JUL-2026'),self.sub(FILING_DATE='06-JUL-2026',AFF10B5ONE=flag),{})
   self.assertEqual(v['calendar_days_transaction_to_filing'],3)
   self.assertEqual(v['reported_code_category'],'open_market_or_private_purchase')
   self.assertFalse(v['economic_direction_verified']);self.assertFalse(v['training_ready'])

 def test_unknown_source_strings_do_not_reflect_into_public_summary(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td)
   def change(s,r,f):s['DOCUMENT_TYPE']='private@example.invalid';r['TRANS_CODE']='private@example.invalid'
   db,z=self.fixture(root,change);summary,rows=m.audit(db,m.sha(db),z,m.sha(z))
   self.assertEqual(summary['reported_code_counts'],{'UNKNOWN':1});self.assertEqual(summary['transaction_rows_by_submission_form'],{'UNKNOWN':1})
   self.assertNotIn('private@example.invalid',json.dumps(summary));self.assertEqual(rows[0]['transaction_fields_as_filed']['TRANS_CODE'],'private@example.invalid')
