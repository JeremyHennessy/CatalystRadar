import copy,hashlib,tempfile,unittest,zipfile
from pathlib import Path
import inline_context_evidence as m

class InlineEvidenceTests(unittest.TestCase):
    def xml(self,facts=None):
        facts=facts or '<ix:nonFraction id="f1" name="g:Revenues" contextRef="c" unitRef="dollars" format="t:zerodash" scale="3">-</ix:nonFraction>'
        return ('''<html xmlns="http://www.w3.org/1999/xhtml" xmlns:ix="http://www.xbrl.org/2013/inlineXBRL" xmlns:x="http://www.xbrl.org/2003/instance" xmlns:g="http://fasb.org/us-gaap/2025" xmlns:t="http://www.xbrl.org/inlineXBRL/transformation/2015-02-26" xmlns:money="http://www.xbrl.org/2003/iso4217" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"><x:context id="c"><x:entity><x:identifier scheme="http://www.sec.gov/CIK">123</x:identifier></x:entity><x:period><x:startDate>2025-05-01</x:startDate><x:endDate>2025-07-31</x:endDate></x:period></x:context><x:unit id="dollars"><x:measure>money:USD</x:measure></x:unit>'''+facts+'</html>').encode()
    def parse(self,b):return m.parse(b,m.digest(b))
    def test_actual_context_not_guessed_unit_or_numeric_value(self):
        f=self.parse(self.xml())[0];self.assertEqual(f['period']['startDate'],'2025-05-01');self.assertEqual(f['unit']['measures'][0]['local_name'],'USD');self.assertEqual(f['unit_ref'],'dollars')
        self.assertEqual(f['text_untransformed'],'-');self.assertEqual(f['scale_as_filed'],'3');self.assertIsNone(f['numeric_value']);self.assertFalse(f['training_ready']);self.assertTrue(f['text_complete'])
        self.assertEqual(f['context_serialization_sha256'],m.digest(f['context_xml_serialized'].encode('ascii')))
    def test_namespace_rebinding_is_per_element(self):
        a='<ix:nonFraction id="f1" name="g:Revenues" contextRef="c" unitRef="dollars">1</ix:nonFraction>'
        b='<div xmlns:g="http://fasb.org/us-gaap/2026">'+a.replace('f1','f2')+'</div>'
        out=self.parse(self.xml(a+b));self.assertEqual([x['concept']['namespace'] for x in out],['http://fasb.org/us-gaap/2025','http://fasb.org/us-gaap/2026'])
    def test_dtd_entity_and_duplicate_ids_fail(self):
        for raw in [b'<!DOCTYPE html>'+self.xml(),b'<!ENTITY x "bad">'+self.xml(),self.xml().replace(b'id="f1"',b'id="c"')]:
            with self.assertRaises(ValueError):self.parse(raw)
    def test_refs_and_namespace_fail_closed(self):
        for old,new in [(b'contextRef="c"',b'contextRef="absent"'),(b'unitRef="dollars"',b'unitRef="missing"'),(b'name="g:Revenues"',b'name="missing:Revenues"'),(b'id="f1"',b'id="bad id"'),(b'unitRef="dollars"',b'unitRef="dollars" continuedAt="missing"')]:
            with self.assertRaises(ValueError):self.parse(self.xml().replace(old,new))
    def test_inverted_or_ambiguous_period(self):
        for raw in [self.xml().replace(b'2025-05-01',b'2025-08-01'),self.xml().replace(b'</x:period>',b'<x:instant>2025-07-31</x:instant></x:period>')]:
            with self.assertRaises(ValueError):self.parse(raw)
    def test_nil_continuation_and_exclusion_not_converted(self):
        raw=self.xml('<ix:nonFraction id="f1" name="g:Revenues" contextRef="c" unitRef="dollars" xsi:nil="true" continuedAt="more"><ix:exclude>note</ix:exclude></ix:nonFraction><ix:continuation id="more">tail</ix:continuation>')
        f=self.parse(raw)[0];self.assertEqual(f['nil_as_filed'],'true');self.assertFalse(f['text_complete']);self.assertTrue(f['exclude_element_present']);self.assertIsNone(f['numeric_value'])
    def test_divided_unit_and_dimensions_preserved(self):
        raw=self.xml().replace(b'<x:measure>money:USD</x:measure>',b'<x:divide><x:unitNumerator><x:measure>money:USD</x:measure></x:unitNumerator><x:unitDenominator><x:measure>x:shares</x:measure></x:unitDenominator></x:divide>').replace(b'</x:entity>',b'<x:segment><typed xmlns="urn:synthetic">dimension</typed></x:segment></x:entity>')
        f=self.parse(raw)[0];self.assertEqual(f['unit']['kind'],'divide');self.assertTrue(f['dimension_or_scenario_present']);self.assertIn('dimension',f['context_xml_serialized'])
    def test_archive_hash_bounds_and_duplicate_member(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'synthetic.zip';raw=self.xml()
            with zipfile.ZipFile(p,'w') as z:z.writestr('primary.htm',raw)
            summary,f=m.extract(p,m.sha(p),'primary.htm',m.digest(raw));self.assertEqual(summary['target_fact_count'],1)
            with self.assertRaises(ValueError):m.extract(p,'0'*64,'primary.htm',m.digest(raw))
            with self.assertWarns(UserWarning):
                with zipfile.ZipFile(p,'a') as z:z.writestr('primary.htm',raw)
            with self.assertRaisesRegex(ValueError,'inventory'):m.extract(p,m.sha(p),'primary.htm',m.digest(raw))
    def test_nested_and_oversized_fact_text_rejected(self):
        inner='<ix:nonFraction id="f2" name="g:Revenues" contextRef="c" unitRef="dollars">1</ix:nonFraction>'
        outer='<ix:nonFraction id="f1" name="g:Revenues" contextRef="c" unitRef="dollars">'+inner+'</ix:nonFraction>'
        for raw in [self.xml(outer),self.xml().replace(b'>-</ix:nonFraction>',b'>'+b'1'*100001+b'</ix:nonFraction>')]:
            with self.assertRaises(ValueError):self.parse(raw)
    def test_utf16_and_alias_member_rejected(self):
        fixture='<!DOCTYPE html [<!ENTITY evil "expanded">]>'+self.xml().decode()
        for encoding in ['utf-16','utf-16-le','utf-16-be','utf-32','utf-32-le','utf-32-be']:
            with self.subTest(encoding=encoding):
                with self.assertRaises(ValueError):self.parse(fixture.encode(encoding))
        with self.assertRaises(ValueError):self.parse(b"<?xml version='1.0' encoding='ISO-8859-1'?>"+self.xml())
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'alias.zip'
            with zipfile.ZipFile(p,'w') as z:z.writestr('./primary.htm',self.xml())
            with self.assertRaises(ValueError):m.extract(p,m.sha(p),'./primary.htm',m.digest(self.xml()))
    def test_missing_or_unsupported_ids_and_fraction(self):
        for raw in [self.xml().replace(b'id="f1" ',b''),self.xml().replace(b'nonFraction',b'fraction'),self.xml().replace(b'/2013/inlineXBRL',b'/2008/inlineXBRL')]:
            with self.assertRaises(ValueError):self.parse(raw)

if __name__=='__main__':unittest.main()
