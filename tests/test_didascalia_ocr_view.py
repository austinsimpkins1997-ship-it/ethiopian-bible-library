"""The Harden OCR browser view must remain source-only and explicitly unverified."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from build_didascalia_ocr_view import build


ROOT = Path(__file__).resolve().parents[1]


class DidascaliaOcrViewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.view = build()
        cls.page = (ROOT / "research" / "didascalia-harden1920-ocr-reader.html").read_text(encoding="utf-8")

    def test_view_matches_the_visual_heading_audit_without_claiming_verified_text(self):
        audit = json.loads((ROOT / self.view["heading_audit_path"]).read_text(encoding="utf-8"))
        self.assertEqual(self.view["chapter_count"], 43)
        self.assertEqual([chapter["chapter_number"] for chapter in self.view["chapters"]], list(range(1, 44)))
        self.assertEqual(
            [(chapter["chapter_number"], chapter["heading"], chapter["ocr_heading_label"])
             for chapter in self.view["chapters"] if chapter["heading_corrected_from_ocr"]],
            [(10, "X", "xX"), (31, "XXXI", "XXXII")],
        )
        self.assertEqual(self.view["source_ocr_sha256"], audit["ocr_xml_sha256"])
        self.assertEqual(self.view["canon_mapping_state"], "uncertain")
        self.assertEqual(self.view["translation_basis_status"], "unknown")
        self.assertIn("body-text accuracy", self.view["scope_note"])
        self.assertIn("US-scoped", self.view["rights_status"])
        self.assertNotIn("canon_id", self.view)
        for chapter in self.view["chapters"]:
            self.assertTrue(chapter["pages"])
            self.assertTrue(all(page["lines"] for page in chapter["pages"]))

    def test_source_card_links_to_view_without_adding_a_reader_or_canon_coverage(self):
        archive = json.loads((ROOT / "archive.json").read_text(encoding="utf-8"))
        source = next(item for item in archive["sources"] if item["source_id"] == "SRC-376")
        self.assertEqual(source["local_research_view_url"], "research/didascalia-harden1920-ocr-reader.html")
        self.assertEqual(source["local_research_view_label"], "Open chapter-indexed unproofread OCR research view")
        self.assertIn(source["local_research_view_url"], (ROOT / "index.html").read_text(encoding="utf-8"))
        self.assertIn("source.local_research_view_label", (ROOT / "app.js").read_text(encoding="utf-8"))
        service_worker = (ROOT / "sw.js").read_text(encoding="utf-8")
        self.assertIn("if (relativePath)", service_worker)
        self.assertIn("chapter-indexed OCR research view", (ROOT / "research/didascalia-source-review.md").read_text(encoding="utf-8"))
        self.assertIn("raw OCR", self.page)
        self.assertIn("body text was not proofread", self.page)
        self.assertIn("external scan record requires internet", self.page)
        self.assertNotIn("<script src=\"http", self.page)


if __name__ == "__main__":
    unittest.main()
