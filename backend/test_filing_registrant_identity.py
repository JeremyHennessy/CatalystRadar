import copy,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from filing_registrant_identity import extract,digest,pinned,strict,save
ACC='0000000001-26-000001'
def fixture():
 h=f'<SEC-DOCUMENT>fixture\n<SEC-HEADER>\nACCESSION NUMBER: {ACC}\n'
 for ci,name in [('0000000001','PARENT CORP'),('0000000002','SUB CORP')]:
  h+=f'FILER:\n\tCOMPANY DATA:\n\t\tCOMPANY CONFORMED NAME: {name}\n\t\tCENTRAL INDEX KEY: {ci}\n\tFILING VALUES:\n\t\tFORM TYPE: 8-K\n\tBUSINESS ADDRESS:\n\t\tSTREET 1: PRIVATE ADDRESS\n'
 return (h+'</SEC-HEADER>\n<DOCUMENT>private document</DOCUMENT>').encode()
class RegistrantIdentityTest(unittest.TestCase):
 def test_distinct_roles_and_exact_field_spans(self):
  raw=fixture();e=extract(raw,ACC);self.assertTrue(e['multiple_filers']);self.assertFalse(e['entities_interchangeable']);self.assertFalse(e['facts_propagated_between_filers'])
  for record in e['filers']:
   for field,key in [('cik','cik'),('name','name_as_filed')]:
    s=record['field_spans'][field];b=raw[s['byte_start']:s['byte_end']];self.assertEqual(b.decode(),record[key]);self.assertEqual(digest(b),s['sha256'])
  self.assertNotIn('PRIVATE ADDRESS',str(e));self.assertNotIn('private document',str(e))
 def test_single_filer_no_plural_inference(self):
  raw=fixture();a=raw.index(b'FILER:',raw.index(b'FILER:')+1);raw=raw[:a]+b'</SEC-HEADER>'
  self.assertFalse(extract(raw,ACC)['multiple_filers'])
 def test_ambiguous_or_unclassified_identity_fails(self):
  for raw in [fixture().replace(b'0000000002',b'0000000001'),fixture().replace(b'CENTRAL INDEX KEY: 0000000002',b'CENTRAL INDEX KEY: 0000000002\n\t\tCENTRAL INDEX KEY: 0000000003'),fixture().replace(b'FILER:',b'SUBJECT COMPANY:',1),fixture().replace(b'\t\tCENTRAL INDEX KEY: 0000000001',b'\t\tCENTRAL INDEX KEY: 0'),fixture().replace(b'\tCOMPANY DATA:',b'\tOTHER ROLE:',1),fixture().replace(b'\tFILING VALUES:',b'\tCOMPANY CONFORMED NAME: OTHER\n\tFILING VALUES:',1)]:
   with self.subTest(raw=raw[:40]),self.assertRaises(ValueError):extract(raw,ACC)
 def test_bounds_header_and_accession_fail(self):
  for raw in [fixture()+b'</SEC-HEADER>',fixture().replace(b'</SEC-HEADER>',b''),fixture().replace(b'PARENT CORP',b'\0BAD'),fixture().replace(b'PARENT CORP',b'<!ENTITY evil>'),fixture().replace(b'\tFILING VALUES:',b'<DOCUMENT>\n\tFILING VALUES:',1),fixture().replace(b'<SEC-HEADER>',b'<SEC-HEADER>'+b' '*100000)]:
   with self.assertRaises(ValueError):extract(raw,ACC)
  with self.assertRaises(ValueError):extract(fixture(),'0000000002-26-000001')
 def test_strict_json_and_single_buffer_pin(self):
  for b in (b'{"x":1,"x":2}',b'{"x":NaN}'):
   with self.assertRaises(ValueError):strict(b)
  with tempfile.TemporaryDirectory() as t:
   p=Path(t)/'input';p.write_bytes(b'abc');self.assertEqual(pinned(p,digest(b'abc'),3),b'abc')
   with self.assertRaises(ValueError):pinned(p,digest(b'abc'),2)
   with self.assertRaises(ValueError):pinned(p,'0'*64,3)
 def test_failed_build_leaves_incomplete(self):
  with tempfile.TemporaryDirectory() as t:
   out=Path(t)/'result'
   with patch('filing_registrant_identity.build',side_effect=ValueError('bad source')):
    with self.assertRaises(ValueError):save('zip','root',out)
   self.assertTrue((out/'INCOMPLETE').exists());self.assertFalse((out/'COMPLETE.json').exists())
if __name__=='__main__':unittest.main()
