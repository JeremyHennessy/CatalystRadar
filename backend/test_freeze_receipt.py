import unittest,json,base64,hashlib
from unittest.mock import patch
from datetime import datetime,timezone
import freeze_receipt as f
class TestReceipt(unittest.TestCase):
 def setUp(self):
  self.order={'id':'E:2026-11-16','state':'FROZEN','session':'2026-11-16','freeze_utc':'2026-11-16T12:58:00Z'}
  self.order['freeze_hash']=f.digest(self.order);self.raw=f.canonical({'orders':[self.order]});self.wf=b'SYNTHETIC REVIEWED WORKFLOW'
  self.sha=lambda b:hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
  self.run={'id':1,'repository':{'full_name':f.REPO},'head_sha':'a'*40,'head_branch':'main','event':'workflow_dispatch','path':f.WORKFLOW,'run_attempt':1,'created_at':'2026-11-16T12:59:00Z'}
  self.args={'run_id':1,'commit_sha':'a'*40,'ledger_path':'data/proxy/00000001.json','order_id':self.order['id'],'freeze_hash':self.order['freeze_hash'],'session':'2026-11-16','expected_workflow_blob_sha':self.sha(self.wf),'fetch':self.fetch}
  self.p=patch.object(f,'datetime',wraps=datetime);self.m=self.p.start();self.m.now.return_value=datetime(2026,11,17,tzinfo=timezone.utc)
 def tearDown(self):self.p.stop()
 def fetch(self,p):
  if p=='/repos/'+f.REPO:return {'full_name':f.REPO,'private':True,'visibility':'private'}
  if '/actions/' in p:return self.run
  raw=self.wf if f.WORKFLOW in p else self.raw
  return {'content':base64.b64encode(raw).decode(),'encoding':'base64','sha':self.sha(raw)}
 def test_success(self):self.assertTrue(f.verify(**self.args)['verified'])
 def test_wrong_head(self):self.run['head_sha']='b'*40;self.assertRaises(ValueError,f.verify,**self.args)
 def test_late(self):self.run['created_at']='2026-11-16T13:00:01Z';self.assertRaises(ValueError,f.verify,**self.args)
 def test_rerun(self):self.run['run_attempt']=2;self.assertRaises(ValueError,f.verify,**self.args)
 def test_push_not_prescribed(self):self.run['event']='push';self.assertRaises(ValueError,f.verify,**self.args)
 def test_unreviewed_workflow(self):self.wf=b'changed';self.assertRaises(ValueError,f.verify,**self.args)
 def test_changed_order(self):self.order['quantity']=999;self.raw=f.canonical({'orders':[self.order]});self.assertRaises(ValueError,f.verify,**self.args)
 def test_receipt_before_freeze(self):self.run['created_at']='2026-11-16T12:57:00Z';self.assertRaises(ValueError,f.verify,**self.args)
 def test_missing_run(self):
  self.run={};self.assertRaises(ValueError,f.verify,**self.args)
 def test_scenario_exact_plan(self):
  from mechanical_scenario import MODEL
  p={'model':MODEL,'entry_session':'2026-11-16','freeze_utc':'2026-11-14T19:00:00Z','records':[]};p['plan_sha256']=f.digest(p)
  self.raw=f.canonical(p);self.run['created_at']='2026-11-14T19:01:00Z'
  args={**self.args,'scenario':True,'order_id':None,'freeze_hash':p['plan_sha256'],'ledger_path':'data/scenarios/'+p['plan_sha256']+'.json'}
  r=f.verify(**args);self.assertEqual(r['plan_sha256'],p['plan_sha256'])
  p['records']=[{'changed':True}];self.raw=f.canonical(p);self.assertRaises(ValueError,f.verify,**args)

 def test_repo_endpoint_is_canonical_not_trailing_slash(self):
  paths=[];original=self.fetch
  def fetch(path):
   paths.append(path)
   if path=='/repos/'+f.REPO+'/':raise AssertionError('GitHub returns404 for trailing slash')
   return original(path)
  f.verify(**{**self.args,'fetch':fetch});self.assertEqual(paths[0],'/repos/'+f.REPO)
