"""Bind the static workspace explanation to the existing reviewed diagnostic."""
import re
import unittest
from pathlib import Path
from html.parser import HTMLParser
from historical_outcome_audit import build

ROOT = Path(__file__).resolve().parents[1]
class Fields(HTMLParser):
    def __init__(self):
        super().__init__(); self.dependencies=[]; self.exclusions=[]; self.links=[]
    def handle_starttag(self, tag, attrs):
        a=dict(attrs)
        if 'data-outcome-dependency' in a:self.dependencies.append(a['data-outcome-dependency'])
        if 'data-outcome-exclusion' in a:self.exclusions.append(a['data-outcome-exclusion'])
        if tag=='a':self.links.append(a.get('href'))

class OutcomeWorkspaceTests(unittest.TestCase):
    def test_scoped_static_explanation_matches_pinned_audit(self):
        audit=build(ROOT)
        page=(ROOT/'web/financial-review.html').read_text()
        section=page.split('<section class="panel" id="outcome-eligibility"',1)[1].split('</section>',1)[0]
        fields=Fields();fields.feed(section)
        self.assertEqual((audit['universe_count'],audit['selection_count'],audit['qualified_outcomes']),(10,1,0))
        selected=audit['selected'][0]
        self.assertEqual(fields.dependencies,selected['missing_dependencies'])
        self.assertEqual(fields.exclusions,[x['reason'] for x in audit['excluded_by_selection']])
        accessions=re.findall(r'<code>(\d{10}-\d{2}-\d{6})</code>',section)
        self.assertEqual(accessions,[selected['event_id']]+[x['event_id'] for x in audit['excluded_by_selection']])
        self.assertIn('<code>'+selected['issuer_cik']+'</code>',section)
        self.assertIn('10 retained header rows reviewed → 1 policy-selected row → 0 qualified outcomes in this sample.',section)
        url=f"https://www.sec.gov/Archives/edgar/data/{int(selected['issuer_cik'])}/{selected['event_id'].replace('-','')}/{selected['event_id']}-index.html"
        self.assertIn(url,fields.links)
        for x in ['separate from the 108-company research queue','not a market-wide finding','not a historical trading decision','No entry or endpoint session','No price download','does not verify earnings content','not a newly verified availability receipt','Training and paper execution remain disabled']:
            self.assertIn(x,section)
        self.assertFalse(selected['declared_first_public_present']);self.assertFalse(selected['declared_decision_present'])
        self.assertFalse(selected['qualified']);self.assertIsNone(selected['return_value'])
        self.assertIsNone(selected['entry_session']);self.assertIsNone(selected['endpoint_session'])
        self.assertFalse(audit['execution_ready']);self.assertFalse(audit['training_ready'])
        self.assertNotIn('<script',section);self.assertNotIn('<button',section)
    def test_existing_workspace_preserved(self):
        page=(ROOT/'web/financial-review.html').read_text()
        for key in ['id="research-queue"','id="review-load"','id="review-results"','company-investigation.js','research-queue.js?v=20261118-financing-queue']:
            self.assertIn(key,page)
        self.assertEqual(page.count('id="outcome-eligibility"'),1)
