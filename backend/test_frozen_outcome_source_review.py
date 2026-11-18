import json,unittest
from pathlib import Path
import frozen_outcome_source_review as m

PARA='Net income from continuing operations totaled $501 thousand, or $0.04 per basic and diluted common share, compared to income from continuing operations of $50 thousand, or $0.00 per basic and diluted common share for the third quarter of 2025.'
def fixture():
 return ('<DOCUMENT>\n<TYPE>EX-99.1\n<FILENAME>ea031220401ex99-1.htm\n<DESCRIPTION>'+m.DESCRIPTION+'\n<TEXT>\n'+''.join('<p>'+x+'</p>' for x in [m.TITLE,m.INTRO]+m.HEADINGS+[PARA])+'\n</TEXT>\n</DOCUMENT>').encode()
class OutcomeSourceTests(unittest.TestCase):
 def test_synthetic_body_context_without_overriding_paragraph_or_conflict(self):
  r=m.inspect(fixture());self.assertTrue(r['description_body_period_conflict']);self.assertEqual(r['description_period_as_reported'],'second quarter 2026');self.assertEqual(r['body_reported_period']['end'],'2026-09-30');self.assertIsNone(r['body_reported_period']['start']);self.assertIsNone(r['continuing_operations_evidence']['current_period']);self.assertIsNone(r['continuing_operations_evidence']['calculated_growth_percent']);self.assertFalse(r['financial_comparability_verified'])
  for x in r['body_anchors']+[r['description']]:
   span=x['source_span'];self.assertEqual(m.sha(fixture()[span['byte_start']:span['byte_end']]),span['sha256'])
 def test_changed_description_body_and_duplicate_fail_closed(self):
  raw=fixture()
  for r in [raw.replace(b'SECOND QUARTER',b'THIRD QUARTER'),raw.replace(b'September 30',b'June 30'),raw.replace(m.TITLE.encode(),b'Unreviewed title'),raw.replace(b'</TEXT>',('<p>'+m.TITLE+'</p></TEXT>').encode()),raw+raw,raw.replace(b'<DESCRIPTION>',b'<DESCRIPTION>x\n<DESCRIPTION>'),raw.replace(b'<DOCUMENT>',b''),b'<!DOCTYPE x>'+raw]:
   with self.assertRaises(ValueError):m.inspect(r)
 def test_scripts_comments_and_order_cannot_supply_context(self):
  raw=fixture();p=('<p>'+m.TITLE+'</p>').encode()
  for wrapped in [b'<!--'+p+b'-->',b'<script>'+p+b'</script>',b'<style>'+p+b'</style>']:
   with self.assertRaises(ValueError):m.inspect(raw.replace(p,wrapped))
  with self.assertRaises(ValueError):m.inspect(raw.replace(p,b'').replace(b'</TEXT>',p+b'</TEXT>'))
 def test_released_sidecar_keeps_fixed_case_and_admission_false(self):
  root=Path(__file__).resolve().parents[1];r=json.loads((root/'web/company-findings/frozen-outcome-txmd-source-review.json').read_text());self.assertEqual(r['accession'],m.ACC);self.assertEqual(r['issuer_cik'],m.CIK);self.assertFalse(r['selection_changed']);self.assertEqual(r['qualified_outcomes'],0)
  for k in ['training_ready','execution_ready']:self.assertIs(r[k],False)
  for k in ['first_public_utc','decision_utc','entry_session','endpoint_session','return_value']:self.assertIsNone(r[k])
  self.assertIn('VERIFIED_EVENT_FIRST_PUBLIC_TIME',r['remaining_dependencies']);self.assertTrue(r['finding']['description_body_period_conflict']);self.assertEqual(r['source']['filing_sha256'],m.RAW_SHA)
  s=json.dumps(r)
  for forbidden in ['lwilson@','212-452','Contact:','api_key','raw_response']:self.assertNotIn(forbidden,s)

 def test_build_rejects_bad_archive_pin_and_changed_frozen_selection(self):
  import tempfile
  from unittest.mock import patch
  root=Path(__file__).resolve().parents[1]
  with tempfile.TemporaryDirectory() as td:
   archive=Path(td)/'bad.zip';archive.write_bytes(b'not the retained original')
   with self.assertRaisesRegex(ValueError,'archive pin'):m.build(root,archive)
   for changed in [{'selected':[]},{'selected':[{'event_id':'different','issuer_cik':m.CIK}]},{'selected':[{'event_id':m.ACC,'issuer_cik':'0000000001'}]}]:
    with patch.object(m,'frozen_audit',return_value=changed):
     with self.assertRaisesRegex(ValueError,'frozen selection changed'):m.build(root,archive)

 def test_cli_failure_creates_no_output_and_does_not_overwrite(self):
  import tempfile,subprocess,sys
  root=Path(__file__).resolve().parents[1]
  with tempfile.TemporaryDirectory() as td:
   d=Path(td);archive=d/'bad.zip';archive.write_bytes(b'invalid');out=d/'result.json'
   command=[sys.executable,'-B',str(root/'backend/frozen_outcome_source_review.py'),str(root),str(archive),str(out)]
   failed=subprocess.run(command,capture_output=True,text=True)
   self.assertNotEqual(failed.returncode,0);self.assertFalse(out.exists());self.assertEqual(failed.stdout,'')
   out.write_bytes(b'previous retained output');failed=subprocess.run(command,capture_output=True,text=True)
   self.assertNotEqual(failed.returncode,0);self.assertEqual(out.read_bytes(),b'previous retained output')
