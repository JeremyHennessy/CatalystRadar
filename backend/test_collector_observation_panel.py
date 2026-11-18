import copy
import json
import unittest
from collector_observation_panel import ROOT, INPUT, START, END, render

class ObservationPanelTests(unittest.TestCase):
    def setUp(self):
        self.d = json.loads((ROOT / INPUT).read_text())
    def test_reproducible_panel(self):
        html = (ROOT / 'web/collectors.html').read_text()
        self.assertEqual(html[html.index(START):html.index(END)+len(END)], render(self.d))
        self.assertIn('16h 38m', render(self.d))
        self.assertIn('15h 43m', render(self.d))
        self.assertIn('not a source failure', render(self.d))
        self.assertIn('not outcome-qualified', render(self.d))
    def test_fail_closed_states(self):
        for mutate in [lambda d:d.update(collection_triggered=True), lambda d:d.update(new_collection_verified=True), lambda d:d['fallback'].update(submitted=True), lambda d:d['fallback'].update(source_requests=1), lambda d:d['collectors'][0].update(dispatch_status='FAILED'), lambda d:d['collectors'][0].update(latest_successful_receipt='2027-01-01T00:00:00+00:00'), lambda d:d['collectors'][0].update(latest_run_url='https://evil.test')]:
            d=copy.deepcopy(self.d); mutate(d)
            with self.assertRaises(ValueError): render(d)
    def test_escape_text(self):
        self.d['collectors'][0]['coverage']='<script>'
        self.assertIn('&lt;script&gt;',render(self.d))
        self.assertNotIn('<script>',render(self.d))
    def test_historical_audit_preserved(self):
        import hashlib
        self.assertEqual(hashlib.sha256((ROOT/'web/collector-run-audit.json').read_bytes()).hexdigest(),'e2806e0e40f1fee281aa1444fa50609a43d7cbc8fca6e26f34a7dce1789eb98f')
    def test_no_price_values_or_activation_fields(self):
        text=(ROOT/INPUT).read_text()
        for key in ['"open":','"close":','"high":','"low":','"volume":','"api_key":','"token":']:
            self.assertNotIn(key,text)
        self.assertFalse(self.d['collection_triggered'])
        self.assertIsNone(self.d['fallback']['source_requests'])
        self.assertIsNone(self.d['fallback']['submitted'])
        self.assertIn('not independently reproducible', render(self.d))
