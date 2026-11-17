"""Inventory repeated occurrences sharing exact source-local fact references."""
import argparse
from collections import Counter,defaultdict
from decimal import Decimal
import hashlib
import json
from pathlib import Path
from inline_numeric_evidence import audit as numeric_audit
from financial_pair_candidates import publish,write_private


def group_occurrences(facts):
    groups=defaultdict(list);seen=set()
    for fact in facts:
        identity=(fact['raw_member_sha256'],fact['fact_id'])
        if identity in seen:raise ValueError('duplicate occurrence identity')
        seen.add(identity)
        key=(fact['raw_member_sha256'],fact['concept']['namespace'],fact['concept']['local_name'],fact['context_ref'],fact['unit_ref'])
        groups[key].append(fact)
    output=[]
    for key,rows in sorted(groups.items()):
        # Source-local shared references must resolve to identical context and units.
        semantics=[{k:r[k] for k in ['context_serialization_sha256','context_namespace_bindings','context_descendant_namespace_bindings','issuer_identifier_as_filed','issuer_identifier_scheme','period','unit','dimension_or_scenario_present']} for r in rows]
        if any(s!=semantics[0] for s in semantics[1:]):raise ValueError('conflicting shared reference resolution')
        interpreted=all(r['numeric_conversion_verified'] is True and isinstance(r['numeric_value'],str) for r in rows)
        values=[Decimal(r['numeric_value']) for r in rows] if interpreted else []
        if any(not v.is_finite() for v in values):raise ValueError('nonfinite converted evidence')
        relation='SINGLE_OCCURRENCE' if len(rows)==1 else ('UNAVAILABLE' if not interpreted else ('NUMERICALLY_EQUAL' if all(v==values[0] for v in values[1:]) else 'DIFFERENT_REPORTED_VALUES'))
        output.append({'source_local_key':list(key),'group_id':hashlib.sha256(json.dumps(key,separators=(',',':')).encode()).hexdigest(),
          'occurrence_count':len(rows),'numeric_relation':relation,'declared_decimals_equal':len({r['decimals_as_filed'] for r in rows})==1,
          'occurrences':rows,'canonical_fact_equivalence_verified':False,'training_ready':False})
    return output

def audit(archive,archive_sha,member,member_sha):
    source_summary,facts=numeric_audit(archive,archive_sha,member,member_sha)
    groups=group_occurrences(facts);repeated=[g for g in groups if g['occurrence_count']>1]
    summary={'schema_version':1,'status':'SOURCE_LOCAL_OCCURRENCE_INVENTORY_NOT_FACT_DEDUPLICATION',
      'archive_sha256':archive_sha,'member':member,'raw_member_sha256':member_sha,
      'source_occurrence_count':len(facts),'source_local_group_count':len(groups),'repeated_group_count':len(repeated),
      'occurrences_in_repeated_groups':sum(g['occurrence_count'] for g in repeated),
      'repeated_group_numeric_relations':dict(sorted(Counter(g['numeric_relation'] for g in repeated).items())),
      'repeated_groups_with_decimals_difference':sum(not g['declared_decimals_equal'] for g in repeated),
      'dimension_or_scenario_occurrences':source_summary['dimension_or_scenario_fact_count'],
      'canonical_fact_equivalence_verified':False,'comparability_verified':False,'training_ready':False,'execution_ready':False,
      'limitations':['Groups share exact concept namespace/name, contextRef and unitRef inside the same raw member hash only.',
      'Different context or unit identifiers are not merged even if their apparent semantics match. This is not canonical XBRL fact equivalence.',
      'Every occurrence and declared decimals attribute remains retained. Numeric equality is not equal financial meaning or a training admission.',
      'No prepared-table join, cross-document equivalence, source authentication, historical availability or financial qualification is inferred.']}
    return summary,groups

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--archive',required=True);p.add_argument('--archive-sha256',required=True);p.add_argument('--member',required=True);p.add_argument('--member-sha256',required=True);p.add_argument('--output-directory',required=True);a=p.parse_args()
    out=Path(a.output_directory).resolve()
    if out.is_relative_to(Path(__file__).resolve().parents[1]) or not out.parent.is_dir():raise ValueError('trusted private parent outside checkout required')
    out.mkdir(mode=0o700,exist_ok=False);write_private(out/'INCOMPLETE',{'status':'INCOMPLETE_NOT_USABLE'})
    summary,groups=audit(a.archive,a.archive_sha256,a.member,a.member_sha256);publish(out,summary,groups);print(json.dumps(summary))
