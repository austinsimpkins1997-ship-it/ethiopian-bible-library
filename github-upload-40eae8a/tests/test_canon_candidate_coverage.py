import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class CanonCandidateCoverageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.archive = json.loads((ROOT / "archive.json").read_text(encoding="utf-8"))
        cls.app = (ROOT / "app.js").read_text(encoding="utf-8")
        cls.books = cls.archive["canon_registry"]["books"]
        cls.readers = cls.archive["readers"]
        cls.translation_registry = cls.archive["translation_registry"]

    def test_candidate_records_do_not_inflate_bundled_reader_count(self):
        reader_canon_ids = {reader.get("canon_id") for reader in self.readers if reader.get("canon_id")}
        candidate_canon_ids = {
            record.get("candidate_canon_id")
            for group in ("translation_leads", "edition_leads", "corpus_leads", "research_corpora")
            for record in self.translation_registry.get(group, [])
            if record.get("candidate_canon_id")
        }
        bundled = [book for book in self.books if book["canon_id"] in reader_canon_ids]
        unbundled = [book for book in self.books if book["canon_id"] not in reader_canon_ids]
        candidates = [book for book in unbundled if book["canon_id"] in candidate_canon_ids]

        self.assertEqual((len(bundled), len(unbundled), len(candidates), len(unbundled) - len(candidates)), (11, 70, 24, 46))
        self.assertIn("const candidateEntryCount = state.canonBooks.filter(book => !readerForCanon(book)", self.app)
        self.assertIn("candidate records are research or bibliographic leads", self.app.lower())
        self.assertIn("No candidate recorded here does not mean no source exists elsewhere.", self.app)


if __name__ == "__main__":
    unittest.main()
