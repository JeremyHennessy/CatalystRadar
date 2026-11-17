"""Synthetic amounts and filing wrappers; not retained issuer data."""
import hashlib
import unittest
from unittest.mock import patch
from continuing_operations_evidence import extract

TEXT=('Net income from continuing operations totaled $700 thousand, or $0.70 per basic and diluted common share, '
      'compared to income from continuing operations of $40 thousand, or $0.00 per basic and diluted common share '
      'for the third quarter of 2025.')

def filing(text=TEXT,kind='EX-99.1'):
    return ('<DOCUMENT>\n<TYPE>'+kind+'\n<TEXT><td>'+text+'</td></TEXT></DOCUMENT>').encode()

class ContinuingEvidenceTests(unittest.TestCase):
    def test_reported_values_and_unknowns_remain_distinct(self):
        raw=filing();r=extract(raw);p=r['records'][0]
        self.assertEqual(p['current_income_scaled'],'700000')
        self.assertEqual(p['prior_income_scaled'],'40000')
        self.assertEqual(p['prior_eps_reported'],'0.00')
        self.assertIsNone(p['current_period']);self.assertIsNone(p['currency_iso'])
        self.assertIsNone(p['calculated_growth_percent']);self.assertFalse(r['qualified'])
        self.assertFalse(p['total_company_gaap_eps_verified']);self.assertFalse(p['comparability_verified'])
        span=p['evidence_span'];self.assertEqual(hashlib.sha256(raw[span['byte_start']:span['byte_end']]).hexdigest(),span['sha256'])

    def test_units_are_per_operand(self):
        r=extract(filing(TEXT.replace('$700 thousand','$1.5 million')))
        self.assertEqual(r['records'][0]['current_income_scaled'],'1500000.0')
        self.assertEqual(r['records'][0]['prior_income_scaled'],'40000')

    def test_unsupported_basis_context_and_losses_stay_unknown(self):
        for text in [TEXT.replace('continuing operations','discontinued operations'),
                     TEXT.replace('basic and diluted','basic'),TEXT.replace('$700','-$700'),
                     'Forecast: '+TEXT,TEXT+' This is adjusted.',TEXT.replace('$700','approximately $700')]:
            self.assertEqual(extract(filing(text))['records'],[])

    def test_nonrelease_documents_and_hidden_text_ignored(self):
        self.assertEqual(extract(filing(kind='EX-10.1'))['records'],[])
        for wrapper in ('<!--{}-->','<script>{}</script>','<style>{}</style>'):
            raw=b'<DOCUMENT>\n<TYPE>EX-99.1\n'+wrapper.format('<td>'+TEXT+'</td>').encode()+b'</DOCUMENT>'
            self.assertEqual(extract(raw)['records'],[])

    def test_duplicates_not_independent_samples(self):
        r=extract(filing()+filing())
        self.assertEqual(r['status'],'AMBIGUOUS_MULTIPLE_MATCHES')
        self.assertFalse(r['qualified']);self.assertEqual(r['orders_created'],0)

    def test_markup_entities_keep_exact_original_span(self):
        raw=filing(TEXT.replace('$700','<b>&#36;700</b>'))
        r=extract(raw);self.assertEqual(r['records'][0]['current_income_reported'],'700')
        p=r['records'][0]['evidence_span'];self.assertEqual(hashlib.sha256(raw[p['byte_start']:p['byte_end']]).hexdigest(),p['sha256'])

    def test_bounded_bytes_only(self):
        with self.assertRaises(ValueError):extract('text')
        with patch('continuing_operations_evidence.MAX_BYTES',1):
            with self.assertRaises(ValueError):extract(filing())

    def test_precision_bound_and_exact_scaling(self):
        from decimal import localcontext
        for amount in ('1234567890123456','1.123456789'):
            self.assertEqual(extract(filing(TEXT.replace('$700', '$'+amount)))['records'],[])
        with localcontext() as context:
            context.prec=3
            r=extract(filing(TEXT.replace('$700 thousand','$999999999999999.12345678 million')))
        self.assertEqual(r['records'][0]['current_income_scaled'],'999999999999999123456.78000000')
