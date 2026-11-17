"""Retain exact inline-XBRL context evidence, without interpreting numeric formats."""
import argparse
import datetime as dt
import hashlib
import io
import json
from pathlib import Path,PurePosixPath
import re
import xml.etree.ElementTree as E
import zipfile
from financial_pair_candidates import TAGS,sha,write_private,publish

IX='http://www.xbrl.org/2013/inlineXBRL'
X='http://www.xbrl.org/2003/instance'
MAX_MEMBER=10_000_000

def digest(raw):return hashlib.sha256(raw).hexdigest()
def qname(text,scope):
    if not isinstance(text,str) or len(text)>256 or not re.fullmatch(r'(?:[A-Za-z_][\w.-]*:)?[A-Za-z_][\w.-]*',text):raise ValueError('invalid QName')
    prefix,local=text.split(':',1) if ':' in text else ('',text)
    if prefix not in scope:raise ValueError('unbound QName prefix')
    return {'namespace':scope[prefix],'local_name':local}

def parse(raw,expected_sha):
    if len(raw)>MAX_MEMBER:raise ValueError('unsupported XML size')
    try:decoded=raw.decode('utf-8-sig')
    except UnicodeDecodeError as exc:raise ValueError('unsupported XML encoding') from exc
    if '\x00' in decoded or '<!DOCTYPE' in decoded.upper() or '<!ENTITY' in decoded.upper():raise ValueError('unsupported XML declaration')
    declaration=re.match(br'^(?:\xef\xbb\xbf)?\s*<\?xml\b([^?]*)\?>',raw,re.I)
    encoding=re.search(br'encoding\s*=\s*[\"\']([^\"\']+)[\"\']',declaration.group(1),re.I) if declaration else None
    if encoding and encoding.group(1).lower() not in {b'utf-8',b'utf8',b'us-ascii',b'ascii'}:raise ValueError('unsupported XML encoding')
    if digest(raw)!=expected_sha:raise ValueError('member hash mismatch')
    scopes={};stack=[];pending=[];binding_slots=0
    parser=E.iterparse(io.BytesIO(raw),events=('start','end','start-ns'))
    for event,item in parser:
        if event=='start-ns':pending.append(item)
        elif event=='start':
            scope=dict(stack[-1]) if stack else {};scope.update(pending);pending=[]
            binding_slots+=len(scope)
            if len(stack)>=256 or len(scopes)>=50000 or len(scope)>64 or binding_slots>500000 or any(len(k)>128 or len(v)>2048 for k,v in scope.items()):raise ValueError('XML scope bounds')
            stack.append(scope);scopes[id(item)]=scope
        else:stack.pop()
    root=parser.root;ids={}
    for node in root.iter():
        if node.get('id'):
            if node.tag in {f'{{{X}}}context',f'{{{X}}}unit',f'{{{IX}}}nonFraction',f'{{{IX}}}continuation'} and not re.fullmatch(r'[A-Za-z_][\w.-]*',node.get('id')):raise ValueError('malformed evidence id')
            if node.get('id') in ids:raise ValueError('duplicate XML id')
            ids[node.get('id')]=node
    output=[];serialized_budget=0;output_bytes=0
    for fact in root.iter():
        if fact.tag.rsplit('}',1)[-1] in {'nonFraction','fraction'} and not fact.tag.startswith('{'+IX+'}'):raise ValueError('unsupported inline namespace')
        if fact.tag not in {f'{{{IX}}}nonFraction',f'{{{IX}}}fraction'}:continue
        concept=qname(fact.get('name'),scopes[id(fact)])
        if concept['local_name'] not in TAGS:continue
        if not re.fullmatch(r'https?://fasb.org/us-gaap/\d{4}',concept['namespace']):raise ValueError('unsupported target taxonomy namespace')
        if fact.tag.endswith('}fraction'):raise ValueError('unsupported fraction representation')
        if not fact.get('id'):raise ValueError('missing target fact id')
        continuation=fact.get('continuedAt')
        if continuation and (continuation not in ids or ids[continuation].tag!=f'{{{IX}}}continuation'):raise ValueError('dangling continuation')
        if any(ref not in ids for ref in (fact.get('footnoteRefs') or '').split()):raise ValueError('dangling footnote')
        nil=fact.get('{http://www.w3.org/2001/XMLSchema-instance}nil')
        if nil not in {None,'true','false','1','0'}:raise ValueError('invalid nil declaration')
        context=ids.get(fact.get('contextRef'));unit=ids.get(fact.get('unitRef'))
        if context is None or context.tag!=f'{{{X}}}context':raise ValueError('missing context')
        if unit is None or unit.tag!=f'{{{X}}}unit':raise ValueError('missing unit')
        entities=context.findall(f'{{{X}}}entity/{{{X}}}identifier')
        periods=context.findall(f'{{{X}}}period')
        if len(entities)!=1 or len(periods)!=1:raise ValueError('ambiguous context structure')
        identifier=(entities[0].text or '').strip()
        if not re.fullmatch(r'\d{1,10}',identifier) or int(identifier)==0 or entities[0].get('scheme')!='http://www.sec.gov/CIK':raise ValueError('unsupported entity identifier')
        dates={}
        for child in periods[0]:
            local=child.tag.removeprefix('{'+X+'}')
            if child.tag not in {f'{{{X}}}startDate',f'{{{X}}}endDate',f'{{{X}}}instant'} or local in dates:raise ValueError('unsupported period')
            text=(child.text or '').strip()
            if not re.fullmatch(r'\d{4}-\d{2}-\d{2}',text):raise ValueError('unsupported date')
            dt.date.fromisoformat(text);dates[local]=text
        if set(dates)=={'startDate','endDate'}:
            if dates['startDate']>dates['endDate']:raise ValueError('inverted duration')
            period={'kind':'duration',**dates}
        elif set(dates)=={'instant'}:period={'kind':'instant',**dates}
        else:raise ValueError('incomplete period')
        def measures(parent):
            children=list(parent)
            if not children or len(children)>16 or any(c.tag!=f'{{{X}}}measure' for c in children):raise ValueError('unsupported unit structure')
            return [qname((c.text or '').strip(),scopes[id(c)]) for c in children]
        if all(c.tag==f'{{{X}}}measure' for c in unit):unit_value={'kind':'simple','measures':measures(unit)}
        elif len(unit)==1 and unit[0].tag==f'{{{X}}}divide':
            div=unit[0];num=div.findall(f'{{{X}}}unitNumerator');den=div.findall(f'{{{X}}}unitDenominator')
            if len(div)!=2 or len(num)!=1 or len(den)!=1:raise ValueError('unsupported divided unit')
            unit_value={'kind':'divide','numerator':measures(num[0]),'denominator':measures(den[0])}
        else:raise ValueError('unsupported unit')
        if any(n is not fact and n.tag in {f'{{{IX}}}nonFraction',f'{{{IX}}}fraction'} for n in fact.iter()):raise ValueError('nested numeric facts unsupported')
        fact_text=''.join(fact.itertext())
        if len(fact_text)>100000:raise ValueError('fact text bounds')
        context_xml=E.tostring(context)
        descendants=list(context.iter())
        namespace_chars=sum(sum(len(k)+len(v) for k,v in scopes[id(n)].items()) for n in descendants)
        serialized_budget+=len(context_xml)+namespace_chars
        if len(output)>=10000 or len(context_xml)+namespace_chars>100000 or serialized_budget>10_000_000:raise ValueError('context output bounds')
        record={'concept':concept,'fact_id':fact.get('id'),'context_ref':fact.get('contextRef'),'unit_ref':fact.get('unitRef'),
          'issuer_identifier_as_filed':identifier,'issuer_identifier_scheme':entities[0].get('scheme'),'period':period,'unit':unit_value,
          'dimension_or_scenario_present':any(n.tag in {f'{{{X}}}segment',f'{{{X}}}scenario'} for n in context.iter()),
          'context_xml_serialized':context_xml.decode('ascii'),'context_namespace_bindings':scopes[id(context)],
          'context_descendant_namespace_bindings':[{'element_ordinal':i,'bindings':scopes[id(n)]} for i,n in enumerate(context.iter())],
          'text_untransformed':fact_text,'text_complete':not bool(continuation),'nil_as_filed':nil,'format':qname(fact.get('format'),scopes[id(fact)]) if fact.get('format') else None,
          'scale_as_filed':fact.get('scale'),'sign_as_filed':fact.get('sign'),'decimals_as_filed':fact.get('decimals'),
          'footnote_refs_as_filed':fact.get('footnoteRefs'),'continuation_ref_as_filed':fact.get('continuedAt'),
          'exclude_element_present':any(n.tag==f'{{{IX}}}exclude' for n in fact.iter()),
          'raw_member_sha256':expected_sha,'context_serialization_sha256':digest(context_xml),
          'context_serialization_method':'xml.etree.ElementTree.tostring; default us-ascii, not raw byte slice or canonical XML',
          'numeric_value':None,'numeric_conversion_verified':False,'comparability_verified':False,'training_ready':False}
        output_bytes+=len(json.dumps(record))
        if output_bytes>20_000_000:raise ValueError('evidence output bounds')
        output.append(record)
    return output

def extract(archive,expected_archive_sha,member,expected_member_sha):
    if Path(archive).stat().st_size>20_000_000 or sha(archive)!=expected_archive_sha:raise ValueError('archive bounds/hash mismatch')
    with zipfile.ZipFile(archive) as z:
        info=z.infolist();names=[i.filename for i in info]
        if not 1<=len(info)<=100 or len(names)!=len(set(names)) or sum(i.file_size for i in info)>50_000_000:raise ValueError('archive inventory bounds')
        for i in info:
            p=PurePosixPath(i.filename)
            if p.is_absolute() or '..' in p.parts or p.as_posix()!=i.filename or i.is_dir() or '\\' in i.filename or i.file_size>MAX_MEMBER or i.flag_bits&1:raise ValueError('unsafe member')
        if member not in names:raise ValueError('missing primary member')
        raw=z.read(member)
    facts=parse(raw,expected_member_sha)
    if sha(archive)!=expected_archive_sha:raise ValueError('archive changed')
    return {'schema_version':1,'status':'INLINE_CONTEXT_EVIDENCE_NOT_NUMERICAL_CONVERSION',
      'archive_sha256':expected_archive_sha,'member':member,'raw_member_sha256':expected_member_sha,
      'target_fact_count':len(facts),'target_concepts':sorted({f['concept']['local_name'] for f in facts}),
      'duration_fact_count':sum(f['period']['kind']=='duration' for f in facts),
      'dimension_or_scenario_fact_count':sum(f['dimension_or_scenario_present'] for f in facts),
      'numeric_conversions':0,'comparability_verified':False,'training_ready':False,'execution_ready':False,
      'limitations':['Resolved namespaces and context dates are declarations in retained source bytes, not source authenticity or historical availability.',
      'Text, format, scale, sign, continuations and exclusions are preserved without numeric transformation or financial qualification.',
      'Exact duration dates do not establish comparable operations, fiscal-period meaning, security identity or outcome labels.']},facts

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--archive',required=True);p.add_argument('--archive-sha256',required=True);p.add_argument('--member',required=True);p.add_argument('--member-sha256',required=True);p.add_argument('--output-directory',required=True);a=p.parse_args()
    out=Path(a.output_directory).resolve()
    if out.is_relative_to(Path(__file__).resolve().parents[1]) or not out.parent.is_dir():raise ValueError('trusted private parent outside checkout required')
    out.mkdir(mode=0o700,exist_ok=False);write_private(out/'INCOMPLETE',{'status':'INCOMPLETE_NOT_USABLE'})
    summary,facts=extract(a.archive,a.archive_sha256,a.member,a.member_sha256);publish(out,summary,facts);print(json.dumps(summary))
