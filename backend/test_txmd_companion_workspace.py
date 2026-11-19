"""Public companion note invariants; no network or original filing publication."""
import hashlib
import json
from pathlib import Path
import unittest
from datetime import datetime

ROOT=Path(__file__).resolve().parent.parent
class CompanionTests(unittest.TestCase):
 def setUp(self):
  self.d=json.loads((ROOT/'web/company-findings/txmd-companion-10q.json').read_text())
  self.html=(ROOT/'web/financial-review.html').read_text()
 def test_source_and_separate_release_pin(self):
  d=self.d
  self.assertEqual(d['issuer_cik'],'0000025743');self.assertEqual(d['accession'],'0001213900-26-119697')
  self.assertEqual(d['source']['raw_sha256'],'b1d9611d086251771ab12b16a836d94aee216ba25c24f1131e70731194c2469a')
  self.assertEqual(d['source']['raw_bytes'],4487035)
  r=d['separate_release'];self.assertEqual(r['accession'],'0001213900-26-119681')
  self.assertEqual(hashlib.sha256((ROOT/r['clock_sidecar']).read_bytes()).hexdigest(),r['clock_sidecar_sha256'])
  c=json.loads((ROOT/r['clock_sidecar']).read_text())
  a=next(x for x in c['clocks'] if x['channel']=='SEC EDGAR')['as_reported']
  self.assertEqual(a,d['acceptance_comparison']['eight_k_as_reported_new_york'])
  delta=datetime.strptime(d['acceptance_comparison']['ten_q_raw_header'],'%Y%m%d%H%M%S')-datetime.fromisoformat(a)
  self.assertEqual(delta.total_seconds(),122)
 def test_distinct_years_and_no_promotions(self):
  a,b,c=self.d['findings'];self.assertEqual(a['sales_year_end'],'2025-12-31');self.assertEqual(a['recognized_quarter_end'],'2026-09-30')
  self.assertEqual(b['sales_year_end'],'2026-12-31');self.assertEqual(b['accounting_quarter_end'],'2026-12-31')
  self.assertEqual(b['after_as_reported'],'approximately 0.1 million')
  self.assertFalse(self.d['readiness_changed']);self.assertFalse(self.d['execution_ready']);self.assertFalse(self.d['training_ready'])
  self.assertIsNone(self.d['first_public_utc']);self.assertEqual(self.d['qualified_outcomes'],0)
  self.assertFalse(self.d['source']['raw_original_published']);self.assertFalse(self.d['acceptance_comparison']['index_bytes_retained'])
 def test_ui_preserves_context_and_inert_links(self):
  block=self.html.split('<details id="txmd-companion-10q">')[1].split('</details>')[0]
  for s in ['calendar-2025','calendar-2026','Note 8','Note 14','MD&amp;A','122 seconds','not proof','zero qualified outcomes','approximately CAD 0.1 million','zero net accounting effect']:
   self.assertIn(s,block)
  self.assertIn('company-findings/txmd-companion-10q.json',block)
  self.assertNotIn('<script',block);self.assertNotIn('76.8%',block)
 def test_span_contract(self):
  spans=self.d['source']['evidence_spans'];self.assertEqual(set(spans),{'note8','note14','mda'})
  for r in spans.values():
   self.assertLess(r['normalized_character_start'],r['normalized_character_end']);self.assertRegex(r['normalized_utf8_sha256'],r'^[a-f0-9]{64}$')
  self.assertIn('not raw byte offsets',self.d['source']['span_method'])
