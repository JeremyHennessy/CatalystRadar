import hashlib
import unittest
from prior_publication_evidence import extract

# Entire fixture is synthetic, no real issuer/source-derived report values.
CLAIM = ('The materials referenced during the presentation were posted in the '
         'Events &amp; Presentations section of our website (https://example.invalid/investors) '
         'prior to the commencement of the presentation.')


def document(text, kind='8-K'):
    return ('<DOCUMENT>\n<TYPE>'+kind+'\n<FILENAME>synthetic.htm\n<TEXT>\n'+text+'\n</TEXT>\n</DOCUMENT>').encode()


class PriorPublicationTests(unittest.TestCase):
    def test_assertion_span_and_unknown_clock(self):
        raw=b'synthetic header\n'+document('<p>'+CLAIM+'</p>')
        result=extract(raw)
        self.assertIsNone(result['issuer_asserts_prior_posting']);self.assertTrue(result['prior_posting_text_cue_found'])
        span=result['evidence'][0]
        self.assertEqual(hashlib.sha256(raw[span['byte_start']:span['byte_end']]).hexdigest(),span['sha256'])
        self.assertEqual(raw[span['byte_start']:span['byte_end']],('<p>'+CLAIM+'</p>').encode())
        self.assertIsNone(result['first_public_utc']);self.assertFalse(result['first_public_verified'])
        self.assertFalse(result['filing_time_proves_novelty']);self.assertFalse(result['qualified'])
        self.assertFalse(span['independent_web_publication_verified'])

    def test_unmatched_never_means_new_or_not_posted(self):
        for text in ('No supported sentence.',CLAIM.replace('prior to','after'),CLAIM.replace('were posted','will be posted')):
            result=extract(document('<p>'+text+'</p>'))
            self.assertEqual(result['evidence'],[]);self.assertIsNone(result['issuer_asserts_prior_posting'])
            self.assertFalse(result['filing_time_proves_novelty'])

    def test_hidden_assertions_excluded(self):
        for wrapper in ('<!--{}-->','<script>{}</script>','<style>{}</style>'):
            result=extract(document(wrapper.format('<p>'+CLAIM+'</p>')))
            self.assertEqual(result['evidence'],[])

    def test_multiple_assertions_are_ambiguous(self):
        result=extract(document(('<p>'+CLAIM+'</p>')*2))
        self.assertEqual(result['status'],'AMBIGUOUS_MULTIPLE_PRIOR_POSTING_ASSERTIONS')
        self.assertEqual(result['evidence'],[]);self.assertIsNone(result['issuer_asserts_prior_posting'])

    def test_wrong_document_amendment_and_multiple_primaries(self):
        paragraph='<p>'+CLAIM+'</p>'
        for raw in (document(paragraph,'EX-99.1'),document(paragraph,'8-K/A'),document(paragraph)*2,
                    document('unrelated')+document(paragraph,'EX-99.1')):
            self.assertEqual(extract(raw)['evidence'],[])

    def test_malformed_inventory_and_input_bounds(self):
        self.assertEqual(extract(b'<DOCUMENT><TEXT>bad</TEXT></DOCUMENT>')['status'],'MALFORMED_DOCUMENT_INVENTORY')
        for raw in ('text',b'x'*25_000_001):
            with self.assertRaises(ValueError):extract(raw)

    def test_missing_empty_document_type_fails_closed(self):
        raw=document('<p>'+CLAIM+'</p>')+b'<DOCUMENT>\n<TYPE>\n<TEXT>bad</TEXT></DOCUMENT>'
        self.assertEqual(extract(raw)['evidence'],[])

    def test_unbalanced_and_blank_type_inventory(self):
        raw=document('<p>'+CLAIM+'</p>')
        for malformed in (b'<DOCUMENT>'+raw,raw+b'</DOCUMENT>',raw+b'<DOCUMENT>\n<TYPE> \n<TEXT>bad</TEXT></DOCUMENT>'):
            self.assertEqual(extract(malformed)['status'],'MALFORMED_DOCUMENT_INVENTORY')

    def test_quoted_or_denied_sentence_never_becomes_issuer_assertion(self):
        for text in ('The following statement is false: '+CLAIM, 'An analyst said: "'+CLAIM+'" We do not confirm it.'):
            result=extract(document('<p>'+text+'</p>'))
            self.assertIsNone(result['issuer_asserts_prior_posting'])
            self.assertEqual(result['status'],'PRIOR_POSTING_TEXT_CUE_REQUIRES_CONTEXT_REVIEW')
            self.assertEqual(result['evidence'][0]['claim_scope'],'UNCONFIRMED_TEXT_CUE_CONTEXT_MAY_QUOTE_OR_DENY')
            self.assertFalse(result['qualified']);self.assertFalse(result['first_public_verified'])

    def test_truncated_extra_and_nested_document_rejected(self):
        raw=document('<p>'+CLAIM+'</p>')
        for malformed in (raw+b'<DOCUMENT>\n<TYPE>8-K\n<TEXT>',b'<DOCUMENT>\n<TYPE>8-K\n<TEXT>'+raw+b'</DOCUMENT>'):
            self.assertEqual(extract(malformed)['status'],'MALFORMED_DOCUMENT_INVENTORY')
