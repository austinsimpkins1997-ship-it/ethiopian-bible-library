"""Ezra/Sutu'el manuscript metadata must stay scoped and rights-aware."""
from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class EzraSutuelDiscoveryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.archive = json.loads((ROOT / "archive.json").read_text(encoding="utf-8"))
        cls.canon = json.loads((ROOT / "canon-registry.json").read_text(encoding="utf-8"))
        cls.translation = json.loads((ROOT / "translation-registry.json").read_text(encoding="utf-8"))

    def test_primary_item_scope_and_access_condition_are_recorded_without_reuse_claim(self):
        source = next(item for item in self.archive["sources"] if item["source_id"] == "SRC-347")
        self.assertEqual(source["url"], "https://eap.bl.uk/archive-file/EAP286-1-1-499")
        self.assertIn("126 TIFF", source["inspection_and_limitations"])
        self.assertIn("research purposes only", source["inspection_and_limitations"])
        self.assertIn("not a copyright license", source["inspection_and_limitations"])
        self.assertIn("No manuscript text or images are copied", source["inspection_and_limitations"])

        lead = next(item for item in self.translation["edition_leads"] if item["edition_id"] == "bl-eap286-1-1-499-ezra-sutuel")
        self.assertIn("SRC-347", lead["source_ids"])
        self.assertFalse(lead["text_bundled"])
        self.assertEqual(lead["rights_classification"], "unknown")
        self.assertIn("research purposes only", lead["rights_status"])
        self.assertIn("remain unreviewed", lead["review_status"])

    def test_grouped_church_entry_and_both_title_rows_remain_unresolved(self):
        book = next(item for item in self.canon["books"] if item["canon_id"] == "eotc-ot-16")
        self.assertEqual(book["display_name"], "Ezra (2nd) and Ezra Sutuel")
        self.assertEqual(set(book["catalogue_ids"]), {"eotc-019", "eotc-090"})
        self.assertIsNone(book["reader_id"])
        self.assertEqual(len(self.canon["books"]), 81)
        self.assertIn("SRC-347", book["source_ids"])
        self.assertIn("remain unresolved", book["mapping_note"])

        rows = {item["catalogue_id"]: item for item in self.archive["catalogue"] if item["catalogue_id"] in {"eotc-019", "eotc-090"}}
        self.assertEqual(set(rows), {"eotc-019", "eotc-090"})
        for row in rows.values():
            self.assertIn("SRC-347", row["evidence_source_ids"])
            self.assertIn("126 TIFF", row["text_availability_status"])
            self.assertIn("research purposes only", row["rights_status"])
            self.assertIn("unknown", row["rights_status"])
            self.assertEqual(row["chapter_count"], "Not established")
            self.assertEqual(row["completeness_status"], "Not assessed")


if __name__ == "__main__":
    unittest.main()
