import copy,unittest
from source_prepared_correspondence import match,USD

class CorrespondenceTests(unittest.TestCase):
    def fixture(self):
        fact={'concept':{'namespace':'http://fasb.org/us-gaap/2025','local_name':'Revenues'},'dimension_or_scenario_present':False,'numeric_conversion_verified':True,'numeric_value':'123.0','issuer_identifier_as_filed':'0000000123','period':{'kind':'duration','startDate':'2025-05-01','endDate':'2025-07-31'},'unit':{'kind':'simple','measures':[USD]}}
        group={'occurrences':[fact],'numeric_relation':'SINGLE_OCCURRENCE','declared_decimals_equal':True}
        sub={'cik':'123','form':'10-Q'}
        row={'rowid':1,'tag':'Revenues','version':'us-gaap/2025','ddate':'20250731','qtrs':'1','uom':'USD','segments':'','coreg':'','value':'123','footnote':''}
        tag={'tag':'Revenues','version':'us-gaap/2025','datatype':'monetary','custom':'0','abstract':'0','iord':'D'}
        return group,sub,[row],[tag],[{'tag':'Revenues','version':'us-gaap/2025'}]
    def test_candidate_not_equivalence(self):
        args=self.fixture();before=copy.deepcopy(args);reason,record=match(*args)
        self.assertEqual(reason,'candidate_numeric_equal');self.assertFalse(record['exact_prepared_start_date_verified']);self.assertFalse(record['training_ready']);self.assertEqual(args,before)
    def test_dimensions_and_issuer_mismatch(self):
        args=self.fixture();args[0]['occurrences'][0]['dimension_or_scenario_present']=True;self.assertEqual(match(*args)[0],'dimension_or_scenario_unassessed')
        args=self.fixture();args[1]['cik']='124';self.assertEqual(match(*args)[0],'issuer_mismatch')
    def test_duplicates_missing_and_nonfinite(self):
        args=self.fixture();args[2].append(dict(args[2][0]));self.assertEqual(match(*args)[0],'missing_or_ambiguous_prepared_row')
        for value in ['',None,'NaN','Infinity']:
            args=self.fixture();args[2][0]['value']=value;self.assertEqual(match(*args)[0],'missing_or_invalid_prepared_value')
    def test_no_52_week_duration_guess(self):
        args=self.fixture();args[0]['occurrences'][0]['period']['startDate']='2025-05-02';self.assertEqual(match(*args)[0],'calendar_span_unassessed')
    def test_taxonomy_unit_presentation_footnotes(self):
        for kind,expected in [('unit','unsupported_unit_or_taxonomy'),('datatype','unsupported_unit_or_taxonomy'),('presentation','missing_presentation'),('footnote','prepared_footnote_requires_review')]:
            args=self.fixture()
            if kind=='unit':args[0]['occurrences'][0]['unit']['measures']=[{'namespace':'wrong','local_name':'USD'}]
            if kind=='datatype':args[3][0]['datatype']='perShare'
            if kind=='presentation':args[4].clear()
            if kind=='footnote':args[2][0]['footnote']='See footnote'
            self.assertEqual(match(*args)[0],expected)
    def test_different_value_not_restatement(self):
        args=self.fixture();args[2][0]['value']='124';reason,row=match(*args);self.assertEqual(reason,'candidate_numeric_different');self.assertFalse(row['comparability_verified'])
    def test_end_to_end_pinned_inputs_and_manifest_rejection(self):
        import tempfile,sqlite3,json,zipfile
        from pathlib import Path
        import test_inline_context_evidence as fixtures
        from source_prepared_correspondence import audit
        from financial_pair_candidates import sha,publish,write_private
        from inline_context_evidence import digest
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);archive=root/'source.zip';db=root/'prepared.sqlite';manifest=root/'manifest.json';adsh='0000000123-25-000001'
            raw=fixtures.InlineEvidenceTests().xml().replace(b' scale="3"',b'')
            with zipfile.ZipFile(archive,'w') as z:z.writestr('primary.htm',raw)
            conn=sqlite3.connect(db)
            sub={'adsh':adsh,'cik':'123','form':'10-Q','period':'20250731'}
            args=self.fixture();num=args[2][0];num=dict(num,adsh=adsh,value='0');num.pop('rowid');tag=args[3][0];pre=dict(args[4][0],adsh=adsh)
            for table,row in [('financial_sub',sub),('financial_num',num),('financial_tag',tag),('financial_pre',pre)]:
                conn.execute('CREATE TABLE '+table+' ('+','.join(k+' TEXT' for k in row)+')')
                conn.execute('INSERT INTO '+table+' VALUES ('+','.join('?' for _ in row)+')',list(row.values()))
            conn.commit();conn.close()
            receipt={'accession':adsh,'zip_sha256':sha(archive),'primary_member_sha256':digest(raw),'primary_member':'primary.htm','issuer_cik_verified':'123','period_of_report':'2025-07-31','source_url':'https://www.sec.gov/Archives/edgar/data/123/000000012325000001/'+adsh+'-xbrl.zip'}
            manifest.write_text(json.dumps(receipt))
            def run():return audit(archive,sha(archive),'primary.htm',digest(raw),db,sha(db),archive,sha(archive),manifest,sha(manifest))
            with self.assertRaisesRegex(ValueError,'manifest bounds/hash'):
                audit(archive,sha(archive),'primary.htm',digest(raw),db,sha(db),archive,sha(archive),manifest,'0'*64)
            summary,records=run();self.assertEqual(summary['group_dispositions'],{'candidate_numeric_equal':1})
            out=root/'out';out.mkdir();write_private(out/'INCOMPLETE',{});publish(out,summary,records)
            self.assertEqual(json.loads((out/'candidate-pairs.json').read_text()),records)
            for mutation in [{'source_url':'https://example.invalid/'},{'issuer_cik_verified':'124'},{'primary_member_sha256':'0'*64},{'period_of_report':'2025-06-30'}]:
                manifest.write_text(json.dumps(dict(receipt,**mutation)))
                with self.assertRaises(ValueError):run()
            manifest.write_text(json.dumps(receipt)[:-1]+',"accession":"'+adsh+'"}')
            with self.assertRaises(ValueError):run()
            manifest.write_text(json.dumps(receipt)[:-1]+',"unused":NaN}')
            with self.assertRaises(ValueError):run()
