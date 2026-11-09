"""Publisher-reported English editions stay discoverable without inflating coverage."""

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class EotcEnglishEditionLeadTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.archive = json.loads((ROOT / "archive.json").read_text(encoding="utf-8"))
        cls.registry = json.loads((ROOT / "translation-registry.json").read_text(encoding="utf-8"))
        cls.coverage = json.loads((ROOT / "book-coverage.json").read_text(encoding="utf-8"))
        cls.sources = {item["source_id"]: item for item in cls.archive["sources"]}
        cls.leads = {
            item["translation_id"]: item for item in cls.registry["translation_leads"]
        }

    def test_publisher_report_has_a_separate_rights_scoped_source_record(self):
        source = self.sources["SRC-448"]
        self.assertIn("2025/11/05/", source["url"])
        self.assertEqual(source["rights_classification"], "all_rights_reserved")
        self.assertIn("All Rights Reserved", source["rights_status"])
        self.assertEqual(source["local_review_url"], "research/eotc-english-edition-leads.html")

    def test_three_sinodos_components_are_source_assertions_not_reader_text(self):
        expected = {
            "sirate-tsion-en-mikhail-sinodos-2025": ("eotc-nt-28", "Sirate Tsion"),
            "tizaz-en-mikhail-sinodos-2025": ("eotc-nt-29", "Tizaz"),
            "abtilis-en-mikhail-sinodos-2025": ("eotc-nt-31", "Abtilis"),
        }
        for identifier, (canon_id, title_fragment) in expected.items():
            with self.subTest(translation_id=identifier):
                lead = self.leads[identifier]
                self.assertEqual(lead["canon_id"], canon_id)
                self.assertEqual(lead["mapping_state"], "asserted_by_source")
                self.assertIn(title_fragment, lead["title"])
                self.assertIn("SRC-448", lead["source_ids"])
                self.assertFalse(lead["text_bundled"])
                self.assertIsNone(lead["translation_path"])
                self.assertEqual(lead["rights_classification"], "unknown")
                self.assertIn("Horner", lead["scope_description"])
                self.assertIn("independently checked", lead["scope_description"])

    def test_clement_record_is_partial_mixed_basis_and_uncertain(self):
        lead = self.leads["ethiopic-clement-6-83-86-en-mikhail-2025-lead"]
        self.assertEqual(lead["canon_id"], "eotc-nt-34")
        self.assertEqual(lead["mapping_state"], "uncertain")
        self.assertIn("6:83", lead["scope_description"])
        self.assertIn("French", lead["scope_description"])
        self.assertFalse(lead["text_bundled"])
        self.assertIsNone(lead["translation_path"])
        self.assertEqual(lead["rights_classification"], "unknown")

    def test_metadata_leads_do_not_increase_bundled_book_coverage(self):
        by_id = {entry["canon_id"]: entry for entry in self.coverage["entries"]}
        for canon_id in ("eotc-nt-28", "eotc-nt-29", "eotc-nt-31", "eotc-nt-34"):
            entry = by_id[canon_id]
            self.assertEqual(entry["reader_availability"], "no_bundled_reader")
            self.assertEqual(entry["canon_linked_readers"], [])
            self.assertTrue(any(lead["source_ids"] and "SRC-448" in lead["source_ids"]
                                for lead in entry["unbundled_leads"]))
        self.assertEqual(self.coverage["availability_counts"]["no_bundled_reader"], 13)


if __name__ == "__main__":
    unittest.main()
