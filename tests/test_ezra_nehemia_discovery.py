import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class EzraNehemiaDiscoveryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.archive = json.loads((ROOT / "archive.json").read_text(encoding="utf-8"))
        cls.canon = json.loads((ROOT / "canon-registry.json").read_text(encoding="utf-8"))
        cls.menu = json.loads((ROOT / "research" / "ezra-nehemia-menu-audit.json").read_text(encoding="utf-8"))
        cls.review = (ROOT / "research" / "ezra-nehemia-source-review.md").read_text(encoding="utf-8")

    def test_grouped_title_match_does_not_claim_a_reader(self):
        book = next(b for b in self.archive["canon_registry"]["books"] if b["canon_id"] == "eotc-ot-15")
        self.assertEqual(book["mapping_state"], "reviewed_match")
        self.assertIsNone(book["reader_id"])
        self.assertEqual(self.archive["canon_registry"]["reader_count"], 19)
        self.assertIn("current EOTC edition", book["mapping_note"])
        self.assertIn("No text or images are bundled", book["mapping_note"])

    def test_source_menu_audit_preserves_exact_scope_without_text(self):
        self.assertEqual(self.menu["form_title"], "Ezra and Nehemia")
        self.assertEqual(self.menu["entry_count"], 23)
        self.assertEqual([row["label"] for row in self.menu["entries"]], list(range(1, 24)))
        self.assertEqual(self.menu["entries"][0]["source_path"], "Ezra/Ezrap 11.html")
        self.assertEqual(self.menu["entries"][-1]["source_path"], "Ezra/Ezrap 92.html")
        structure = self.menu["printed_edition_structure"]
        self.assertEqual(structure["chapter_count"], 23)
        self.assertEqual(structure["book_sections"], {"Ezra": "I–X", "Nehemiah": "XI–XXIII"})
        self.assertFalse(structure["completeness_verified"])
        self.assertIn("not individually matched to print pages", self.review)
        self.assertIn("chapter divisions vary", self.review)
        self.assertIn("No local scan, OCR, or scripture wording was created", self.review)

    def test_print_structure_is_attributed_and_manuscript_variants_are_retained(self):
        source = next(s for s in self.archive["sources"] if s["source_id"] == "SRC-362")
        self.assertEqual(source["url"], "https://www.patristique.org/sites/patristique.org/IMG/pdf/po_66_xiii_5.pdf")
        self.assertIn("21 chapters", source["inspection_and_limitations"])
        self.assertIn("no chapter divisions", source["inspection_and_limitations"])
        self.assertIn("No pages or wording are bundled", source["inspection_and_limitations"])

    def test_rights_are_limited_and_source_review_is_linked(self):
        source = next(s for s in self.archive["sources"] if s["source_id"] == "SRC-097")
        self.assertEqual(source["local_review_url"], "research/ezra-nehemia-source-review.md")
        lead = next(x for x in self.archive["translation_registry"]["edition_leads"] if x["edition_id"] == "tau-pereira-ezra-nehemia-1919")
        self.assertEqual(lead["mapping_state"], "reviewed_match")
        self.assertFalse(lead["text_bundled"])
        self.assertEqual(lead["rights_classification"], "permission_limited")
        self.assertIn("French text", lead["rights_status"])
        service_worker = (ROOT / "sw.js").read_text(encoding="utf-8")
        self.assertIn("if (relativePath)", service_worker)
        app = (ROOT / "app.js").read_text(encoding="utf-8")
        self.assertIn("Read local source review", app)

    def test_split_catalogue_rows_scope_counts_to_the_printed_edition(self):
        rows = [r for r in self.archive["catalogue"] if r["catalogue_id"] in {"eotc-017", "eotc-018"}]
        self.assertEqual(len(rows), 2)
        self.assertTrue(all("23 numbered chapters" in row["chapter_count"] for row in rows))
        self.assertTrue(all("Manuscript divisions vary" in row["chapter_count"] for row in rows))
        self.assertTrue(all("not individually collated" in row["chapter_order_status"] for row in rows))
        self.assertTrue(all("no local transcription" in row["text_availability_status"] for row in rows))


if __name__ == "__main__":
    unittest.main()
