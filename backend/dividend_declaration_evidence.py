"""Positive declared-dividend evidence only, never total-return/entitlement data."""
from datetime import datetime
from decimal import Decimal
import re
from financial_admission_rehearsal import plain
from filing_feature_rows import sha

DATE=r'([A-Z][a-z]+ [0-9]{1,2}, 20[0-9]{2})'
DECLARATION=re.compile(r'the board of directors declared a ([0-9]+(?:\.[0-9]+)?) cents-per-share regular quarterly cash dividend\. The dividend is payable '+DATE+r', to shareholders of record as of '+DATE+r'\.')

def extract(raw):
    """Caller validates complete submission identity/hash. Unsupported => unknown.

    Exact grammar is intentionally narrow. No ex-date calculation, ticker map,
    split adjustment, pay-date credit, shareholder entitlement or completeness.
    """
    result={'status':'NO_SUPPORTED_DECLARATION','declarations':[],
        'coverage_complete':False,'total_return_ready':False,'execution_eligible':False}
    docs=list(re.finditer(rb'<DOCUMENT>.*?</DOCUMENT>',raw,re.S))
    if len(docs)!=raw.count(b'<DOCUMENT>') or len(docs)!=raw.count(b'</DOCUMENT>'):
        result['status']='MALFORMED_DOCUMENT_INVENTORY';return result
    exhibits=[]
    for d in docs:
        header=d[0].split(b'<TEXT>',1)[0]
        types=re.findall(rb'^<TYPE>([^\r\n]+)',header,re.M)
        names=re.findall(rb'^<FILENAME>([^\r\n]+)',header,re.M)
        if b'<TEXT>' not in d[0] or len(types)!=1 or len(names)!=1 or not names[0].strip():
            result['status']='MALFORMED_DOCUMENT_INVENTORY';return result
        if types[0].strip()==b'8-K/A':
            result['status']='AMENDMENT_REQUIRES_REVIEW';return result
        if types[0].strip()==b'EX-99.1':exhibits.append(d)
    if len(exhibits)>1:
        result['status']='AMBIGUOUS_EXHIBITS';return result
    for d in exhibits:
        hidden=[(m.start(),m.end())for m in re.finditer(rb'<!--.*?(?:-->|$)|<(script|style)\b[^>]*>.*?(?:</\1\s*>|$)',d[0],re.S|re.I)]
        for p in re.finditer(rb'<(div|p|td)\b[^>]*>.*?</\1>',d[0],re.S|re.I):
            if any(p.start()<b and p.end()>a for a,b in hidden):continue
            for m in DECLARATION.finditer(plain(p[0])):
                try:
                    pay=datetime.strptime(m[2],'%B %d, %Y').date()
                    record=datetime.strptime(m[3],'%B %d, %Y').date()
                    amount=Decimal(m[1])
                    if amount<=0 or pay<record:raise ValueError('invalid dates/amount')
                except ValueError:
                    result['status']='INVALID_SUPPORTED_DECLARATION';result['declarations']=[];return result
                result['declarations'].append({'kind':'REPORTED_REGULAR_QUARTERLY_CASH_DIVIDEND',
                    'amount_cents_per_share':str(amount),'currency_iso':None,
                    'record_date':record.isoformat(),'payment_date':pay.isoformat(),
                    'ex_dividend_date':None,'declaration_date':None,'share_class_verified':False,
                    'payment_occurred_verified':False,'entitlement_verified':False,
                    'historical_security_mapping_verified':False,
                    'evidence_span':{'byte_start':d.start()+p.start(),'byte_end':d.start()+p.end(),'sha256':sha(p[0])},
                    'exhibit_sha256':sha(d[0]),
                    'blockers':['EX_DATE_UNVERIFIED','CURRENCY_AND_SHARE_CLASS_UNVERIFIED',
                                'HISTORICAL_AVAILABILITY_UNVERIFIED','ACTION_COVERAGE_INCOMPLETE']})
    if len(result['declarations'])>1:
        result['status']='AMBIGUOUS_MULTIPLE_DECLARATIONS'
    elif result['declarations']:result['status']='POSITIVE_DECLARATION_ONLY'
    return result
