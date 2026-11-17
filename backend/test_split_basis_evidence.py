"""Synthetic split disclosures; no market truth inferred."""
import hashlib,json,sqlite3,tempfile,unittest
from pathlib import Path
from sec_notes_data import SCHEMAS
from split_basis_evidence import scan,correspondence,load_pairs,RATIO

class Tests(unittest.TestCase):
 def conn(self):
  c=sqlite3.connect(':memory:');c.row_factory=sqlite3.Row
  for name in ['sub','tag','dim','num','txt']:
   c.execute('CREATE TABLE notes_'+name+' ('+','.join('"'+k+'" TEXT' for k in SCHEMAS[name+'.tsv'])+')')
  return c
 def put(self,c,t,**kw):
  fields=SCHEMAS[t+'.tsv'];c.execute('INSERT INTO notes_'+t+' VALUES ('+','.join('?' for _ in fields)+')',[kw.get(k,'') for k in fields])
 def fixture(self):
  c=self.conn();self.put(c,'sub',adsh='0000000001-26-000001',cik='0001',form='10-Q')
  self.put(c,'dim',dimhash='zero',segments='',segt='')
  self.put(c,'tag',tag=RATIO,version='us-gaap/2026',custom='0',abstract='0',datatype='pure')
  self.put(c,'num',adsh='0000000001-26-000001',tag=RATIO,version='us-gaap/2026',dimh='zero',uom='pure',value='2.0000',ddate='20260930',qtrs='0')
  return c
 def test_exact_context_retained_without_event_inference(self):
  c=self.fixture();rows,counts,ids=scan(c)
  self.assertEqual(ids,{'1'});self.assertEqual(rows[0]['raw']['value'],'2.0000');self.assertEqual(rows[0]['raw']['rowid'],1)
  self.assertFalse(rows[0]['effective_date_verified']);self.assertEqual(counts['ratio_filings_with_standard_narrative'],0)
 def test_repeated_facts_not_deduplicated(self):
  c=self.fixture();c.execute('INSERT INTO notes_num SELECT * FROM notes_num');rows,counts,_=scan(c)
  self.assertEqual(counts['num'],2);self.assertEqual(counts['ratio_filings'],1);self.assertEqual([r['raw']['rowid'] for r in rows],[1,2])
 def test_missing_and_duplicate_context_fail_closed(self):
  for t in ['sub','dim','tag']:
   for op in ['DELETE FROM notes_'+t,'INSERT INTO notes_'+t+' SELECT * FROM notes_'+t]:
    with self.subTest(op=op):
     c=self.fixture();c.execute(op)
     with self.assertRaises(ValueError):scan(c)
 def test_wrong_taxonomy_fails(self):
  c=self.fixture();c.execute("UPDATE notes_tag SET custom='1'")
  with self.assertRaises(ValueError):scan(c)
 def test_blank_negative_and_nonfinite_ratio_retained_unusable(self):
  for value in ['', '-2','0','NaN','Infinity']:
   with self.subTest(value=value):
    c=self.fixture();c.execute('UPDATE notes_num SET value=?',(value,));rows,counts,_=scan(c)
    self.assertEqual(rows[0]['disposition'],'UNUSABLE_NUMERIC_LITERAL');self.assertEqual(rows[0]['raw']['value'],value);self.assertEqual(counts['positive_ratio_literals'],0)
 def test_custom_version_excluded_not_promoted(self):
  c=self.fixture();c.execute("UPDATE notes_num SET version='0000000001-26-000001'");r,counts,ids=scan(c)
  self.assertEqual(r,[]);self.assertEqual(ids,set())
 def test_narrative_same_filing_is_not_same_event(self):
  c=self.fixture();tag='StockholdersEquityReverseStockSplit'
  self.put(c,'tag',tag=tag,version='us-gaap/2026',custom='0',abstract='0',datatype='string')
  self.put(c,'txt',adsh='0000000001-26-000001',tag=tag,version='us-gaap/2026',dimh='zero',value='The board did not approve a split.')
  r,s,_=scan(c);self.assertEqual(s['ratio_rows_with_standard_narrative'],1);self.assertEqual(r[1]['raw']['value'],'The board did not approve a split.');self.assertEqual(r[1]['disposition'],'NARRATIVE_AS_FILED_NOT_INTERPRETED')
 def test_issuer_overlap_not_security_or_time_claim(self):
  r={'issuer_cik_as_filed':'0001','current':{'tag':'EarningsPerShareDiluted'}}
  counts,matches=correspondence({'q2':[r]}, {'1'})
  self.assertEqual(counts['q2']['diluted_eps_pairs_at_same_issuer'],1);self.assertFalse(matches[0]['split_applies_to_candidate_verified']);self.assertFalse(matches[0]['known_at_candidate_time_verified'])
 def pair_fixture(self,p):
  s={'candidate_pairs':1,'database_sha256':'d','source_archive_sha256':'a'};r=[{'issuer_cik_as_filed':'1','training_ready':False,'comparability_verified':False,'decision_utc':None,'outcome':None,'database_sha256':'d','source_archive_sha256':'a'}]
  b=json.dumps(r).encode();sb=json.dumps(s).encode();h=lambda b:hashlib.sha256(b).hexdigest()
  (p/'candidate-pairs.json').write_bytes(b);(p/'summary.json').write_bytes(sb);(p/'COMPLETE.json').write_text(json.dumps({'candidate_pairs_sha256':h(b),'summary_sha256':h(sb)}))
  return dict(s,private_candidates_sha256=h(b))
 def test_completed_input_pinning(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);expected=self.pair_fixture(p);self.assertEqual(len(load_pairs(p,expected)),1)
   (p/'candidate-pairs.json').write_text('[]')
   with self.assertRaises(ValueError):load_pairs(p,expected)
 def test_incomplete_marker_rejected(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);expected=self.pair_fixture(p);(p/'INCOMPLETE').touch()
   with self.assertRaises(ValueError):load_pairs(p,expected)
 def test_nonstandard_marker_json_rejected(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);expected=self.pair_fixture(p);f=p/'COMPLETE.json';f.write_text(f.read_text()[:-1]+',"x":NaN}')
   with self.assertRaises(ValueError):load_pairs(p,expected)
if __name__=='__main__':unittest.main()
