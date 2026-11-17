import copy
import unittest
from unittest.mock import patch
import sqlite3,tempfile
from pathlib import Path
import financial_pair_candidates as m

class PairCandidateTests(unittest.TestCase):
    def setUp(self):
        self.sub=dict(form='10-Q',period='20260331',fp='Q1',filed='20260501',accepted='2026-05-01 16:00:00.0',cik='123')
        self.base=dict(rowid=1,adsh='test',tag='Revenues',version='us-gaap/2026',ddate='20260331',qtrs='1',uom='USD',segments='',coreg='',value='0',footnote='')
        self.rows=[self.base,dict(self.base,rowid=2,ddate='20250331',value='123')]
        self.tax={('Revenues','us-gaap/2026'):[dict(rowid=1,custom='0',abstract='0',iord='D',datatype='monetary')]}
    def call(self):return m.classify(self.rows,self.sub,self.tax)
    def test_zero_is_valid_candidate_not_admission(self):
        reason,p=self.call();self.assertEqual(reason,'context_matched_candidate');self.assertEqual(p['current']['value'],'0');self.assertFalse(p['comparability_verified']);self.assertIsNone(p['decision_utc']);self.assertFalse(p['training_ready'])
    def test_missing_invalid_values(self):
        for x in ['', 'NaN','Infinity','1,000','1'*101]:
            self.rows[0]['value']=x;self.assertEqual(self.call()[0],'missing_or_invalid_value')
    def test_duplicate_identical_and_other_period(self):
        self.rows.append(dict(self.rows[0]));self.assertEqual(self.call()[0],'ambiguous_context')
        self.rows=[dict(self.base,ddate='20240331')]*2;self.assertEqual(self.call()[0],'ambiguous_context')
    def test_taxonomy_unknown_and_duplicate(self):
        self.tax={};self.assertEqual(self.call()[0],'missing_or_ambiguous_taxonomy')
        self.tax={('Revenues','us-gaap/2026'):[{},{}]};self.assertEqual(self.call()[0],'missing_or_ambiguous_taxonomy')
    def test_calendar_and_unit_limits(self):
        self.sub['period']='20240229';self.assertEqual(self.call()[0],'unsupported_period')
        self.sub['period']='20260331';self.rows[1]['ddate']='20250330';self.assertEqual(self.call()[0],'missing_prior_calendar_period')
        self.rows[0]['uom']=self.rows[1]['uom']='EUR';self.assertEqual(self.call()[0],'unsupported_unit')
    def test_footnotes_preserved_rejected(self):
        self.rows[1]['footnote']='Recast';self.assertEqual(self.call()[0],'footnote_requires_review')
    def test_mixed_context_not_joined(self):
        for k,v in [('uom','EUR'),('version','us-gaap/2025'),('qtrs','2'),('segments','dimension'),('coreg','co')]:
            rows=copy.deepcopy(self.rows);rows[1][k]=v
            self.assertEqual(m.classify(rows,self.sub,self.tax)[0],'mixed_or_unsupported_context')
    def test_full_readonly_audit_hashes_rows_and_presentation(self):
        with tempfile.TemporaryDirectory() as td:
            db=Path(td)/'fixture.sqlite';archive=Path(td)/'synthetic.zip';archive.write_bytes(b'synthetic fixture not actual SEC data')
            c=sqlite3.connect(db)
            c.execute('CREATE TABLE financial_sub(adsh,cik,form,period,fp,filed,accepted)')
            c.execute('INSERT INTO financial_sub VALUES(?,?,?,?,?,?,?)',('test','123','10-Q','20260331','Q1','20260501','2026-05-01 16:00:00.0'))
            c.execute('CREATE TABLE financial_tag(tag,version,custom,abstract,iord,datatype)')
            c.execute('INSERT INTO financial_tag VALUES(?,?,?,?,?,?)',('Revenues','us-gaap/2026','0','0','D','monetary'))
            c.execute('CREATE TABLE financial_pre(adsh,tag,version,inpth,stmt)')
            c.execute('INSERT INTO financial_pre VALUES(?,?,?,?,?)',('test','Revenues','us-gaap/2026','0','IS'))
            c.execute('CREATE TABLE financial_num(adsh,tag,version,ddate,qtrs,uom,segments,coreg,value,footnote)')
            for row in self.rows:c.execute('INSERT INTO financial_num VALUES('+','.join('?'*10)+')',tuple(row[k] for k in m.NUM_FIELDS[1:]))
            extra=dict(self.base,segments='axis=member')
            c.execute('INSERT INTO financial_num VALUES('+','.join('?'*10)+')',tuple(extra[k] for k in m.NUM_FIELDS[1:]))
            c.commit();c.close();before=m.sha(db)
            summary,pairs=m.audit(db,before,archive,m.sha(archive))
            self.assertEqual(summary['candidate_pairs'],1);self.assertEqual(summary['row_counts']['excluded_segment_or_coreg_rows'],1)
            self.assertEqual(pairs[0]['database_sha256'],before);self.assertEqual(pairs[0]['current']['rowid'],1);self.assertEqual(pairs[0]['prior']['rowid'],2)
            self.assertEqual(pairs[0]['presentation'][0]['inpth'],'0');self.assertEqual(m.sha(db),before)
            with self.assertRaisesRegex(ValueError,'hash mismatch'):m.audit(db,'0'*64,archive,m.sha(archive))
    def test_output_failure_remains_incomplete(self):
        with tempfile.TemporaryDirectory() as td:
            out=Path(td);m.write_private(out/'INCOMPLETE',{})
            original=m.write_private
            def fail(path,obj):
                if Path(path).name=='summary.json':raise OSError('synthetic disk failure')
                original(path,obj)
            with patch.object(m,'write_private',side_effect=fail):
                with self.assertRaises(OSError):m.publish(out,{},[])
            self.assertTrue((out/'INCOMPLETE').exists());self.assertFalse((out/'COMPLETE.json').exists())
    def test_output_success_hash_receipt_permissions(self):
        import json,stat
        with tempfile.TemporaryDirectory() as td:
            out=Path(td);m.write_private(out/'INCOMPLETE',{});m.publish(out,{'status':'synthetic'},[])
            self.assertFalse((out/'INCOMPLETE').exists());receipt=json.loads((out/'COMPLETE.json').read_text())
            self.assertEqual(receipt['candidate_pairs_sha256'],m.sha(out/'candidate-pairs.json'))
            self.assertEqual(receipt['summary_sha256'],m.sha(out/'summary.json'))
            self.assertEqual(stat.S_IMODE((out/'candidate-pairs.json').stat().st_mode),0o600)
    def test_form_and_custom_version(self):
        self.sub['form']='S-1';self.assertEqual(self.call()[0],'unsupported_form')
        self.sub['form']='10-Q';self.rows[0]['version']=self.rows[1]['version']='000123-26-000001';self.assertEqual(self.call()[0],'nonstandard_taxonomy')

if __name__=='__main__':unittest.main()
