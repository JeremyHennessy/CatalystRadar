"""Local bare-Git experiments, NOT a GitHub adapter or remote safety proof.
No network URLs, credentials, workflows or provider requests. Temp repositories.
"""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from sec_request_accounting import GENESIS, propose, replay

AT='2026-11-23T11:00:00+00:00'

class LocalGitAppendContractTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(); self.root=Path(self.temp.name)
        self.remote=self.root/'remote.git';self.work=self.root/'objects'
        self.env={**os.environ,'GIT_AUTHOR_NAME':'Synthetic Test','GIT_AUTHOR_EMAIL':'test@example.invalid','GIT_COMMITTER_NAME':'Synthetic Test','GIT_COMMITTER_EMAIL':'test@example.invalid','GIT_TERMINAL_PROMPT':'0','GIT_CONFIG_NOSYSTEM':'1','GIT_CONFIG_GLOBAL':'/dev/null'}
        self.call(['git','init','--bare',str(self.remote)])
        self.call(['git','init',str(self.work)])
        self.initial=self.commit([],None,'synthetic genesis')
        self.push(self.initial)
    def tearDown(self):self.temp.cleanup()
    def call(self,args,stdin=None,check=True):
        return subprocess.run(args,input=stdin,text=True,capture_output=True,env=self.env,check=check,timeout=10)
    def git(self,*args,stdin=None,check=True):return self.call(['git','-C',str(self.work),*args],stdin,check)
    def commit(self,events,parent,message):
        blob=self.git('hash-object','-w','--stdin',stdin=json.dumps(events)).stdout.strip()
        tree=self.git('mktree',stdin=f'100644 blob {blob}\tledger.json\n').stdout.strip()
        args=['commit-tree',tree,'-m',message]+(['-p',parent] if parent else [])
        return self.git(*args).stdout.strip()
    def event(self,run='1'):
        return propose([],GENESIS,AT,'RESERVE',run_id=run,consumer='sec_metadata_watchlist_v1',issuer_cik='0000820318',request_id=run+':0000820318',url='https://data.sec.gov/submissions/CIK0000820318.json')['event']
    def push(self,sha,force=False,check=True):
        args=['push',str(self.remote),sha+':refs/heads/ledger']
        if force:args.insert(1,'--force')
        return self.git(*args,check=check)
    def tip(self):return self.call(['git','--git-dir='+str(self.remote),'rev-parse','refs/heads/ledger']).stdout.strip()
    def retained(self):return json.loads(self.call(['git','--git-dir='+str(self.remote),'show','refs/heads/ledger:ledger.json']).stdout)
    def test_sequential_sibling_children_only_one_append(self):
        a=self.commit([self.event('1')],self.initial,'A');b=self.commit([self.event('2')],self.initial,'B')
        self.push(a);self.assertNotEqual(self.push(b,check=False).returncode,0)
        self.assertEqual(self.tip(),a);self.assertEqual(len(self.retained()),1)
    def test_local_object_construction_without_push_does_not_reserve(self):
        self.commit([self.event()],self.initial,'orphan object')
        self.assertEqual(self.tip(),self.initial);self.assertEqual(self.retained(),[])
    def test_simulated_lost_acknowledgment_reconciles_without_repeating_intent(self):
        candidate=self.commit([self.event()],self.initial,'lost acknowledgment')
        self.push(candidate) # result deliberately discarded as if caller lost ack
        self.assertEqual(self.tip(),candidate)
        state=replay(self.retained(),AT)
        self.assertEqual(state['pending_request_id'],'1:0000820318');self.assertFalse(state['collection_enabled'])
        with self.assertRaises(ValueError):
            propose(self.retained(),state['tip_sha256'],AT,'RESERVE',run_id='2',consumer='sec_metadata_watchlist_v1',issuer_cik='0000012659',request_id='2:0000012659',url='https://data.sec.gov/submissions/CIK0000012659.json')
    def test_same_commit_retry_does_not_double_reserve(self):
        candidate=self.commit([self.event()],self.initial,'retry');self.push(candidate);self.push(candidate)
        self.assertEqual(replay(self.retained(),AT)['reserved_requests'],1)
    def test_simulated_post_reservation_stop_leaves_pending_not_reclaimed(self):
        self.push(self.commit([self.event()],self.initial,'pending'))
        state=replay(self.retained(),'2026-11-23T12:00:00+00:00')
        self.assertEqual(state['pending_request_id'],'1:0000820318');self.assertFalse(state['collection_enabled'])
    def test_unprotected_force_reset_demonstrates_missing_guarantee(self):
        candidate=self.commit([self.event()],self.initial,'unsafe reset example');self.push(candidate)
        self.push(self.initial,force=True)
        self.assertEqual(self.retained(),[]) # why cooperative FF alone is insufficient
