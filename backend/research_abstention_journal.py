"""Offline ABSTAIN-only journal protocol; no actual freeze or persisted journal.

Only the hard-allowlisted reviewed snapshot is accepted; caller-chosen hashes
cannot authorize new inputs. New snapshots require separate source review/code
version. A complete pinned retrospective snapshot binds the eligible/excluded audit
universe. Exact source objects are verified on every append. Registrant/accession
associations are trusted only from the reviewed allowlisted snapshot; this is
not a generic reconstruction of identity across arbitrary source schemas.
The local clock (injectable only for deterministic testing) is NOT external
attestation. Earlier-than-deadline records remain prospective_eligible=False;
late records say LATE rather than backdating. Receipt bytes are only hash-bound:
a future reviewed external adapter would have to authenticate exact final record
bytes and its trusted receipt clock, not a caller boolean or command hash alone.

Replay proves internal hash-chain consistency, not source authenticity, writer
identity, durable persistence or completeness/anti-rollback. A caller must retain
and independently protect its expected tip; a removed suffix is not detectable
without that external checkpoint. No outcome values or free-form claims can be
appended, no promotion operation exists, and no disk/network/UI/ledger is used.
"""
from datetime import datetime, timezone
import hashlib
import json
import re
from research_scanner import encoded, pointer, digest

ZERO='0'*64
MAX_RECORDS=256
APPROVED_SNAPSHOTS=frozenset({'28e8b1d7b80a34de480ad03e9bdf7a5d18b65fdf5816239968f2f2fd52e6196a'})
OBSERVATION_MEANINGS=frozenset({'source_observed_as_recorded','retrieved_utc_as_recorded','metadata_observation_utc_as_recorded','source_local_verified_not_download_or_first_public'})
REASONS={'MISSING_MARKET_DATA','UNVERIFIED_SECURITY_IDENTITY','UNVERIFIED_CORPORATE_ACTIONS','UNVERIFIED_TRADING_SESSION','UNVERIFIED_SOURCE_AVAILABILITY','UNVERIFIED_DATA_RIGHTS','UNQUALIFIED_COMPARISON'}

def sha(raw):return hashlib.sha256(raw).hexdigest()
def instant(s):
 if not isinstance(s,str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z',s):raise ValueError('UTC seconds required')
 return datetime.fromisoformat(s.replace('Z','+00:00'))
def source_instant(s):
 if not isinstance(s,str):raise ValueError('source clock type')
 value=datetime.fromisoformat(s.replace('Z','+00:00'))
 if value.tzinfo is None:raise ValueError('source clock timezone')
 return value.astimezone(timezone.utc)
def unique(rows):
 d={}
 for k,v in rows:
  if k in d:raise ValueError('duplicate key')
  d[k]=v
 return d

def decode(raw,limit,canonical_required=True):
 if type(raw) is not bytes or not 0<len(raw)<=limit:raise ValueError('bounded bytes required')
 try:
  obj=json.loads(raw,object_pairs_hook=unique)
  canonical=(json.dumps(obj,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False)+'\n').encode()
  if canonical_required and canonical!=raw:raise ValueError('canonical finite JSON required')
  return obj
 except (UnicodeError,RecursionError) as e:raise ValueError('invalid JSON') from e

def local_now():return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
def command(*,command_id,snapshot_raw,snapshot_sha256,thesis_id,issuer_cik,accession,source_bytes,deadline_utc,reasons,receipt_raw=None):
 """Validate exact retained source bindings. Hash pins do not prove authenticity."""
 if not re.fullmatch(r'[a-z0-9_-]{1,64}',command_id) or not re.fullmatch(r'(?!0000000000)[0-9]{10}',issuer_cik) or not re.fullmatch(r'[0-9]{10}-[0-9]{2}-[0-9]{6}',accession):raise ValueError('identity')
 if snapshot_sha256 not in APPROVED_SNAPSHOTS or sha(snapshot_raw)!=snapshot_sha256:raise ValueError('snapshot pin')
 s=decode(snapshot_raw,2_000_000)
 if s.get('mode')!='RETROSPECTIVE_RESEARCH_PRIORITY' or s.get('execution_ready') is not False or s.get('training_ready') is not False:raise ValueError('snapshot mode')
 matches=[x for x in s['ideas'] if x['id']==thesis_id]
 if len(matches)!=1:raise ValueError('thesis not unique')
 idea=matches[0]
 rows=[r for r in idea['source_records'] if accession in r['source_accessions'] and issuer_cik in [a['issuer_cik'] for a in r['issuer_associations']]]
 if any(r['source_accessions']!=[accession] or len(r['issuer_associations'])!=1 or r['issuer_associations'][0]['issuer_cik']!=issuer_cik for r in rows):raise ValueError('ambiguous multi-registrant/accession source record')
 if not rows or idea['execution_ready'] is not False or idea['actionability']!='UNPRICED_NOT_ACTIONABLE':raise ValueError('exact joint source association')
 if not isinstance(reasons,list) or not reasons or len(reasons)!=len(set(reasons)) or not set(reasons)<=REASONS:raise ValueError('bounded reason codes')
 if type(source_bytes) is not dict or len(source_bytes)>32 or sum(len(b) for b in source_bytes.values())>8_000_000:raise ValueError('source bounds')
 refs=[];observations=[]
 for row in rows:
  for c in row['clocks']:
   if c['meaning'] in OBSERVATION_MEANINGS:
    if source_instant(c['value_as_reported'])>instant(s['cutoff_utc']):raise ValueError('source observation after snapshot cutoff')
    observations.append({'meaning':c['meaning'],'value_as_reported':c['value_as_reported']})
  ref=row['source_ref'];pin=s['source_pins'][ref['key']];raw=source_bytes.get(ref['key'])
  if type(raw) is not bytes or len(raw)!=pin['bytes'] or sha(raw)!=pin['sha256']:raise ValueError('source pin')
  obj=decode(raw,2_000_000,canonical_required=False)
  selected=pointer(obj,ref['json_pointer'])
  if digest(selected)!=ref['object_sha256']:raise ValueError('source object mismatch')
  if ref['key']=='coherent' and (selected.get('issuer_cik')!=issuer_cik or selected.get('accession')!=accession):raise ValueError('native Coherent identity mismatch')
  refs.append({'source_key':ref['key'],'source_sha256':pin['sha256'],'json_pointer':ref['json_pointer'],'object_sha256':ref['object_sha256']})
 deadline=instant(deadline_utc)
 if instant(s['cutoff_utc'])>deadline:raise ValueError('deadline before snapshot cutoff')
 if receipt_raw is not None and (type(receipt_raw) is not bytes or not 0<len(receipt_raw)<=65536):raise ValueError('receipt bound')
 counts=s['counts'];decisions=s['candidate_decisions']
 ids=[d['source_id'] for d in decisions]
 included=[d for d in decisions if d['decision']=='INCLUDED_IN_THESIS'];excluded=[d for d in decisions if d['decision']=='EXCLUDED']
 membership={sid:x['id'] for x in s['all_scored_candidates'] for sid in x['source_ids']}
 if len(ids)!=len(set(ids)) or counts['evaluated']!=len(decisions) or len(included)!=counts['eligible_source_records'] or len(excluded)!=counts['excluded'] or len(included)+len(excluded)!=len(decisions) or membership!={d['source_id']:d['thesis_id'] for d in included}:raise ValueError('denominator membership')
 return {'audit':{k:counts[k] for k in ('evaluated','excluded','eligible_source_records')}|{'decisions_sha256':digest(decisions)},'source_observation_clocks':observations,'command_id':command_id,'snapshot_sha256':snapshot_sha256,'snapshot_cutoff_utc':s['cutoff_utc'],'thesis_id':thesis_id,'issuer_cik':issuer_cik,'accession':accession,'source_refs':sorted(refs,key=lambda x:(x['source_key'],x['json_pointer'])),'deadline_utc':deadline_utc,'reasons':sorted(reasons),'receipt_pin':None if receipt_raw is None else {'sha256':sha(receipt_raw),'bytes':len(receipt_raw)}}

COMMAND_KEYS={'audit','source_observation_clocks','command_id','snapshot_sha256','snapshot_cutoff_utc','thesis_id','issuer_cik','accession','source_refs','deadline_utc','reasons','receipt_pin'}
def validate_command(c):
 if type(c) is not dict or set(c)!=COMMAND_KEYS:raise ValueError('command schema')
 if c['snapshot_sha256'] not in APPROVED_SNAPSHOTS:raise ValueError('unreviewed snapshot')
 if not re.fullmatch('[a-z0-9_-]{1,64}',c['command_id']) or not re.fullmatch('[a-f0-9]{64}',c['snapshot_sha256']) or not re.fullmatch('research-[a-f0-9]{24}',c['thesis_id']):raise ValueError('command identity')
 if not re.fullmatch('(?!0000000000)[0-9]{10}',c['issuer_cik']) or not re.fullmatch('[0-9]{10}-[0-9]{2}-[0-9]{6}',c['accession']):raise ValueError('source identity')
 if instant(c['snapshot_cutoff_utc'])>instant(c['deadline_utc']):raise ValueError('cutoff ordering')
 a=c['audit']
 if set(a)!={'evaluated','excluded','eligible_source_records','decisions_sha256'} or any(type(a[k]) is not int or a[k]<0 for k in ('evaluated','excluded','eligible_source_records')) or a['excluded']+a['eligible_source_records']!=a['evaluated'] or not re.fullmatch('[a-f0-9]{64}',a['decisions_sha256']):raise ValueError('audit denominator')
 if type(c['source_observation_clocks']) is not list or len(c['source_observation_clocks'])>64:raise ValueError('clock bounds')
 for value in c['source_observation_clocks']:
  if set(value)!={'meaning','value_as_reported'} or value['meaning'] not in OBSERVATION_MEANINGS or source_instant(value['value_as_reported'])>instant(c['snapshot_cutoff_utc']):raise ValueError('source clock after cutoff')
 if not c['reasons'] or c['reasons']!=sorted(set(c['reasons'])) or not set(c['reasons'])<=REASONS:raise ValueError('reasons')
 if not isinstance(c['source_refs'],list) or not 1<=len(c['source_refs'])<=32:raise ValueError('source references')
 for r in c['source_refs']:
  if set(r)!={'source_key','source_sha256','json_pointer','object_sha256'} or not re.fullmatch('[a-z0-9_]{1,64}',r['source_key']) or not all(re.fullmatch('[a-f0-9]{64}',r[k]) for k in ('source_sha256','object_sha256')) or not isinstance(r['json_pointer'],str) or len(r['json_pointer'])>256:raise ValueError('reference schema')
 p=c['receipt_pin']
 if p is not None and (type(p) is not dict or set(p)!={'sha256','bytes'} or not re.fullmatch('[a-f0-9]{64}',p['sha256']) or type(p['bytes']) is not int or not 0<p['bytes']<=65536):raise ValueError('receipt pin')

def replay(journal):
 if type(journal) is not list or len(journal)>MAX_RECORDS or sum(len(r) for r in journal)>2_000_000:raise ValueError('journal bounds')
 tip=ZERO;commands={};last=None
 for i,raw in enumerate(journal,1):
  r=decode(raw,16384)
  if set(r)!={'version','sequence','previous_sha256','command','command_sha256','recorded_utc','clock_basis','timing_status','receipt_status','decision','prospective_eligible','execution_ready','training_ready','sha256'}:raise ValueError('record schema')
  c=r['command'];validate_command(c);now=instant(r['recorded_utc'])
  timing='LOCAL_CLOCK_BEFORE_DEADLINE_UNAUTHENTICATED' if now<=instant(c['deadline_utc']) else 'LATE_LOCAL_RECORD_NOT_PROSPECTIVE'
  if type(r['version']) is not int or r['version']!=1 or type(r['sequence']) is not int or r['sequence']!=i or r['previous_sha256']!=tip or r['command_sha256']!=digest(c) or r['sha256']!=digest({k:v for k,v in r.items() if k!='sha256'}):raise ValueError('chain mismatch')
  if c['command_id'] in commands or (last is not None and now<last) or now<instant(c['snapshot_cutoff_utc']):raise ValueError('reused ID or local clock regression')
  if r['clock_basis']!='LOCAL_SYSTEM_CLOCK_NOT_AUTHENTICATED' or r['timing_status']!=timing or r['receipt_status']!=('MISSING' if c['receipt_pin'] is None else 'HASH_BOUND_NOT_AUTHENTICATED') or r['decision']!='ABSTAIN' or any(r[k] is not False for k in ('prospective_eligible','execution_ready','training_ready')):raise ValueError('unsupported promotion')
  commands[c['command_id']]=r;tip=r['sha256'];last=now
 return {'tip_sha256':tip,'records':commands}

def append(journal,*,expected_tip,clock=local_now,**source_inputs):
 """Return a new in-memory transcript. Persistence/anti-rollback are external."""
 c=command(**source_inputs)
 state=replay(journal);validate_command(c)
 existing=state['records'].get(c['command_id'])
 if existing:
  if existing['command_sha256']!=digest(c):raise ValueError('idempotency conflict')
  return list(journal),existing
 if state['tip_sha256']!=expected_tip:raise ValueError('stale tip')
 now=clock();instant(now)
 r={'version':1,'sequence':len(journal)+1,'previous_sha256':expected_tip,'command':c,'command_sha256':digest(c),'recorded_utc':now,'clock_basis':'LOCAL_SYSTEM_CLOCK_NOT_AUTHENTICATED','timing_status':'LOCAL_CLOCK_BEFORE_DEADLINE_UNAUTHENTICATED' if instant(now)<=instant(c['deadline_utc']) else 'LATE_LOCAL_RECORD_NOT_PROSPECTIVE','receipt_status':'MISSING' if c['receipt_pin'] is None else 'HASH_BOUND_NOT_AUTHENTICATED','decision':'ABSTAIN','prospective_eligible':False,'execution_ready':False,'training_ready':False}
 r['sha256']=digest(r);out=[*journal,encoded(r)];replay(out)
 return out,r
