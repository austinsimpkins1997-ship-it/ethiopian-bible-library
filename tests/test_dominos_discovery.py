import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class DominosDiscoveryTests(unittest.TestCase):
    def test_two_work_candidates_are_distinct_and_unbundled(self):
        archive = json.loads((ROOT / "archive.json").read_text(encoding="utf-8"))
        registry = json.loads((ROOT / "translation-registry.json").read_text(encoding="utf-8"))
        leads = {item["edition_id"]: item for item in registry["edition_leads"]}
        first = leads["betamasaheft-testamentum-domini-cae2461"]
        second = leads["betamasaheft-testamentum-domini-galilea-cae2462"]
        books = {item["canon_id"]: item for item in archive["canon_registry"]["books"]}
        self.assertEqual((first["candidate_canon_id"], first["mapping_state"]), ("eotc-nt-32", "uncertain"))
        self.assertEqual((second["candidate_canon_id"], second["mapping_state"]), ("eotc-nt-33", "uncertain"))
        self.assertFalse(first["text_bundled"])
        self.assertFalse(second["text_bundled"])
        self.assertEqual(first["language_tag"], second["language_tag"])
        self.assertIsNone(books["eotc-nt-32"].get("reader_id"))
        self.assertIsNone(books["eotc-nt-33"].get("reader_id"))
        self.assertIn("Epistula Apostolorum", second["scope_description"])
        self.assertEqual(archive["canon_registry"]["reader_count"], 19)
        self.assertTrue((ROOT / "research/dominos-source-review.md").is_file())


if __name__ == "__main__":
    unittest.main()
