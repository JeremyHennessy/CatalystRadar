import hashlib,json,tempfile,unittest
from pathlib import Path
from filing_comparisons import extract,build,ACCESSION,CIK
from archive_reviewed_filings import run

def fixture():
    return (f'<SEC-DOCUMENT>file\n<SEC-HEADER>\nACCESSION NUMBER: {ACCESSION}\nCENTRAL INDEX KEY: {CIK}\nCONFORMED SUBMISSION TYPE: 8-K\n</SEC-HEADER>\n'.encode()+
        b'<DOCUMENT>\n<TYPE>EX-99.1\n<TEXT><P>For the quarter ended September 30, 2026, IEH had revenues of $10,700,084\nas compared to $7,077,592 for the quarter ended September 30, 2025, reflecting a 51% increase;</P></TEXT></DOCUMENT>')

class ComparisonTests(unittest.TestCase):
    def test_pair_preserves_basis_units_periods(self):
        r=extract(fixture(),CIK,ACCESSION)
        self.assertEqual(r['current']['value'],'10700084');self.assertEqual(r['prior']['value'],'7077592')
        self.assertEqual(r['calculated_percent_change'],'51.182549')
        self.assertIsNone(r['currency_iso']);self.assertIsNone(r['prior']['period_start'])
        self.assertFalse(r['cross_filing_comparability_verified'])
    def test_span_hash(self):
        r=extract(fixture(),CIK,ACCESSION)['evidence_span']
        self.assertEqual(hashlib.sha256(fixture()[r['byte_start']:r['byte_end']]).hexdigest(),r['sha256'])
    def test_amendment_not_silently_substituted(self):
        with self.assertRaises(ValueError):extract(fixture().replace(b'TYPE: 8-K',b'TYPE: 8-K/A'),CIK,ACCESSION)
    def test_wrong_historical_identity(self):
        with self.assertRaises(ValueError):extract(fixture(),'108772',ACCESSION)
    def test_wrong_accession(self):
        with self.assertRaises(ValueError):extract(fixture(),CIK,'0001174947-26-000992')
    def test_duplicate_paragraph(self):
        raw=fixture();raw+=raw[raw.index(b'<DOCUMENT>'):]
        with self.assertRaises(ValueError):extract(raw,CIK,ACCESSION)
    def test_missing_prior(self):
        with self.assertRaises(ValueError):extract(fixture().replace(b'$7,077,592',b'not available'),CIK,ACCESSION)
    def test_zero_prior(self):
        with self.assertRaises(ValueError):extract(fixture().replace(b'$7,077,592',b'$0'),CIK,ACCESSION)
    def test_other_period(self):
        with self.assertRaises(ValueError):extract(fixture().replace(b'September 30, 2025',b'June 30, 2025'),CIK,ACCESSION)
    def test_wrong_exhibit(self):
        with self.assertRaises(ValueError):extract(fixture().replace(b'EX-99.1',b'EX-99.2'),CIK,ACCESSION)
    def test_inconsistent_values(self):
        with self.assertRaises(ValueError):extract(fixture().replace(b'10,700,084',b'20,700,084'),CIK,ACCESSION)
    def test_actual_builder_preserves_unknowns_missing_cases_and_clocks(self):
        with tempfile.TemporaryDirectory()as d:
            root=Path(d);raw=fixture();h=hashlib.sha256(raw).hexdigest()
            review={'issuer_cik':CIK,'accession':ACCESSION,'source_sha256':h,'status':'OUTSIDE_UNIVERSE','reason':'OTCQX not approved'}
            reviews=root/'reviews.json';reviews.write_text(json.dumps({'records':[review]}));archive=root/'archive'
            run([review],archive,get=lambda _:raw,clock=lambda:'2026-11-15T00:00:00Z',sleep=lambda _:None)
            r=build(reviews,archive,'2026-11-15T01:00:00Z');self.assertEqual(r['reported_comparisons'],1)
            row=r['rows'][0];self.assertFalse(row['eligible']);self.assertIsNone(row['historical_ticker']);self.assertIsNone(row['first_public_utc'])
            self.assertEqual(r['qualified_comparisons'],0)
            self.assertEqual(build(reviews,archive,'2026-11-14T00:00:00Z')['reported_comparisons'],0)
            next(archive.glob('*.txt')).unlink();r=build(reviews,archive)
            self.assertEqual(len(r['rows']),1);self.assertEqual(r['reported_comparisons'],0)

if __name__=='__main__':unittest.main()
