import json,unittest
from pathlib import Path
from company_note_projection import project
class ProjectionTests(unittest.TestCase):
    def test_reviewed_public_boundary(self):
        p=Path(__file__).resolve().parents[1]/'web/company-findings/emerson-note-offering.json'
        d=json.loads(p.read_bytes());self.assertEqual(d['issuer']['cik'],'0000032604')
        self.assertEqual(len(d['coverage']['abstentions']),9);self.assertTrue(d['coverage']['absence_is_not_no_financing'])
        self.assertIsNone(d['facts']['net_proceeds']);self.assertIsNone(d['facts']['first_public_utc'])
        self.assertFalse(d['execution_ready']);self.assertEqual(d['qualified_outcomes'],0)
        self.assertEqual(d['facts']['principal_unscaled'],'750000000')
        self.assertEqual(d['facts']['coupon_percent_as_reported'],'4.000')
    def test_unreviewed_input_rejected(self):
        for a in [{},{'rows':[]},{'private':'unexpected'}]:
            with self.assertRaisesRegex(ValueError,'reviewed audit changed'):project(a)
    def test_invalid_cli_does_not_create_output(self):
        import tempfile,subprocess,sys
        with tempfile.TemporaryDirectory() as t:
            source=Path(t)/'invalid.zip';source.write_bytes(b'invalid')
            output=Path(t)/'result.json'
            process=subprocess.run([sys.executable,str(Path(__file__).with_name('company_note_projection.py')),str(source),str(output)],capture_output=True)
            self.assertNotEqual(process.returncode,0);self.assertFalse(output.exists())
