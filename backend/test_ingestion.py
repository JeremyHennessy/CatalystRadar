import unittest
from batch_ingest import extract
A='0000000001-26-000001'
def sample(date='20261113160500'):
 return (f'<SEC-DOCUMENT>{A}.txt\n<SEC-HEADER>\n<ACCEPTANCE-DATETIME>{date}\nACCESSION NUMBER: {A}\nCENTRAL INDEX KEY: 0000000001\nITEM INFORMATION: Results of Operations and Financial Condition\n<DOCUMENT><TYPE>8-K\n<FILENAME>report.htm\n<TEXT><html>Item 2.02 Results</html></TEXT></DOCUMENT>').encode()
class Tests(unittest.TestCase):
 def test_winter_timezone(self):self.assertEqual(extract(sample(),A,'1')['sec_accepted_utc'],'2026-11-13T21:05:00+00:00')
 def test_summer_timezone(self):self.assertEqual(extract(sample('20260713160500'),A,'1')['sec_accepted_utc'],'2026-07-13T20:05:00+00:00')
 def test_identity(self):self.assertRaises(ValueError,extract,sample(),A,'2')
 def test_multi_entity(self):self.assertTrue(extract(sample().replace(b'<DOCUMENT>',b'CENTRAL INDEX KEY: 0000000002\n<DOCUMENT>',1),A,'2')['multi_entity_header'])
 def test_ex101_excluded(self):self.assertEqual(extract(sample().replace(b'<TYPE>8-K',b'<TYPE>EX-101.SCH'),A)['selected_document_inventory'],[])
 def test_invalid_response(self):self.assertRaises(ValueError,extract,b'<html>Forbidden</html>',A)
 def test_no_first_public(self):self.assertIsNone(extract(sample(),A)['first_public_utc'])
 def test_inventory(self):self.assertEqual(extract(sample(),A)['selected_document_inventory'][0]['item_mentions_not_verified_headings'],['2.02'])
if __name__=='__main__':unittest.main()
