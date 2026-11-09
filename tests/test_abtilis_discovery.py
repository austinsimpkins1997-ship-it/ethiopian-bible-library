import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class AbtilisDiscoveryTests(unittest.TestCase):
    def test_abtilis_lead_preserves_recensions_and_rights_uncertainty(self):
        archive = json.loads((ROOT / "archive.json").read_text(encoding="utf-8"))
        registry = json.loads((ROOT / "translation-registry.json").read_text(encoding="utf-8"))
        source = next(item for item in archive["sources"] if item["source_id"] == "SRC-285")
        lead = next(
            item for item in registry["edition_leads"]
            if item["edition_id"] == "betamasaheft-abtelisat-81-ca2677"
        )
        book = next(item for item in archive["canon_registry"]["books"] if item["canon_id"] == "eotc-nt-31")
        catalogue = next(item for item in archive["catalogue"] if item["catalogue_id"] == "eotc-085")
        self.assertIn("80-canon", source["inspection_and_limitations"])
        self.assertIn("CC BY-NC-SA 4.0", source["inspection_and_limitations"])
        self.assertEqual((lead["candidate_canon_id"], lead["mapping_state"]), ("eotc-nt-31", "uncertain"))
        self.assertFalse(lead["text_bundled"])
        self.assertEqual(lead["rights_classification"], "unknown")
        self.assertIn("Apostolic canons (56)", catalogue["alternate_names_or_notes"])
        self.assertIsNone(book.get("reader_id"))
        self.assertEqual(archive["canon_registry"]["reader_count"], 19)


if __name__ == "__main__":
    unittest.main()
