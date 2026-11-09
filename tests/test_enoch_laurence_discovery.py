import json
from pathlib import Path
import unittest

from build_enoch_laurence_discovery import (
    HTML_URL,
    ITEM_URL,
    REVIEW_PATH,
    SOURCE_RECORDS,
    TRANSLATION_ID,
    apply,
)


ROOT = Path(__file__).resolve().parents[1]


class EnochLaurenceDiscoveryTests(unittest.TestCase):
    def test_records_bibliographic_lead_and_rights_conflict_without_bundling_text(self):
        archive = {
            "sources": [],
            "translation_registry": {"translation_leads": []},
            "readers": [],
        }
        apply(archive)
        apply(archive)

        self.assertEqual([source["source_id"] for source in archive["sources"]], ["SRC-444", "SRC-445"])
        sources = {source["source_id"]: source for source in archive["sources"]}
        self.assertEqual(sources["SRC-444"]["url"], ITEM_URL)
        self.assertEqual(sources["SRC-444"]["rights_classification"], "unknown")
        self.assertEqual(sources["SRC-445"]["url"], HTML_URL)
        self.assertEqual(sources["SRC-445"]["rights_classification"], "mixed")
        self.assertIn("reserved", sources["SRC-445"]["rights_status"])
        self.assertIn("U.S.-scoped", sources["SRC-445"]["rights_status"])

        self.assertEqual(len(archive["translation_registry"]["translation_leads"]), 1)
        lead = archive["translation_registry"]["translation_leads"][0]
        self.assertEqual(lead["translation_id"], TRANSLATION_ID)
        self.assertEqual(lead["canon_id"], "eotc-ot-14")
        self.assertEqual(lead["mapping_state"], "reviewed_match")
        self.assertEqual(lead["translation_path"], ["gez", "en"])
        self.assertFalse(lead["text_bundled"])
        self.assertEqual(archive["readers"], [])

    def test_local_review_page_states_source_scope_and_does_not_embed_text(self):
        apply({"sources": [], "translation_registry": {"translation_leads": []}})
        page = (ROOT / REVIEW_PATH).read_text(encoding="utf-8")
        self.assertIn(ITEM_URL, page)
        self.assertIn(HTML_URL, page)
        self.assertIn("does not contain a reader or a transcription", page)
        self.assertIn("No text is bundled", page)
        self.assertIn("exact manuscript shelfmark", page)
        self.assertEqual(len(SOURCE_RECORDS), 2)


if __name__ == "__main__":
    unittest.main()
