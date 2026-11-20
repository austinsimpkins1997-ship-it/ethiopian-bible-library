"""Coverage, provenance and independent temporal axes for The Book."""
import ast
import hashlib
import json
from pathlib import Path
import unittest

from build_the_book import build, integrate_html, STANDINGS, REVIEW_STEPS

ROOT = Path(__file__).resolve().parents[1]


class TheBookTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.archive = json.loads((ROOT / 'archive.json').read_text(encoding='utf-8'))
        cls.model = json.loads((ROOT / 'the-book.json').read_text(encoding='utf-8'))
        cls.packages = {r['reader_id']: r['package_path'] for r in cls.model['readers']}

    def test_every_bundled_reader_has_exactly_one_working_entry(self):
        expected = {r['reader_id'] for r in self.archive['readers']}
        self.assertEqual(set(self.packages), expected)
        self.assertEqual(len(self.model['readers']), len(expected))
        self.assertEqual(self.model['reader_count'], len(expected))
        for row in self.model['readers']:
            reader = json.loads((ROOT / row['package_path']).read_text(encoding='utf-8'))
            self.assertEqual(reader['reader_id'], row['reader_id'])
            self.assertEqual(reader.get('source_ids', []), row['source_ids'])
            self.assertEqual(reader.get('canon_id'), row['canon_id'])

    def test_unavailable_canon_entries_are_not_filled_with_fabricated_text(self):
        self.assertEqual(self.model['canon_entries'], self.archive['canon_registry']['books'])
        self.assertEqual(len(self.model['catalogue_entries']), len(self.archive['catalogue']))
        self.assertTrue(any(not row.get('reader_id') for row in self.model['canon_entries']))
        self.assertNotIn('chapters', self.model)

    def test_source_is_hash_pinned_and_coverage_gaps_are_named(self):
        source = self.model['source']
        self.assertEqual(source['sha256'], hashlib.sha256((ROOT / source['path']).read_bytes()).hexdigest())
        self.assertIn('Excerpts only', source['coverage'])
        self.assertIn('not scripture', source['role'])

    def test_rebuild_is_deterministic_and_does_not_mutate_archive(self):
        before = json.dumps(self.archive, ensure_ascii=False)
        self.assertEqual(build(self.archive, self.packages), self.model)
        self.assertEqual(json.dumps(self.archive, ensure_ascii=False), before)
        with self.assertRaisesRegex(ValueError, 'no package'):
            build(self.archive, {})

    def test_review_and_standing_catalogs_match_each_owning_axis(self):
        self.assertEqual(tuple(self.model['standings']), STANDINGS)
        self.assertEqual(tuple(self.model['review_steps']), REVIEW_STEPS)
        self.assertNotIn('TO_BE', STANDINGS)
        self.assertNotIn('BEING', STANDINGS)
        source = ROOT.parent.parent / 'ChronoRealm Whole 4/engines/temporal/chronotense.py'
        if source.exists():
            assignments = {}
            for item in ast.parse(source.read_text(encoding='utf-8')).body:
                if isinstance(item, ast.Assign) and isinstance(item.targets[0], ast.Name):
                    name = item.targets[0].id
                    if name in ('STANDINGS', 'REVIEW_CYCLE'):
                        assignments[name] = assignments[item.value.id] if isinstance(item.value, ast.Name) else ast.literal_eval(item.value)
            self.assertEqual(STANDINGS, assignments['STANDINGS'])
            self.assertEqual(REVIEW_STEPS, assignments['REVIEW_CYCLE'])

    def test_optional_html_is_idempotent_and_reader_stays_first(self):
        html = (ROOT / 'index.html').read_text(encoding='utf-8')
        self.assertEqual(integrate_html(html), html)
        self.assertEqual(html.count('id="the-book"'), 1)
        self.assertLess(html.index('id="reader"'), html.index('id="the-book"'))
        self.assertIn('id="the-book-disclosure"', html)
        self.assertNotIn('id="the-book-disclosure" open', html)
        self.assertIn('the-book.js', (ROOT / 'sw.js').read_text(encoding='utf-8'))

    def test_all_four_paths_and_ten_conceptual_groups_are_available(self):
        self.assertEqual([row['id'] for row in self.model['scope_paths']], list('ABCD'))
        self.assertEqual(len(self.model['principles']), 10)
        self.assertEqual(len(self.model['completion_checks']), 7)
        for source in self.model['canon_sources']:
            self.assertTrue(source['url'].startswith('https://'))
            self.assertTrue(source['limit'])


if __name__ == '__main__':
    unittest.main()
