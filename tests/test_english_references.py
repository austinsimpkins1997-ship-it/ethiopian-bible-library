import json
import unittest
from pathlib import Path
from build_english_reference_index import build, work_code

ROOT = Path(__file__).resolve().parents[1]

class EnglishReferenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.archive = json.loads((ROOT / 'archive.json').read_text(encoding='utf-8'))
        cls.index = build(cls.archive)

    def test_every_current_reader_has_english_or_a_sourced_reference(self):
        readers = self.archive['readers']
        self.assertEqual(set(self.index['readers']), {r['reader_id'] for r in readers})
        by_id = {r['reader_id']:r for r in readers}
        for reader in readers:
            item = self.index['readers'][reader['reader_id']]
            if reader['language_tag'] == 'en':
                self.assertEqual(item['state'], 'already_english')
            else:
                self.assertEqual(item['state'], 'english_reference', reader['reader_id'])
                english = by_id[item['english_reader_id']]
                self.assertEqual(english['language_tag'], 'en')
                self.assertTrue(english['chapters'])
                self.assertEqual(work_code(english)[0], item['work_code'])
                self.assertTrue(set(english['source_ids']).issubset(item['source_ids']))
        self.assertEqual(self.index['counts']['unavailable'], 0)

    def test_index_is_reproducible_and_keeps_canon_outside_mapping(self):
        self.assertEqual(self.index, json.loads((ROOT / 'english-reference-index.json').read_text(encoding='utf-8')))
        for item in self.index['readers'].values():
            self.assertNotIn('canon_id', item)
            self.assertIn('not a translation', item['relationship'])
            self.assertNotIn('chapters', item)

    def test_unknown_and_ambiguous_codes_do_not_guess_from_titles(self):
        code, basis = work_code({'reader_id':'new-book', 'title':'Genesis', 'source_pages':'unknown'})
        self.assertIsNone(code)
        self.assertEqual(basis, 'unresolved_book_code')
        self.assertIsNone(work_code({'reader_id':'two-books','source_pages':'01-GENtest.usfm; 02-EXOtest.usfm'})[0])

    def test_export_schema_accepts_existing_mapping_vocabulary_without_relabeling(self):
        schema = json.loads((ROOT / 'schemas/reader-package.schema.json').read_text(encoding='utf-8'))
        accepted = set(schema['properties']['canon_mapping']['properties']['state']['enum'])
        actual = {r.get('canon_mapping_state', 'unknown')
                  for r in self.archive['translation_registry']['research_corpora']}
        self.assertTrue(actual.issubset(accepted), actual - accepted)
        self.assertIn('reviewed_match', accepted)

if __name__ == '__main__':unittest.main()
