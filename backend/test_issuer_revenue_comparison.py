import json,tempfile,unittest
from decimal import localcontext
from pathlib import Path
from unittest.mock import patch
import issuer_revenue_comparison as m

TEXT='For the quarter ended September 30, 2026, SYNTHETIC had revenues of $15,000 as compared to $10,000 for the quarter ended September 30, 2025, reflecting a 50% increase; an operating profit of $100 for 2nd quarter fiscal year 2027 as compared to an operating loss of $10 for 2nd quarter fiscal year 2026; net income of $80 for 2nd quarter fiscal year 2027 as compared to a net loss of $5 for 2nd quarter fiscal year 2026; and a basic gain per share of $.55 for 2nd quarter fiscal year 2027 as compared to a basic loss per share of $.01 for 2nd quarter fiscal year 2026.'
def document(text=TEXT):return ('<DOCUMENT>\n<TYPE>EX-99.1\n<FILENAME>ex99.htm\n<TEXT>\n<P>'+text+'</P>\n</TEXT>\n</DOCUMENT>').encode()
class ComparisonTests(unittest.TestCase):
 def test_reported_comparison_not_comparability_currency_or_start(self):
  e=m.extract(document());self.assertEqual(e['status'],'ONE_REPORTED_TEXT_COMPARISON');r=e['records'][0];self.assertEqual(r['current_value'],'15000');self.assertEqual(r['prior_value'],'10000');self.assertEqual(r['arithmetic']['difference'],'5000');self.assertEqual(r['arithmetic']['percent_rounded_two_decimals'],'50.00');self.assertTrue(r['reported_percent_matches_nearest_whole']);self.assertIsNone(r['currency_iso']);self.assertIsNone(r['current_period_start']);self.assertFalse(r['accounting_comparability_verified']);self.assertFalse(e['training_ready']);span=r['evidence_span'];self.assertEqual(m.digest(document()[span['byte_start']:span['byte_end']]),span['sha256'])
 def test_negative_quote_partial_and_other_grammar_not_assertions(self):
  for text in ['The following is false: '+TEXT,'"'+TEXT+'"',TEXT+' We deny the preceding comparison.',TEXT.replace('had revenues','may have revenues'),TEXT[:150]]:
   self.assertEqual(m.extract(document(text))['status'],'NO_SUPPORTED_COMPARISON')
 def test_hidden_comments_multiple_and_malformed_inventory(self):
  b=document().replace(b'<P>',b'<!--<P>').replace(b'</P>',b'</P>-->');self.assertEqual(m.extract(b)['status'],'NO_SUPPORTED_COMPARISON')
  self.assertEqual(m.extract(document()+document())['status'],'AMBIGUOUS_MULTIPLE_COMPARISONS')
  for b in [document()+b'<DOCUMENT>',document().replace(b'<P>',b'<DOCUMENT><P>'),document().replace(b'</TEXT>',b''),document().replace(b'ex99.htm',b'../ex99.htm')]:
   with self.assertRaises(ValueError):m.extract(b)
 def test_encoding_declaration_and_bound(self):
  for b in [document().decode().encode('utf-16'),b'<!ENTITY x "a">'+document(),b'<!DOCTYPE html>'+document(),b'x'*25_000_001,b'']:
   with self.assertRaises((ValueError,UnicodeError)):m.extract(b)
 def test_zero_negative_bad_commas_precision_and_dates(self):
  for text in [TEXT.replace('$10,000','$0'),TEXT.replace('$15,000','$1,000')]:
   with self.assertRaises(ValueError):m.extract(document(text))
  self.assertEqual(m.extract(document(TEXT.replace('$15,000','$15,00')))['status'],'NO_SUPPORTED_COMPARISON')
  with self.assertRaises(ValueError):m.extract(document(TEXT.replace('September 30, 2026','February 30, 2026')))
  with localcontext() as c:
   c.prec=3;r=m.exact_ratio('10,700,084','7,077,592');self.assertEqual(r['difference'],'3622492');self.assertEqual(r['percent_rounded_two_decimals'],'51.18');self.assertEqual(r['percent_rounded_whole'],51)
 def test_rounded_report_mismatch_is_preserved(self):
  r=m.extract(document(TEXT.replace('50%','49%')))['records'][0];self.assertFalse(r['reported_percent_matches_nearest_whole']);self.assertEqual(r['reported_percent_increase'],'49')
 def test_private_completion_failure_and_existing_destination(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);card={'private_test':False};e={'source_paragraph_text':'private test context'}
   with patch.object(m,'load_source',return_value=(b'',{})),patch.object(m,'build',return_value=(card,e)):
    self.assertEqual(m.save('fixture',root/'out'),card)
   self.assertFalse((root/'out/INCOMPLETE').exists());self.assertEqual(json.loads((root/'out/COMPLETE.json').read_text())['finding_sha256'],m.sha(root/'out/finding.json'));self.assertEqual((root/'out/finding.json').stat().st_mode&0o777,0o600)
   with self.assertRaises(ValueError):m.save('fixture',root/'out')
   with patch.object(m,'load_source',side_effect=ValueError('bad hash')):
    with self.assertRaises(ValueError):m.save('fixture',root/'failed')
   self.assertTrue((root/'failed/INCOMPLETE').exists());self.assertFalse((root/'failed/COMPLETE.json').exists())
 def test_unreviewed_source_and_wrong_receipt_fail_closed(self):
  with self.assertRaises(ValueError):m.build(document(),{})
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/'bad.zip';p.write_bytes(b'not source')
   with self.assertRaises(ValueError):m.load_source(p)
