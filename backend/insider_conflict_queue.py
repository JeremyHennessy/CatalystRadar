"""Bounded offline source-review queue. Contradictions are not source-error findings."""
from collections import Counter, defaultdict
import datetime as dt
import re
from insider_transaction_evidence import audit, date

FLAG = 'PURCHASE_SALE_DIRECTION_CONTRADICTION'
ARCHIVE_URL = 'https://www.sec.gov/files/datastandardsinnovation/data/insider-transactions-data-sets/2026q2_form345.zip'
LIMITATIONS = [
 'This is a source-review queue, not evidence of erroneous filings, misconduct, market trades, coordinated intent, or profitable opportunities.',
 'P/S includes open-market OR private transactions. Opposing acquisition/disposition fields remain as filed and unresolved.',
 'Counts are source rows, not unique economic transactions or people. Amendments remain separate, not independent confirmations; Form 4/A may amend selected lines without repeating unchanged lines, so whole-filing replacement is not assumed.',
 'Q2 is a filing-date batch, not a transaction quarter. Audit time is not download, first-public availability or a decision clock.',
 'Footnote links have not been substantively reviewed; original filing and amendment lineage remain prerequisites.',
 'No owner names, prices, quantities, currency, dollar totals or footnote narratives are published. No prediction, execution or training qualification is granted.',
 'The archive is retained evidence; SEC search links are navigation aids, not verified original-document retrievals.'
]

def project(records):
    if not isinstance(records,list) or not 0 < len(records) <= 100000: raise ValueError('bounded audited records required')
    groups=defaultdict(list);seen=set()
    for r in records:
        fields=r['transaction_fields_as_filed'];code=fields['TRANS_CODE'];direction=fields['TRANS_ACQUIRED_DISP_CD']
        conflict=code in ('P','S') and direction in ('A','D') and direction != {'P':'A','S':'D'}[code]
        flagged=FLAG in r['diagnostic_flags']
        if flagged != conflict: raise ValueError('contradiction diagnostic mismatch')
        if not conflict:continue
        s=r['submission_as_filed'];acc=r['accession'];key=r['transaction_key']
        if not isinstance(acc,str) or not re.fullmatch(r'[0-9]{10}-[0-9]{2}-[0-9]{6}',acc) or s['ACCESSION_NUMBER']!=acc:raise ValueError('accession mismatch')
        if not isinstance(key,str) or not re.fullmatch(r'[0-9]{1,20}',key) or (acc,key) in seen:raise ValueError('duplicate/invalid transaction identity')
        seen.add((acc,key));cik=s['ISSUERCIK']
        if not isinstance(cik,str) or not re.fullmatch(r'[0-9]{1,10}',cik) or not int(cik):raise ValueError('invalid issuer')
        filed=date(s['FILING_DATE'])
        if filed is None or not dt.date(2026,4,1)<=filed<=dt.date(2026,6,30):raise ValueError('filing outside Q2 batch')
        if s['DOCUMENT_TYPE'] not in ('4','4/A','5','5/A'):raise ValueError('unsupported transaction form')
        if not isinstance(r['source_row_sha256'],str) or not re.fullmatch(r'[a-f0-9]{64}',r['source_row_sha256']):raise ValueError('missing row lineage')
        groups[acc].append(r)
    if len(groups)>100:raise ValueError('queue over bounded filing count')
    cards=[]
    for acc,rows in sorted(groups.items()):
        s=rows[0]['submission_as_filed']
        if any(r['submission_as_filed']!=s for r in rows):raise ValueError('conflicting submission identity')
        codes=Counter(r['transaction_fields_as_filed']['TRANS_CODE']+':'+r['transaction_fields_as_filed']['TRANS_ACQUIRED_DISP_CD'] for r in rows)
        flags=Counter(f for r in rows for f in r['diagnostic_flags'])
        # Only fixed known labels, no source-provided narrative or owner/value fields.
        context={f:flags[f] for f in ('FOOTNOTE_CONTEXT_REQUIRED','AMENDMENT_NOT_RECONCILED','DEEMED_EXECUTION_DATE_REQUIRES_REVIEW','TRANS_PRICEPERSHARE_ZERO') if flags[f]}
        cards.append({'lead_id':'insider-field-conflict:2026q2:'+acc,'issuer_cik':str(int(s['ISSUERCIK'])).zfill(10),'accession':acc,
                      'filing_date':date(s['FILING_DATE']).isoformat(),'form_as_filed':s['DOCUMENT_TYPE'],
                      'status':'REQUIRES_SOURCE_REVIEW_NOT_SOURCE_ERROR_FINDING','conflicting_source_rows':len(rows),
                      'reported_code_direction_counts':dict(sorted(codes.items())),'additional_context_row_counts':context,
                      'source_row_lineage':[{'transaction_key':r['transaction_key'],'sha256':r['source_row_sha256']} for r in rows],
                      'source_archive_url':ARCHIVE_URL,'sec_search_url':'https://www.sec.gov/edgar/search/#/q='+acc,
                      'missing_requirements':['Original filing and field context review','Referenced footnote explanation review','Original/amended filing line-level lineage reconciliation','Verified security identity and historical availability'],
                      'research_question':'How do the original filing and footnotes explain these opposing reported code and acquisition/disposition fields?',
                      'economic_direction_verified':False,'execution_ready':False,'training_ready':False})
    return cards

def build(database,database_sha256,archive,archive_sha256):
    if database_sha256!='503b308fe6529dd2573f4e307e2855d672a407009b71b8b5eb453c4907859386' or archive_sha256!='11f1b2bbbdcbe6347a34437c02d04202fda0eca1dbb023726e4b56504b802e27':
        raise ValueError('Q2 retained source lineage changed; re-audit')
    summary,records=audit(database,database_sha256,archive,archive_sha256)
    cards=project(records)
    return {'schema_version':1,'status':'BOUNDED_OFFLINE_SOURCE_REVIEW_QUEUE','filing_batch':'2026q2',
            'generated_at':dt.datetime.now(dt.timezone.utc).isoformat(),'selection_rule':'Every audited nonderivative row with P:D or S:A in Q2 filing-date batch; grouped by accession; max100 filings',
            'source_archive_sha256':archive_sha256,'database_sha256':database_sha256,'source_archive_url':ARCHIVE_URL,
            'audited_nonderivative_rows':summary['counts']['transaction_rows'],'conflicting_source_rows':sum(c['conflicting_source_rows'] for c in cards),
            'filings':len(cards),'issuer_ciks':len({c['issuer_cik'] for c in cards}),
            'collection_performed':False,'execution_ready':False,'training_ready':False,'limitations':LIMITATIONS,'cards':cards}
