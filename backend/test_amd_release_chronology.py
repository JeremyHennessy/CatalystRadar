import copy,json,tempfile,unittest
from decimal import localcontext
from pathlib import Path
from unittest.mock import patch
import amd_release_chronology as m
ROOT=Path(__file__).resolve().parents[1]
def fixture():
 s=json.loads((ROOT/m.SAMPLE_PATH).read_bytes());a=json.loads((ROOT/'web/company-findings/amd-release-chronology.json').read_bytes())
 n={'verification_date_utc':a['manual_review']['verification_date_utc'],'method':a['manual_review']['method'],'original_http_bytes_retained':False,'authenticated_historical_first_public_utc':None,'issuer_cik':m.CIK,'sample_accession':m.ACC,'q2_release':a['earlier_source_dated_release'],'later_release':a['later_quarter_release'],'limits':a['limitations'][:5]};return s,n
class ChronologyTests(unittest.TestCase):
 def test_actual_reproduction_and_no_upgrade(self):
  s,n=fixture();a=m.project(s,n);self.assertEqual(a,json.loads((ROOT/'web/company-findings/amd-release-chronology.json').read_bytes()));self.assertEqual(a['display_scaled_checks'][0]['display_scaled_decimal'],'11536000000');self.assertEqual(a['display_scaled_checks'][1]['display_scaled_decimal'],'7685000000');self.assertFalse(a['original_xbrl_retention_gap_resolved']);self.assertIsNone(a['first_public_utc']);self.assertFalse(a['growth_calculated'])
 def test_wrong_packet_identity_accession_and_row_pins(self):
  for key,v in [('id','wrong'),('issuer_cik','0000000001'),('accession','0000002488-26-000124'),('source_sub_row_sha256','0'*64)]:
   s,n=fixture();p=next(p for p in s['packets'] if p['id']==m.ID);p[key]=v
   with self.assertRaises(ValueError):m.project(s,n)
  s,n=fixture();p=next(p for p in s['packets'] if p['id']==m.ID);p['facts'][0]['source_row_sha256']='0'*64
  with self.assertRaises(ValueError):m.project(s,n)
  s,n=fixture();s['packets'].append(copy.deepcopy(next(p for p in s['packets'] if p['id']==m.ID)))
  with self.assertRaises(ValueError):m.project(s,n)
 def test_amount_scale_unit_and_later_comparative_mismatches(self):
  for key,field,v in [('q2_release','unit_as_displayed','$B'),('q2_release','current_display','11,537'),('q2_release','prior_display','7,686'),('later_release','q2_comparative_display','11,535'),('q2_release','prior_fiscal_label','Q2 2024'),('later_release','fiscal_label','Q2 2026')]:
   s,n=fixture();n[key][field]=v
   with self.assertRaises(ValueError):m.project(s,n)
 def test_calendar_strict_order_and_same_day_abstention(self):
  for key,v in [('q2_release','2026-08-05'),('q2_release','2026-08-06'),('q2_release','2026-02-30'),('later_release','2026-08-05'),('later_release','2026-11-19')]:
   s,n=fixture();n[key]['source_declared_date']=v
   with self.assertRaises(ValueError):m.project(s,n)
  s,n=fixture();n['verification_date_utc']='2099-01-01'
  with self.assertRaises(ValueError):m.project(s,n)
 def test_nonfinite_unsafe_urls_and_manual_authority(self):
  for value in ['NaN','Infinity','1e6','-1','11,53','11,536.0']:
   with self.assertRaises(ValueError):m.millions(value,'$M')
  for value in ['NaN','Infinity','1e6']:
   with self.assertRaises(ValueError):m.amount(value)
  for url in ['javascript:alert(1)','https://ir.amd.com.evil.test/news','https://ir.amd.com/news-events/press-releases/detail/1295/other']:
   s,n=fixture();n['q2_release']['url']=url
   with self.assertRaises(ValueError):m.project(s,n)
  for k,v in [('original_http_bytes_retained',True),('authenticated_historical_first_public_utc','2026-08-04T00:00:00Z'),('issuer_cik','wrong')]:
   s,n=fixture();n[k]=v
   with self.assertRaises(ValueError):m.project(s,n)
 def test_decimal_context_and_no_percent(self):
  with localcontext() as c:c.prec=2;self.assertEqual(m.millions('11,536','$M').to_eng_string(),'11536000000')
  s,n=fixture();a=m.project(s,n);self.assertNotIn('percentage_change',a);self.assertTrue(all(x['currency_iso_equivalence_independently_verified'] is False for x in a['display_scaled_checks']))
 def test_changed_note_pin_and_failure_completion(self):
  with tempfile.TemporaryDirectory() as td:
   n=Path(td)/'note';n.write_bytes(b'{}');out=Path(td)/'failed'
   with self.assertRaises(ValueError):m.save(ROOT,n,out)
   self.assertTrue((out/'INCOMPLETE').exists());self.assertFalse((out/'annotation.json').exists());self.assertFalse((out/'COMPLETE.json').exists())
   s,n=fixture();d=m.project(s,n);out=Path(td)/'success'
   with patch.object(m,'build',return_value=d):m.save(ROOT,'unused',out)
   self.assertEqual(out.stat().st_mode&511,448);self.assertEqual((out/'annotation.json').stat().st_mode&511,384);self.assertFalse((out/'INCOMPLETE').exists())
 def test_source_packet_pin(self):
  self.assertEqual(m.sha(ROOT/m.SAMPLE_PATH),m.SAMPLE_SHA)
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);p=root/m.SAMPLE_PATH;p.parent.mkdir(parents=True);p.write_bytes(b'{}')
   with self.assertRaises(ValueError):m.build(root,'notread')
if __name__=='__main__':unittest.main()
