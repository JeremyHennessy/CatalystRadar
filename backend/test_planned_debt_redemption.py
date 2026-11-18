import copy
import json
from pathlib import Path
import unittest
from unittest.mock import patch
import planned_debt_redemption as m

ROOT=Path(__file__).resolve().parents[1]
def fixture():
    h=('<SEC-DOCUMENT>\n<SEC-HEADER>\nACCESSION NUMBER: '+m.ACCESSION+'\nITEM INFORMATION: Regulation FD Disclosure\nFILER:\n COMPANY DATA:\n  COMPANY CONFORMED NAME: GOODYEAR TIRE & RUBBER CO /OH/\n  CENTRAL INDEX KEY: '+m.CIK+'\n FILING VALUES:\n</SEC-HEADER>\n<DOCUMENT>\n<TYPE>8-K\n<FILENAME>gt-20261113.htm\n<TEXT>\n').encode()
    def context(t,n):
        b=('<div><span style="">'+t+'</span></div>').encode();return b.replace(b'style=""',b'style="'+b'a'*(n-len(b))+b'"')
    return h+b' '*(19300-len(h))+context(m.TERMS,575)+b' '*29+context(m.CAVEAT,327)+b'\n</TEXT></DOCUMENT>'
class RedemptionTests(unittest.TestCase):
    def test_context_and_exact_spans(self):
        raw=fixture();r=m.inspect_context(raw)
        for s in r.values():self.assertEqual(m.digest(raw[s['byte_start']:s['byte_end']]),s['sha256'])
    def test_ambiguity_negation_identity_context(self):
        raw=fixture()
        for bad in (raw.replace(b'</TEXT>',raw[19300:19875]+b'</TEXT>'),raw.replace(b'called for',b'did not call for'),raw.replace(b'0000042582',b'0000042583'),raw.replace(b'gt-20261113.htm',b'xx-20261113.htm'),raw.replace(b'<TYPE>8-K',b'<TYPE>8-K/A'),raw.replace(b'Regulation FD Disclosure',b'Other Events'),raw.replace(b'100%',b'101%'),raw.replace(b'not a notice',b'now a notice'),raw[:19300]+b'<!--'+raw[19300:]+b'-->'):
            with self.subTest(bad=bad[-40:]):
                with self.assertRaises(ValueError):m.inspect_context(bad)
    def test_archive_pin_and_source_pin(self):
        with self.assertRaises((ValueError,FileNotFoundError)):m.build('/missing')
        with patch.object(m,'validate_archive',return_value={'packages':[{'accession':m.ACCESSION,'source_sha256':'0'*64}]}):
            with self.assertRaises(ValueError):m.build('unused')
    def test_public_semantics(self):
        r=json.loads((ROOT/'web/company-findings/planned-debt-redemption.json').read_text())
        self.assertEqual(r['principal_scaled_value'],'700000000');self.assertEqual(r['planned_redemption_date'],'2026-12-15')
        for k in ('currency_iso','net_debt_change','cash_change','first_public_utc','security_id','actual_completion_date'):self.assertIsNone(r[k])
        for k in ('redemption_completion_verified','filing_is_redemption_notice','market_outcome_qualified','training_ready','execution_ready'):self.assertIs(r[k],False)
if __name__=='__main__':unittest.main()
