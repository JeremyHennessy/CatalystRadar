import copy,unittest
from insider_conflict_queue import project,build,FLAG

def row(key='1',code='P',direction='D'):
 return {'accession':'0000000001-26-000001','transaction_key':key,'source_row_sha256':'a'*64,
 'submission_as_filed':{'ACCESSION_NUMBER':'0000000001-26-000001','ISSUERCIK':'1','FILING_DATE':'01-APR-2026','DOCUMENT_TYPE':'4'},
 'transaction_fields_as_filed':{'TRANS_CODE':code,'TRANS_ACQUIRED_DISP_CD':direction,'TRANS_SHARES':'SECRET','TRANS_PRICEPERSHARE':'PRIVATE'},'diagnostic_flags':[FLAG]}
class ConflictQueue(unittest.TestCase):
 def test_source_only_aggregation_and_privacy(self):
  rows=[row(),row('2','S','A')];rows[0]['owner_name']='PRIVATE OWNER';cards=project(rows)
  self.assertEqual(len(cards),1);self.assertEqual(cards[0]['conflicting_source_rows'],2)
  self.assertEqual(cards[0]['reported_code_direction_counts'],{'P:D':1,'S:A':1})
  self.assertNotIn('PRIVATE',str(cards));self.assertNotIn('SECRET',str(cards));self.assertFalse(cards[0]['execution_ready'])
 def test_diagnostic_mismatch_rejected(self):
  x=row();x['diagnostic_flags']=[]
  with self.assertRaises(ValueError):project([x])
 def test_consistent_no_conflict_empty_state(self):
  x=row(direction='A');x['diagnostic_flags']=[];self.assertEqual(project([x]),[])
 def test_duplicate_and_bad_identity_rejected(self):
  with self.assertRaises(ValueError):project([row(),row()])
  x=row();x['submission_as_filed']['ISSUERCIK']='0'
  with self.assertRaises(ValueError):project([x])
 def test_wrong_period_rejected(self):
  x=row();x['submission_as_filed']['FILING_DATE']='01-JUL-2026'
  with self.assertRaises(ValueError):project([x])
 def test_conflicting_filing_identity_rejected(self):
  x=row('2');x['submission_as_filed']['ISSUERCIK']='2'
  with self.assertRaises(ValueError):project([row(),x])
 def test_missing_lineage_rejected(self):
  x=row();x['source_row_sha256']=''
  with self.assertRaises(ValueError):project([x])
 def test_no_unbounded_input(self):
  with self.assertRaises(ValueError):project([])

 def test_wrong_source_lineage_rejected(self):
  with self.assertRaises(ValueError):build('unused','a'*64,'unused','b'*64)
