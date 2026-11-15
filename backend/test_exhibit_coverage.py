import unittest
from exhibit_coverage import inventory

def doc(typ='EX-99.1',seq='2'):
 return f'<DOCUMENT>\n<TYPE>{typ}\n<SEQUENCE>{seq}\n<FILENAME>ex.htm\n<TEXT><P>body</P><IMG src="a.png"></TEXT></DOCUMENT>'.encode()
class CoverageTests(unittest.TestCase):
 def test_all_types_counted_exhibits_bounded(self):
  r=inventory(doc()+doc('GRAPHIC','3'))
  self.assertEqual(r['embedded_document_count'],2);self.assertEqual(len(r['ex99_exhibits']),1)
  self.assertEqual(r['ex99_exhibits'][0]['html_image_reference_count'],1)
  self.assertFalse(r['ex99_exhibits'][0]['text_and_graphics_completeness_reviewed'])
 def test_span_hash(self):
  import hashlib
  raw=b'prefix'+doc();r=inventory(raw)['ex99_exhibits'][0]
  self.assertEqual(hashlib.sha256(raw[r['byte_start']:r['byte_end']]).hexdigest(),r['sha256'])
 def test_incomplete(self):
  with self.assertRaises(ValueError):inventory(doc()[:-11])
 def test_duplicate_sequence(self):
  with self.assertRaises(ValueError):inventory(doc()+doc())
 def test_missing_type(self):
  with self.assertRaises(ValueError):inventory(doc().replace(b'<TYPE>',b'<OTHER>'))
 def test_type_in_body_does_not_define_exhibit(self):
  self.assertEqual(len(inventory(doc('GRAPHIC').replace(b'body',b'<TYPE>EX-99.1'))['ex99_exhibits']),0)
 def test_no_exhibits_not_missing_documents(self):
  self.assertEqual(inventory(doc('8-K'))['ex99_exhibits'],[])
 def test_amendment_is_not_original(self):
  self.assertEqual(inventory(doc('8-K/A'))['document_type_counts'],{'8-K/A':1})
if __name__=='__main__':unittest.main()
