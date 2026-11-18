import unittest,tempfile
from pathlib import Path
from unittest.mock import patch
import material_agreement_screen as m
def fixture(item=True,kind='8-K'):
 return ('<SEC-HEADER>\n'+('ITEM INFORMATION:\t'+m.ITEM+'\n' if item else '')+'</SEC-HEADER>\n<DOCUMENT>\n<TYPE>'+kind+'\n<FILENAME>filing.htm\n<TEXT>\n<p>Example.</p></TEXT></DOCUMENT>\n<DOCUMENT>\n<TYPE>EX-10.1\n<FILENAME>contract.htm\n<TEXT>\n<p>Example.</p></TEXT></DOCUMENT>').encode()
class AgreementTests(unittest.TestCase):
 def test_declared_item_is_review_only(self):
  raw=fixture();r=m.screen(raw);self.assertTrue(r['item_1_01_declared']);self.assertFalse(r['event_verified']);self.assertEqual(len(r['contract_or_security_exhibits']),1);s=r['primary']['source_span'];self.assertEqual(m.digest(raw[s['byte_start']:s['byte_end']]),s['sha256'])
 def test_absent_header_not_no_agreement(self):
  r=m.screen(fixture(False));self.assertIn('NOT_NO_AGREEMENT',r['status']);self.assertEqual(len(r['contract_or_security_exhibits']),1)
 def test_amendment_requires_review(self):self.assertEqual(m.screen(fixture(kind='8-K/A'))['status'],'AMENDMENT_REQUIRES_REVIEW')
 def test_invalid_inventory(self):
  for raw in [fixture()+b'<DOCUMENT>',fixture().replace(b'<TEXT>',b'<DOCUMENT><TEXT>',1),fixture().replace(b'contract.htm',b'../bad'),fixture().replace(b'<TYPE>8-K',b'<TYPE>8-K\n<TYPE>8-K'),fixture().replace(b'</SEC-HEADER>',('ITEM INFORMATION:'+m.ITEM+'\n</SEC-HEADER>').encode()),fixture().replace(b'<TYPE>EX-10.1',b'<TYPE>8-K')]:
   with self.assertRaises(ValueError):m.screen(raw)
 def test_encoding_and_review_pin(self):
  with self.assertRaises((ValueError,UnicodeError)):m.screen(fixture().decode().encode('utf-16'))
  with self.assertRaises(ValueError):m.reviewed_exchange(fixture())
 def test_failure_marker(self):
  with tempfile.TemporaryDirectory() as t:
   out=Path(t)/'out'
   with patch.object(m,'build',side_effect=ValueError('pin')):
    with self.assertRaises(ValueError):m.save('bad',out)
   self.assertTrue((out/'INCOMPLETE').exists());self.assertFalse((out/'COMPLETE.json').exists())
if __name__=='__main__':unittest.main()
