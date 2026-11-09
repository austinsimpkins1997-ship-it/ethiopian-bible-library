import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class DanielDiscoveryTests(unittest.TestCase):
    def test_source_lead_is_metadata_only_pending_rights_clarification(self):
        archive = json.loads((ROOT / "archive.json").read_text(encoding="utf-8"))
        registry = json.loads((ROOT / "translation-registry.json").read_text(encoding="utf-8"))
        canon = json.loads((ROOT / "canon-registry.json").read_text(encoding="utf-8"))
        source = next(x for x in archive["sources"] if x["source_id"] == "SRC-282")
        lead = next(x for x in registry["edition_leads"] if x["edition_id"] == "betamasaheft-daniel-tei-2026")
        catalogue = next(x for x in archive["catalogue"] if x["catalogue_id"] == "eotc-040")
        book = next(x for x in canon["books"] if x["canon_id"] == "eotc-ot-32")
        withheld = next(x for x in archive["rights_withheld_texts"] if x["reader_id"] == "daniel-betamasaheft-tei")

        self.assertFalse(lead["text_bundled"])
        self.assertNotIn("bundled_reader_id", lead)
        self.assertEqual((lead["candidate_canon_id"], lead["mapping_state"]), ("eotc-ot-32", "uncertain"))
        self.assertEqual(lead["rights_classification"], "mixed")
        self.assertFalse(withheld["public_text_included"])
        self.assertEqual((withheld["chapter_count"], withheld["unit_count"]), (14, 437))
        self.assertIn("14 ordered chapter divisions", lead["scope_description"])
        self.assertIn("chapter 14 line labels run 0", lead["scope_description"])
        self.assertIn("437 labeled line elements", source["inspection_and_limitations"])
        self.assertIn("Susanna, Bel and the Dragon", lead["scope_description"])
        self.assertIn("withheld", catalogue["text_availability_status"].lower())
        self.assertIsNone(book["reader_id"])
        self.assertEqual(canon["reader_count"], 19)
        self.assertFalse(any(x.get("reader_id") == "daniel-betamasaheft-tei" for x in archive["readers"]))
        self.assertFalse((ROOT / "readers/daniel-betamasaheft-tei.json").exists())
        self.assertFalse((ROOT / "readers/source/daniel/LIT3529Daniel-original.xml").exists())


if __name__ == "__main__":
    unittest.main()
