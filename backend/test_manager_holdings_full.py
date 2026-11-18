import hashlib,json,sqlite3,tempfile,unittest,zipfile
from pathlib import Path
from unittest.mock import patch
import manager_holdings_sample as m
from manager_holdings_full import project,write_bundle
import test_manager_holdings_sample as fixtures

class FullRowsTests(unittest.TestCase):
    def fixture(self,root,count=12,mismatch=False):
        db,z=fixtures.ManagerSampleTests().fixture(root)
        c=sqlite3.connect(db)
        for i in range(2,count+1):
            c.execute('INSERT INTO holdings_infotable SELECT * FROM holdings_infotable WHERE rowid=1')
            c.execute('UPDATE holdings_infotable SET INFOTABLE_SK=? WHERE rowid=?',(str(i+12),i))
        c.commit();c.close()
        with zipfile.ZipFile(z) as old:parts={n:old.read(n) for n in old.namelist()}
        header,row=parts['INFOTABLE.tsv'].decode().splitlines();values=row.split('\t');fields=header.split('\t');lines=[header,row]
        for i in range(2,count+1):
            v=values[:];v[fields.index('INFOTABLE_SK')]=str(i+12)
            if mismatch and i==count:v[fields.index('CUSIP')]='MISMATCH'
            lines.append('\t'.join(v))
        parts['INFOTABLE.tsv']=('\n'.join(lines)+'\n').encode()
        with zipfile.ZipFile(z,'w') as out:
            for name,b in parts.items():out.writestr(name,b)
        return db,z
    def test_all_rows_and_original_sample_unchanged(self):
        with tempfile.TemporaryDirectory() as t:
            db,z=self.fixture(Path(t))
            with patch.object(m,'DB_SHA',m.sha(db)),patch.object(m,'ZIP_SHA',m.sha(z)):
                sample=m.build(db,z);full=m.build(db,z,all_selected_rows=True)
            self.assertEqual(sample['filings'][0]['displayed_rows'],10)
            self.assertEqual(full['filings'][0]['displayed_rows'],12)
            self.assertEqual(full['filings'][0]['holdings'][:10],sample['filings'][0]['holdings'])
            self.assertEqual(full['source']['raw_rows_checked'],15)
            bundle=project(full);manifest=json.loads(bundle['manifest.json']);entry=manifest['filings'][0]
            self.assertEqual(entry['sha256'],hashlib.sha256(bundle[entry['path']]).hexdigest())
            self.assertEqual(entry['bytes'],len(bundle[entry['path']]))
            self.assertNotIn('VALUE',json.loads(bundle[entry['path']])['filing']['holdings'][0])
            write_bundle(bundle,Path(t)/'out')
            with self.assertRaises(FileExistsError):write_bundle(bundle,Path(t)/'out')
            with self.assertRaises(ValueError):project(sample)
            full['filings'][0]['omitted_from_sample_rows']=1
            with self.assertRaises(ValueError):project(full)
    def test_mismatch_beyond_old_sample_rejected(self):
        with tempfile.TemporaryDirectory() as t:
            db,z=self.fixture(Path(t),mismatch=True)
            with patch.object(m,'DB_SHA',m.sha(db)),patch.object(m,'ZIP_SHA',m.sha(z)):
                with self.assertRaisesRegex(ValueError,'archive row mismatch'):m.build(db,z,all_selected_rows=True)
    def test_full_bound_rejects_not_truncates(self):
        with tempfile.TemporaryDirectory() as t:
            db,z=self.fixture(Path(t),count=1001)
            with patch.object(m,'DB_SHA',m.sha(db)),patch.object(m,'ZIP_SHA',m.sha(z)):
                with self.assertRaisesRegex(ValueError,'row bound'):m.build(db,z,all_selected_rows=True)
