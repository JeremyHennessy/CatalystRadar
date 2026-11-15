import hashlib,json,tempfile,unittest
from pathlib import Path
from financial_admission_rehearsal import extract,plain,build
from fact_admission import admit_facts
from unittest.mock import patch

SENTENCE=b'The Company recorded $1.3 million in license revenue for the third quarter of 2026, an increase of $475 thousand, or 60.6%, compared to $784 thousand in license revenue for the third quarter of 2025.'
def fixture(sentence=SENTENCE):
    return b'<DOCUMENT>\n<TYPE>EX-99.1\n<TEXT><TD><FONT>'+sentence+b'</FONT></TD></TEXT></DOCUMENT>'

class FinancialAdmissionTests(unittest.TestCase):
    def test_actual_grammar_preserves_rounding_basis(self):
        docs,status=extract(fixture(),'25743','x');r=docs[0]['metrics'][0]
        self.assertEqual(status,'REPORTED_PAIR_ONLY')
        self.assertEqual(r['current_scaled_value'],'1300000.0')
        self.assertEqual(r['prior_scaled_value'],'784000')
        self.assertEqual(r['issuer_reported_percent'],'60.6')
        self.assertIsNone(r['calculated_growth_percent']);self.assertIsNone(r['currency_iso'])
        self.assertTrue(r['same_quarter_prior_year'])
        self.assertIn('NOT_VERIFIED_TOTAL_GAAP',r['basis'])
        self.assertIsNone(docs[0]['economic_event_group_id'])
    def test_evidence_span_and_document_hash(self):
        raw=fixture();d=extract(raw,'25743','x')[0][0];s=d['metrics'][0]['evidence_span']
        self.assertEqual(s['sha256'],hashlib.sha256(raw[s['byte_start']:s['byte_end']]).hexdigest())
        self.assertEqual(d['document_sha256'],hashlib.sha256(raw).hexdigest())
    def test_not_accession_or_date_whitelist(self):
        raw=fixture(SENTENCE.replace(b'2026',b'2024').replace(b'2025',b'2023'))
        self.assertEqual(extract(raw,'999','other')[1],'REPORTED_PAIR_ONLY')
    def test_amended_or_duplicate_documents_not_independent_samples(self):
        d,s=extract(fixture()*2,'1','x')
        self.assertEqual(s,'AMBIGUOUS_MULTIPLE_MATCHES');self.assertEqual(len(d),2)
        self.assertEqual(d[0]['filing_group_id'],d[1]['filing_group_id'])
    def test_period_mismatch_preserved_not_comparable(self):
        d,_=extract(fixture(SENTENCE.replace(b'quarter of 2025',b'quarter of 2023')),'1','x')
        self.assertFalse(d[0]['metrics'][0]['same_quarter_prior_year'])
    def test_other_metric_and_incomplete_sentence_unknown(self):
        for text in (SENTENCE.replace(b'license revenue',b'total revenue'),SENTENCE[:-20]):
            self.assertEqual(extract(fixture(text),'1','x')[1],'NO_SUPPORTED_FINANCIAL_GRAMMAR')
    def test_only_exhibit(self):
        self.assertEqual(extract(fixture().replace(b'EX-99.1',b'8-K'),'1','x')[0],[])
    def test_markup_whitespace_and_entities(self):
        self.assertEqual(plain(b'<b>Hello</b> &amp;\nworld'),'Hello & world')
        self.assertEqual(extract(fixture(SENTENCE.replace(b'quarter',b'quarter\n')),'1','x')[1],'REPORTED_PAIR_ONLY')
    def test_hidden_context_is_not_reported_fact(self):
        for before,after in [(b'<!--',b'-->'),(b'<script>',b'</script>'),(b'<style>',b'</style>'),(b'<SCRIPT>',b'')]:
            raw=fixture().replace(b'<TD>',before+b'<TD>').replace(b'</TD>',b'</TD>'+after)
            self.assertEqual(extract(raw,'1','x')[1],'NO_SUPPORTED_FINANCIAL_GRAMMAR')
        raw=fixture().replace(b'<FONT>',b'<script><FONT>').replace(b'</FONT>',b'</FONT></script>')
        self.assertEqual(extract(raw,'1','x')[1],'NO_SUPPORTED_FINANCIAL_GRAMMAR')
    def test_hidden_preceding_text_preserves_real_span(self):
        raw=fixture().replace(b'<TD>',b'<!-- harmless -->\n<TD>')
        docs,status=extract(raw,'1','x');self.assertEqual(status,'REPORTED_PAIR_ONLY')
        span=docs[0]['metrics'][0]['evidence_span']
        self.assertEqual(span['sha256'],hashlib.sha256(raw[span['byte_start']:span['byte_end']]).hexdigest())
    def test_zero_prior_not_divided(self):
        d,_=extract(fixture(SENTENCE.replace(b'$784',b'$0')),'1','x')
        self.assertIsNone(d[0]['metrics'][0]['calculated_growth_percent'])
    def test_rehearsal_connects_real_admission_and_does_not_promote_license(self):
        with tempfile.TemporaryDirectory() as t:
            raw=fixture();h=hashlib.sha256(raw).hexdigest();Path(t,h+'.txt').write_bytes(raw)
            headers={'computed_at':'2026-11-15T04:00:00Z','reviews_sha256':'review','manifest_sha256':'manifest',
                'rows':[{'event_id':'x','issuer_id':'1','review_status':'PENDING','review_reason':'review',
                    'features':[{'name':'header_is_8k_amendment','value':0,'sources':[{'source_ref':'https://www.sec.gov/x','sha256':h,'observed_utc':'2026-11-15T03:00:00Z'}]}]}]}
            with patch('financial_admission_rehearsal.build_headers',return_value=headers):
                r=build('unused',t)
                self.assertEqual(r['counts']['reported_pair_rows'],1)
                self.assertEqual(r['rows'][0]['fact_admission']['EARNINGS_GROWTH'],admit_facts('EARNINGS_GROWTH',{}))
                self.assertEqual(r['counts']['qualified'],0);self.assertFalse(r['protocol_activated'])
                headers['rows'][0]['features'][0]['value']=1
                self.assertEqual(build('unused',t)['rows'][0]['status'],'AMENDMENT_REQUIRES_ECONOMIC_EVENT_REVIEW')
                Path(t,h+'.txt').write_bytes(b'changed')
                with self.assertRaises(ValueError):build('unused',t)
    def test_missing_source_retained(self):
        h={'computed_at':'now','reviews_sha256':'r','manifest_sha256':'m','rows':[{'event_id':'x','issuer_id':'1','review_status':'pending','review_reason':'none','features':[]}]}
        with patch('financial_admission_rehearsal.build_headers',return_value=h):
            r=build('unused','unused');self.assertEqual(r['counts']['source_validated'],0)
            self.assertEqual(r['rows'][0]['status'],'SOURCE_UNAVAILABLE_OR_INVALID')
