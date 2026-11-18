import copy,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import financial_insider_links as m
import insider_review_cards as cards
import test_insider_review_cards as fixtures
class LinkTests(unittest.TestCase):
 def source(self):return {'training_ready':False,'execution_ready':False,'records':[{'id':'a'*64,'issuer_cik':'0000820318','status':'EVIDENCE_REVIEW_REQUIRED','comparability_verified':False,'first_observed_utc':None,'outcome_status':'INSUFFICIENT_EVIDENCE','metric':'Revenues','reported_end_date':'2025-06-30','issuer_names_as_filed':['Financial old name'],'observations':[{'accession':'0000000001-26-000001','filing_date_as_filed':'2026-04-01'},{'accession':'0000000001-26-000002','filing_date_as_filed':'2026-07-01'}]}]}
 def test_exact_cik_independent_dates_names_no_shared_event(self):
  g=m.validate_financial(self.source())
  with tempfile.TemporaryDirectory() as td:
   rows,subs,_,_=fixtures.ReviewCardTests().fixture(Path(td));fs,_=cards.project('2026q3',rows,subs,set(g));cs=m.assemble(g,fs)
  c=cs[0];self.assertEqual(c['issuer_cik'],'0000820318');self.assertEqual(c['financial_issuer_names_as_filed'],['Financial old name']);self.assertEqual(c['financial_cases'][0]['prepared_context_date_as_reported'],'2025-06-30');self.assertEqual(c['insider_selected_rows'],1)
  for k in ['same_event_verified','causal_relationship_verified','security_mapping_verified','temporal_alignment_verified','training_ready','execution_ready']:self.assertFalse(c[k])
  self.assertNotIn('PRIVATE',json.dumps(c));self.assertNotIn('2.50',json.dumps(c))
 def test_invalid_financial_ids_clocks_labels_dates_and_duplicates(self):
  for key,value in [('issuer_cik','0'),('id','../x'),('comparability_verified',True),('first_observed_utc','2026-01-01'),('reported_end_date','2026-02-30'),('issuer_names_as_filed',['x\n'])]:
   d=self.source();d['records'][0][key]=value
   with self.assertRaises(ValueError):m.validate_financial(d)
  d=self.source();d['records']*=2
  with self.assertRaises(ValueError):m.validate_financial(d)
 def test_absence_scope_and_no_ticker_name_join(self):
  g=m.validate_financial(self.source());c=m.assemble(g,[])[0];self.assertEqual(c['insider_scope_status'],'NO_SELECTED_P_S_ROWS_IN_THESE_TWO_BATCHES');self.assertEqual(c['insider_filing_refs'],[])
  with tempfile.TemporaryDirectory() as td:
   rows,subs,_,_=fixtures.ReviewCardTests().fixture(Path(td));rows[0]['submission_as_filed']['ISSUERCIK']='1';self.assertEqual(cards.project('2026q3',rows,subs,set(g)),([],[]))
 def test_cohort_and_duplicate_insider_validation(self):
  with tempfile.TemporaryDirectory() as td:
   rows,subs,_,_=fixtures.ReviewCardTests().fixture(Path(td))
   for cohort in [set(),{'0000820318'},{'x'},{'0'},['820318']]:
    with self.assertRaises(ValueError):cards.project('2026q3',rows,subs,cohort)
   fs,_=cards.project('2026q3',rows,subs,{'820318'});g=m.validate_financial(self.source())
   with self.assertRaises(ValueError):m.assemble(g,fs+fs)
   fs[0]['issuer_cik']='0000000001'
   with self.assertRaises(ValueError):m.assemble(g,fs)
 def test_end_to_end_pins_and_completion(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);config=[]
   for batch in ('2026q2','2026q3'):
    d=root/batch;d.mkdir();_,_,db,z=fixtures.ReviewCardTests().fixture(d)
    if batch=='2026q2':
     import sqlite3
     c=sqlite3.connect(db);c.execute("UPDATE insider_submission SET FILING_DATE='03-APR-2026'");c.execute("UPDATE insider_nonderiv_trans SET TRANS_DATE='01-APR-2026'");c.commit();c.close()
    config.append(dict(batch_id=batch,database=str(db),database_sha256=m.sha(db),archive=str(z),archive_sha256=m.sha(z)))
   f=root/'financial.json';f.write_text(json.dumps(self.source()));out=root/'out';p=m.save(f,m.sha(f),config,out)
   self.assertEqual(p['counts']['selected_insider_rows'],2);self.assertEqual(p['counts']['financial_contexts_for_linked_issuers'],1);self.assertFalse((out/'INCOMPLETE').exists());self.assertEqual(json.loads((out/'summary.json').read_text()),p);self.assertEqual(json.loads((out/'COMPLETE.json').read_text())['summary_sha256'],m.sha(out/'summary.json'))
   with self.assertRaises(ValueError):m.build(f,'0'*64,config)
 def test_failure_retains_incomplete(self):
  with tempfile.TemporaryDirectory() as td:
   out=Path(td)/'failed'
   with patch.object(m,'build',side_effect=ValueError('failure')):
    with self.assertRaises(ValueError):m.save('fixture','0'*64,[],out)
   self.assertTrue((out/'INCOMPLETE').exists());self.assertFalse((out/'COMPLETE.json').exists())
