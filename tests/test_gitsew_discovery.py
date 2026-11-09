import json
import hashlib
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class GitsewDiscoveryTests(unittest.TestCase):
    def test_acquisition_report_is_metadata_only_and_rights_are_not_inferred(self):
        archive = json.loads((ROOT / "archive.json").read_text(encoding="utf-8"))
        registry = json.loads((ROOT / "translation-registry.json").read_text(encoding="utf-8"))
        source = next(item for item in archive["sources"] if item["source_id"] == "SRC-284")
        lead = next(
            item for item in registry["edition_leads"]
            if item["edition_id"] == "eob-project-gitsew-acquisition-report-2017"
        )
        book = next(item for item in archive["canon_registry"]["books"] if item["canon_id"] == "eotc-nt-30")
        self.assertIn("acquired a complete Gitsew text", source["inspection_and_limitations"])
        self.assertEqual(source["local_review_url"], "research/gitsew-source-review.md")
        self.assertTrue((ROOT / source["local_review_url"]).is_file())
        self.assertIn("All Rights Reserved", source["inspection_and_limitations"])
        self.assertEqual((lead["candidate_canon_id"], lead["mapping_state"]), ("eotc-nt-30", "uncertain"))
        self.assertEqual(lead["language_tags"], ["gez", "am"])
        self.assertFalse(lead["text_bundled"])
        self.assertEqual(lead["rights_classification"], "unknown")
        self.assertIn("if (relativePath)", (ROOT / "sw.js").read_text(encoding="utf-8"))
        self.assertIsNone(book.get("reader_id"))
        self.assertTrue((ROOT / "research/gitsew-source-review.md").is_file())

    def test_candidate_discovery_does_not_inflate_reader_coverage(self):
        archive = json.loads((ROOT / "archive.json").read_text(encoding="utf-8"))
        self.assertEqual(archive["canon_registry"]["reader_count"], 19)
        self.assertEqual(len(archive["canon_registry"]["books"]), 81)

    def test_publisher_modernization_is_cited_as_an_unbundled_claim(self):
        archive = json.loads((ROOT / "archive.json").read_text(encoding="utf-8"))
        registry = json.loads((ROOT / "translation-registry.json").read_text(encoding="utf-8"))
        source = next(item for item in archive["sources"] if item["source_id"] == "SRC-443")
        lead = next(
            item for item in registry["translation_leads"]
            if item["translation_id"] == "gitsew-modern-english-schoddederived-2026"
        )
        book = next(item for item in archive["canon_registry"]["books"] if item["canon_id"] == "eotc-nt-30")
        self.assertIn("publisher statement", source["source_name"])
        self.assertEqual(source["rights_classification"], "unknown")
        self.assertEqual(lead["mapping_state"], "asserted_by_source")
        self.assertEqual(lead["translation_path"], ["gez", "en"])
        self.assertFalse(lead["text_bundled"])
        self.assertEqual(lead["rights_classification"], "unknown")
        self.assertIn("not a new direct Geʽez translation", lead["scope_description"])
        source_ids = {item["source_id"] for item in archive["sources"]}
        self.assertTrue(set(lead["source_ids"]) <= source_ids)
        self.assertIsNone(book.get("reader_id"))

    def test_schodde_heading_inventory_is_bounded_and_not_reader_text(self):
        archive = json.loads((ROOT / "archive.json").read_text(encoding="utf-8"))
        registry = json.loads((ROOT / "translation-registry.json").read_text(encoding="utf-8"))
        source = next(item for item in archive["sources"] if item["source_id"] == "SRC-433")
        audit_path = ROOT / source["local_heading_audit_url"]
        audit = json.loads(audit_path.read_text(encoding="utf-8"))
        labels = [item["printed_label"] for item in audit["headings"]]
        pdf = ROOT / audit["source_path"]
        lead = next(item for item in registry["edition_leads"] if item["edition_id"] == "gitsew-ethiopic-apostolic-canons-schodde-1885")
        book = next(item for item in archive["canon_registry"]["books"] if item["canon_id"] == "eotc-nt-30")

        self.assertEqual(labels, [roman for roman in (
            "I II III IV V VI VII VIII IX X XI XII XIII XIV XV XVI XVII XVIII XIX XX XXI XXII XXIII XXIV XXV XXVI "
            "XXVII XXVIII XXIX XXX XXXI XXXII XXXIII XXXIV XXXV XXXVI XXXVII XXXVIII XXXIX XL XLI XLII XLIII "
            "XLIV XLV XLVI XLVII XLVIII XLIX L LI LII LIII LIV LV LVI LVII"
        ).split()])
        self.assertEqual(audit["scope"]["heading_count"], 57)
        self.assertEqual(audit["source_sha256"], hashlib.sha256(pdf.read_bytes()).hexdigest())
        self.assertEqual({item["pdf_page"] for item in audit["headings"]}, set(range(4, 14)))
        self.assertTrue(all(63 <= item["printed_page"] <= 72 for item in audit["headings"]))
        expected_page_spans = {
            4: ("I", "VII", 63), 5: ("VIII", "XIII", 64),
            6: ("XIV", "XX", 65), 7: ("XXI", "XXVI", 66),
            8: ("XXVII", "XXXI", 67), 9: ("XXXII", "XXXVII", 68),
            10: ("XXXVIII", "XLVI", 69), 11: ("XLVII", "LI", 70),
            12: ("LII", "LIV", 71), 13: ("LV", "LVII", 72),
        }
        for pdf_page, expected in expected_page_spans.items():
            page_rows = [row for row in audit["headings"] if row["pdf_page"] == pdf_page]
            self.assertEqual((page_rows[0]["printed_label"], page_rows[-1]["printed_label"], page_rows[0]["printed_page"]), expected)
        self.assertIn("does not proofread", " ".join(audit["limitations"]))
        self.assertIn("wording remains unproofread", source["heading_audit_status"])
        self.assertFalse(lead["text_bundled"])
        self.assertIsNone(book.get("reader_id"))
        self.assertEqual(archive["canon_registry"]["reader_count"], 19)


if __name__ == "__main__":
    unittest.main()
