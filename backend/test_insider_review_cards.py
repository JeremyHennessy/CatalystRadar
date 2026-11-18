import copy,json,tempfile,unittest,sqlite3
from pathlib import Path
import insider_review_cards as m
import test_insider_transaction_evidence as fixtures

class ReviewCardTests(unittest.TestCase):
 def fixture(self,root,code='P',ad='D',form='4/A'):
  helper=fixtures.InsiderEvidenceTests()
  def mutate(s,r,f):
   s.update(ISSUERCIK='0000820318',ISSUERNAME='<script>issuer</script>',ISSUERTRADINGSYMBOL='HIST',DOCUMENT_TYPE=form,PERIOD_OF_REPORT='01-JUL-2026')
   r.update(TRANS_CODE=code,TRANS_ACQUIRED_DISP_CD=ad)
  db,z=helper.fixture(root,mutate);summary,rows=m.source_audit(db,m.sha(db),z,m.sha(z));c=sqlite3.connect(db);c.row_factory=sqlite3.Row;subs={r['ACCESSION_NUMBER']:dict(r) for r in c.execute('SELECT rowid,* FROM insider_submission')};c.close();return rows,subs,db,z
 def test_projection_privacy_conflicts_amendments_and_no_admission(self):
  with tempfile.TemporaryDirectory() as td:
   rows,subs,_,_=self.fixture(Path(td));cards,private=m.project('2026q3',rows,subs);c=cards[0]
   self.assertEqual(c['issuer_cik'],'0000820318');self.assertEqual(c['reported_code_counts'],{'P':1});self.assertEqual(c['diagnostic_row_counts']['PURCHASE_SALE_DIRECTION_CONTRADICTION'],1);self.assertFalse(c['amendment_reconciled']);self.assertFalse(c['training_ready']);self.assertFalse(c['original_reviewed']);self.assertIsNone(c['first_public_utc'])
   self.assertEqual(c['issuer_name_as_filed'],'<script>issuer</script>') # consumer must render as text
   for secret in ['Private owner context','2.50','1.25','FOOTNOTE_TXT','TRANS_PRICEPERSHARE','transaction_fields_as_filed']:self.assertNotIn(secret,json.dumps(c))
   self.assertEqual(private,rows)
 def test_identity_hash_join_duplicate_and_date_fail_closed(self):
  with tempfile.TemporaryDirectory() as td:
   rows,subs,_,_=self.fixture(Path(td))
   for mutate in [lambda r:r['submission_as_filed'].update(ISSUERCIK='0'),lambda r:r.update(accession='../x'),lambda r:r.update(submission_rowid=999),lambda r:r['submission_as_filed'].update(FILING_DATE='01-JAN-2026')]:
    a=copy.deepcopy(rows);mutate(a[0])
    with self.assertRaises(ValueError):m.project('2026q3',a,subs)
   with self.assertRaises(ValueError):m.project('2026q3',rows+rows,subs)
   with self.assertRaises(ValueError):m.project('2026q2',rows,subs)
 def test_selection_excludes_other_codes_and_ciks_not_absence_claim(self):
  with tempfile.TemporaryDirectory() as td:
   rows,subs,_,_=self.fixture(Path(td),code='G',ad='A');self.assertEqual(m.project('2026q3',rows,subs),([],[]))
  with tempfile.TemporaryDirectory() as td:
   rows,subs,_,_=self.fixture(Path(td));rows[0]['submission_as_filed']['ISSUERCIK']='1';self.assertEqual(m.project('2026q3',rows,subs),([],[]))
 def test_invalid_dates_preserved_not_repaired(self):
  with tempfile.TemporaryDirectory() as td:
   rows,subs,_,_=self.fixture(Path(td));rows[0]['transaction_fields_as_filed']['TRANS_DATE']='';c,_=m.project('2026q3',rows,subs);self.assertIsNone(c[0]['transaction_date_min']);self.assertEqual(c[0]['invalid_transaction_date_rows'],1)
 def test_exact_config_and_labels(self):
  for value in [[],[{'batch_id':'2026q3'}],[{'batch_id':'2026q3'},{'batch_id':'2026q3'}]]:
   with self.assertRaises(ValueError):m.build(value)
  for v in ['x\n','x'*501]:
   with self.assertRaises(ValueError):m.label(v)
 def test_two_batch_build_and_durable_public_projection(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);config=[]
   for batch in ('2026q2','2026q3'):
    d=root/batch;d.mkdir();_,_,db,z=self.fixture(d)
    if batch=='2026q2':
     c=sqlite3.connect(db);c.execute("UPDATE insider_submission SET FILING_DATE='03-APR-2026', PERIOD_OF_REPORT='01-APR-2026'");c.execute("UPDATE insider_nonderiv_trans SET TRANS_DATE='01-APR-2026'");c.commit();c.close()
    config.append(dict(batch_id=batch,database=str(db),database_sha256=m.sha(db),archive=str(z),archive_sha256=m.sha(z)))
   public,private=m.build(config);self.assertEqual(public['counts']['filings'],2);self.assertEqual(public['counts']['selected_transaction_rows'],2);self.assertEqual(public['counts']['issuers_with_selected_rows'],1)
   self.assertEqual(sum(i['status']=='NO_SELECTED_P_S_ROWS_IN_THESE_BATCHES' for i in public['issuers']),9)
   c=public['filings'][0];self.assertTrue(c['sec_accession_lookup_url'].endswith('0000000001-26-000001'));self.assertTrue(any('conflict' in q for q in c['review_questions']));self.assertTrue(any('amendment' in q for q in c['review_questions']))
   out=root/'out';out.mkdir(mode=0o700);m.write_private(out/'INCOMPLETE',{});m.publish(out,public,private)
   self.assertFalse((out/'INCOMPLETE').exists());self.assertEqual(json.loads((out/'summary.json').read_text()),public);self.assertTrue((out/'COMPLETE.json').exists())
