"""Conservative explicit same-event exhibit relationships, not global dedup."""
import re
from financial_admission_rehearsal import plain
from filing_feature_rows import sha

LINK=re.compile(r'The full text of the press release and the presentation issued in connection with (Investor Day 20[0-9]{2}) are furnished as Exhibit 99\.1 and Exhibit 99\.2, respectively, to this Current Report on Form 8-K\.')

def relate(raw,cik,accession):
    """Archive validator must verify identity before calling. Fail closed.

    Only explicit supported primary-form text establishes this relationship.
    Filing/period dates, similar titles, CIK or nearby timestamps do not.
    """
    documents=[];malformed_documents=0
    for m in re.finditer(rb'<DOCUMENT>.*?</DOCUMENT>',raw,re.S):
        header=m[0].split(b'<TEXT>',1)[0]
        types=re.findall(rb'^<TYPE>([^\r\n]+)',header,re.M);names=re.findall(rb'^<FILENAME>([^\r\n]+)',header,re.M)
        if b'<TEXT>' not in m[0] or len(types)!=1 or len(names)!=1 or not types[0].strip() or not names[0].strip():
            malformed_documents+=1;continue
        documents.append({'type':types[0].strip().decode('ascii',errors='replace'),
            'filename':names[0].strip().decode('ascii',errors='replace'),
            'byte_start':m.start(),'byte_end':m.end(),'sha256':sha(m[0])})
    primary=[d for d in documents if d['type']=='8-K']
    result={'status':'NO_SUPPORTED_EXPLICIT_RELATIONSHIP','bundles':[],
        'global_event_group_complete':False,'cross_filing_dedup_verified':False,
        'first_public_utc':None,'qualified':False,'malformed_documents':malformed_documents}
    if malformed_documents:
        result['status']='MALFORMED_DOCUMENT_INVENTORY';return result
    if len(primary)!=1:
        result['status']='PRIMARY_FORM_MISSING_AMENDED_OR_AMBIGUOUS';return result
    d=primary[0];body=raw[d['byte_start']:d['byte_end']]
    # Reject hidden-context matches without rewriting evidence byte positions.
    excluded=[(m.start(),m.end())for m in re.finditer(rb'<!--.*?(?:-->|$)|<(script|style)\b[^>]*>.*?(?:</\1\s*>|$)',body,re.S|re.I)]
    found=[]
    for p in re.finditer(rb'<(div|p|td)\b[^>]*>.*?</\1>',body,re.S|re.I):
        if any(p.start()<end and p.end()>start for start,end in excluded):continue
        for m in LINK.finditer(plain(p[0])):
            found.append((m[1],{'byte_start':d['byte_start']+p.start(),
                'byte_end':d['byte_start']+p.end(),'sha256':sha(p[0])}))
    if not found:return result
    if len(found)!=1:
        result['status']='AMBIGUOUS_MULTIPLE_PRIMARY_LINKS';return result
    targets=[]
    for typ in ('EX-99.1','EX-99.2'):
        rows=[x for x in documents if x['type']==typ]
        if len(rows)!=1:
            result['status']='LINKED_EXHIBIT_MISSING_OR_DUPLICATED';return result
        targets.append(rows[0])
    if targets[0]['filename']==targets[1]['filename']:
        result['status']='LINKED_EXHIBIT_FILENAME_CONFLICT';return result
    label,span=found[0]
    result['status']='EXPLICIT_SAME_EVENT_EXHIBIT_BUNDLE'
    result['bundles']=[{'bundle_id':f'{cik}:{accession}:explicit-ex99.1-ex99.2',
        'issuer_cik':cik,'accession':accession,'event_label':label,
        'relationship':'PRIMARY_FORM_EXPLICITLY_LINKS_PRESS_RELEASE_AND_PRESENTATION_TO_SAME_NAMED_EVENT',
        'primary_document':d,'relationship_evidence_span':span,'linked_documents':targets,
        'economic_event_date':None,'event_completion_verified':False,
        'all_related_filings_identified':False,'independent_sample_count':None}]
    return result
