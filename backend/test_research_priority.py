import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import research_priority as m
ROOT=Path(__file__).resolve().parents[1]
class PriorityTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.index=json.loads((ROOT/m.OUTPUT).read_bytes());cls.actual=m.project(cls.index)
 def test_actual_deterministic_rebuild_and_content_address(self):
  a=m.build(ROOT);self.assertEqual(a,m.build(ROOT))
  for path,raw in a.items():self.assertEqual((ROOT/path).read_bytes(),raw)
  latest=json.loads(a[m.BASE+'latest.json']);p=latest['snapshot']
  self.assertEqual(p['sha256'],m.sha(a[p['path']]))
  self.assertIn(p['sha256'],p['path']);self.assertEqual(p['bytes'],len(a[p['path']]))
 def test_conservation_and_scope(self):
  d=self.actual;self.assertEqual(d['counts'],{'evaluated':905,'eligible_source_records':6,'excluded':899,'consolidated_theses':5,'returned':5,'actionable_trades':0,'paper_trades_placed':0})
  self.assertEqual(len({x['source_id'] for x in d['candidate_decisions']}),905)
  self.assertEqual(sorted(x['source_id'] for x in d['candidate_decisions']),sorted(r['id'] for r in self.index['records']))
  self.assertEqual(sum(len(x['source_records']) for x in d['ideas']),6)
 def test_original_objects_and_entity_attribution(self):
  originals={r['id']:r for r in self.index['records']}
  for x in self.actual['ideas']:
   for r in x['source_records']:self.assertEqual(r,originals[r['id']])
  xerox=next(x for x in self.actual['ideas'] if x['category']=='REPORTED_EXCHANGE')
  self.assertEqual(len(xerox['issuer_associations']),2)
  vita=next(x for x in self.actual['ideas'] if x['issuer_associations'][0]['issuer_cik']=='0001697884')
  self.assertEqual(len(vita['source_records']),2)
 def test_score_coverage_and_no_trade_fields(self):
  for x in self.actual['ideas']:
   self.assertEqual(sum(f['weight'] for f in x['factors']),100)
   self.assertEqual(x['research_priority_score'],sum(f['points'] or 0 for f in x['factors']))
   for f in x['factors']:
    if f['value'] is None:self.assertIsNone(f['points'])
    else:self.assertEqual(f['points'],f['weight']*f['value'])
   self.assertEqual(x['status'],'WATCH');self.assertEqual(x['actionability'],'UNPRICED_NOT_ACTIONABLE')
   self.assertIs(x['execution_ready'],False);self.assertIs(x['training_ready'],False)
   for k in ['current_price','expected_return','return_outcome','security_mapping','first_public_verified']:self.assertIsNone(x['coverage'][k])
   self.assertFalse(set(x)&{'price','target_price','stop_loss','quantity','allocation','buy','sell','probability'})
   self.assertTrue(all(s['path'].startswith('web/') and 'prices' not in s['path'] for s in x['source_links']))
 def test_duplicate_and_readiness_fail_closed(self):
  for mutation in ['duplicate','ready']:
   d=copy.deepcopy(self.index)
   if mutation=='duplicate':d['records'].append(d['records'][0])
   else:next(r for r in d['records'] if r['category']=='REPORTED_EXCHANGE')['execution_ready']=True
   with self.assertRaises(ValueError):m.project(d)
 def test_cutoff_no_lookahead_and_clock_precision(self):
  with self.assertRaises(ValueError):m.project(self.index,'2026-11-20T00:00:00Z')
  d=copy.deepcopy(self.index);r=next(r for r in d['records'] if r['category']=='REPORTED_EXCHANGE')
  r['clocks'][0]['value_as_reported']='2026-11-19T18:57:50Z'
  with self.assertRaises(ValueError):m.project(d)
 def test_unknown_filing_recency_not_zero_or_observation_proxy(self):
  emr=next(x for x in self.actual['ideas'] if x['category']=='REPORTED_FINANCING')
  factor=next(f for f in emr['factors'] if f['id']=='declared_filing_age')
  self.assertIsNone(factor['value']);self.assertIsNone(factor['points'])
  self.assertEqual(emr['coverage']['known_factor_weight'],60)
 def test_order_invariance(self):
  d=copy.deepcopy(self.index);d['records'].reverse()
  self.assertEqual(m.project(d),self.actual)
 def test_offlist_scores_preserved(self):
  d=copy.deepcopy(self.index);template=next(r for r in d['records'] if r['category']=='REPORTED_FINANCING')
  for n in range(12):
   r=copy.deepcopy(template);r['id']='synthetic-extra-'+str(n);r['source_accessions']=['synthetic-'+str(n)];d['records'].append(r)
  out=m.project(d)
  self.assertEqual(len(out['ideas']),10);self.assertEqual(len(out['all_scored_candidates']),17)
  self.assertEqual([x['id'] for x in out['ideas']],[x['id'] for x in out['all_scored_candidates'][:10]])
  self.assertTrue(all(x['factors'] for x in out['all_scored_candidates']))
 def test_compact_filing_date_tie_consistency(self):
  d=copy.deepcopy(self.index)
  r=next(r for r in d['records'] if r['source_ref']['key']=='ieh')
  c=next(c for c in r['clocks'] if c['meaning']=='filing_date_as_reported')
  c.update(meaning='filing_date_as_filed_YYYYMMDD',value_as_reported='20261113')
  out=m.project(d);row=next(x for x in out['ideas'] if x['source_ref']['key']=='ieh')
  self.assertEqual(row['declared_filing_date'],'2026-11-13');self.assertEqual(row['rank'],1)
 def test_pin_failure(self):
  with patch.object(m,'INDEX_SHA','0'*64):
   with self.assertRaises(ValueError):m.build(ROOT)
if __name__=='__main__':unittest.main()
