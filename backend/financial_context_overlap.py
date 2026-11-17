"""Repeated retained fact contexts are leakage warnings, not revised-event labels."""
from collections import defaultdict,Counter
from decimal import Decimal
import argparse
import hashlib
import json
from pathlib import Path
import re
from financial_pair_candidates import finite,sha,write_private,publish
from private_prices import unique_object

KEY_FIELDS=('tag','version','ddate','qtrs','uom','segments','coreg')
def invalid_constant(_):raise ValueError('nonstandard JSON constant')
def read(path,limit=64_000_000):
    with Path(path).open('rb') as f:raw=f.read(limit+1)
    if len(raw)>limit:raise ValueError('input too large')
    return json.loads(raw,object_pairs_hook=unique_object,parse_constant=invalid_constant)

def contexts(batches):
    groups=defaultdict(list);source_refs=set();observations=0
    for batch,pairs in sorted(batches.items()):
        for pair in pairs:
            if pair.get('training_ready') is not False or pair.get('comparability_verified') is not False or pair.get('decision_utc') is not None or pair.get('outcome') is not None:
                raise ValueError('input is outside unqualified candidate scope')
            cik=pair['issuer_cik_as_filed']
            if not isinstance(cik,str) or not re.fullmatch(r'\d{1,10}',cik) or int(cik)==0:raise ValueError('invalid issuer CIK')
            for side in ('current','prior'):
                r=pair[side]
                if r['adsh']!=pair['accession'] or not finite(r['value']):raise ValueError('invalid source fact')
                ref=(pair['database_sha256'],r['rowid'])
                # No duplicate source fact can masquerade as an independent observation.
                if ref in source_refs:raise ValueError('duplicate source fact reference')
                source_refs.add(ref);observations+=1
                key=(str(int(cik)),)+tuple(r[k] for k in KEY_FIELDS)
                groups[key].append({'issuer_cik_as_filed':cik,'batch':batch,'accession':pair['accession'],'role':side,
                  'database_sha256':pair['database_sha256'],'source_archive_sha256':pair['source_archive_sha256'],
                  'source_rowid':r['rowid'],'value_as_filed':r['value'],
                  'filed_as_filed':pair['filing_date_as_filed'],'accepted_as_filed':pair['accepted_as_filed']})
    near=defaultdict(set)
    for key in groups:near[key[:2]+key[3:]].add(key[2])
    repeated=[];counts=Counter()
    for key,observed in sorted(groups.items()):
        if len(observed)<=1:continue
        accessions={o['accession'] for o in observed};batch_ids={o['batch'] for o in observed}
        if len(accessions)<=1:category='same_accession_multiple_sources'
        else:category='multiple_accession_context'
        values={Decimal(o['value_as_filed']) for o in observed}
        numeric='numerically_equal' if len(values)==1 else 'different_reported_numbers'
        cross=len(batch_ids)>1
        counts[category]+=1
        if category=='multiple_accession_context':
            counts[numeric]+=1
            if cross:counts['cross_batch_multiple_accession_contexts']+=1;counts['cross_batch_'+numeric]+=1
        encoded=json.dumps(key,separators=(',',':')).encode()
        repeated.append({'context_id':hashlib.sha256(encoded).hexdigest(),'context':dict(zip(('issuer_cik',)+KEY_FIELDS,key)),
          'category':category,'numeric_relation':numeric,'cross_batch':cross,'observations':observed,
          'restatement_verified':False,'comparability_verified':False,'event_group_verified':False,'training_ready':False})
    return {'fact_observations':observations,'exact_context_keys':len(groups),'repeated_contexts':len(repeated),
      'unique_accessions':len({o['accession'] for v in groups.values() for o in v}),
      'version_different_near_contexts_unassessed':sum(len(v)>1 for v in near.values()),
      'overlap_counts':dict(sorted(counts.items()))},repeated

def audit(checkpoint,batch_directories):
    checkpoint_sha=sha(checkpoint)
    expected=read(checkpoint,1_000_000)
    if set(batch_directories)!=set(expected['batches']):raise ValueError('batch coverage mismatch')
    batches={};inputs={};guards=[(Path(checkpoint),checkpoint_sha)]
    for name,directory in sorted(batch_directories.items()):
        p=Path(directory)
        if (p/'INCOMPLETE').exists():raise ValueError('incomplete input')
        marker=read(p/'COMPLETE.json',10000);summary=read(p/'summary.json',100000)
        reference=dict(expected['batches'][name]);pair_sha=reference.pop('private_candidates_sha256')
        if summary!=reference:raise ValueError('summary differs from approved checkpoint')
        pair_path=p/'candidate-pairs.json';summary_path=p/'summary.json'
        if sha(pair_path)!=pair_sha or marker.get('candidate_pairs_sha256')!=pair_sha or marker.get('summary_sha256')!=sha(summary_path):raise ValueError('completed input hash mismatch')
        rows=read(pair_path)
        if not isinstance(rows,list) or len(rows)!=summary['candidate_pairs']:raise ValueError('pair count mismatch')
        for row in rows:
            if row.get('database_sha256')!=summary['database_sha256'] or row.get('source_archive_sha256')!=summary['source_archive_sha256']:raise ValueError('source binding mismatch')
        batches[name]=rows;inputs[name]={'candidate_pairs_sha256':pair_sha,'database_sha256':summary['database_sha256'],'source_archive_sha256':summary['source_archive_sha256']}
        guards.extend([(pair_path,pair_sha),(summary_path,sha(summary_path)),(p/'COMPLETE.json',sha(p/'COMPLETE.json'))])
    counts,groups=contexts(batches)
    for path,digest in guards:
        if sha(path)!=digest or (path.parent/'INCOMPLETE').exists():raise ValueError('input changed')
    summary={'schema_version':1,'status':'REPEATED_CONTEXT_WARNINGS_NOT_EVENT_OR_RESTATEMENT_LABELS','checkpoint_sha256':checkpoint_sha,'inputs':inputs,**counts,
      'comparability_verified':False,'event_groups_verified':False,'training_ready':False,'execution_ready':False,
      'limitations':['Exact raw taxonomy version/unit/dimension/date keys are intentionally narrow; unmatched contexts can still describe related events.',
      'Different reported numbers are not proof of error, restatement or economic change; equal numbers are not proof of independent observations.',
      'CIK groups issuers, not individual tradable securities. No historical symbol mapping is established.',
      'Filing/accepted dates remain source fields; no historical public-availability or decision clock inferred.',
      'These warnings do not define complete event families, train/test splits or qualified examples. No values, returns or model metrics published.']}
    return summary,groups

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--checkpoint',required=True);p.add_argument('--q2-directory',required=True);p.add_argument('--q3-directory',required=True);p.add_argument('--output-directory',required=True);a=p.parse_args()
    out=Path(a.output_directory).resolve();repo=Path(__file__).resolve().parents[1]
    if out.is_relative_to(repo) or not out.parent.is_dir():raise ValueError('trusted private parent outside checkout required')
    out.mkdir(mode=0o700,exist_ok=False);write_private(out/'INCOMPLETE',{'status':'INCOMPLETE_NOT_USABLE'})
    summary,groups=audit(a.checkpoint,{'q2_2026_filing_batch':a.q2_directory,'q3_2026_filing_batch':a.q3_directory})
    # Existing output protocol uses candidate-pairs.json as its generic private-record filename.
    publish(out,summary,groups);print(json.dumps(summary))
