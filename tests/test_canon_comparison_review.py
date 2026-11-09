import json
from pathlib import Path
import unittest

from build_canon_comparison_review import REVIEW_PATH, SOURCES, apply


ROOT = Path(__file__).resolve().parents[1]


class CanonComparisonReviewTests(unittest.TestCase):
    def test_canon_comparison_is_source_scoped_and_does_not_change_reader_coverage(self):
        archive = {"sources": [], "readers": [{"reader_id": "existing-reader"}]}
        apply(archive)
        apply(archive)
        self.assertEqual([item["source_id"] for item in archive["sources"]], ["SRC-446", "SRC-447"])
        self.assertEqual(len(archive["readers"]), 1)
        self.assertTrue(all(item["local_review_url"] == REVIEW_PATH for item in archive["sources"]))
        self.assertEqual([item["rights_classification"] for item in SOURCES], ["unknown", "unknown"])

    def test_review_keeps_count_claims_and_theological_verdict_separate(self):
        apply({"sources": []})
        page = (ROOT / REVIEW_PATH).read_text(encoding="utf-8")
        self.assertIn("81 canonized books: 46 Old Testament and 35 New Testament", page)
        self.assertIn("differs in both Testaments", page)
        self.assertIn("not a census of every Protestant body", page)
        self.assertIn("does not claim that the traditions cannot contradict", page)
        self.assertIn("Avoid saying “nothing is removed, rewritten, or replaced,”", page)
        self.assertIn("promotional copy supplied for review is not treated as evidence", page)
        self.assertIn("SRC-029", page)
        self.assertIn("SRC-446", page)
        self.assertIn("SRC-447", page)
        self.assertNotIn("Nothing is removed, rewritten, or replaced", page)


if __name__ == "__main__":
    unittest.main()
