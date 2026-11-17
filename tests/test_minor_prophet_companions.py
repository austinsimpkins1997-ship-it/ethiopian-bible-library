import copy
import importlib
import json
import unittest

from build_brenton_research_readers import build_records
from build_minor_prophet_companions import PAIRS, ROOT, prepare_pair


class MinorProphetCompanionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.english = {r['reader_id']: r for r in build_records()[0]}

    def inputs(self, code='OBA'):
        _, slug, reader_id, _ = next(row for row in PAIRS if row[0] == code)
        source, _ = importlib.import_module(f'build_{slug}_reader').build()
        stored = json.loads((ROOT / 'readers' / f'{reader_id}.json').read_text(encoding='utf-8'))
        return source, self.english[f'brenton-lxx-{code.lower()}-research'], stored['parallel_translation']

    def test_all_source_units_and_english_structure_are_preserved_without_shared_rights(self):
        for code, _, reader_id, count in PAIRS:
            with self.subTest(book=code):
                source, english, companion = self.inputs(code)
                before = copy.deepcopy(source)
                result = prepare_pair(source, english, companion, code=code)
                self.assertEqual(source, before, 'preflight must not mutate its input')
                self.assertEqual(result['chapters'], source['chapters'])
                self.assertEqual(result['parallel_translation']['chapters'], english['chapters'])
                self.assertEqual(result['copyright_notice'], source['copyright_notice'])
                self.assertEqual(result['rights_classification'], 'permission_limited')
                self.assertEqual(result['parallel_translation']['rights_classification'], 'public_domain_claimed')
                self.assertIn('unverified', result['parallel_translation']['translation_basis'])
                self.assertEqual(result['chapter_count'], count)

    def test_different_label_totals_are_not_silently_padded_or_truncated(self):
        for code, expected in [('NAM', (48, 47)), ('ZEP', (52, 53)), ('HAG', (37, 38))]:
            source, english, companion = self.inputs(code)
            result = prepare_pair(source, english, companion, code=code)
            self.assertEqual((result['unit_count'], result['parallel_translation']['unit_count']), expected)

    def test_stale_wording_fails_even_when_counts_agree(self):
        source, english, companion = self.inputs()
        bad = copy.deepcopy(companion)
        bad['chapters'][0]['verses'][0]['text'] += ' UNVERIFIED ADDITION'
        with self.assertRaisesRegex(ValueError, 'freshly parsed'):
            prepare_pair(source, english, bad, code='OBA')

    def test_unknown_rights_hold_copying(self):
        source, english, companion = self.inputs()
        bad = copy.deepcopy(english)
        bad['rights_classification'] = 'unknown'
        with self.assertRaisesRegex(ValueError, 'rights'):
            prepare_pair(source, bad, companion, code='OBA')

    def test_wrong_identity_or_chapter_sequence_is_not_admitted(self):
        source, english, companion = self.inputs()
        wrong = copy.deepcopy(source)
        wrong['reader_id'] = 'another-witness'
        with self.assertRaisesRegex(ValueError, 'identity'):
            prepare_pair(wrong, english, companion, code='OBA')
        wrong = copy.deepcopy(companion)
        wrong['chapters'][0]['chapter'] = 2
        with self.assertRaisesRegex(ValueError, 'Chapter sequence'):
            prepare_pair(source, english, wrong, code='OBA')

    def test_unreviewed_candidates_are_held(self):
        with self.assertRaisesRegex(ValueError, 'outside'):
            prepare_pair({}, {}, {}, code='MAL')


if __name__ == '__main__':
    unittest.main()
