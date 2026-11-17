"""Synthetic correspondence cases, not market evidence."""
import sqlite3,unittest
from holdings_figi_evidence import scan,COVER,index_mappings
class HoldingsFigiTests(unittest.TestCase):
 def setUp(self):
  self.c=sqlite3.connect(':memory:');self.c.row_factory=sqlite3.Row
  self.c.execute('create table holdings_infotable(ACCESSION_NUMBER text,FIGI text,PUTCALL text,CUSIP text,VALUE text,SSHPRNAMTTYPE text)')
  self.c.execute('create table holdings_submission(ACCESSION_NUMBER text,CIK text,PERIODOFREPORT text,SUBMISSIONTYPE text)')
  self.c.execute('create table holdings_coverpage('+','.join(x+' text' for x in COVER)+')')
  self.a='0000000001-26-000001'
  self.c.execute('insert into holdings_submission values(?,?,?,?)',(self.a,'1','30-JUN-2026','13F-HR'))
  cover={k:'' for k in COVER};cover.update(ACCESSION_NUMBER=self.a,REPORTCALENDARORQUARTER='30-JUN-2026',ISAMENDMENT='N')
  self.c.execute('insert into holdings_coverpage values('+','.join('?' for _ in COVER)+')',list(cover.values()))
  self.mapping={'mappings':[{'query_ticker':'SYNTH','request_position':0,'candidates':[{'figi':'BBG000BLNNH6','compositeFIGI':'BBG000BLNNH6','shareClassFIGI':'BBG001S5S399'}]}]}
 def tearDown(self):self.c.close()
 def add(self,identifier,option=''):
  self.c.execute('insert into holdings_infotable values(?,?,?,?,?,?)',(self.a,identifier,option,'SECRET_CUSIP_FIXTURE','123.45','PRN'))
 def test_row_count_scope_and_private_context(self):
  self.add('BBG000BLNNH6','Put');s,p=scan(self.c,self.mapping)
  self.assertEqual(s['matched_holding_rows'],1);self.assertEqual(s['matched_rows_by_identifier_field'],{'figi':1,'compositeFIGI':1})
  self.assertEqual(p[0]['holding']['VALUE'],'123.45');self.assertEqual(p[0]['holding']['SSHPRNAMTTYPE'],'PRN')
  self.assertEqual(p[0]['submission']['CIK'],'1');self.assertFalse(s['historical_security_link_verified']);self.assertNotIn('123.45',str(s));self.assertNotIn('SECRET_CUSIP_FIXTURE',str(s))
 def test_census_invalid_not_repaired_and_shareclass(self):
  for i in ['', ' ', 'BBG000BLNNH7',' BBG000BLNNH6','BBG001S5S399']:self.add(i)
  s,p=scan(self.c,self.mapping);self.assertEqual(s['census']['blank_rows'],2);self.assertEqual(s['census']['invalid_structure_or_checksum_rows'],2)
  self.assertEqual(s['matched_holding_rows'],1);self.assertEqual(p[0]['mapping_matches'][0]['matching_identifier_fields'],['shareClassFIGI'])
 def test_cross_query_ambiguity_explicit(self):
  self.mapping['mappings'].append(dict(self.mapping['mappings'][0],query_ticker='OTHER',request_position=1));self.add('BBG000BLNNH6')
  s,p=scan(self.c,self.mapping);self.assertEqual(s['matched_holding_rows'],1);self.assertEqual(s['identifiers_shared_across_query_tickers'],2);self.assertEqual(len(p[0]['mapping_matches']),2)
 def test_missing_ambiguous_or_conflicting_submissions(self):
  self.add('BBG000BLNNH6');self.c.execute('update holdings_coverpage set REPORTCALENDARORQUARTER=?',('30-JUN-2025',))
  with self.assertRaises(ValueError):scan(self.c,self.mapping)
  self.c.execute('delete from holdings_submission')
  with self.assertRaises(ValueError):scan(self.c,self.mapping)
 def test_amendment_conflict_preserved(self):
  self.add('BBG000BLNNH6');self.c.execute("update holdings_coverpage set ISAMENDMENT='Y'")
  s,p=scan(self.c,self.mapping);self.assertEqual(s['matched_amendment_flag_conflicts'],1);self.assertTrue(p[0]['amendment_flag_conflict'])
 def test_bad_candidate_and_nontext_source_fail(self):
  self.mapping['mappings'][0]['candidates'][0]['figi']='bad'
  with self.assertRaises(ValueError):index_mappings(self.mapping)
  self.add(None)
  with self.assertRaises(ValueError):scan(self.c,{'mappings':[]})

 def test_public_categories_fail_closed(self):
  self.add('BBG000BLNNH6','arbitrary private text')
  with self.assertRaises(ValueError):scan(self.c,self.mapping)
  self.c.execute("update holdings_infotable set PUTCALL=''")
  self.c.execute("update holdings_submission set PERIODOFREPORT='private text'")
  with self.assertRaises(ValueError):scan(self.c,self.mapping)
 def test_pinned_end_to_end_audit(self):
  import tempfile,json
  from pathlib import Path
  import test_openfigi_evidence as fixtures
  from holdings_figi_evidence import audit
  from openfigi_evidence import digest
  from financial_pair_candidates import sha
  self.add('BBG000BLNNH6');self.c.commit()
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);db=root/'source.sqlite';target=sqlite3.connect(db);self.c.backup(target);target.close()
   archive=root/'source.zip';archive.write_bytes(b'SYNTHETIC archive identity only; not proof of ingestion')
   request,response,receipt,_,_=fixtures.FigiTests().fixture()
   rb=json.dumps(request).encode();sb=json.dumps(response).encode();receipt.update(request_sha256=digest(rb),response_sha256=digest(sb),response_bytes=len(sb))
   raw=[rb,sb,json.dumps(receipt).encode()];paths=[root/x for x in ('request','response','receipt')]
   for p,b in zip(paths,raw):p.write_bytes(b)
   args=[db,sha(db),archive,sha(archive)]
   for p,b in zip(paths,raw):args.extend([p,digest(b)])
   summary,private=audit(*args);self.assertEqual(summary['matched_holding_rows'],1);self.assertEqual(len(private['correspondences']),1)
   args[1]='0'*64
   with self.assertRaises(ValueError):audit(*args)
