import unittest,tempfile
from pathlib import Path
from manager_holdings_sample import holding,build,one
class ManagerSampleTests(unittest.TestCase):
    def row(self):
        return dict(rowid=7,INFOTABLE_SK='12',NAMEOFISSUER='Reported name',TITLEOFCLASS='CL A',CUSIP='001234567',FIGI='',PUTCALL='Put',SSHPRNAMTTYPE='SH',INVESTMENTDISCRETION='SOLE',OTHERMANAGER='',VALUE='900000',SSHPRNAMT='1000',PHONE='private')
    def test_allowlist_retains_semantics_not_values(self):
        p=holding(self.row());self.assertEqual(p['CUSIP'],'001234567');self.assertEqual(p['TITLEOFCLASS'],'CL A')
        self.assertEqual(p['PUTCALL'],'Put');self.assertEqual(p['source_data_row'],7);self.assertFalse(p['security_identity_verified'])
        for k in ['VALUE','SSHPRNAMT','PHONE']:self.assertNotIn(k,p)
    def test_blank_preserved(self):
        r=self.row();r['PUTCALL']='';self.assertEqual(holding(r)['PUTCALL'],'')
    def test_source_strings_not_repaired(self):
        r=self.row();r['CUSIP']='bad source identifier';self.assertEqual(holding(r)['CUSIP'],'bad source identifier')
    def test_field_bound(self):
        r=self.row();r['NAMEOFISSUER']='x'*501
        with self.assertRaises(ValueError):holding(r)
    def test_changed_source_rejected(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'invalid';p.write_bytes(b'not reviewed')
            with self.assertRaisesRegex(ValueError,'source pin'):build(p,p)
    def test_ambiguous_join(self):
        import sqlite3
        c=sqlite3.connect(':memory:');c.row_factory=sqlite3.Row;c.execute('CREATE TABLE sample (ACCESSION_NUMBER TEXT)')
        with self.assertRaises(ValueError):one(c,'sample','a')
        c.executemany('INSERT INTO sample VALUES (?)',[('a',),('a',)])
        with self.assertRaises(ValueError):one(c,'sample','a')
    def fixture(self,root,mismatch=False):
        import sqlite3,zipfile,csv,io
        from sec_13f_data import SCHEMAS
        sub={'ACCESSION_NUMBER':'0000000123-26-000001','CIK':'0000000123','SUBMISSIONTYPE':'13F-HR','FILING_DATE':'14-AUG-2026','PERIODOFREPORT':'30-JUN-2026'}
        cover={'ACCESSION_NUMBER':sub['ACCESSION_NUMBER'],'REPORTCALENDARORQUARTER':sub['PERIODOFREPORT'],'FILINGMANAGER_NAME':'Test manager','ISAMENDMENT':'N'}
        summary={'ACCESSION_NUMBER':sub['ACCESSION_NUMBER'],'ISCONFIDENTIALOMITTED':'N'}
        h={**self.row(),'ACCESSION_NUMBER':sub['ACCESSION_NUMBER']}
        source={'SUBMISSION.tsv':sub,'COVERPAGE.tsv':cover,'SUMMARYPAGE.tsv':summary,'INFOTABLE.tsv':h}
        database=root/'db';archive=root/'archive.zip';c=sqlite3.connect(database)
        with zipfile.ZipFile(archive,'w') as z:
            for name,fields in SCHEMAS.items():
                table='holdings_'+name[:-4].lower();c.execute('CREATE TABLE '+table+'('+','.join('"'+f+'" TEXT' for f in fields)+')')
                out=io.StringIO();writer=csv.writer(out,delimiter='\t');writer.writerow(fields)
                if name in source:
                    vals=[source[name].get(f,'') for f in fields]
                    c.execute('INSERT INTO '+table+' VALUES('+','.join('?' for f in fields)+')',vals)
                    if mismatch and name=='INFOTABLE.tsv':vals[fields.index('CUSIP')]='DIFFERENT'
                    writer.writerow(vals)
                z.writestr(name,out.getvalue())
            z.writestr('FORM13F_metadata.json','{}');z.writestr('FORM13F_readme.htm','fixture')
        c.commit();c.close();return database,archive
    def test_actual_build_source_rows_and_mismatch(self):
        from unittest.mock import patch
        import manager_holdings_sample as m
        for mismatch in [False,True]:
            with self.subTest(mismatch=mismatch),tempfile.TemporaryDirectory() as t:
                db,z=self.fixture(Path(t),mismatch)
                with patch.object(m,'DB_SHA',m.sha(db)),patch.object(m,'ZIP_SHA',m.sha(z)):
                    if mismatch:
                        with self.assertRaisesRegex(ValueError,'archive row mismatch'):m.build(db,z)
                    else:
                        out=m.build(db,z);self.assertEqual(out['source']['raw_rows_checked'],4)
                        self.assertEqual(out['filings'][0]['displayed_rows'],1)
                        self.assertEqual(out['filings'][0]['source_url_status'],'CONSTRUCTED_FROM_RETAINED_IDENTIFIERS_NOT_FETCHED')
    def test_source_mutation_before_final_pin_check(self):
        from unittest.mock import patch
        import manager_holdings_sample as m
        with tempfile.TemporaryDirectory() as t:
            db,z=self.fixture(Path(t));original=m.rows
            def mutate(archive,name):
                yield from original(archive,name)
                if name=='INFOTABLE.tsv':
                    with db.open('ab') as f:f.write(b'changed')
            with patch.object(m,'DB_SHA',m.sha(db)),patch.object(m,'ZIP_SHA',m.sha(z)),patch.object(m,'rows',mutate):
                with self.assertRaisesRegex(ValueError,'source changed'):m.build(db,z)
