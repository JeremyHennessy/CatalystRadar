import unittest
from retained_security_class import inspect, ACC, CIK, FIELDS

# Synthetic minimal XHTML/SGML fixture; no retained raw filing or private prices.
def fixture():
    fields=''.join('<td><ix:nonNumeric contextRef="AsOf2026-11-13" id="f'+str(i)+'" name="dei:'+name+'"'+(' format="ixt-sec:exchnameen"' if name=='SecurityExchangeName' else '')+'>'+value+'</ix:nonNumeric></td>' for i,(name,value) in enumerate(FIELDS.items()))
    fields=fields.replace('<td><ix:nonNumeric contextRef="AsOf2026-11-13" id="f2"','<td>The <ix:nonNumeric contextRef="AsOf2026-11-13" id="f2"').replace('>Nasdaq</ix:nonNumeric></td>','>Nasdaq</ix:nonNumeric> Stock Market LLC</td>')
    return (f'''<SEC-DOCUMENT>\n<SEC-HEADER>
ACCESSION NUMBER: {ACC}
FILER:
 COMPANY DATA:
  COMPANY CONFORMED NAME: TherapeuticsMD, Inc.
  CENTRAL INDEX KEY: {CIK}
 FILING VALUES:
  FORM TYPE: 8-K
</SEC-HEADER>
<DOCUMENT>
<TYPE>8-K
<FILENAME>ea0312204-8k_therapeu.htm
<TEXT>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:ix="http://www.xbrl.org/2013/inlineXBRL" xmlns:xbrli="http://www.xbrl.org/2003/instance" xmlns:dei="http://xbrl.sec.gov/dei/2026"><body>
<xbrli:context id="AsOf2026-11-13"><xbrli:entity><xbrli:identifier scheme="http://www.sec.gov/CIK">{CIK}</xbrli:identifier></xbrli:entity><xbrli:period><xbrli:startDate>2026-11-13</xbrli:startDate><xbrli:endDate>2026-11-13</xbrli:endDate></xbrli:period></xbrli:context>
<table><tr><td>Title of Each Class</td><td>Trading Symbol</td><td>Name of Each Exchange on Which Registered</td></tr><tr>{fields}</tr></table>
</body></html>
</TEXT>
</DOCUMENT>
</SEC-DOCUMENT>''').encode()

class SecurityClassTests(unittest.TestCase):
    def test_source_spans_and_context_not_mapping(self):
        import hashlib
        raw=fixture();d=inspect(raw)
        for f in list(d['fields'].values())+[d['context']]:
            s=f['source_span'];self.assertEqual(hashlib.sha256(raw[s['byte_start']:s['byte_end']]).hexdigest(),s['sha256'])
        self.assertEqual(d['context']['period_kind'],'DURATION_AS_FILED_NOT_EFFECTIVE_INTERVAL')
        self.assertFalse(d['registrant_evidence']['security_mapping_verified'])
    def test_negative_cases(self):
        raw=fixture()
        changes=[(b'>TXMD<',b'>OTHER<'),(b'name="dei:TradingSymbol"',b'name="dei:TradingSymbol" continuedAt="more"'),(b'xmlns:dei="http://xbrl.sec.gov/dei/2026"',b'xmlns:dei="https://evil.test"'),(b'<table>',b'<table style="display:none">'),(b'<table>',b'<table hidden="hidden">'),(b'<xbrli:period>',b'<xbrli:segment/><xbrli:period>'),(b'<xbrli:endDate>2026-11-13',b'<xbrli:endDate>2026-11-14'),(b'<TYPE>8-K',b'<TYPE>8-K/A'),(b'>0000025743</xbrli:identifier>',b'>0000000001</xbrli:identifier>'),(b'<td>The <ix:',b'</tr><tr><td>The <ix:'),(b'Title of Each Class',b'Not a security class'),(b'format="ixt-sec:exchnameen"',b'format="evil:exchange"')]
        for old,new in changes:
            with self.subTest(new=new),self.assertRaises(ValueError):inspect(raw.replace(old,new))
    def test_duplicate_context_fact_doc_and_comment(self):
        import re
        raw=fixture()
        for pattern in [rb'<xbrli:context.*?</xbrli:context>',rb'<ix:nonNumeric[^>]*name="dei:TradingSymbol".*?</ix:nonNumeric>',rb'<DOCUMENT>.*?</DOCUMENT>']:
            part=re.search(pattern,raw,re.S)[0]
            with self.assertRaises(ValueError):inspect(raw.replace(part,part+part))
        part=re.search(rb'<ix:nonNumeric[^>]*name="dei:TradingSymbol".*?</ix:nonNumeric>',raw,re.S)[0]
        with self.assertRaises(ValueError):inspect(raw.replace(part,b'<!--'+part+b'-->'))
    def test_entities_and_malformed(self):
        for raw in [fixture()+b'\0',fixture().replace(b'<body>',b'<!DOCTYPE x><body>'),fixture().replace(b'</table>',b'')]:
            with self.assertRaises(ValueError):inspect(raw)

class SecurityClassBoundaryTests(unittest.TestCase):
    def test_real_bad_archive_no_output(self):
        import tempfile
        from pathlib import Path
        from retained_security_class import main
        with tempfile.TemporaryDirectory() as tmp:
            archive=Path(tmp)/'invalid.zip';archive.write_bytes(b'not the pinned archive')
            output=Path(tmp)/'result.json'
            with self.assertRaises(ValueError):main([str(Path(__file__).resolve().parent.parent),str(archive),str(output)])
            self.assertFalse(output.exists())
    def test_failed_frozen_selection_no_output(self):
        import tempfile
        from pathlib import Path
        from unittest.mock import patch
        from retained_security_class import main
        with tempfile.TemporaryDirectory() as tmp:
            output=Path(tmp)/'result.json'
            with patch('retained_security_class.source_review',side_effect=ValueError('frozen selection changed')) as review, self.assertRaises(ValueError):main(['root','archive',str(output)])
            review.assert_called_once_with('root','archive')
            self.assertFalse(output.exists())
    def test_no_overwrite_even_successful_build(self):
        import tempfile
        from pathlib import Path
        from unittest.mock import patch
        from retained_security_class import main
        with tempfile.TemporaryDirectory() as tmp:
            output=Path(tmp)/'result.json';output.write_bytes(b'immutable prior output')
            with patch('retained_security_class.build',return_value={'synthetic':True}), self.assertRaises(FileExistsError):main(['root','archive',str(output)])
            self.assertEqual(output.read_bytes(),b'immutable prior output')
    def test_build_projection_abstains_and_only_carries_source(self):
        import hashlib,json,tempfile,zipfile
        from pathlib import Path
        from unittest.mock import patch
        from retained_security_class import build
        raw=fixture();digest=hashlib.sha256(raw).hexdigest()
        with tempfile.TemporaryDirectory() as tmp:
            archive=Path(tmp)/'synthetic.zip'
            with zipfile.ZipFile(archive,'w') as z:z.writestr(digest+'.txt',raw)
            with patch('retained_security_class.source_review',return_value={'source':{'synthetic':True},'private_unrelated':'must not propagate'}),patch('retained_security_class.RAW_SHA',digest):d=build('root',archive)
        self.assertNotIn('private_unrelated',d)
        for k in ['security_id','effective_from','effective_to','first_public_utc']:self.assertIsNone(d[k])
        for k in ['selection_changed','historical_mapping_verified','corporate_action_continuity_verified','price_join_performed','execution_ready','training_ready']:self.assertIs(d[k],False)
        self.assertEqual(d['qualified_outcomes'],0)
        for token in ['response_base64','entry_price','return_value','"orders":','BUSINESS ADDRESS']:self.assertNotIn(token,json.dumps(d))
