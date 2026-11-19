import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from research_dossiers import REVIEW, build
from research_readiness import _read_pin, sha

ROOT = Path(__file__).resolve().parents[1]


class DossierTests(unittest.TestCase):
    def test_both_archives_replay_exactly_without_changing_rankings(self):
        results = build(ROOT)
        self.assertEqual(results, build(ROOT))
        self.assertEqual(len(results), 2)
        for path, raw in results.items():
            self.assertEqual(Path(path).stem, sha(raw))
            self.assertEqual((ROOT / path).read_bytes(), raw)
            dossier = json.loads(raw)
            pin = dossier['snapshot']
            snap = _read_pin(ROOT, pin['path'], pin['bytes'], pin['sha256'])
            self.assertEqual([r['thesis_id'] for r in dossier['notes']], [r['id'] for r in snap['ideas']])
            self.assertIn(len(dossier['notes']), (5, 7))
            self.assertTrue(all(len(note['sources']) > 0 for note in dossier['notes']))
        self.assertEqual(len(REVIEW), 7)

    def test_source_pin_rejects_changed_bytes(self):
        with tempfile.TemporaryDirectory() as base:
            path = Path(base) / 'public.json'
            path.write_bytes(b'{"bad":2}')
            original = b'{"bad":1}'
            with self.assertRaises(ValueError):
                _read_pin(Path(base), 'public.json', len(original), sha(original))

    def test_source_object_mismatch_prevents_build(self):
        with patch('research_dossiers.digest', return_value='0' * 64):
            with self.assertRaisesRegex(ValueError, 'does not match rank provenance'):
                build(ROOT)

    def test_missing_review_fails_rather_than_using_generic_text(self):
        notes = dict(REVIEW)
        notes.pop(next(iter(notes)))
        with patch('research_dossiers.REVIEW', notes):
            with self.assertRaises(KeyError):
                build(ROOT)
