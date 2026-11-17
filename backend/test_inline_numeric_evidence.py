"""Synthetic lexical fixtures; not market evidence."""
import copy
from decimal import localcontext
import unittest
from inline_numeric_evidence import convert,TRR3

class NumericTests(unittest.TestCase):
    def fixture(self,text='1,234.50',kind='numdotdecimal'):
        return {'text_complete':True,'exclude_element_present':False,'continuation_ref_as_filed':None,'nil_as_filed':None,'scale_as_filed':None,'sign_as_filed':None,'format':{'namespace':TRR3,'local_name':kind},'text_untransformed':text}
    def test_decimal_and_sign(self):
        f=self.fixture();self.assertEqual(convert(f),'1234.50');f['sign_as_filed']='-';self.assertEqual(convert(f),'-1234.50')
    def test_exact_low_context(self):
        with localcontext() as c:
            c.prec=3
            self.assertEqual(convert(self.fixture('123456789012345678901234567890.123456789')), '123456789012345678901234567890.123456789')
    def test_dash_not_missing(self):
        self.assertEqual(convert(self.fixture(' \n-\t','zerodash')),'0')
        for t in ['','—','0','nil','1']:
            with self.subTest(t=t),self.assertRaises(ValueError):convert(self.fixture(t,'zerodash'))
    def test_lexical_rejections(self):
        for t in ['-1','+1','1e3','NaN','Infinity','.1','1.','12,34','1 234','1\u00a0234','١','1'*101,' '*257]:
            with self.subTest(t=t),self.assertRaises(ValueError):convert(self.fixture(t))
    def test_semantic_rejections(self):
        for k,v in [('text_complete',False),('exclude_element_present',True),('continuation_ref_as_filed','next'),('nil_as_filed','true'),('scale_as_filed','0'),('scale_as_filed','10000000'),('sign_as_filed','+'),('format',None),('format',{'namespace':TRR3+'x','local_name':'numdotdecimal'}),('format',{'namespace':TRR3,'local_name':'fixed-zero'})]:
            f=self.fixture();f[k]=v
            with self.subTest(k=k,v=v),self.assertRaises(ValueError):convert(f)
    def test_accuracy_preserved_no_rounding(self):
        f=self.fixture('1.2345');f['decimals_as_filed']='0';before=copy.deepcopy(f)
        self.assertEqual(convert(f),'1.2345');self.assertEqual(f,before)
    def test_actual_archive_flow_preserves_unsupported_records(self):
        import tempfile,zipfile,json
        from pathlib import Path
        import test_inline_context_evidence as fixtures
        from inline_numeric_evidence import audit
        from inline_context_evidence import digest,sha
        from financial_pair_candidates import publish,write_private
        raw=fixtures.InlineEvidenceTests().xml()
        # One supported zero and one scaled fact outside the declared subset.
        original=raw[raw.index(b'<ix:nonFraction'):raw.index(b'</ix:nonFraction>')+len(b'</ix:nonFraction>')]
        raw=raw.replace(original,original.replace(b' scale="3"',b'')+original.replace(b'id="f1"',b'id="f2"'))
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'fixture.zip'
            with zipfile.ZipFile(p,'w') as z:z.writestr('primary.htm',raw)
            summary,rows=audit(p,sha(p),'primary.htm',digest(raw))
            self.assertEqual(summary['numeric_conversions'],1);self.assertEqual(summary['unsupported_fact_count'],1)
            self.assertEqual(rows[0]['numeric_value'],'0');self.assertIsNone(rows[1]['numeric_value'])
            self.assertFalse(rows[1]['numeric_conversion_verified']);self.assertFalse(summary['training_ready'])
            out=Path(td)/'output';out.mkdir();write_private(out/'INCOMPLETE',{'status':'INCOMPLETE'})
            publish(out,summary,rows)
            self.assertFalse((out/'INCOMPLETE').exists());self.assertTrue((out/'COMPLETE.json').exists())
            self.assertEqual(json.loads((out/'candidate-pairs.json').read_text()),rows)
