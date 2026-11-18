"""Bind static TXMD adjudication to the released source and unchanged audit."""
import hashlib
import json
import re
import unittest
from pathlib import Path
from html.parser import HTMLParser
from historical_outcome_audit import build

ROOT = Path(__file__).resolve().parents[1]
PIN = 'fe7fc58256104bae75d7c5822f03a5a625e7c03cc8c6cbaa575cab218654953f'

class Annotation(HTMLParser):
    def __init__(self):
        super().__init__(); self.depth=0; self.tags=[]; self.attrs={}; self.text=[]; self.links=[]
    def handle_starttag(self, tag, attrs):
        a=dict(attrs)
        if tag=='details' and a.get('id')=='txmd-source-review': self.depth=1
        elif self.depth and tag=='details': self.depth+=1
        if self.depth:
            self.tags.append(tag)
            for k,v in attrs:
                if k.startswith('data-txmd-'): self.attrs.setdefault(k,[]).append(v)
                if k.startswith('on'): raise AssertionError('Inline action in static annotation')
            if tag=='a': self.links.append(a['href'])
    def handle_endtag(self,tag):
        if self.depth and tag=='details': self.depth-=1
    def handle_data(self,text):
        if self.depth:self.text.append(text)

class TxmdOutcomeWorkspaceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw=(ROOT/'web/company-findings/frozen-outcome-txmd-source-review.json').read_bytes()
        cls.d=json.loads(cls.raw);cls.page=(ROOT/'web/financial-review.html').read_text()
        cls.parsed=Annotation();cls.parsed.feed(cls.page);cls.text=' '.join(cls.parsed.text)

    def test_exact_source_and_rendered_field_bindings(self):
        self.assertEqual(len(self.raw),5885);self.assertEqual(hashlib.sha256(self.raw).hexdigest(),PIN)
        d=self.d;f=d['finding'];m=f['continuing_operations_evidence']
        expected={'cik':d['issuer_cik'],'accession':d['accession'],'description-period':f['description_period_as_reported'],'body-period':f['body_reported_period']['quarter_as_reported'],'period-end':f['body_reported_period']['end'],'filename':f['filename'],'observation':d['source']['recorded_retrieved_utc']}
        expected.update({k:m[k.replace('-','_')+'_reported'] for k in ['current-income','prior-income','current-eps','prior-eps']})
        self.assertEqual(self.parsed.attrs,{'data-txmd-'+k:[v] for k,v in expected.items()})
        self.assertIn(PIN,self.text);self.assertIn(f['document_sha256'],self.text)
        self.assertIn(d['source']['url'],self.parsed.links)
        for link in ['company-findings/frozen-outcome-txmd-source-review.json','../docs/research/frozen-outcome-source-review.md']:
            self.assertIn(link,self.parsed.links);self.assertTrue((ROOT/'web'/link).is_file())
        self.assertEqual(self.page.count('id="txmd-source-review"'),1)
        for tag in ['script','button','input','form','iframe']:self.assertNotIn(tag,self.parsed.tags)

    def test_conflicting_periods_and_metric_limits_stay_unresolved(self):
        f=self.d['finding'];m=f['continuing_operations_evidence']
        self.assertTrue(f['source_content_reviewed']);self.assertTrue(f['description_body_period_conflict'])
        self.assertEqual(f['conflict_resolution'],'UNRESOLVED_NO_SILENT_CORRECTION')
        self.assertEqual([m[k] for k in ['current_income_reported','prior_income_reported','current_eps_reported','prior_eps_reported']],['501','50','0.04','0.00'])
        self.assertEqual(m['current_income_unit'],'thousand reported dollars');self.assertEqual(m['prior_income_unit'],'thousand reported dollars')
        self.assertEqual(m['eps_basis'],'REPORTED_COMBINED_BASIC_AND_DILUTED_CONTINUING_OPERATIONS')
        for key in ['current_period','currency_iso','calculated_growth_percent']:self.assertIsNone(m[key])
        self.assertIsNone(f['body_reported_period']['start'])
        self.assertFalse(m['total_company_gaap_eps_verified']);self.assertFalse(m['comparability_verified']);self.assertFalse(f['financial_comparability_verified'])
        for phrase in ['quarter conflict is unresolved','Neither text silently replaces the other','rounded prior 0.00 is not an exact-zero denominator','No percentage growth is calculated','current comparison period unresolved','prior label is third quarter 2025','Do not automatically assign','ISO currency, exact period starts, total-company GAAP EPS and accounting comparability remain unverified','does not supply independent basic and diluted series']:
            self.assertIn(phrase,self.text)

    def test_frozen_selection_clocks_and_all_six_dependencies_preserved(self):
        d=self.d;audit=build(ROOT);selected=audit['selected'][0]
        self.assertEqual((audit['universe_count'],audit['selection_count'],audit['qualified_outcomes']),(10,1,0))
        self.assertEqual(selected['event_id'],d['accession']);self.assertEqual(selected['issuer_cik'],d['issuer_cik'])
        self.assertEqual(d['remaining_dependencies'],selected['missing_dependencies'])
        self.assertEqual(re.findall('data-outcome-dependency="([^"]+)"',self.page),d['remaining_dependencies'])
        self.assertFalse(d['selection_changed']);self.assertEqual(d['qualified_outcomes'],0)
        for k in ['first_public_utc','decision_utc','entry_session','endpoint_session','return_value']:self.assertIsNone(d[k])
        for k in ['training_ready','execution_ready']:self.assertFalse(d[k])
        self.assertFalse(d['source']['retrieval_clock_independently_authenticated'])
        self.assertEqual(d['source']['link_status'],'RETAINED_RECEIPT_NOT_NEW_FETCH')
        for phrase in ['without changing the frozen 10-row header audit','zero qualified outcomes','All six dependencies below still apply','not a zero return','not a new fetch','not independently authenticated and is not first-public time','No ticker join, price value, order or simulated trade is introduced','opening it does not fetch or revalidate']:
            self.assertIn(phrase,self.text)
