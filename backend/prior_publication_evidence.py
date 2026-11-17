"""Offline prior-posting text cue; not a verified issuer assertion or timing.

Caller must validate filing identity and retained source hash. No networking,
trade admission or inference that the SEC acceptance time was first publication.
"""
import re
from hashlib import sha256
from financial_admission_rehearsal import plain

MAX_BYTES = 25_000_000
# Deliberately narrow supported assertion. Other timing language stays unknown.
ASSERTION = re.compile(
    r'The materials referenced during the presentation were posted in the '
    r'Events & Presentations section of our website '
    r'\(https://[A-Za-z0-9.-]+(?:/[A-Za-z0-9._~/-]*)?\) '
    r'prior to the commencement of the presentation\.')


def extract(raw):
    if not isinstance(raw, bytes) or len(raw) > MAX_BYTES:
        raise ValueError('bounded filing bytes required')
    result = {'status': 'NO_SUPPORTED_PRIOR_POSTING_ASSERTION',
        'evidence': [], 'issuer_asserts_prior_posting': None, 'prior_posting_text_cue_found': False,
        'first_public_utc': None, 'first_public_verified': False,
        'filing_time_proves_novelty': False, 'qualified': False}
    documents = []
    matches = list(re.finditer(rb'<DOCUMENT>.*?</DOCUMENT>', raw, re.S))
    if raw.count(b'<DOCUMENT>') != len(matches) or raw.count(b'</DOCUMENT>') != len(matches):
        result['status'] = 'MALFORMED_DOCUMENT_INVENTORY'
        return result
    for match in matches:
        header = match[0].split(b'<TEXT>', 1)[0]
        types = re.findall(rb'^<TYPE>([^\r\n]+)', header, re.M)
        if len(types) != 1 or not types[0].strip() or b'<TEXT>' not in match[0]:
            result['status'] = 'MALFORMED_DOCUMENT_INVENTORY'
            return result
        documents.append((types[0].strip(), match))
    primaries = [m for kind, m in documents if kind in (b'8-K', b'8-K/A')]
    if len(primaries) != 1 or next(kind for kind, m in documents if m is primaries[0]) != b'8-K':
        result['status'] = 'PRIMARY_FORM_MISSING_AMENDED_OR_AMBIGUOUS'
        return result
    document = primaries[0]
    body = document[0]
    excluded = [(m.start(), m.end()) for m in re.finditer(
        rb'<!--.*?(?:-->|$)|<(script|style)\b[^>]*>.*?(?:</\1\s*>|$)', body, re.S | re.I)]
    evidence = []
    for paragraph in re.finditer(rb'<p\b[^>]*>.*?</p>', body, re.S | re.I):
        if any(paragraph.start() < end and paragraph.end() > start for start, end in excluded):
            continue
        text = plain(paragraph[0])
        for _ in ASSERTION.finditer(text):
            evidence.append({'document_sha256': sha256(body).hexdigest(),
                'byte_start': document.start() + paragraph.start(),
                'byte_end': document.start() + paragraph.end(),
                'sha256': sha256(paragraph[0]).hexdigest(),
                'claim_scope': 'UNCONFIRMED_TEXT_CUE_CONTEXT_MAY_QUOTE_OR_DENY',
                'event_time_utc': None, 'independent_web_publication_verified': False})
    if len(evidence) > 1:
        result['status'] = 'AMBIGUOUS_MULTIPLE_PRIOR_POSTING_ASSERTIONS'
    elif evidence:
        result.update(status='PRIOR_POSTING_TEXT_CUE_REQUIRES_CONTEXT_REVIEW',
            evidence=evidence, prior_posting_text_cue_found=True)
    return result
