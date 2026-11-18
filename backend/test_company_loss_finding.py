import copy,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import company_loss_finding as m
import test_company_revenue_finding as fixtures

class LossTests(unittest.TestCase):
 def fixture(self):
  s,r,p=fixtures.Tests().fixture()
  for i,(start,end,value,ids) in enumerate(m.PERIODS):
   c=copy.deepcopy(r[i]['candidate']);num=c['prepared_num'];num.update(tag='NetIncomeLoss',value=value+'.0000',rowid=50+i)
   base=c['source_group']['occurrences'][0];base.update(concept={'namespace':'http://fasb.org/us-gaap/2025','local_name':'NetIncomeLoss'},numeric_value=value,text_untransformed=format(abs(int(value)),','),format={'namespace':'http://www.xbrl.org/inlineXBRL/transformation/2015-02-26','local_name':'numdotdecimal'},sign_as_filed='-',scale_as_filed=None,footnote_refs_as_filed=None)
   c['source_group']['occurrences']=[]
   for fid in ids:
    f=copy.deepcopy(base);f['fact_id']=fid;c['source_group']['occurrences'].append(f)
   r.append({'disposition':'candidate_numeric_equal','candidate':c})
  return s,r,p
 def test_loss_not_growth_or_profit_and_duplicate_scope(self):
  s,r,p=self.fixture();c=m.build(s,r,p);self.assertEqual([f['value'] for f in c['facts']],['-110845','-218662']);self.assertEqual(c['calculation']['value'],'107817');self.assertIsNone(c['calculation']['percentage_growth']);self.assertIsNone(c['calculation']['causal_explanation']);self.assertFalse(c['training_ready']);self.assertFalse(c['execution_ready']);self.assertEqual(len(c['facts']),2);self.assertTrue(all(len(f['source_occurrences'])==2 for f in c['facts']));self.assertNotIn('PRIVATE',json.dumps(c));self.assertEqual(c['filing']['filing_date_as_reported'],'2026-06-17');self.assertEqual(c['provenance']['source_local_verified_utc'],p['local_verified_utc'])
 def test_context_sign_scale_identity_and_footnotes_rejected(self):
  for key,value in [('numeric_value','110845'),('sign_as_filed',None),('scale_as_filed','0'),('dimension_or_scenario_present',True),('issuer_identifier_as_filed','0000000001'),('period',{'kind':'duration','startDate':'2025-02-01','endDate':'2025-07-31'}),('unit',{'kind':'simple','measures':[]}),('footnote_refs_as_filed','note1'),('decimals_as_filed','INF')]:
   s,r,p=self.fixture();r[2]['candidate']['source_group']['occurrences'][0][key]=value
   with self.assertRaises(ValueError):m.build(s,r,p)
 def test_missing_duplicate_or_conflicting_presentation_rejected(self):
  for mode in ('missing','duplicate','context','prepared','sub','admission'):
   s,r,p=self.fixture()
   if mode=='missing':r[2]['candidate']['source_group']['occurrences'].pop()
   elif mode=='duplicate':r.append(copy.deepcopy(r[2]))
   elif mode=='context':r[2]['candidate']['source_group']['occurrences'][1]['context_ref']='different'
   elif mode=='prepared':r[2]['candidate']['prepared_num']['value']='-1'
   elif mode=='sub':r[2]['candidate']['prepared_submission']['rowid']=999
   elif mode=='admission':s['comparability_verified']=True
   with self.assertRaises(ValueError):m.build(s,r,p)
 def test_preserves_six_months_outside_selected_facts(self):
  s,r,p=self.fixture();extra=copy.deepcopy(r[2]);extra['candidate']['source_group']['occurrences'][0]['fact_id']='other1';extra['candidate']['source_group']['occurrences'][1]['fact_id']='other2';r.append(extra);self.assertEqual(len(m.build(s,r,p)['facts']),2)
 def test_completion_and_failure_no_success_marker(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);s,r,p=self.fixture()
   with patch.object(m,'correspondence',return_value=(s,r)),patch.object(m,'read_pinned',return_value=(p,b'')):
    c=m.save({'manifest':'fixture','manifest_sha':'a'*64},root/'ok')
   self.assertEqual(json.loads((root/'ok/finding.json').read_text()),c);self.assertEqual(json.loads((root/'ok/COMPLETE.json').read_text())['finding_sha256'],m.sha(root/'ok/finding.json'));self.assertFalse((root/'ok/INCOMPLETE').exists());self.assertEqual((root/'ok/finding.json').stat().st_mode&0o777,0o600)
   with patch.object(m,'correspondence',side_effect=ValueError('bad source')):
    with self.assertRaises(ValueError):m.save({},root/'failed')
   self.assertTrue((root/'failed/INCOMPLETE').exists());self.assertFalse((root/'failed/COMPLETE.json').exists())
