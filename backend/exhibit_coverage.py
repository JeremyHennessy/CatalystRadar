"""Source-bound complete-submission inventory; not earnings qualification."""
import argparse
from collections import Counter
import json
from pathlib import Path
import re
from filing_feature_rows import build as header_build,sha

def inventory(raw):
    docs=list(re.finditer(rb'<DOCUMENT>.*?</DOCUMENT>',raw,re.S))
    if len(docs)!=raw.count(b'<DOCUMENT>')or len(docs)!=raw.count(b'</DOCUMENT>')or not docs:raise ValueError('incomplete document framing')
    counts=Counter();exhibits=[];sequences=set()
    for d in docs:
        b=d.group();head=b.split(b'<TEXT>',1)[0]
        def field(name):
            matches=re.findall(b'<'+name+b'>([^\r\n]+)',head)
            if len(matches)!=1:raise ValueError('missing or duplicate metadata')
            return matches[0].decode('ascii').strip()
        typ=field(b'TYPE');seq=field(b'SEQUENCE');filename=field(b'FILENAME')
        if not seq.isdigit()or seq in sequences:raise ValueError('ambiguous sequence')
        sequences.add(seq);counts[typ]+=1
        if re.fullmatch(r'EX-99(?:\.\d+)?',typ):
            exhibits.append({'type':typ,'sequence':seq,'filename':filename,
                'byte_start':d.start(),'byte_end':d.end(),'sha256':sha(b),
                'html_image_reference_count':len(re.findall(rb'<img\b',b,re.I)),
                'text_and_graphics_completeness_reviewed':False})
    return {'embedded_document_count':len(docs),'document_type_counts':dict(sorted(counts.items())),
            'ex99_exhibits':exhibits,'inventory_only_not_content_validation':True}

NEXT={
 '0001213900-26-119681':['EXHIBIT_DESCRIPTION_SECOND_QUARTER_BODY_THIRD_QUARTER_CONFLICT','CONTINUING_OPERATIONS_NOT_TOTAL_DILUTED_EPS','ROUNDED_ZERO_EPS_COMPARATOR','REVENUE_MILESTONE_AND_ROUNDING_REQUIRE_RECONCILIATION'],
 '0001628280-26-073578':['PRESENTATION_GRAPHICS_REQUIRE_REVIEW','PRIOR_NOVEMBER_3_2026_PRO_FORMA_GUIDANCE_SOURCE_REQUIRED','EXCLUSIONS_AND_SAME_PERIOD_BASIS_NOT_RECONCILED'],
 '0001193125-26-460589':['INVESTOR_DAY_EVENT_NOVEMBER_10_NOT_NOVEMBER_13_FILING','PRIOR_SAME_PERIOD_GUIDANCE_REQUIRED'],
 '0001174947-26-000991':['OUTSIDE_APPROVED_UNIVERSE','LATER_RELEASE_REVENUE_PAIR_ONLY_NOT_PRIOR_ORIGINAL_VERIFIED']}

def build(reviews_path,archive_dir,computed_at=None):
    headers=header_build(reviews_path,archive_dir,computed_at);rows=[]
    for h in headers['rows']:
        row={'accession':h['event_id'],'issuer_cik':h['issuer_id'],'review_status':h['review_status'],
            'review_reason':h['review_reason'],'status':'SOURCE_MISSING_CHANGED_OR_INVALID','inventory':None,
            'source':None,'first_public_utc':None,'qualified':False,
            'content_review_followups':NEXT.get(h['event_id'],['EXISTING_OUTSIDE_SIGNAL_FAMILY_REVIEW_UNCHANGED'])}
        if h['features']:
            try:
                s=h['features'][0]['sources'][0];raw=(Path(archive_dir)/(s['sha256']+'.txt')).read_bytes()
                if sha(raw)!=s['sha256']:raise ValueError('source changed')
                row['inventory']=inventory(raw);row['source']={k:s[k]for k in ('source_ref','sha256','observed_utc')}
                row['status']='DOCUMENT_FRAMING_AND_METADATA_INVENTORIED_NOW'
                row['header_results_of_operations_marker']=h['features'][1]['value']
            except (ValueError,OSError,UnicodeError):pass
        rows.append(row)
    return {'mode':'RETROSPECTIVE_EXHIBIT_COVERAGE_NOT_FINANCIAL_QUALIFICATION','analysis_utc':headers['computed_at'],
            'reviews_sha256':headers['reviews_sha256'],'manifest_sha256':headers['manifest_sha256'],'rows':rows,
            'inventoried_submissions':sum(r['inventory']is not None for r in rows),
            'embedded_documents':sum(r['inventory']['embedded_document_count']for r in rows if r['inventory']),
            'ex99_exhibits':sum(len(r['inventory']['ex99_exhibits'])for r in rows if r['inventory']),
            'financial_signals':0,'orders':0,'historical_availability_verified':False,
            'limitations':['Framing and metadata coverage is not semantic review of every exhibit or image.',
                'Followups preserve current manual review context, not automated financial findings.',
                'Invocation/reproduction clock is not authenticated completion or historical knowledge.',
                'Item 2.02 marker is not a complete earnings-exhibit search or qualification gate.']}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--reviews',required=True);p.add_argument('--archive-dir',required=True);p.add_argument('--output',required=True);a=p.parse_args()
    r=build(a.reviews,a.archive_dir)
    with Path(a.output).open('x')as f:f.write(json.dumps(r,indent=2)+'\n')
    print(json.dumps({k:r[k]for k in ('inventoried_submissions','embedded_documents','ex99_exhibits')}))
