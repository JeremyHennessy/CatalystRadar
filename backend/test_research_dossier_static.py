import copy,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import research_dossier_static as m

class StaticDossierTests(unittest.TestCase):
 def snapshot(self):return {'records':[{'issuer_cik':str(n).zfill(10)} for n in range(1,109)],'sources':{}}
 def result(self,root,cik,section,limit,offset):
  total=7 if section=='financial' else 0 if section=='insider' else None
  records=[{'id':str(i),'issuer_cik':cik,'name':'<script>not evaluated</script>'} for i in range(total or 0)]
  selected=records[offset:offset+limit]
  return {'status':'COMPANY_IN_REVIEWED_SNAPSHOT','query':{'issuer_cik':cik,'section':section,'limit':limit,'offset':offset},'snapshot':{'sha256':'a'*64},'holdings_linkage':{'status':'NOT_ASSESSED'},'interpretation':['test'],'model_inference_performed':False,'provider_requests_made':False,'training_ready':False,'execution_ready':False,'selected_section':{'coverage':'NOT_EVALUATED_IN_THIS_SNAPSHOT' if total is None else 'SCOPED','source_key':section if total is not None else None,'total_source_records':total,'returned_records':len(selected),'offset':offset,'limit':limit,'next_offset':offset+len(selected) if offset+len(selected)<len(records) else None,'records':selected}}
 def run_build(self,fn=None,snapshot=None):
  with patch.object(m,'load_verified',return_value=snapshot or self.snapshot()),patch.object(m,'dossier',side_effect=fn or self.result):return m.build('.')
 def test_deterministic_pages_and_scoped_empty(self):
  p=self.run_build();self.assertEqual(p,self.run_build());index=json.loads(p[m.BASE+'index.json']);self.assertEqual(108,index['company_count']);self.assertEqual(217,len(p))
  for company in index['companies']:
   sections=company['sections'];self.assertIsNone(sections['reported']['total_source_records']);self.assertEqual(0,sections['insider']['total_source_records']);self.assertEqual([],sections['insider']['pages']);self.assertEqual([],sections['reported']['pages'])
   refs=sections['financial']['pages'];self.assertEqual([0,5],[r['offset'] for r in refs]);rows=[]
   for ref in refs:
    raw=p[ref['path']];self.assertEqual(ref['bytes'],len(raw));self.assertEqual(ref['sha256'],m.digest(raw));page=json.loads(raw);self.assertEqual(company['issuer_cik'],page['issuer_cik']);rows+=page['selected_section']['records']
   self.assertEqual([str(i) for i in range(7)],[r['id'] for r in rows]);self.assertEqual('<script>not evaluated</script>',rows[0]['name'])
 def test_duplicate_cohort(self):
  s=self.snapshot();s['records'][1]=s['records'][0]
  with self.assertRaises(ValueError):self.run_build(snapshot=s)
 def test_changed_page_identity_or_totals(self):
  for field,value in [('total_source_records',8),('next_offset',99),('returned_records',4)]:
   def broken(*args):
    r=self.result(*args)
    if args[-1]==5:r['selected_section'][field]=value
    return r
   with self.assertRaises(ValueError):self.run_build(broken)
  def wrong(*args):
   r=self.result(*args);r['query']['issuer_cik']='0000009999';return r
  with self.assertRaises(ValueError):self.run_build(wrong)
 def test_empty_contradiction(self):
  def broken(*args):
   r=self.result(*args)
   if args[2]=='reported':r['selected_section']['records']=[{'id':'unexpected'}]
   return r
  with self.assertRaises(ValueError):self.run_build(broken)
 def test_bounds_and_source_recheck(self):
  with patch.object(m,'MAX_PAGE',10):
   with self.assertRaises(ValueError):self.run_build()
  with patch.object(m,'MAX_TOTAL',10):
   with self.assertRaises(ValueError):self.run_build()
  with patch.object(m,'load_verified',side_effect=[self.snapshot(),{'changed':True}]),patch.object(m,'dossier',side_effect=self.result):
   with self.assertRaises(ValueError):m.build('.')
 def test_persist_complete_and_failure(self):
  p=self.run_build()
  with tempfile.TemporaryDirectory() as tmp:
   dest=Path(tmp)/'ok';m.save(p,dest);self.assertFalse((dest/'INCOMPLETE').exists());complete=json.loads((dest/'COMPLETE.json').read_bytes())
   for path,meta in complete.items():self.assertEqual(meta['sha256'],m.digest((dest/path).read_bytes()))
   with self.assertRaises(FileExistsError):m.save(p,dest)
   dest=Path(tmp)/'failure'
   with patch.object(Path,'write_bytes',side_effect=OSError('injected')):
    with self.assertRaises(OSError):m.save(p,dest)
   self.assertTrue((dest/'INCOMPLETE').exists());self.assertFalse((dest/'COMPLETE.json').exists())
if __name__=='__main__':unittest.main()
