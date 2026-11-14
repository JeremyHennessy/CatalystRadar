import unittest
from hashlib import sha256
from halts_observation import parse_halts

OBS = '2026-11-14T20:00:00Z'

def feed(fields=None):
    item = '' if fields is None else '<item>' + ''.join(f'<n:{k}>{v}</n:{k}>' for k,v in fields.items()) + '</item>'
    return ('<rss xmlns:n="urn:synthetic-test"><channel>' + item + '</channel></rss>').encode()

def fixture(**changes):
    d = {'IssueSymbol':'TEST','HaltDate':'11/13/2026','HaltTime':'15:59:00','ReasonCode':'T1'}
    d.update(changes)
    return feed(d)

def parse(raw, **args):
    return parse_halts(raw,retrieved_utc=OBS,now_utc=OBS,query_kind='haltdate',query_date='11132026',**args)

class HaltTests(unittest.TestCase):
    def test_empty_never_complete(self):
        x=parse(feed()); self.assertFalse(x['complete']); self.assertIsNone(x['ordinary_close']); self.assertEqual(x['carry_in_status'],'BOOTSTRAP_UNKNOWN')
    def test_exact_hash_and_eastern(self):
        raw=fixture(); x=parse(raw); self.assertEqual(x['sha256'],sha256(raw).hexdigest()); self.assertEqual(x['events'][0]['halt_start_utc'],'2026-11-13T20:59:00Z')
    def test_quote_not_trade(self):
        x=parse(fixture(ResumptionDate='11/13/2026',ResumptionQuoteTime='16:01:00')); self.assertIsNone(x['events'][0]['scheduled_trade_resume_utc']); self.assertIsNone(x['ordinary_close'])
    def test_scheduled_trade_not_close(self):
        x=parse(fixture(ResumptionDate='11/13/2026',ResumptionTradeTime='16:02:00')); self.assertIsNone(x['ordinary_close']); self.assertFalse(x['complete'])
    def test_carry_in_not_cleared(self):
        x=parse(fixture(HaltDate='11/12/2026')); self.assertEqual(x['carry_in_status'],'BOOTSTRAP_UNKNOWN')
    def test_bad_timestamp_is_not_absence(self):
        x=parse(fixture(HaltTime='garbage')); self.assertTrue(x['parse_errors']); self.assertFalse(x['complete'])
    def test_ambiguous_dst(self):
        x=parse(fixture(HaltDate='11/01/2026',HaltTime='01:30:00')); self.assertTrue(x['parse_errors'])
    def test_nonexistent_dst(self):
        x=parse(fixture(HaltDate='03/08/2026',HaltTime='02:30:00')); self.assertTrue(x['parse_errors'])
    def test_summer_offset(self):
        x=parse(fixture(HaltDate='07/01/2026',HaltTime='15:00:00')); self.assertEqual(x['events'][0]['halt_start_utc'],'2026-07-01T19:00:00Z')
    def test_bad_root_and_dtd(self):
        for raw in (b'<html/>',b'<!DOCTYPE rss><rss><channel/></rss>',b'<rss>'):
            with self.assertRaises(Exception):parse(raw)
    def test_future_retrieval(self):
        with self.assertRaises(ValueError):parse_halts(feed(),retrieved_utc=OBS,now_utc='2026-11-13T00:00:00Z',query_kind='current')
    def test_missing_or_future_start(self):
        for changes in ({'HaltTime':''},{'HaltDate':'11/15/2026'}):self.assertTrue(parse(fixture(**changes))['parse_errors'])
    def test_invalid_or_unbounded_inputs(self):
        with self.assertRaises(ValueError):parse(b' ' * 2_000_001)
        with self.assertRaises(ValueError):parse_halts(feed(),retrieved_utc=OBS,now_utc=OBS,query_kind='range')
    def test_utf16_entity_bypass_rejected(self):
        xml='<!DOCTYPE rss [<!ENTITY e "TEST">]><rss><channel><item><IssueSymbol>&e;</IssueSymbol></item></channel></rss>'
        for encoding in ('utf-16','utf-16-le','utf-16-be','utf-32'):
            with self.assertRaises(ValueError):parse(xml.encode(encoding))
    def test_unsupported_declared_encoding(self):
        with self.assertRaises(ValueError):parse(b'<?xml version="1.0" encoding="ISO-8859-1"?><rss><channel/></rss>')
    def test_utf8_bom_and_declaration_supported(self):
        x=parse(b'\xef\xbb\xbf<?xml version="1.0" encoding="UTF-8"?><rss><channel/></rss>')
        self.assertFalse(x['complete'])
    def test_duplicate_channels_rejected(self):
        with self.assertRaises(ValueError):parse(b'<rss><channel/><channel/></rss>')
    def test_outside_channel_items_rejected(self):
        with self.assertRaises(ValueError):parse(b'<rss><channel/><item/></rss>')
    def test_nested_scalar_fields_rejected(self):
        x=parse(fixture().replace(b'TEST',b'TE<hidden>BAD</hidden>ST'))
        self.assertTrue(x['parse_errors']);self.assertFalse(x['events'])
    def test_duplicate_local_field_rejected(self):
        x=parse(fixture().replace(b'</item>',b'<IssueSymbol>OTHER</IssueSymbol></item>'))
        self.assertTrue(x['parse_errors']);self.assertFalse(x['events'])
    def test_orphan_resumption_fields(self):
        for changes in ({'ResumptionTradeTime':'broken'}, {'ResumptionQuoteTime':'16:00:00'}, {'ResumptionDate':'11/13/2026'}):
            self.assertTrue(parse(fixture(**changes))['parse_errors'])
    def test_resumption_before_start(self):
        self.assertTrue(parse(fixture(ResumptionDate='11/12/2026',ResumptionTradeTime='16:00:00'))['parse_errors'])

if __name__=='__main__':unittest.main()
