"""Offline research catalog validation; never authorizes collection or model use."""
import argparse
import datetime as dt
import json
import re
from pathlib import Path
from urllib.parse import urlsplit
from private_prices import unique_object

STATUSES = {'VERIFIED','PARTIAL','BLOCKED','RESEARCHED','UNVERIFIED','NOT_APPLICABLE'}
RIGHTS = {'collection','storage','model_training','redistribution'}
REQUIRED = {'id','provider','dataset','status','priority','verified_on','verification_scope',
 'documented_access','verified_access','integration','rights','quotas','delay','history',
 'instruments','storage_estimate','quality','features','limitations','unknowns','next_action',
 'evidence','training_ready','implementation_complexity','signal_usefulness',
 'source_reliability','current_operational_access'}

def reject_constant(_):
    raise ValueError('nonstandard JSON constant')

def load(path):
    with Path(path).open('rb') as f:
        raw=f.read(1_000_001)
    if len(raw)>1_000_000: raise ValueError('registry too large')
    return json.loads(raw,object_pairs_hook=unique_object,parse_constant=reject_constant)

def date(value):
    if not isinstance(value,str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}',value):
        raise ValueError('invalid date')
    return dt.date.fromisoformat(value)

def url(value):
    p=urlsplit(value)
    if p.scheme!='https' or not p.hostname or p.username or p.password or p.fragment:
        raise ValueError('invalid evidence URL')

def validate(data, today=None):
    today=today or dt.datetime.now(dt.timezone.utc).date()
    if not isinstance(data,dict) or data.get('schema_version')!=1:
        raise ValueError('unsupported registry')
    if data.get('collection_enabled') is not False: raise ValueError('catalog cannot activate collection')
    cutoff=date(data['verified_on'])
    if cutoff>today: raise ValueError('future verification')
    if not re.fullmatch('[a-f0-9]{40}',data.get('basis_git_head','')): raise ValueError('invalid basis commit')
    rows=data.get('records')
    if not isinstance(rows,list) or not 1<=len(rows)<=200: raise ValueError('invalid records')
    seen=set()
    for r in rows:
        if not isinstance(r,dict) or not REQUIRED<=r.keys(): raise ValueError('missing source fields')
        key=r['id']
        if not isinstance(key,str) or not re.fullmatch('[a-z][a-z0-9_]{1,79}',key) or key in seen:
            raise ValueError('invalid or duplicate source id')
        seen.add(key)
        if r['status'] not in STATUSES or r['priority'] not in {'P0','P1','P2','P3','P4'}: raise ValueError('invalid status/priority')
        if date(r['verified_on'])>cutoff: raise ValueError('future source verification')
        if r['training_ready'] is not False: raise ValueError('catalog cannot admit training')
        for field in ['provider','verification_scope','quotas','delay','history','instruments','next_action']:
            if not isinstance(r[field],str) or not r[field].strip(): raise ValueError('missing source detail')
        for field in ['dataset','features','limitations','unknowns']:
            if not isinstance(r[field],list) or not r[field] or any(not isinstance(x,str) or not x.strip() for x in r[field]): raise ValueError('invalid detail list')
        if not isinstance(r['rights'],dict) or set(r['rights'])!=RIGHTS: raise ValueError('rights must be separate')
        evidence=r['evidence']
        if not isinstance(evidence,list) or not evidence: raise ValueError('missing evidence')
        cited=set()
        for e in evidence:
            url(e['url']);cited.add(e['url'])
            if not isinstance(e.get('supports'),str) or not e['supports'].strip(): raise ValueError('missing claim mapping')
            if date(e['checked_date'])>cutoff: raise ValueError('future evidence')
        for right in r['rights'].values():
            if right['status'] not in STATUSES or not isinstance(right.get('detail'),str) or not right['detail'].strip(): raise ValueError('invalid rights')
            links=right.get('evidence_urls')
            if not isinstance(links,list) or not links or any(u not in cited for u in links): raise ValueError('uncited rights evidence')
        for field in ['verified_access','integration','quality','implementation_complexity','signal_usefulness','source_reliability','current_operational_access']:
            obj=r[field]
            if not isinstance(obj,dict) or obj.get('status') not in STATUSES or not isinstance(obj.get('detail'),str) or not obj['detail'].strip(): raise ValueError('invalid scoped assessment')
        if r['current_operational_access']['status']!='UNVERIFIED': raise ValueError('current access requires a separate operational receipt')
        n=r['verified_access'].get('downloaded_records')
        if n is not None and (type(n)!=int or n<0): raise ValueError('invalid record count')
        if r['verified_access']['status']=='UNVERIFIED' and n!=0: raise ValueError('unverified access cannot claim downloads')
        s=r['storage_estimate']
        if s.get('status') not in STATUSES or (s.get('bytes') is not None and (type(s['bytes'])!=int or s['bytes']<0)): raise ValueError('invalid storage estimate')
    return data

def render(data):
    validate(data)
    lines=['# Source registry: initial research checkpoint','',
      'This catalog is not an access permission, training admission or complete source survey. No provider data requests were made for this package. Existing integrations describe historical verified evidence, not live freshness. Approved UI and execution controls are unchanged.','',
      '## Acquisition priority','',
      'Rights and zero-cost eligibility are hard gates, not scores that predictive promise can outweigh. Within eligible routes, prioritize missing label/security foundations (P0), then reliable timely catalyst/macro context (P1), specialized positioning (P2), experimental alternatives (P3), and unsuitable/paid routes (P4). Official provenance does not prove data quality or predictive value. No numerical utility ranking is invented.','',
      'Next: audit existing private daily observations and security/action context within approved rights; separately verify original-agency keyless macro routes before a bounded collection. Neither route currently solves qualified intraday labels. Do not acquire restricted data merely to increase row counts.','',
      'Unfinished survey categories: '+ '; '.join(data['remaining_survey_categories'])+'.','',
      'Machine-readable source: `source-registry.json`. Validation: `python3 backend/source_registry.py docs/research/source-registry.json`. This validator checks structure and conservative states, not legal correctness or source authenticity.','']
    for r in data['records']:
        lines += [f"## {r['provider']} / {r['id']}",'',f"{r['priority']} · {r['status']} · reviewed {r['verified_on']}",'',
        'Datasets: '+ '; '.join(r['dataset']), 'Verification: '+r['verification_scope'],
        'Documented access: '+json.dumps(r['documented_access'],ensure_ascii=False),
        'Historical verified access: '+r['verified_access']['status']+' — '+r['verified_access']['detail'],
        'Integration: '+r['integration']['status']+' — '+r['integration']['detail'],
        'Current operational access: '+r['current_operational_access']['status']+' — '+r['current_operational_access']['detail'],'']
        for k,v in r['rights'].items():lines += [f"- {k}: {v['status']}. {v['detail']}"]
        for k in ['quotas','delay','history','instruments']:lines+=['',k.title()+': '+r[k]]
        for k in ['quality','implementation_complexity','signal_usefulness','source_reliability']:lines+=['',k.replace('_',' ').title()+': '+r[k]['status']+'. '+r[k]['detail']]
        lines += ['', 'Storage estimate: '+json.dumps(r['storage_estimate'],ensure_ascii=False),'', 'Proposed features (unvalidated): '+'; '.join(r['features']), '', 'Limitations: '+'; '.join(r['limitations']), '', 'Unknowns: '+'; '.join(r['unknowns']), '', 'Next action: '+r['next_action'],'']
        for e in r['evidence']:lines += [f"- [{e['supports']}]({e['url']}) (checked {e['checked_date']})"]
        for p in r.get('project_evidence',[]):lines += ['- Project evidence: `'+p+'`']
        lines+=['']
    return '\n'.join(lines)+'\n'

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('registry');p.add_argument('--markdown');a=p.parse_args()
    d=validate(load(a.registry))
    if a.markdown:
        with open(a.markdown,'x') as f:f.write(render(d))
    print(f"Validated {len(d['records'])} research records; collection and training remain disabled.")
