import unittest
from revvity_basis_review import compare_text,exhibit

PRIOR='For the full year 2026, on a pro forma basis, the Company forecasts total revenue of approximately $2.86 billion, pro forma organic revenue growth of approximately 5%, and pro forma adjusted earnings per share of $5.40-$5.45. forward-looking guidance is provided on a pro forma basis only and excludes China IDX.'
LATER='2026E Revenue: ~$2.9B based on 2026 pro forma guidance as provided on November 3, 2026 Immunodiagnostics business in China ~6% organic growth 2027 considerations Formal 2027 guidance to be provided on our Q4 earnings call'
class BasisTests(unittest.TestCase):
 def test_rounding_not_raise_cross_year_not_delta(self):
  r=compare_text(PRIOR,LATER)
  self.assertEqual(r['rounded_prior_one_decimal'],'2.9');self.assertFalse(r['guidance_raise_verified'])
  self.assertEqual(r['organic_growth_comparison'],'DIFFERENT_FISCAL_YEAR_NO_SAME_PERIOD_DELTA')
  self.assertIsNone(r['eps_raise_comparison']);self.assertIsNone(r['fy2026_prior']['currency_iso'])
 def test_missing_exclusion_rejected(self):
  with self.assertRaises(ValueError):compare_text(PRIOR.replace('excludes China IDX','includes China IDX'),LATER)
 def test_wrong_prior_basis(self):
  with self.assertRaises(ValueError):compare_text(PRIOR.replace('pro forma','reported'),LATER)
 def test_new_values_require_review(self):
  with self.assertRaises(ValueError):compare_text(PRIOR.replace('2.86','3.00'),LATER)
 def test_missing_period_rejected(self):
  with self.assertRaises(ValueError):compare_text(PRIOR,LATER.replace('2027 considerations','2026 considerations'))
 def test_missing_formal_caveat_rejected(self):
  with self.assertRaises(ValueError):compare_text(PRIOR,LATER.replace('Formal 2027 guidance to be provided on our Q4 earnings call',''))
 def raw(self,form='8-K',cik='31791'):
  return f'<SEC-DOCUMENT>file\n<SEC-HEADER>\nACCESSION NUMBER: 0000031791-26-000031\nCENTRAL INDEX KEY: {cik}\nCONFORMED SUBMISSION TYPE: {form}\n</SEC-HEADER>\n<DOCUMENT>\n<TYPE>EX-99.1\n<TEXT><p>literal</p></TEXT></DOCUMENT>'.encode()
 def test_amendment_rejected(self):
  with self.assertRaises(ValueError):exhibit(self.raw('8-K/A'),'0000031791-26-000031','EX-99.1')
 def test_wrong_entity_rejected(self):
  with self.assertRaises(ValueError):exhibit(self.raw(cik='108772'),'0000031791-26-000031','EX-99.1')
 def test_span_hash(self):
  import hashlib
  raw=self.raw();_,s=exhibit(raw,'0000031791-26-000031','EX-99.1')
  self.assertEqual(hashlib.sha256(raw[s['byte_start']:s['byte_end']]).hexdigest(),s['sha256'])
if __name__=='__main__':unittest.main()
