"""Offline, bounded reported-metric extraction; never a qualified forecast.

Supports one explicit license-revenue narrative grammar, not general earnings
understanding. Raw originals remain private. No network calls or trade actions.
"""
import argparse
from decimal import Decimal
from html.parser import HTMLParser
import json
from pathlib import Path
import re
from filing_feature_rows import build as build_headers, sha
from fact_admission import unknown_families, admit_facts

class Text(HTMLParser):
    def __init__(self): super().__init__(convert_charrefs=True); self.parts=[]
    def handle_data(self,data): self.parts.append(data)

def plain(raw):
    p=Text();p.feed(raw.decode('utf-8',errors='strict'))
    return ' '.join(' '.join(p.parts).split())

# Reported license revenue is NOT promoted to total GAAP revenue. Preserve
# rounded numbers and the issuer's rounded percentage, never invert them.
N=r'([0-9]+(?:\.[0-9]+)?)'
Q=r'(first|second|third|fourth)'
LICENSE=re.compile(r'The Company recorded \$'+N+r' (million|thousand) in license revenue for the '+Q+r' quarter of (20[0-9]{2}), an increase of \$'+N+r' (million|thousand), or '+N+r'%, compared to \$'+N+r' (million|thousand) in license revenue for the '+Q+r' quarter of (20[0-9]{2})\.')

def extract(raw,cik,accession):
    """Caller must validate archive identity/hash. No year/accession whitelist."""
    groups=[];matches=[]
    for d in re.finditer(rb'<DOCUMENT>.*?</DOCUMENT>',raw,re.S):
        if not re.search(rb'<TYPE>EX-99\.1\s*\n',d[0]):continue
        # Hash scopes a document occurrence, not an underlying economic event.
        group={'document_sha256':sha(d[0]),'document_byte_start':d.start(),
            'document_byte_end':d.end(),'filing_group_id':f'{cik}:{accession}',
            'economic_event_group_id':None,'group_status':'DOCUMENT_ONLY_NOT_ECONOMIC_EVENT',
            'metrics':[]}
        excluded=[(x.start(),x.end()) for x in re.finditer(
            rb'<!--.*?(?:-->|$)|<(script|style)\b[^>]*>.*?(?:</\1\s*>|$)',d[0],re.S|re.I)]
        for p in re.finditer(rb'<(p|td)\b[^>]*>.*?</\1>',d[0],re.S|re.I):
            # Reject intersecting contexts; never transform offsets or use text
            # in comments/scripts/styles as an issuer narrative paragraph.
            if any(p.start()<end and p.end()>start for start,end in excluded):continue
            text=plain(p[0]); found=list(LICENSE.finditer(text))
            for m in found:
                v=m.groups();current,prior=Decimal(v[0]),Decimal(v[7])
                row={'metric':'license_revenue_reported_pair','current_reported_value':str(current),
                    'current_unit':v[1]+' reported dollars','prior_reported_value':str(prior),
                    'prior_unit':v[8]+' reported dollars','current_period':v[2]+' quarter '+v[3],
                    'prior_period':v[9]+' quarter '+v[10],'currency_iso':None,
                    'issuer_reported_increase':v[4],'increase_unit':v[5]+' reported dollars',
                    'issuer_reported_percent':v[6],'calculated_growth_percent':None,
                    'current_scaled_value':str(current*(1000000 if v[1]=='million' else 1000)),
                    'prior_scaled_value':str(prior*(1000000 if v[8]=='million' else 1000)),
                    'basis':'LICENSE_REVENUE_NOT_VERIFIED_TOTAL_GAAP_REVENUE',
                    'same_quarter_prior_year':v[2]==v[9] and int(v[3])==int(v[10])+1,
                    'evidence_span':{'byte_start':d.start()+p.start(),'byte_end':d.start()+p.end(),'sha256':sha(p[0])},
                    'status':'REPORTED_ROUNDED_PAIR_NOT_ADMISSIBLE'}
                group['metrics'].append(row);matches.append(row)
        groups.append(group)
    # More than one supported paragraph is ambiguity, not more samples. Keep
    # evidence but admit nothing, including duplicated or amended releases.
    status='NO_SUPPORTED_FINANCIAL_GRAMMAR' if not matches else ('AMBIGUOUS_MULTIPLE_MATCHES' if len(matches)>1 else 'REPORTED_PAIR_ONLY')
    return groups,status

def build(reviews_path,archive_dir,computed_at=None):
    headers=build_headers(reviews_path,archive_dir,computed_at)
    rows=[]
    for h in headers['rows']:
        row={'accession':h['event_id'],'issuer_cik':h['issuer_id'],'analysis_utc':headers['computed_at'],
            'source':None,'documents':[],'status':'SOURCE_UNAVAILABLE_OR_INVALID',
            'fact_admission':unknown_families(),'qualified':False,'signal':None,
            'first_public_utc':None,'decision_utc':None,'economic_event_group_id':None,
            'explicit_document_relationships':None,'dividend_declaration_evidence':None,
            'continuing_operations_evidence':None,
            'review_status':h['review_status'],'review_reason':h['review_reason'],
            'blockers':['RETROSPECTIVE_SELECTION','HISTORICAL_AVAILABILITY_UNVERIFIED',
                'ECONOMIC_EVENT_GROUP_UNRESOLVED','MISSING_TOTAL_GAAP_EPS_AND_COMPARABILITY',
                'NO_FROZEN_CLASSIFICATION_RECEIPT','OUTCOMES_UNQUALIFIED']}
        if h['features']:
            source=h['features'][0]['sources'][0]
            raw=(Path(archive_dir)/(source['sha256']+'.txt')).read_bytes()
            if sha(raw)!=source['sha256']:raise ValueError('source changed during extraction')
            row['source']={k:source[k] for k in ('source_ref','sha256','observed_utc')}
            if any(f['name']=='header_is_8k_amendment' and f['value'] for f in h['features']):
                row['status']='AMENDMENT_REQUIRES_ECONOMIC_EVENT_REVIEW'
            else:
                row['documents'],row['status']=extract(raw,h['issuer_id'],h['event_id'])
                from event_document_links import relate
                row['explicit_document_relationships']=relate(raw,h['issuer_id'],h['event_id'])
                from dividend_declaration_evidence import extract as dividend_evidence
                row['dividend_declaration_evidence']=dividend_evidence(raw)
                from continuing_operations_evidence import extract as continuing_evidence
                row['continuing_operations_evidence']=continuing_evidence(raw)
            # Intentionally no license-revenue -> gaap_revenue mapping. This
            # invokes the actual admission contract, not a hand-coded outcome.
            row['fact_admission']['EARNINGS_GROWTH']=admit_facts('EARNINGS_GROWTH',{})
        rows.append(row)
    return {'mode':'SOURCE_GROUNDED_FINANCIAL_ADMISSION_REHEARSAL','computed_at':headers['computed_at'],
        'reviews_sha256':headers['reviews_sha256'],'manifest_sha256':headers['manifest_sha256'],
        'rows':rows,'counts':{'rows':len(rows),'source_validated':sum(r['source'] is not None for r in rows),
            'reported_pair_rows':sum(r['status']=='REPORTED_PAIR_ONLY' for r in rows),
            'explicit_same_event_bundles':sum(len((r['explicit_document_relationships'] or {}).get('bundles',[])) for r in rows),
            'positive_dividend_declaration_rows':sum((r['dividend_declaration_evidence'] or {}).get('status')=='POSITIVE_DECLARATION_ONLY' for r in rows),
            'financial_fact_complete':0,'qualified':0,'economic_event_groups_verified':0},
        'orders':0,'protocol_activated':False,'source_authenticity_verified':False,
        'limitations':['Exact supported narrative grammar only; all other layouts remain unknown.',
            'Rounded reported license revenue is not total GAAP revenue; no growth forecast computed.',
            'Document groups are provenance scopes, not independent economic events.',
            'Private source bytes verified only during this offline rehearsal, not by public CI.',
            'Current retrieval and computation do not establish first-public or pre-event availability.']}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--reviews',required=True);p.add_argument('--archive-dir',required=True);p.add_argument('--output',required=True);a=p.parse_args()
    result=build(a.reviews,a.archive_dir)
    with Path(a.output).open('x') as f:f.write(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result['counts']))
