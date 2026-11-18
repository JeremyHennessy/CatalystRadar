"""One reviewed filing's reported class assertion, never a historical security join."""
import argparse
import json
import re
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from frozen_outcome_source_review import build as source_review, ACC, CIK, RAW_SHA, sha, ref
from filing_registrant_identity import extract as filers

H='http://www.w3.org/1999/xhtml'
I='http://www.xbrl.org/2013/inlineXBRL'
X='http://www.xbrl.org/2003/instance'
FIELDS={'Security12bTitle':'Common Stock, par value $0.001 per share','TradingSymbol':'TXMD','SecurityExchangeName':'Nasdaq'}

def text(node):
    return ' '.join(''.join(node.itertext()).split())

def inspect(raw):
    if type(raw) is not bytes or not 0<len(raw)<=25000000 or b'\0' in raw or re.search(rb'<!\s*(?:DOCTYPE|ENTITY)',raw,re.I):
        raise ValueError('bounded source without entities required')
    identity=filers(raw,ACC)
    if [(f['cik'],f['name_as_filed']) for f in identity['filers']]!=[(CIK,'TherapeuticsMD, Inc.')]:
        raise ValueError('single reviewed registrant required')
    docs=list(re.finditer(rb'<DOCUMENT>.*?</DOCUMENT>',raw,re.S))
    if len(docs)!=raw.count(b'<DOCUMENT>') or len(docs)!=raw.count(b'</DOCUMENT>'):
        raise ValueError('document inventory')
    selected=[]
    for d in docs:
        header=d[0].split(b'<TEXT>',1)[0]
        kind=re.findall(rb'^<TYPE>([^\r\n]+)',header,re.M)
        if len(kind)!=1:raise ValueError('document type')
        if kind==[b'8-K']:selected.append(d)
    if len(selected)!=1:raise ValueError('unique 8-K required')
    doc=selected[0]
    if re.findall(rb'^<FILENAME>([^\r\n]+)',doc[0].split(b'<TEXT>',1)[0],re.M)!=[b'ea0312204-8k_therapeu.htm']:
        raise ValueError('reviewed primary document')
    htmls=list(re.finditer(rb'<html\b.*?</html>',doc[0],re.S))
    if len(htmls)!=1:raise ValueError('unique XHTML required')
    hm=htmls[0];html=hm[0];offset=doc.start()+hm.start()
    try:root=ET.fromstring(html)
    except ET.ParseError as e:raise ValueError('invalid XHTML') from e
    if root.tag!='{'+H+'}html':raise ValueError('XHTML namespace')
    if re.findall(rb'xmlns:dei="([^"]+)"',html)!=[b'http://xbrl.sec.gov/dei/2026']:raise ValueError('DEI namespace')
    parents={c:p for p in root.iter() for c in p}
    contexts=[n for n in root.iter('{'+X+'}context') if n.get('id')=='AsOf2026-11-13']
    if len(contexts)!=1:raise ValueError('unique reviewed context')
    context=contexts[0]
    if [n.tag for n in context]!=['{'+X+'}entity','{'+X+'}period'] or len(list(context)[0])!=1 or len(list(context)[1])!=2:raise ValueError('context structure')
    identifiers=list(context.iter('{'+X+'}identifier'))
    if len(identifiers)!=1 or identifiers[0].attrib!={'scheme':'http://www.sec.gov/CIK'} or identifiers[0].text!=CIK:
        raise ValueError('context entity')
    # This as-filed start/end is NOT an effective interval or an instant.
    expected={X+'}entity',X+'}identifier',X+'}period',X+'}startDate',X+'}endDate',X+'}context'}
    if any(n.tag.removeprefix('{') not in expected for n in context.iter()):raise ValueError('context scope/dimensions')
    for tag in ['startDate','endDate']:
        ns=list(context.iter('{'+X+'}'+tag))
        if len(ns)!=1 or ns[0].text!='2026-11-13':raise ValueError('context period')
    records={};rows=[]
    for name,value in FIELDS.items():
        nodes=[n for n in root.iter('{'+I+'}nonNumeric') if n.get('name')=='dei:'+name]
        if len(nodes)!=1:raise ValueError('unique class fact')
        node=nodes[0]
        allowed={'name','id','contextRef'}|({'format'} if name=='SecurityExchangeName' else set())
        if set(node.attrib)!=allowed or node.get('contextRef')!='AsOf2026-11-13' or text(node)!=value or list(node):
            raise ValueError('reviewed fact attributes/text')
        if name=='SecurityExchangeName' and node.get('format')!='ixt-sec:exchnameen':raise ValueError('exchange transform')
        lineage=[];p=node
        while p in parents:p=parents[p];lineage.append(p)
        if any(p.tag in ('{'+I+'}hidden','{'+H+'}script','{'+H+'}style') or 'hidden' in p.attrib or re.search(r'display\s*:\s*none|visibility\s*:\s*hidden',p.get('style',''),re.I) for p in lineage):raise ValueError('hidden class fact')
        row=[p for p in lineage if p.tag=='{'+H+'}tr']
        if len(row)!=1:raise ValueError('class row')
        rows.append(row[0])
        matches=list(re.finditer(rb'<ix:nonNumeric\b[^>]*\bname="dei:'+name.encode()+rb'"[^>]*>.*?</ix:nonNumeric>',html,re.S))
        if len(matches)!=1:raise ValueError('byte correspondence')
        m=matches[0]
        records[name]={'text_as_reported':value,'context_ref':'AsOf2026-11-13','source_span':ref(raw,offset+m.start(),offset+m.end())}
    if any(r is not rows[0] for r in rows):raise ValueError('separate class rows')
    table=parents[rows[0]]
    if table.tag!='{'+H+'}table' or len(list(table))!=2 or list(table)[1] is not rows[0]:raise ValueError('reviewed table structure')
    headers=[text(n) for n in list(table)[0] if text(n)]
    if headers!=['Title of Each Class','Trading Symbol','Name of Each Exchange on Which Registered']:raise ValueError('class column headers')
    cells=[text(n) for n in rows[0] if text(n)]
    if cells!=[FIELDS['Security12bTitle'],'TXMD','The Nasdaq Stock Market LLC']:raise ValueError('class column correspondence')
    cm=list(re.finditer(rb'<xbrli:context id="AsOf2026-11-13">.*?</xbrli:context>',html,re.S))
    if len(cm)!=1:raise ValueError('context byte correspondence')
    return {'fields':records,'exchange_cell_text_as_reported':'The Nasdaq Stock Market LLC','inline_exchange_transformation':'ixt-sec:exchnameen (not evaluated)','context':{'issuer_cik_as_reported':CIK,'start_date_as_reported':'2026-11-13','end_date_as_reported':'2026-11-13','period_kind':'DURATION_AS_FILED_NOT_EFFECTIVE_INTERVAL','source_span':ref(raw,offset+cm[0].start(),offset+cm[0].end())},'registrant_evidence':identity,'primary_document_sha256':sha(doc[0])}

def build(root,archive):
    prior=source_review(root,archive) # Existing frozen cohort, archive/member hashes and receipt identity.
    with zipfile.ZipFile(archive) as z:raw=z.read(RAW_SHA+'.txt')
    if sha(raw)!=RAW_SHA:raise ValueError('filing changed')
    finding=inspect(raw)
    return {'schema_version':1,'id':'txmd-retained-cover-class','status':'FILING_REPORTED_CLASS_ASSERTION_NOT_SECURITY_MAPPING','issuer_cik':CIK,'accession':ACC,'selection_changed':False,'source':prior['source'],'finding':finding,'security_id':None,'effective_from':None,'effective_to':None,'historical_mapping_verified':False,'corporate_action_continuity_verified':False,'price_join_performed':False,'first_public_utc':None,'qualified_outcomes':0,'execution_ready':False,'training_ready':False,'limitations':['The cover associates a reported class, symbol and exchange within this filing only. It is not a historical security identifier or verified effective-date interval.','The context reports equal start and end dates; no instant, listing date or continuous listing is inferred.','No absence of splits, dividends, symbol changes, delisting or trading halts is established.','Raw inline Nasdaq text and exchange-cell wording are preserved; the exchange transformation is not evaluated.','No private quotes, returns, CUSIP/FIGI mapping, first-public time, prices, fills or orders are added. Only a narrow issuer-disclosed class assertion is published; original retained filing bytes stay private.']}

def main(argv=None):
    p=argparse.ArgumentParser();p.add_argument('root');p.add_argument('archive');p.add_argument('output');a=p.parse_args(argv)
    result=build(a.root,a.archive)
    with Path(a.output).open('x') as f:json.dump(result,f,indent=2);f.write('\n')

if __name__=="__main__":main()
