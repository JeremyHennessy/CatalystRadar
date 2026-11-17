"""Narrow TRR3 lexical conversion; not financial qualification or XBRL validation."""
import argparse
from collections import Counter
from decimal import Decimal
import json
from pathlib import Path
import re
from inline_context_evidence import extract
from financial_pair_candidates import publish,write_private

TRR3='http://www.xbrl.org/inlineXBRL/transformation/2015-02-26'

def convert(fact):
    """Interpret a supported complete fact. Unsupported input stays unavailable."""
    if fact.get('text_complete') is not True or fact.get('exclude_element_present') is not False or fact.get('continuation_ref_as_filed') is not None:
        raise ValueError('unsupported text semantics')
    if fact.get('nil_as_filed') not in {None,'false','0'}:raise ValueError('nil or invalid nil')
    if fact.get('scale_as_filed') is not None:raise ValueError('scale outside supported subset')
    if fact.get('sign_as_filed') not in {None,'-'}:raise ValueError('unsupported sign')
    fmt=fact.get('format')
    if not isinstance(fmt,dict) or fmt.get('namespace')!=TRR3:raise ValueError('unsupported format namespace')
    text=fact.get('text_untransformed')
    if not isinstance(text,str) or not 1<=len(text)<=256:raise ValueError('text bounds')
    # XML Schema whiteSpace collapse, not arbitrary Unicode whitespace stripping.
    text=re.sub(r'[ \t\r\n]+',' ',text).strip(' ')
    if fmt.get('local_name')=='zerodash':
        if text!='-':raise ValueError('unsupported dash lexical form')
        value='0'
    elif fmt.get('local_name')=='numdotdecimal':
        # Deliberately narrower than the registry: no space/NBSP separators.
        if not re.fullmatch(r'(?:[0-9]+|[0-9]{1,3}(?:,[0-9]{3})+)(?:\.[0-9]+)?',text):raise ValueError('unsupported decimal lexical form')
        value=text.replace(',','')
        if sum(c.isdigit() for c in value)>100:raise ValueError('digit bounds')
    else:raise ValueError('unsupported transform')
    # Decimal construction and fixed-point formatting do not apply context rounding.
    number=Decimal(('-' if fact.get('sign_as_filed')=='-' else '')+value)
    return format(number,'f')

def audit(archive,archive_sha,member,member_sha):
    context_summary,facts=extract(archive,archive_sha,member,member_sha)
    output=[];rejections=Counter();formats=Counter()
    for f in facts:
        row=dict(f)
        try:
            row['numeric_value']=convert(f);row['numeric_conversion_verified']=True
            row['numeric_conversion_status']='LEXICAL_TRANSFORM_ONLY'
            formats[f['format']['local_name']]+=1
        except ValueError as exc:
            row['numeric_conversion_status']='UNSUPPORTED';row['numeric_conversion_reason']=str(exc)
            rejections[str(exc)]+=1
        output.append(row)
    summary={'schema_version':1,'status':'BOUNDED_LEXICAL_INTERPRETATION_NOT_FINANCIAL_QUALIFICATION',
      'archive_sha256':archive_sha,'member':member,'raw_member_sha256':member_sha,
      'source_fact_count':len(output),'numeric_conversions':sum(formats.values()),'format_counts':dict(sorted(formats.items())),
      'unsupported_fact_count':sum(rejections.values()),'rejection_counts':dict(sorted(rejections.items())),
      'dimension_or_scenario_fact_count':context_summary['dimension_or_scenario_fact_count'],
      'comparability_verified':False,'training_ready':False,'execution_ready':False,
      'limitations':['Only TRR3 numdotdecimal without space separators and ASCII zerodash; absent scale and absent/minus sign supported.',
      'Declared accuracy is retained, never used to round; lexical conversion is not full XBRL validation or financial truth.',
      'Source byte integrity does not prove source authenticity, first-public timing, comparable operations or predictive availability.',
      'Dimensional contexts remain separate and preserved. No prepared-data join, arithmetic, returns or training admission.']}
    return summary,output

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--archive',required=True);p.add_argument('--archive-sha256',required=True);p.add_argument('--member',required=True);p.add_argument('--member-sha256',required=True);p.add_argument('--output-directory',required=True);a=p.parse_args()
    out=Path(a.output_directory).resolve()
    if out.is_relative_to(Path(__file__).resolve().parents[1]) or not out.parent.is_dir():raise ValueError('trusted private parent outside checkout required')
    out.mkdir(mode=0o700,exist_ok=False);write_private(out/'INCOMPLETE',{'status':'INCOMPLETE_NOT_USABLE'})
    summary,facts=audit(a.archive,a.archive_sha256,a.member,a.member_sha256);publish(out,summary,facts);print(json.dumps(summary))
