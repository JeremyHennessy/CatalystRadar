import hashlib,unittest
from completed_note_offering import extract
ACC='0000000123-26-000001'
TEXT='On November 13, 2026, Example Co. (the “Company”) completed its previously announced public offering of €750,000,000 aggregate principal amount of the Company’s 4.000% Notes due 2032 (the “Notes”). The pricing of the Notes was previously announced in a Current Report on Form 8-K filed on November 12, 2026.'
def fixture(text=TEXT):
    return (f'<SEC-DOCUMENT>file\n<SEC-HEADER>\nACCESSION NUMBER: {ACC}\nCENTRAL INDEX KEY: 123\nCONFORMED SUBMISSION TYPE: 8-K\n</SEC-HEADER>\n<DOCUMENT>\n<TYPE>8-K\n<TEXT><div>'+text+'</div></TEXT></DOCUMENT>').encode()
class NoteTests(unittest.TestCase):
    def test_positive(self):
        r=extract(fixture(),'123',ACC);f=r['facts'][0]
        self.assertEqual(f['principal_unscaled'],'750000000');self.assertEqual(f['currency'],'EUR')
        self.assertEqual(f['coupon_percent_as_reported'],'4.000');self.assertTrue(f['previously_announced'])
        self.assertIsNone(f['net_proceeds']);self.assertIsNone(f['equity_dilution']);self.assertIsNone(f['first_public_utc'])
        s=f['evidence_span'];self.assertEqual(hashlib.sha256(fixture()[s['byte_start']:s['byte_end']]).hexdigest(),s['sha256'])
    def test_no_issuer_whitelist(self):
        self.assertEqual(extract(fixture(TEXT.replace('Example Co.','Other Ltd.')),'123',ACC)['facts'][0]['issuer_name_as_reported'],'Other Ltd.')
    def test_amendment(self):
        self.assertEqual(extract(fixture().replace(b'TYPE: 8-K',b'TYPE: 8-K/A'),'123',ACC)['status'],'AMENDMENT_REQUIRES_REVIEW')
    def test_duplicate(self):
        b=fixture();b+=b[b.index(b'<DOCUMENT>'):]
        self.assertEqual(extract(b,'123',ACC)['status'],'AMBIGUOUS_MULTIPLE_MATCHES')
    def test_unsupported_and_negation(self):
        for text in [TEXT.replace('completed','plans to complete'), 'It is not true that '+TEXT,TEXT.replace('€','$'),TEXT.replace('November 12','November 14'),TEXT.replace('4.000%','140.000%')]:
            self.assertEqual(extract(fixture(text),'123',ACC)['facts'],[])
    def test_hidden_code_not_paragraph(self):
        for wrap in ['<script>{}</script>','<style>{}</style>','<!--{}-->']:
            paragraph=('<div>'+TEXT+'</div>').encode()
            raw=fixture().replace(paragraph,wrap.format(paragraph.decode()).encode())
            self.assertEqual(extract(raw,'123',ACC)['facts'],[])
    def test_identity_mismatch(self):
        with self.assertRaises(ValueError):extract(fixture(),'999',ACC)
    def test_invalid_calendar_date_rejected(self):
        with self.assertRaises(ValueError):extract(fixture(TEXT.replace('November 13','November 31')),'123',ACC)
    def test_build_pin_and_bound(self):
        from completed_note_offering import build
        from pathlib import Path
        import tempfile
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'bad.zip';p.write_bytes(b'not a reviewed archive')
            with self.assertRaisesRegex(ValueError,'package bound or pin'):build(p)
            with p.open('wb') as f:f.truncate(20_000_001)
            with self.assertRaisesRegex(ValueError,'package bound or pin'):build(p)
