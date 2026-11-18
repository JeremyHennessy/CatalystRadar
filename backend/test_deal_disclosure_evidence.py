"""Synthetic disclosure fixtures; no transaction or market truth."""
import hashlib,json,sqlite3,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import deal_disclosure_evidence as m

class Tests(unittest.TestCase):
 def put(self,c,t,**kw):
  fields=m.SCHEMAS[t+'.tsv'];c.execute('INSERT INTO notes_'+t+' VALUES ('+','.join('?' for _ in fields)+')',[kw.get(k,'') for k in fields])
 def fixture(self):
  c=sqlite3.connect(':memory:');c.row_factory=sqlite3.Row
  for n in ('sub','tag','dim','txt'):c.execute('CREATE TABLE notes_'+n+' ('+','.join('"'+k+'" TEXT' for k in m.SCHEMAS[n+'.tsv'])+')')
  self.put(c,'sub',adsh='0000000001-26-000001',cik='0001',name='Synthetic Issuer',form='10-Q',filed='20261001',period='20260630',accepted='2026-10-01 00:00:00.0')
  self.put(c,'tag',tag=m.TAGS[0],version=m.VERSIONS[1],custom='0',abstract='0',datatype='textBlock')
  self.put(c,'dim',dimhash='zero',segments='',segt='')
  self.put(c,'txt',adsh='0000000001-26-000001',tag=m.TAGS[0],version=m.VERSIONS[1],dimh='zero',dimn='0',escaped='1',lang='en',context='c1',value='We did not acquire Example. &amp; prior 2019 disposal; <script>not executable</script>')
  return c
 def test_exact_text_and_unknown_event_fields(self):
  c=self.fixture();r,s=m.scan(c);self.assertIn('&amp;',r[0]['raw']['value']);self.assertIn('<script>',r[0]['raw']['value'])
  self.assertIsNone(r[0]['event_type']);self.assertIsNone(r[0]['announcement_utc']);self.assertFalse(r[0]['training_ready'])
  self.assertEqual(r[0]['raw_row_canonical_sha256'],m.canonical_hash(dict(c.execute('select * from notes_txt').fetchone())))
  self.assertEqual(s['disclosure_records'],1);self.assertNotIn('Synthetic Issuer',json.dumps(s));self.assertNotIn('script',json.dumps(s))
 def test_duplicate_occurrences_remain_not_events(self):
  c=self.fixture();c.execute('INSERT INTO notes_txt SELECT * FROM notes_txt');r,s=m.scan(c);self.assertEqual(s['disclosure_records'],2);self.assertEqual(s['filings'],1);self.assertEqual(r[0]['raw_row_canonical_sha256'],r[1]['raw_row_canonical_sha256']);self.assertNotEqual(r[0]['raw']['rowid'],r[1]['raw']['rowid'])
 def test_missing_or_ambiguous_joins(self):
  for t in ('sub','tag','dim'):
   for op in ['DELETE FROM notes_'+t,'INSERT INTO notes_'+t+' SELECT * FROM notes_'+t]:
    c=self.fixture();c.execute(op)
    with self.assertRaises(ValueError):m.scan(c)
 def test_wrong_taxonomy_and_unsupported_version(self):
  for field,value in [('custom','1'),('abstract','1'),('datatype','string')]:
   c=self.fixture();c.execute('UPDATE notes_tag SET '+field+'=?',(value,))
   with self.assertRaises(ValueError):m.scan(c)
  c=self.fixture();c.execute("UPDATE notes_txt SET version='custom/2026'")
  with self.assertRaises(ValueError):m.scan(c)
 def test_dimensions_escaping_and_empty_retained(self):
  c=self.fixture();c.execute("UPDATE notes_dim SET segments='Segment=Example'");c.execute("UPDATE notes_txt SET dimn='1',escaped='0',value=''")
  r,s=m.scan(c);self.assertEqual(s['records_with_dimensions'],1);self.assertEqual(s['empty_text_records'],1);self.assertEqual(r[0]['raw']['escaped'],'0');self.assertEqual(r[0]['dimensions']['segments'],'Segment=Example')
 def test_invalid_identity_date_schema_dimension(self):
  for sql in ["UPDATE notes_sub SET cik='0'","UPDATE notes_sub SET filed='20260930'","UPDATE notes_txt SET dimn='bad'","UPDATE notes_txt SET adsh='bad'","ALTER TABLE notes_txt ADD COLUMN unsupported TEXT"]:
   c=self.fixture();c.execute(sql)
   with self.assertRaises(ValueError):m.scan(c)
 def test_public_forms_allowlist(self):
  c=self.fixture();c.execute("UPDATE notes_sub SET form='sensitive@example.invalid'");r,s=m.scan(c);self.assertEqual(s['by_filing_form'],{'OTHER_AS_FILED':1});self.assertNotIn('@',json.dumps(s))
 def test_end_to_end_pinned_output_and_completion(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);db=p/'notes.sqlite';dest=sqlite3.connect(db);src=self.fixture();src.commit();src.backup(dest);dest.close();src.close();z=p/'fixture.zip';z.write_bytes(b'synthetic hash fixture, not original archive')
   summary,rows=m.audit(db,m.sha(db),z,m.sha(z));out=p/'out';out.mkdir(mode=0o700);m.write_private(out/'INCOMPLETE',{});m.publish(out,summary,rows)
   complete=json.loads((out/'COMPLETE.json').read_text());self.assertEqual(complete['candidate_pairs_sha256'],m.sha(out/'candidate-pairs.json'));self.assertFalse((out/'INCOMPLETE').exists());self.assertEqual(summary['verified_events'],0)
   with self.assertRaises(ValueError):m.audit(db,'0'*64,z,m.sha(z))
 def test_write_failure_keeps_incomplete(self):
  with tempfile.TemporaryDirectory() as d:
   out=Path(d);m.write_private(out/'INCOMPLETE',{})
   with patch('financial_pair_candidates.write_private',side_effect=OSError('synthetic failure')):
    with self.assertRaises(OSError):m.publish(out,{},[])
   self.assertTrue((out/'INCOMPLETE').exists());self.assertFalse((out/'COMPLETE.json').exists())
if __name__=='__main__':unittest.main()
