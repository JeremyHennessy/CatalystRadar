"""Observation-only Nasdaq halt RSS parser. Never certifies interval or fills.

No networking, scheduling, raw redistribution, or production adapter registration.
Caller retains original bytes privately until source storage rights are reviewed.
The source field names the expected format, not authenticated origin. A trusted
collector must separately bind the official URL, HTTP receipt and actual clock.
"""
from datetime import datetime, timezone
from hashlib import sha256
import re
import xml.etree.ElementTree as ET
from zoneinfo import ZoneInfo

ET_ZONE = ZoneInfo('America/New_York')
MAX_BYTES = 2_000_000
MAX_ITEMS = 10_000


def _utc(value):
    if not isinstance(value, str):
        raise ValueError('UTC observation timestamp required')
    stamp = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if stamp.tzinfo is None or stamp.utcoffset().total_seconds() != 0:
        raise ValueError('UTC observation timestamp required')
    return stamp


def _event_time(day, clock):
    if clock and not day:
        raise ValueError('orphan event time without date')
    if not clock:
        return None
    if not re.fullmatch(r'\d{2}/\d{2}/\d{4}', day):
        raise ValueError('unexpected event date')
    if not re.fullmatch(r'\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?', clock):
        raise ValueError('unexpected event time')
    local = datetime.strptime(day + ' ' + clock,
                              '%m/%d/%Y %H:%M:%S.%f' if '.' in clock else '%m/%d/%Y %H:%M:%S')
    candidates = []
    for fold in (0, 1):
        aware = local.replace(tzinfo=ET_ZONE, fold=fold)
        utc = aware.astimezone(timezone.utc)
        if utc.astimezone(ET_ZONE).replace(tzinfo=None) == local:
            candidates.append(utc)
    if not candidates or len(set(candidates)) != 1:
        raise ValueError('nonexistent or ambiguous Eastern timestamp')
    return candidates[0].isoformat().replace('+00:00', 'Z')


def parse_halts(raw, *, retrieved_utc, now_utc, query_kind, query_date=None):
    """Parse retained response bytes; output observations, not negative evidence.

    query_kind: current, haltdate, resumedate. Query date selects event date,
    NOT all overlapping halts. now_utc is caller's actual trusted clock.
    Feed publication dates do not become event or first-observation dates.
    """
    if not isinstance(raw, bytes) or len(raw) > MAX_BYTES:
        raise ValueError('bounded raw bytes required')
    observed, now = _utc(retrieved_utc), _utc(now_utc)
    if observed > now:
        raise ValueError('future retrieval')
    if query_kind not in ('current', 'haltdate', 'resumedate'):
        raise ValueError('unsupported query')
    if query_kind != 'current':
        if not isinstance(query_date, str) or not re.fullmatch(r'\d{8}', query_date):
            raise ValueError('query date must be MMDDYYYY')
        datetime.strptime(query_date, '%m%d%Y')
    elif query_date is not None:
        raise ValueError('current query has no date filter')
    # Decode first: byte scanning alone misses UTF-16/32 DTD declarations.
    # This observation parser intentionally accepts only UTF-8/ASCII XML.
    try:
        xml = raw.decode('utf-8-sig')
    except UnicodeDecodeError as exc:
        raise ValueError('only UTF-8 XML supported') from exc
    if '\x00' in xml:
        raise ValueError('NUL/UTF-16 XML unsupported')
    declaration = re.match(r'<\?xml\s+([^?]*)\?>', xml)
    if declaration:
        encoding = re.search(r'encoding\s*=\s*[\"\']([^\"\']+)', declaration.group(1), re.I)
        if encoding and encoding.group(1).upper() not in ('UTF-8', 'US-ASCII'):
            raise ValueError('only UTF-8 XML supported')
    if '<!DOCTYPE' in xml.upper() or '<!ENTITY' in xml.upper():
        raise ValueError('DTD/entities unsupported')
    root = ET.fromstring(xml)
    if root.tag != 'rss' or len(root.findall('channel')) != 1:
        raise ValueError('exactly one RSS channel required')
    if any(node.tag == 'item' for node in root if node.tag != 'channel'):
        raise ValueError('item outside RSS channel')
    items = root.findall('./channel/item')
    if len(items) > MAX_ITEMS:
        raise ValueError('too many items')
    events, errors = [], []
    for index, item in enumerate(items):
        fields = {}
        try:
            for node in item:
                if len(node):
                    raise ValueError('nested scalar field unsupported')
                key = node.tag.rsplit('}', 1)[-1]
                if key in fields:
                    raise ValueError('duplicate field')
                fields[key] = (node.text or '').strip()
            symbol = fields.get('IssueSymbol', '')
            if not symbol or len(symbol) > 32 or not re.fullmatch(r'[A-Za-z0-9.$/^_-]+', symbol):
                raise ValueError('missing/invalid security symbol')
            start = _event_time(fields.get('HaltDate'), fields.get('HaltTime'))
            if start is None:
                raise ValueError('missing halt start')
            if fields.get('ResumptionDate') and not (fields.get('ResumptionQuoteTime') or fields.get('ResumptionTradeTime')):
                raise ValueError('orphan resumption date without time')
            quote = _event_time(fields.get('ResumptionDate'), fields.get('ResumptionQuoteTime'))
            trade = _event_time(fields.get('ResumptionDate'), fields.get('ResumptionTradeTime'))
            if _utc(start) > observed:
                raise ValueError('halt starts after retrieval')
            if any(_utc(t) < _utc(start) for t in (quote, trade) if t):
                raise ValueError('resumption precedes halt')
            events.append({'symbol': symbol, 'halt_start_utc': start,
                           'scheduled_quote_resume_utc': quote,
                           'scheduled_trade_resume_utc': trade,
                           'reason_code': fields.get('ReasonCode') or None,
                           'market': fields.get('Market') or None,
                           'observed_utc': retrieved_utc, 'source_fields': fields,
                           'confidence': 'SOURCE_OBSERVATION_NOT_EXECUTION_PROOF'})
        except (ValueError, TypeError) as exc:
            errors.append({'item_index': index, 'error': str(exc)})
    return {'source': 'nasdaq_trade_halt_rss', 'sha256': sha256(raw).hexdigest(),
            'retrieved_utc': retrieved_utc, 'query_kind': query_kind,
            'query_date': query_date, 'events': events, 'parse_errors': errors,
            'parsed_items': len(items), 'complete': False, 'ordinary_close': None,
            'carry_in_status': 'BOOTSTRAP_UNKNOWN',
            'confidence': 'PARTIAL_OBSERVATIONS' if not errors else 'INVALID_ITEMS_PRESENT',
            'coverage_warning': 'Event-date query is not interval coverage; empty feed proves no absence.'}
