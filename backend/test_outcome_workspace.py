"""Bind the static workspace explanation to the existing reviewed diagnostic."""
import re
import hashlib
import json
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
    def test_xerox_annotation_bound_to_reviewed_identity(self):
        raw=(ROOT/'web/company-findings/xerox-filing-identity.json').read_bytes()
        pin='db91d59be91d6c534a165605519943afe740d84e97411060280fec620f1b256c'
        self.assertEqual(len(raw),4171)
        self.assertEqual(hashlib.sha256(raw).hexdigest(),pin)
        d=json.loads(raw)
        page=(ROOT/'web/financial-review.html').read_text()
        section=page.split('<details id="xerox-identity">',1)[1].split('<p>Historical snapshot only.',1)[0]
        self.assertEqual(re.findall(r'data-xerox-accession="([^"]+)"',section),[d['accession']])
        self.assertEqual(re.findall(r'data-xerox-cik="([^"]+)"',section),[f['cik'] for f in d['identity_evidence']['filers']])
        for f in d['identity_evidence']['filers']:
            self.assertIn(f['name_as_filed'],section);self.assertEqual(f['role'],'FILER')
        for a in d['associations']:
            self.assertIn(a['source_url'],section);self.assertIn(a['observed_utc_as_recorded'],section)
        self.assertEqual(d['status'],'BOTH_CIKS_EXPLICIT_FILERS_NOT_INTERCHANGEABLE')
        for k in ['training_ready','execution_ready','issuer_merge_performed','facts_reassigned']:
            self.assertFalse(d[k])
        for k in ['entities_interchangeable','facts_propagated_between_filers','security_mapping_verified']:
            self.assertFalse(d['identity_evidence'][k])
        self.assertIsNone(d['provenance']['first_public_utc'])
        self.assertFalse(d['provenance']['current_source_access_verified'])
        for x in [pin,'does not change the header-selection result','not first-public times','discrepancy history remain unchanged','neither CIK is replaced or merged','not copied between filers','14 issuer/accession pairs across 13 accessions','zero endpoint-coverage passes','nor replaces the first-public study','does not fetch or revalidate']:
            self.assertIn(x,section)
        for href in ['company-findings/xerox-filing-identity.json','../docs/research/xerox-filing-identity.md','../docs/research/observed-outcome-coverage.md']:
            self.assertIn(href,section);self.assertTrue((ROOT/'web'/href).is_file())
        self.assertNotIn('<script',section);self.assertNotIn('<button',section)

    def test_existing_workspace_preserved(self):
        page=(ROOT/'web/financial-review.html').read_text()
        for key in ['id="research-queue"','id="review-load"','id="review-results"','company-investigation.js','research-queue.js?v=20261118-dossier-pages']:
            self.assertIn(key,page)
        self.assertEqual(page.count('id="outcome-eligibility"'),1)
