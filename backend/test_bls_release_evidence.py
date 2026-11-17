"""Synthetic release layouts test literal evidence, not economic conclusions."""
import unittest
from bls_release_evidence import parse
class BlsTests(unittest.TestCase):
 def fixture(self):return '''Transmission of material in this news release is embargoed until USDL-26-0000
8:30 a.m. (ET) Friday, November 6, 2026
THE EMPLOYMENT SITUATION — OCTOBER 2026
Total nonfarm payroll employment rose by 165,000 in October, and the unemployment rate changed
little at 4.1 percent, the U.S. Bureau of Labor Statistics reported today.
The change in total nonfarm payroll employment for August was revised up by 53,000, from +133,000
to +186,000, and the change for September was revised up by 31,000, from +29,000 to +60,000.'''
 def runparse(self,text):return parse(text,'empsit','2026-11-17T22:44:00+00:00')
 def test_declared_clock_separate_and_spans(self):
  text=self.fixture();x=self.runparse(text);self.assertEqual(x['declared_embargo_utc'],'2026-11-06T13:30:00+00:00');self.assertIsNone(x['authenticated_first_public_at']);self.assertFalse(x['training_ready'])
  f=x['headline_evidence'][0];self.assertEqual(text[f['text_start']:f['text_end']],f['text']);self.assertFalse(f['semantic_context_verified']);self.assertEqual(len(x['revision_evidence']),1)
 def test_no_invented_clocks(self):
  for old,new in [('Friday','Thursday'),('2026','2099'),('October,','September,'),('embargoed','published'),('165,000','-165,000')]:
   with self.subTest(old=old),self.assertRaises(ValueError):self.runparse(self.fixture().replace(old,new))
 def test_duplicate_and_missing_revisions_fail(self):
  t=self.fixture()
  with self.assertRaises(ValueError):self.runparse(t+t)
  with self.assertRaises(ValueError):self.runparse(t.split('The change')[0])
 def test_quote_does_not_assert_semantic_truth(self):
  t=self.fixture().replace('Total nonfarm','The following statement is disputed: Total nonfarm')
  self.assertFalse(self.runparse(t)['headline_evidence'][0]['semantic_context_verified'])
 def test_dst_declaration(self):
  t=self.fixture().replace('Friday, November 6','Friday, October 2').replace('OCTOBER 2026','SEPTEMBER 2026').replace('in October,','in September,')
  self.assertEqual(self.runparse(t)['declared_embargo_utc'],'2026-10-02T12:30:00+00:00')
 def test_cpi_missing_annual_comparator_not_zero(self):
  text='''Transmission of material in this release is embargoed until USDL-26-0000
8:30 a.m. (ET) Tuesday, November 10, 2026
CONSUMER PRICE INDEX – OCTOBER 2026
The Consumer Price Index for All Urban Consumers (CPI-U) increased 0.4 percent on a seasonally
adjusted basis in October after rising 0.6 percent in September, the U.S. Bureau of Labor Statistics
reported today.
The index for all items less food and energy rose 0.3 percent in October, as it did in September and
August.
BLS did not collect survey data for October 2025 because of a lapse in appropriations. For most CPI series, BLS cannot publish 12-month
percent changes for October 2026 for indexes where October 2025 data are unavailable.'''
  x=parse(text,'cpi','2026-11-17T22:44:00+00:00');self.assertEqual(len(x['headline_evidence']),2);self.assertEqual(len(x['missing_comparator_evidence']),1);self.assertIsNone(x['surprise'])
  with self.assertRaises(ValueError):parse(text.split('BLS did not')[0],'cpi','2026-11-17T22:44:00+00:00')
 def test_pinned_pdf_buffer_and_receipt(self):
  import tempfile,json
  from pathlib import Path
  from unittest.mock import patch
  from bls_release_evidence import audit,digest
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/'source.pdf';raw=b'%PDF-SYNTHETIC-DO-NOT-PARSE';p.write_bytes(raw)
   receipt={'source_url':'https://www.bls.gov/news.release/archives/empsit_11062026.pdf','method':'GET','authentication':'NONE','requested_at':'2026-11-17T22:43:00+00:00','finished_at':'2026-11-17T22:44:00+00:00','http_status':200,'content_type':'application/pdf','status':'RETAINED_NOT_YET_VERIFIED','bytes':len(raw),'sha256':digest(raw)}
   q=Path(td)/'receipt.json';q.write_text(json.dumps(receipt));qsha=digest(q.read_bytes())
   def fake_run(args,**kwargs):
    self.assertEqual(kwargs['input'],raw);self.assertEqual(kwargs['timeout'],30);self.assertTrue(callable(kwargs['preexec_fn']));kwargs['stdout'].write(self.fixture().encode())
   with patch('bls_release_evidence.subprocess.run',side_effect=fake_run):
    s,e=audit(p,digest(raw),q,qsha,'empsit');self.assertEqual(s['headline_statement_count'],1)
    with self.assertRaises(ValueError):audit(p,'0'*64,q,qsha,'empsit')
   def at_cap(args,**kwargs):kwargs['stdout'].write(self.fixture().encode().ljust(2000000,b' '))
   with patch('bls_release_evidence.subprocess.run',side_effect=at_cap),self.assertRaises(ValueError):audit(p,digest(raw),q,qsha,'empsit')
   receipt['source_url']='https://other.invalid/source.pdf';q.write_text(json.dumps(receipt))
   with patch('bls_release_evidence.subprocess.run',side_effect=fake_run),self.assertRaises(ValueError):audit(p,digest(raw),q,digest(q.read_bytes()),'empsit')
 def test_real_child_output_cap_and_incomplete_on_failure(self):
  import subprocess,sys,tempfile
  from pathlib import Path
  from unittest.mock import patch
  from bls_release_evidence import cap_output,run
  with tempfile.TemporaryFile() as output:
   result=subprocess.run([sys.executable,'-c','import os; os.write(1,b"x"*3000000); os.write(1,b"x")'],stdout=output,stderr=subprocess.DEVNULL,preexec_fn=cap_output,timeout=10)
   self.assertNotEqual(result.returncode,0);output.seek(0,2);self.assertLessEqual(output.tell(),2000000)
  with tempfile.TemporaryDirectory() as td:
   out=Path(td)/'failed'
   with patch('bls_release_evidence.audit',side_effect=subprocess.CalledProcessError(1,'pdftotext')),self.assertRaises(subprocess.CalledProcessError):
    run('unused','unused','unused','unused','empsit',out)
   self.assertTrue((out/'INCOMPLETE').is_file());self.assertFalse((out/'COMPLETE.json').exists());self.assertFalse((out/'summary.json').exists())
