import csv,io,sqlite3,tempfile,unittest,zipfile
from pathlib import Path
from unittest.mock import patch
import manager_reported_difference as m
import test_manager_holdings_sample as fixtures
from sec_13f_data import SCHEMAS
class DifferenceTests(unittest.TestCase):
    def test_literal_keys_not_names_or_values(self):
        a=fixtures.ManagerSampleTests().row();b=dict(a,NAMEOFISSUER='Changed label',VALUE='1')
        x=m.compare([a],[b]);self.assertEqual(x['common_literal_keys'],1);self.assertFalse(x['economic_changes_qualified'])
        for key in m.KEY:
            b=dict(a);b[key]='DIFFERENT';x=m.compare([a],[b]);self.assertEqual(len(x['earlier_only']),1);self.assertEqual(len(x['later_only']),1)
            self.assertNotIn('VALUE',x['earlier_only'][0]['source_rows'][0])
    def test_duplicates_preserved_not_aggregated(self):
        a=fixtures.ManagerSampleTests().row();x=m.compare([a,dict(a,rowid=8)],[])
        self.assertEqual(x['repeated_key_groups_earlier'],1);self.assertEqual(len(x['earlier_only'][0]['source_rows']),2)
    def fixture(self,root,amended=False,mismatch=False):
        db,z=fixtures.ManagerSampleTests().fixture(root);c=sqlite3.connect(db)
        for name in ['submission','coverpage','summarypage','infotable']:
            table='holdings_'+name;c.execute('INSERT INTO '+table+' SELECT * FROM '+table+' WHERE rowid=1');c.execute('UPDATE '+table+' SET ACCESSION_NUMBER=? WHERE rowid=2',('0000000123-26-000002',))
        c.execute("UPDATE holdings_submission SET PERIODOFREPORT='31-MAR-2026' WHERE rowid=1")
        c.execute("UPDATE holdings_coverpage SET REPORTCALENDARORQUARTER='31-MAR-2026' WHERE rowid=1")
        c.execute("UPDATE holdings_coverpage SET REPORTTYPE='13F HOLDINGS REPORT'")
        c.execute("UPDATE holdings_summarypage SET TABLEENTRYTOTAL='1'")
        if amended:c.execute("UPDATE holdings_coverpage SET ISAMENDMENT='Y' WHERE rowid=1")
        c.commit()
        with zipfile.ZipFile(z,'w') as out:
            for name,fields in SCHEMAS.items():
                buf=io.StringIO();w=csv.writer(buf,delimiter='\t');w.writerow(fields)
                rs=c.execute('SELECT * FROM holdings_'+name[:-4].lower()).fetchall()
                for i,r in enumerate(rs):
                    r=list(r)
                    if mismatch and name=='INFOTABLE.tsv' and i==1:r[fields.index('CUSIP')]='wrong'
                    w.writerow(r)
                out.writestr(name,buf.getvalue())
            out.writestr('FORM13F_metadata.json','{}');out.writestr('FORM13F_readme.htm','fixture')
        c.close();return db,z
    def test_build_original_match_and_failures(self):
        for amended,mismatch in [(False,False),(True,False),(False,True)]:
            with self.subTest(amended=amended,mismatch=mismatch),tempfile.TemporaryDirectory() as t:
                db,z=self.fixture(Path(t),amended,mismatch)
                with patch.object(m,'DB_SHA',m.sha(db)),patch.object(m,'ZIP_SHA',m.sha(z)):
                    if amended or mismatch:
                        with self.assertRaises(ValueError):m.build(db,z)
                    else:
                        x=m.build(db,z);self.assertEqual(x['source']['rows_checked'],8);self.assertEqual(x['comparison']['common_literal_keys'],1)
    def test_wrong_pin(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'bad';p.write_bytes(b'bad')
            with self.assertRaisesRegex(ValueError,'source pin'):m.build(p,p)
    def test_period_ambiguity_confidentiality_and_count_rejected(self):
        statements=["INSERT INTO holdings_submission SELECT * FROM holdings_submission WHERE rowid=1", "UPDATE holdings_summarypage SET ISCONFIDENTIALOMITTED='Y'", "UPDATE holdings_summarypage SET TABLEENTRYTOTAL='999'", "UPDATE holdings_coverpage SET CONFDENIEDEXPIRED='Y'"]
        for sql in statements:
            with self.subTest(sql=sql),tempfile.TemporaryDirectory() as t:
                db,z=self.fixture(Path(t));c=sqlite3.connect(db);c.execute(sql);c.commit();c.close()
                with patch.object(m,'DB_SHA',m.sha(db)),patch.object(m,'ZIP_SHA',m.sha(z)):
                    with self.assertRaises(ValueError):m.build(db,z)
