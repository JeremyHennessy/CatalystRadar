"""Bounded continuing-operations narrative pairs, never total-company EPS.

Caller must verify filing identity and byte digest. No network or trade actions.
Unknown current period, currency ISO, total-company basis and comparability stay
unknown; a reported combined basic/diluted figure is not two independent facts.
"""
from decimal import Decimal
import re
from financial_admission_rehearsal import plain
from filing_feature_rows import sha
from archive_reviewed_filings import MAX_BYTES

N = r'([0-9]+(?:\.[0-9]+)?)'
PAIR = re.compile(r'Net income from continuing operations totaled \$'+N+
    r' (thousand|million), or \$'+N+
    r' per basic and diluted common share, compared to income from continuing operations of \$'+N+
    r' (thousand|million), or \$'+N+
    r' per basic and diluted common share for the (first|second|third|fourth) quarter of (20[0-9]{2})\.')


def extract(raw):
    if type(raw) is not bytes or len(raw) > MAX_BYTES:
        raise ValueError('bounded exact filing bytes required')
    records = []
    for document in re.finditer(rb'<DOCUMENT>.*?</DOCUMENT>',raw,re.S):
        if not re.search(rb'<TYPE>EX-99\.1\s*\n',document[0]):
            continue
        excluded=[(x.start(),x.end()) for x in re.finditer(
            rb'<!--.*?(?:-->|$)|<(script|style)\b[^>]*>.*?(?:</\1\s*>|$)',document[0],re.S|re.I)]
        for paragraph in re.finditer(rb'<(p|td)\b[^>]*>.*?</\1>',document[0],re.S|re.I):
            if any(paragraph.start()<end and paragraph.end()>start for start,end in excluded):
                continue
            # Full paragraph grammar: no combining unrelated numbers or headings.
            match=PAIR.fullmatch(plain(paragraph[0]))
            if not match:
                continue
            current,unit,eps,prior,prior_unit,prior_eps,quarter,year=match.groups()
            records.append(dict(
                metric='CONTINUING_OPERATIONS_INCOME_AND_COMBINED_BASIC_DILUTED_EPS',
                current_income_reported=current,current_income_unit=unit+' reported dollars',
                prior_income_reported=prior,prior_income_unit=prior_unit+' reported dollars',
                current_income_scaled=str(Decimal(current)*(1000 if unit=='thousand' else 1000000)),
                prior_income_scaled=str(Decimal(prior)*(1000 if prior_unit=='thousand' else 1000000)),
                current_eps_reported=eps,prior_eps_reported=prior_eps,
                eps_basis='REPORTED_COMBINED_BASIC_AND_DILUTED_CONTINUING_OPERATIONS',
                current_period=None,prior_period=quarter+' quarter '+year,currency_iso=None,
                total_company_gaap_eps_verified=False,comparability_verified=False,
                calculated_growth_percent=None,
                document_sha256=sha(document[0]),
                evidence_span={'byte_start':document.start()+paragraph.start(),
                    'byte_end':document.start()+paragraph.end(),'sha256':sha(paragraph[0])},
                status='REPORTED_PAIR_NOT_ADMISSIBLE'))
    return dict(status=('NO_SUPPORTED_CONTINUING_OPERATIONS_GRAMMAR' if not records else
        'AMBIGUOUS_MULTIPLE_MATCHES' if len(records)>1 else 'REPORTED_CONTINUING_OPERATIONS_PAIR_ONLY'),
        records=records,qualified=False,signal=None,orders_created=0,
        limitations=['Continuing operations is not verified total-company GAAP income or EPS.',
            'Current period is not stated in the supported paragraph; no year inferred.',
            'Reported rounded zero EPS is preserved, not treated as missing or an exact zero denominator.',
            'No growth ratio, same-share-basis claim or trading-fact mapping is produced.'])
