import copy
import json
from pathlib import Path
from unittest.mock import patch
import unittest
import research_abstention_journal as j
ROOT=Path(__file__).resolve().parents[1]
RANK='28e8b1d7b80a34de480ad03e9bdf7a5d18b65fdf5816239968f2f2fd52e6196a'
class AbstentionTests(unittest.TestCase):
 def setUp(self):
  raw=(ROOT/f'web/trade-ideas/v1/snapshots/{RANK}.json').read_bytes();s=json.loads(raw)
  self.args={'command_id':'synthetic-test-only','snapshot_raw':raw,'snapshot_sha256':RANK,'thesis_id':'research-88f4fe3fecb3853d4c6596aa','issuer_cik':'0000820318','accession':'0001193125-26-467737','deadline_utc':'2026-11-20T21:00:00Z','reasons':['MISSING_MARKET_DATA','UNVERIFIED_SECURITY_IDENTITY'],'source_bytes':{k:(ROOT/p['path']).read_bytes() for k,p in s['source_pins'].items() if k=='coherent'}}
  # Source binding test only. No transcript is persisted or claimed actually frozen.
  self.clock=lambda:'2026-11-20T12:00:00Z'
 def put(self,rows=None,tip=j.ZERO,**changes):
  a=copy.deepcopy(self.args);a.update(changes)
  return j.append(rows or [],expected_tip=tip,clock=self.clock,**a)
 def test_retained_coherent_binding_unattested_abstention(self):
  rows,r=self.put();self.assertEqual(len(rows),1);self.assertEqual(j.replay(rows)['tip_sha256'],r['sha256'])
  self.assertEqual(r['decision'],'ABSTAIN');self.assertFalse(r['prospective_eligible']);self.assertEqual(r['receipt_status'],'MISSING')
  self.assertEqual(r['command']['issuer_cik'],'0000820318')
  self.assertEqual(r['command']['accession'],'0001193125-26-467737')
 def test_lost_ack_retry_and_conflict(self):
  rows,r=self.put();same,ack=self.put(rows,tip=j.ZERO)
  self.assertEqual(same,rows);self.assertEqual(ack,r)
  with self.assertRaises(ValueError):self.put(rows,tip=r['sha256'],reasons=['MISSING_MARKET_DATA'])
 def test_stale_tip_and_unchanged_inputs(self):
  rows,r=self.put();before=list(rows)
  with self.assertRaises(ValueError):self.put(rows,command_id='second')
  nextrows,_=self.put(rows,tip=r['sha256'],command_id='second');self.assertEqual(rows,before);self.assertEqual(nextrows[:1],rows)
 def test_source_hash_and_exact_joint_identity(self):
  for changes in [{'snapshot_sha256':'0'*64},{'issuer_cik':'0000012659'},{'accession':'0001193125-26-000000'},{'source_bytes':{}},{'reasons':['BUY']},{'receipt_raw':b'x'*65537}]:
   with self.assertRaises(ValueError):self.put(**changes)
 def test_future_source_clock_rejected_and_cutoff_change_conflicts(self):
  s=json.loads(self.args['snapshot_raw']);idea=next(x for x in s['ideas'] if x['id']==self.args['thesis_id'])
  c=next(c for c in idea['source_records'][0]['clocks'] if c['meaning']=='metadata_observation_utc_as_recorded')
  c['value_as_reported']='2026-11-21T12:00:00Z';raw=j.encoded(s)
  with patch.object(j,'APPROVED_SNAPSHOTS',frozenset({j.sha(raw)})):
   with self.assertRaisesRegex(ValueError,'source observation after'):self.put(snapshot_raw=raw,snapshot_sha256=j.sha(raw))
  rows,r=self.put()
  with self.assertRaises(ValueError):self.put(rows,tip=r['sha256'],deadline_utc='2026-11-21T21:00:00Z')
 def test_unreviewed_snapshot_and_ambiguous_pair_rejected(self):
  s=json.loads(self.args['snapshot_raw']);s['heading']='changed';raw=j.encoded(s)
  with self.assertRaisesRegex(ValueError,'snapshot pin'):self.put(snapshot_raw=raw,snapshot_sha256=j.sha(raw))
  for field in ('issuer_associations','source_accessions'):
   s=json.loads(self.args['snapshot_raw']);idea=next(x for x in s['ideas'] if x['id']==self.args['thesis_id']);row=idea['source_records'][0]
   row[field].append({'issuer_cik':'0000012659','names_as_reported':['TEST'],'role':'SEPARATE_EXPLICIT_FILER'} if field=='issuer_associations' else '0001193125-26-000000')
   raw=j.encoded(s)
   with patch.object(j,'APPROVED_SNAPSHOTS',frozenset({j.sha(raw)})):
    with self.assertRaisesRegex(ValueError,'ambiguous'):self.put(snapshot_raw=raw,snapshot_sha256=j.sha(raw))
 def test_denominator_and_native_identity_adversarial_fixtures(self):
  for mutation in ('duplicate','counts','identity'):
   s=json.loads(self.args['snapshot_raw'])
   if mutation=='duplicate':s['candidate_decisions'][0]=s['candidate_decisions'][1]
   elif mutation=='counts':s['counts']['excluded']-=1;s['counts']['eligible_source_records']+=1
   else:
    row=next(x for x in s['ideas'] if x['id']==self.args['thesis_id'])['source_records'][0]
    row['issuer_associations'][0]['issuer_cik']='0000000001'
   raw=j.encoded(s);kwargs={'snapshot_raw':raw,'snapshot_sha256':j.sha(raw)}
   if mutation=='identity':kwargs['issuer_cik']='0000000001'
   with patch.object(j,'APPROVED_SNAPSHOTS',frozenset({j.sha(raw)})):
    with self.assertRaises(ValueError):self.put(**kwargs)
 def test_replay_clock_meaning_allowlist(self):
  rows,r=self.put();x=copy.deepcopy(r);x['command']['source_observation_clocks'][0]['meaning']='BUY NOW'
  x['command_sha256']=j.digest(x['command']);x['sha256']=j.digest({k:v for k,v in x.items() if k!='sha256'})
  with self.assertRaises(ValueError):j.replay([j.encoded(x)])
 def test_late_clock_is_not_backdated(self):
  self.clock=lambda:'2026-11-21T00:00:00Z';_,r=self.put()
  self.assertEqual(r['timing_status'],'LATE_LOCAL_RECORD_NOT_PROSPECTIVE');self.assertFalse(r['prospective_eligible'])
 def test_receipt_is_only_hash_bound(self):
  _,r=self.put(receipt_raw=b'{"verified":true,"server_received_utc":"2026-11-20T12:00:00Z"}')
  self.assertEqual(r['receipt_status'],'HASH_BOUND_NOT_AUTHENTICATED');self.assertFalse(r['prospective_eligible'])
 def test_tamper_promotion_reordering_and_clock_regression(self):
  rows,r=self.put();more,_=self.put(rows,tip=r['sha256'],command_id='second')
  with self.assertRaises(ValueError):j.replay(list(reversed(more)))
  for field,value in [('prospective_eligible',True),('decision','BUY'),('sequence',True),('recorded_utc','2026-11-18T00:00:00Z')]:
   x=copy.deepcopy(r);x[field]=value;x['sha256']=j.digest({k:v for k,v in x.items() if k!='sha256'})
   with self.assertRaises(ValueError):j.replay([j.encoded(x)])
  self.clock=lambda:'2026-11-20T11:59:59Z'
  with self.assertRaises(ValueError):self.put(rows,tip=r['sha256'],command_id='second')
 def test_canonical_finite_json_and_limits(self):
  for raw in [b'{"x":1e999}',b'{"x":NaN}',b'{"x":1,"x":2}',b'{}']:
   with self.assertRaises(ValueError):j.decode(raw,100)
  with self.assertRaises(ValueError):j.replay([b'{}\n']*257)
if __name__=='__main__':unittest.main()
