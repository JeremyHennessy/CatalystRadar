import copy,hashlib,json,tempfile,unittest
from decimal import Decimal,localcontext
from pathlib import Path
from unittest.mock import patch
import financial_assertion_audit as m
ROOT=Path(__file__).resolve().parents[1]
# Synthetic values/years; grammar exercises the supported full-context shape.
TEXT='The Company recorded $1.2 million in license revenue for the third quarter of 2024, an increase of $300 thousand, or 60.0%, compared to $500 thousand in license revenue for the third quarter of 2023. The increase is primarily attributable to the achievement of an IMVEXXY sales-based milestone by Knight relating to IMVEXXY sales for the year ended December 31, 2023, resulting in a $200 thousand milestone payment that was recognized and confirmed by Knight in the third quarter of 2024.'
def document(text=TEXT,tag='TD'):
 return ('<DOCUMENT>\n<TYPE>EX-99.1\n<FILENAME>synthetic.htm\n<TEXT>\n<'+tag+'>'+text+'</'+tag+'>\n</TEXT>\n</DOCUMENT>').encode()
class AssertionAuditTests(unittest.TestCase):
 def test_positive_endpoint_and_reported_claim_checks_distinct(self):
  x=m.arithmetic('1300000.0','784000','DISPLAYED_MIXED_SCALE_LITERALS','475000','60.6',1)
  self.assertEqual(x['signed_difference_of_literals'],'516000.0');self.assertEqual(x['endpoint_percentage_check']['rounded_value'],'65.8');self.assertFalse(x['endpoint_percentage_check']['matches_reported_percent_at_check_precision']);self.assertEqual(x['reported_increase_percentage_check']['rounded_value'],'60.6');self.assertTrue(x['reported_increase_percentage_check']['matches_reported_percent_at_check_precision']);self.assertIsNone(x['true_unrounded_change']);self.assertFalse(x['qualified_growth'])
 def test_negative_and_zero_bases_abstain_not_zero_growth(self):
  for a,b,delta,reason in [('0','0','0','ZERO_COMPARISON_BASE_UNDEFINED'),('-110845','-218662','107817','NEGATIVE_BASE_NOT_PRESENTED_AS_GROWTH'),('0.55','-0.01','0.56','NEGATIVE_BASE_NOT_PRESENTED_AS_GROWTH')]:
   x=m.arithmetic(a,b,'DECLARED_INLINE_NUMERIC_VALUES');self.assertEqual(x['signed_difference_of_literals'],delta);self.assertEqual(x['percentage_abstention'],reason);self.assertIsNone(x['endpoint_percentage_check'])
 def test_exact_arithmetic_under_small_ambient_precision(self):
  with localcontext() as c:
   c.prec=2;x=m.arithmetic('10700084','7077592','REPORTED_UNSCALED_LITERALS',reported_percent='51',percent_places=0);v=m.scaled('1.3','million')
  self.assertEqual(v,'1300000.0');self.assertEqual(x['signed_difference_of_literals'],'3622492');self.assertEqual(x['endpoint_percentage_check']['numerator'],'45281150');self.assertEqual(x['endpoint_percentage_check']['denominator'],'884699');self.assertTrue(x['endpoint_percentage_check']['matches_reported_percent_at_check_precision'])
 def test_bounds_nonfinite_exponents_and_scale_fail_closed(self):
  for n in ['NaN','Infinity','1e3','1'*21,'0.'+'1'*11,'+1']:
   with self.assertRaises(ValueError):m.arithmetic(n,'1','REPORTED_UNSCALED_LITERALS')
  with self.assertRaises(ValueError):m.scaled('1','billions')
  with self.assertRaises(ValueError):m.arithmetic('1','1','UNKNOWN')
  with self.assertRaises(ValueError):m.arithmetic('2','1','REPORTED_UNSCALED_LITERALS',percent_places=7)
 def test_whole_cell_and_paragraph_with_tail_preserved(self):
  for tag in ['P','TD']:
   raw=document(tag=tag);x=m.txmd_extract(raw);self.assertEqual(x['status'],'ONE_SUPPORTED_FULL_PARAGRAPH');r=x['records'][0];v=r['values_as_reported'];self.assertEqual(v['milestone'],'200');self.assertEqual(v['sales_end'],'December 31, 2023');self.assertEqual(v['recognition_year'],'2024');s=r['paragraph_span'];self.assertEqual(m.digest(raw[s['byte_start']:s['byte_end']]),s['sha256'])
   for k,s in r['normalized_literal_spans'].items():self.assertEqual(m.digest(TEXT[s['character_start']:s['character_end']].encode()),s['utf8_sha256'])
 def test_negation_quotes_partial_or_changed_tail_not_promoted(self):
  for text in ['This is false: '+TEXT,'"'+TEXT+'"',TEXT+' Not confirmed.',TEXT.split('. The increase')[0]+'.',TEXT.replace('was recognized and confirmed','might be recognized'),TEXT.replace('in license revenue','in total GAAP revenue')]:
   self.assertEqual(m.txmd_extract(document(text))['status'],'NOT_SUPPORTED_GRAMMAR')
  for raw in [b'<blockquote>'+document()+b'</blockquote>',b'<q>'+document(),document().replace(b'<TD>',b'<TD><q>').replace(b'</TD>',b'</q></TD>')]:
   with self.assertRaises(ValueError):m.txmd_extract(raw)
 def test_duplicate_hidden_malformed_encoding_and_periods(self):
  self.assertEqual(m.txmd_extract(document()+document())['status'],'AMBIGUOUS_MULTIPLE_SUPPORTED_PARAGRAPHS')
  self.assertEqual(m.txmd_extract(document().replace(b'<TD>',b'<!--<TD>').replace(b'</TD>',b'</TD>-->'))['status'],'NOT_SUPPORTED_GRAMMAR')
  for raw in [document()+b'<DOCUMENT>',document().decode().encode('utf-16'),b'<!DOCTYPE html>'+document(),document(TEXT.replace('third quarter of 2023','second quarter of 2023'))]:
   with self.assertRaises((ValueError,UnicodeError)):m.txmd_extract(raw)
 def test_completion_failure_marker_and_modes(self):
  with tempfile.TemporaryDirectory() as td:
   out=Path(td)/'done'
   with patch.object(m,'build',return_value=({'safe':True},[{'private':'text'}])):m.save(ROOT,'fixture',{},'policy',out)
   self.assertFalse((out/'INCOMPLETE').exists());self.assertEqual(out.stat().st_mode&0o777,0o700);self.assertEqual((out/'finding.json').stat().st_mode&0o777,0o600);self.assertEqual(json.loads((out/'COMPLETE.json').read_text())['finding_sha256'],m.sha(out/'finding.json'))
   with self.assertRaises(ValueError):m.save(ROOT,'fixture',{},'policy',out)
   with patch.object(m,'build',side_effect=ValueError('source mismatch')):
    with self.assertRaises(ValueError):m.save(ROOT,'fixture',{},'policy',Path(td)/'failed')
   self.assertTrue((Path(td)/'failed/INCOMPLETE').exists());self.assertFalse((Path(td)/'failed/COMPLETE.json').exists())
 def test_build_rejects_changed_adapter_source_and_vita_pins_before_completion(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);(root/'backend').mkdir();adapter=root/'backend/adapter.py';adapter.write_bytes(b'original adapter')
   source=root/'source.json';source.write_bytes(b'{}')
   policy={'existing_module_versions':{'adapter.py':m.sha(adapter)},'vita_archive_sha256':'a'*64}
   policy_path=root/'policy.json';policy_path.write_text(json.dumps(policy))
   pins={'fixture':{'path':'source.json','bytes':2,'sha256':m.sha(source)}}
   with patch.object(m,'POLICY_SHA',m.sha(policy_path)),patch.object(m,'PINS',pins),patch.object(m,'inventory_audit') as inventory:
    for failure in ['vita','adapter','source']:
     adapter.write_bytes(b'original adapter');source.write_bytes(b'{}');cfg={'archive_sha':'a'*64}
     if failure=='vita':cfg['archive_sha']='b'*64
     if failure=='adapter':adapter.write_bytes(b'changed adapter')
     if failure=='source':source.write_bytes(b'[]')
     out=root/('failed-'+failure)
     with self.assertRaises(ValueError):m.save(root,'not-read.zip',cfg,policy_path,out)
     self.assertTrue((out/'INCOMPLETE').exists());self.assertFalse((out/'COMPLETE.json').exists());self.assertFalse((out/'finding.json').exists())
    inventory.assert_not_called()
 def test_published_scope_and_old_artifact_pins(self):
  for p in m.PINS.values():
   b=(ROOT/p['path']).read_bytes();self.assertEqual(len(b),p['bytes']);self.assertEqual(m.digest(b),p['sha256'])
  raw=(ROOT/'web/company-findings/financial-assertion-audit.json').read_bytes();d=json.loads(raw)
  self.assertEqual(d['counts'],{'packages':11,'supported_packages':3,'unsupported_packages':8,'metric_pairs':7});self.assertNotIn(b'source_paragraph_text',raw);self.assertNotIn(b'/workspace/',raw)
  for p in d['packages']:
   for pair in p['metric_pairs']:
    self.assertIn('current_value_for_arithmetic',pair);self.assertIn('prior_value_for_arithmetic',pair);self.assertNotIn('current_literal',pair);self.assertFalse(pair['comparability_verified']);self.assertFalse(pair['training_ready']);self.assertFalse(pair['arithmetic']['qualified_growth'])
  tx=next(p for p in d['packages'] if p['accession']==m.TXMD_ACC);self.assertTrue(tx['source_period_conflict']['description_body_period_conflict']);self.assertEqual(tx['metric_pairs'][0]['issuer_reported_attribution']['sales_year_end_as_reported'],'December 31, 2025');self.assertIsNone(tx['metric_pairs'][0]['periods_as_reported']['prior_end'])
if __name__=='__main__':unittest.main()
