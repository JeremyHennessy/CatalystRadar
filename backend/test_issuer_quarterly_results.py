import copy,hashlib,json,tempfile,unittest
from decimal import localcontext
from pathlib import Path
from unittest.mock import patch
import issuer_quarterly_results as m
from test_issuer_revenue_comparison import TEXT,document
ROOT=Path(__file__).resolve().parents[1]
class QuarterlyResultsTests(unittest.TestCase):
 def test_signed_results_exact_differences_and_limits(self):
  with localcontext() as c:
   c.prec=2;r=m.extract(document())
  self.assertEqual([x['absolute_difference_current_minus_prior'] for x in r['metrics']],['110','85','0.56'])
  self.assertEqual([x['facts'][1]['signed_value'] for x in r['metrics']],['-10','-5','-0.01'])
  for x in r['metrics']:
   self.assertIsNone(x['percentage_change']);self.assertIsNone(x['currency_iso']);self.assertFalse(x['accounting_comparability_verified'])
   for f in x['facts']:
    self.assertIsNone(f['period_start']);span=f['normalized_literal_span'];literal=TEXT[span['character_start']:span['character_end']];self.assertEqual(literal,f['literal_as_reported']);self.assertEqual(hashlib.sha256(literal.encode()).hexdigest(),span['utf8_sha256'])
 def test_negation_quotes_and_extra_qualifiers_rejected(self):
  for text in ['Not true: '+TEXT,'"'+TEXT+'"',TEXT+' This was denied.',TEXT.replace('had revenues','may have revenues')]:
   with self.assertRaises(ValueError):m.extract(document(text))
  for raw in [b'<blockquote>'+document()+b'</blockquote>',b'<q>'+document(),document().replace(b'<P>',b'<P><q>').replace(b'</P>',b'</q></P>')]:
   with self.assertRaises(ValueError):m.extract(raw)
 def test_duplicate_partial_and_hidden_rejected(self):
  for raw in [document()+document(),document(TEXT[:100]),document().replace(b'<P>',b'<!--<P>').replace(b'</P>',b'</P>-->'),document()+b'<DOCUMENT>']:
   with self.assertRaises(ValueError):m.extract(raw)
 def test_period_labels_units_signs_and_basic_only(self):
  for text in [TEXT.replace('2nd quarter fiscal year 2027','3rd quarter fiscal year 2027',1),TEXT.replace('2nd quarter fiscal year 2026','2nd quarter fiscal year 2024'),TEXT.replace('operating profit','operating loss'),TEXT.replace('net loss','net income'),TEXT.replace('basic gain','diluted gain'),TEXT.replace('$100','€100'),TEXT.replace('$100','-$100'),TEXT.replace('$.55','$0.55')]:
   with self.assertRaises(ValueError):m.extract(document(text))
 def test_zero_nonfinite_and_malformed_literal(self):
  for text in [TEXT.replace('$100','$0'),TEXT.replace('$100','$10,00'),TEXT.replace('$100','$NaN')]:
   with self.assertRaises(ValueError):m.extract(document(text))
  with self.assertRaises(ValueError):m.signed('1','unknown')
  with localcontext() as c:
   c.prec=2;self.assertEqual(m.signed('104,380','loss'),'-104380')
 def test_wrong_prior_source_and_raw_binding_fail_closed(self):
  with self.assertRaises(ValueError):m.build(document(),{}, {})
 def test_prior_revenue_correspondence_mismatch(self):
  prior=json.loads((ROOT/m.REVENUE_PATH).read_bytes())
  for field in ('issuer','filing','comparison','provenance'):
   bad=copy.deepcopy(prior);bad[field]['unexpected']='changed'
   with patch.object(m.revenue,'build',return_value=(prior,{})):
    with self.assertRaises(ValueError):m.build(b'ignored',{},bad)
 def test_private_completion_and_failure(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);public={'safe':True};private={'source_paragraph_text':'private'}
   with patch.object(m,'read_pinned',return_value=({},m.REVENUE_BYTES)),patch.object(m.revenue,'load_source',return_value=(b'',{})),patch.object(m,'build',return_value=(public,private)):
    self.assertEqual(m.save(ROOT,'fixture',root/'out'),public)
   self.assertFalse((root/'out/INCOMPLETE').exists());self.assertEqual((root/'out').stat().st_mode&0o777,0o700)
   self.assertEqual((root/'out/finding.json').stat().st_mode&0o777,0o600)
   self.assertEqual(json.loads((root/'out/COMPLETE.json').read_text())['finding_sha256'],m.sha(root/'out/finding.json'))
   with self.assertRaises(ValueError):m.save(ROOT,'fixture',root/'out')
   with patch.object(m,'read_pinned',side_effect=ValueError('pin')):
    with self.assertRaises(ValueError):m.save(ROOT,'fixture',root/'fail')
   self.assertTrue((root/'fail/INCOMPLETE').exists());self.assertFalse((root/'fail/COMPLETE.json').exists())
 def test_published_existing_revenue_unchanged_and_supplement_scope(self):
  raw=(ROOT/m.REVENUE_PATH).read_bytes();self.assertEqual(len(raw),m.REVENUE_BYTES);self.assertEqual(hashlib.sha256(raw).hexdigest(),m.REVENUE_SHA)
  p=ROOT/'web/company-findings/ieh-reported-quarterly-results.json'
  if not p.exists():self.skipTest('public copy not yet staged')
  d=json.loads(p.read_bytes());self.assertEqual(d['issuer']['cik'],'0000050292');self.assertEqual(d['revenue_cross_reference']['sha256'],m.REVENUE_SHA);self.assertEqual([x['absolute_difference_current_minus_prior'] for x in d['metrics']],['1150876','1390275','0.56']);self.assertNotIn('source_paragraph_text',p.read_text());self.assertFalse(d['training_ready']);self.assertFalse(d['execution_ready'])
if __name__=='__main__':unittest.main()
