import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class SirateTsionDiscoveryTests(unittest.TestCase):
    def test_candidate_keeps_29_vs_30_discrepancy_and_uncertainty(self):
        archive = json.loads((ROOT / "archive.json").read_text(encoding="utf-8"))
        registry = json.loads((ROOT / "translation-registry.json").read_text(encoding="utf-8"))
        source = next(item for item in archive["sources"] if item["source_id"] == "SRC-289")
        church_source = next(item for item in archive["sources"] if item["source_id"] == "SRC-442")
        lead = next(
            item for item in registry["edition_leads"]
            if item["edition_id"] == "betamasaheft-canons-after-ascension-cae2673"
        )
        book = next(item for item in archive["canon_registry"]["books"] if item["canon_id"] == "eotc-nt-28")
        self.assertIn("29", source["inspection_and_limitations"])
        self.assertIn("30", source["inspection_and_limitations"])
        self.assertIn("Sirate Tsion", church_source["inspection_and_limitations"])
        self.assertIn("not a manuscript witness", church_source["inspection_and_limitations"])
        catalogue = next(item for item in archive["catalogue"] if item["catalogue_id"] == "eotc-082")
        self.assertIn("SRC-442", catalogue["evidence_source_ids"])
        self.assertEqual((lead["candidate_canon_id"], lead["mapping_state"]), ("eotc-nt-28", "uncertain"))
        self.assertFalse(lead["text_bundled"])
        self.assertEqual(lead["rights_classification"], "unknown")
        self.assertIsNone(book.get("reader_id"))
        self.assertIn("29-versus-30", lead["review_status"])
        self.assertEqual(archive["canon_registry"]["reader_count"], 19)
        self.assertTrue((ROOT / "research/sirate-tsion-source-review.md").is_file())


if __name__ == "__main__":
    unittest.main()
