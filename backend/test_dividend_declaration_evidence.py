import hashlib,unittest
from dividend_declaration_evidence import extract
TEXT=b'the board of directors declared a 94 cents-per-share regular quarterly cash dividend. The dividend is payable January 15, 2027, to shareholders of record as of December 23, 2026.'
def doc(typ,body):return b'<DOCUMENT>\n<TYPE>'+typ+b'\n<FILENAME>x.htm\n<TEXT>'+body+b'</TEXT></DOCUMENT>'
def fixture(text=TEXT):return doc(b'8-K',b'primary')+doc(b'EX-99.1',b'<div>'+text+b'</div>')
class DividendTests(unittest.TestCase):
 def test_dates_not_ex_or_entitlement(self):
  r=extract(fixture());d=r['declarations'][0]
  self.assertEqual(r['status'],'POSITIVE_DECLARATION_ONLY');self.assertEqual(d['amount_cents_per_share'],'94')
  self.assertEqual(d['record_date'],'2026-12-23');self.assertEqual(d['payment_date'],'2027-01-15')
  for k in ('currency_iso','ex_dividend_date','declaration_date'):self.assertIsNone(d[k])
  for k in ('coverage_complete','total_return_ready','execution_eligible'):self.assertFalse(r[k])
 def test_span(self):
  raw=fixture();s=extract(raw)['declarations'][0]['evidence_span']
  self.assertEqual(s['sha256'],hashlib.sha256(raw[s['byte_start']:s['byte_end']]).hexdigest())
 def test_unsupported_does_not_prove_absence(self):
  r=extract(fixture(b'No grammar'));self.assertEqual(r['declarations'],[]);self.assertFalse(r['coverage_complete'])
 def test_hidden(self):
  for a,b in [(b'<!--',b'-->'),(b'<script>',b'</script>'),(b'<STYLE>',b'</STYLE>')]:
   self.assertEqual(extract(fixture(a+TEXT+b))['declarations'],[])
 def test_hidden_paragraph(self):
  self.assertEqual(extract(doc(b'EX-99.1',b'<!--<p>'+TEXT+b'</p>-->'))['declarations'],[])
 def test_ambiguous_paragraphs(self):
  self.assertEqual(extract(fixture(TEXT+TEXT))['status'],'AMBIGUOUS_MULTIPLE_DECLARATIONS')
 def test_amended(self):
  self.assertEqual(extract(fixture().replace(b'<TYPE>8-K\n',b'<TYPE>8-K/A\n'))['status'],'AMENDMENT_REQUIRES_REVIEW')
 def test_duplicate_exhibit(self):
  self.assertEqual(extract(fixture()+doc(b'EX-99.1',b'x'))['status'],'AMBIGUOUS_EXHIBITS')
 def test_malformed_inventory(self):
  for raw in [fixture()+b'<DOCUMENT>',fixture()+doc(b'EX-99.1',b'x').replace(b'<FILENAME>',b'<TYPE>EX-99.1\n<FILENAME>')]:
   self.assertEqual(extract(raw)['status'],'MALFORMED_DOCUMENT_INVENTORY')
 def test_impossible_date_and_negative_order(self):
  for t in [TEXT.replace(b'December 23',b'February 30'),TEXT.replace(b'January 15, 2027',b'January 15, 2026'),TEXT.replace(b'94 cents',b'0 cents')]:
   self.assertEqual(extract(fixture(t))['status'],'INVALID_SUPPORTED_DECLARATION')
 def test_primary_text_not_exhibit(self):
  self.assertEqual(extract(doc(b'8-K',b'<p>'+TEXT+b'</p>'))['declarations'],[])
