import json
import hashlib
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class DidascaliaDiscoveryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.archive = json.loads((ROOT / "archive.json").read_text(encoding="utf-8"))
        cls.registry = json.loads((ROOT / "translation-registry.json").read_text(encoding="utf-8"))
        cls.heading_audit = json.loads(
            (ROOT / "research" / "didascalia-harden1920-chapter-heading-audit.json").read_text(encoding="utf-8")
        )

    def test_church_page_context_is_distinguished_from_edition_identity(self):
        review = (ROOT / "research" / "didascalia-source-review.md").read_text(encoding="utf-8")
        self.assertIn("first seven books of the Apostolic Constitutions", review)
        self.assertIn("Latin, Arabic, and Syriac versions", review)
        self.assertIn("does not identify the Platt or Harden witnesses as the exact current Church-list edition", review)
        church_source = next(item for item in self.archive["sources"] if item["source_id"] == "SRC-029")
        self.assertIn("https://www.ethiopianorthodox.org/english/canonical/books.html?lang=en", church_source["url"])

    def test_source_records_distinguish_menu_rights_and_edition(self):
        sources = {record["source_id"]: record for record in self.archive["sources"]}
        self.assertIn("I–XXII", sources["SRC-086"]["inspection_and_limitations"])
        edition = next(item for item in self.registry["edition_leads"] if item["edition_id"] == "tau-platt-ethiopic-didascalia-1834")
        self.assertIn("SRC-100", edition["source_ids"])
        self.assertIn("SRC-359", edition["source_ids"])
        self.assertIn("SRC-360", edition["source_ids"])
        self.assertEqual(sources["SRC-345"]["url"], "https://www.tau.ac.il/~hacohen/Didas/Information.html")
        self.assertEqual(sources["SRC-346"]["url"], "https://www.digitale-sammlungen.de/en/details/bsb10218768")
        qnl = sources["SRC-359"]
        qnl_rights = sources["SRC-360"]
        self.assertEqual(qnl["url"], "https://ediscovery.qnl.qa/islandora/object/QNL:00012804")
        self.assertEqual(qnl["rights_classification"], "unknown")
        self.assertIn("No Known Copyright", qnl["rights_status"])
        self.assertIn("not a reuse grant", qnl["rights_status"])
        self.assertIn("2 unnumbered pages, xvi, 131 pages", qnl["inspection_and_limitations"])
        self.assertIn("No Known Copyright", qnl["inspection_and_limitations"])
        self.assertEqual(qnl_rights["url"], "https://ediscovery.qnl.qa/disclaimer")
        self.assertIn("repository-wide disclaimer", qnl_rights["inspection_and_limitations"])
        self.assertEqual(qnl_rights["rights_classification"], "unknown")
        self.assertIn("repository-wide guidance", qnl_rights["rights_status"])
        self.assertIn("no reuse right", qnl_rights["rights_status"])
        ia_source = next(item for item in sources.values() if item["url"] == "https://archive.org/details/ethiopicdidascal00platrich")
        self.assertEqual(ia_source["rights_classification"], "public_domain_claimed")
        self.assertIn("United States", ia_source["rights_status"])
        self.assertIn("not a license", ia_source["rights_status"])
        self.assertIn("not reader text", ia_source["archive_status"])
        self.assertIn("US only", ia_source["inspection_and_limitations"])

    def test_catalogue_and_canon_counts_remain_unbundled(self):
        row = next(item for item in self.archive["catalogue"] if item["catalogue_id"] == "eotc-089")
        self.assertIn("first 23 chapters", row["chapter_count"])
        self.assertIn("I–XXII", row["chapter_count"])
        self.assertIn("Not assessed", row["completeness_status"])
        canon = next(item for item in self.archive["canon_registry"]["books"] if item["canon_id"] == "eotc-nt-35")
        self.assertIsNone(canon["reader_id"])
        self.assertNotIn("Bundled:", canon["reader_status"])
        self.assertIn("SRC-345", canon["source_ids"])

    def test_2012_scholarly_scope_claim_is_attributed_without_promoting_coverage(self):
        source = next(item for item in self.archive["sources"] if item["source_id"] == "SRC-423")
        self.assertIn("Mebratu Kiros Gebru", source["source_name"])
        self.assertEqual(source["url"], "https://www.collectionscanada.gc.ca/obj/thesescanada/vol2/OTU/TC-OTU-35210.pdf")
        self.assertEqual(source["rights_classification"], "unknown")
        self.assertIn("Platt's 1834 translation contains only the first 23 chapters", source["inspection_and_limitations"])
        self.assertIn("attributed scholarly interpretation", source["inspection_and_limitations"])
        canon = next(item for item in self.archive["canon_registry"]["books"] if item["canon_id"] == "eotc-nt-35")
        self.assertIn("SRC-423", canon["source_ids"])
        self.assertIsNone(canon["reader_id"])
        lead = next(item for item in self.registry["translation_leads"] if item["translation_id"] == "didascalia-en-platt-1834")
        self.assertFalse(lead["text_bundled"])
        self.assertIn("first 23 chapters", lead["scope_description"])
        self.assertIn("SRC-423", lead["source_ids"])

    def test_edition_and_translation_leads_do_not_promote_text(self):
        edition = next(item for item in self.registry["edition_leads"] if item["edition_id"] == "tau-platt-ethiopic-didascalia-1834")
        ia_source = next(item for item in self.archive["sources"] if item["url"] == "https://archive.org/details/ethiopicdidascal00platrich")
        self.assertEqual(edition["mapping_state"], "uncertain")
        self.assertFalse(edition["text_bundled"])
        self.assertEqual(edition["language_tag"], "gez")
        self.assertEqual(edition["rights_classification"], "permission_limited")
        english = next(item for item in self.registry["translation_leads"] if item["canon_id"] == "eotc-nt-35" and item["language_tag"] == "en")
        self.assertFalse(english["text_bundled"])
        self.assertEqual(english["translation_path"], ["gez", "en"])
        self.assertIn("bibliographic attribution only", english["review_status"])
        self.assertIn("not verified by comparing text", english["notes"])
        self.assertIn(ia_source["source_id"], edition["source_ids"])
        expected_count = sum(
            1
            for key in ("translation_leads", "edition_leads", "corpus_leads")
            for item in self.registry.get(key, [])
            if item.get("text_bundled") is False
        )
        self.assertRegex(self.registry["coverage_statement"], rf"contains {expected_count} unbundled translation, source-edition, or corpus leads")

    def test_harden_1920_ocr_is_locally_accessible_but_not_promoted_as_reader(self):
        sources = {record["source_id"]: record for record in self.archive["sources"]}
        ia = sources["SRC-376"]
        google_books = sources["SRC-377"]
        harden_biography = sources["SRC-429"]
        edition = next(item for item in self.registry["edition_leads"] if item["edition_id"] == "harden-ethiopic-didascalia-1920")
        self.assertEqual(ia["url"], "https://archive.org/details/cu31924096083336")
        self.assertEqual(ia["local_ocr_url"], "readers/source/didascalia-harden1920/djvu.txt")
        self.assertEqual(ia["local_metadata_url"], "readers/source/didascalia-harden1920/capture-manifest.json")
        self.assertEqual(ia["local_heading_audit_url"], "research/didascalia-harden1920-chapter-heading-audit.json")
        self.assertEqual(ia["rights_classification"], "public_domain_claimed")
        self.assertIn("United States", ia["rights_status"])
        self.assertIn("scan/OCR files", ia["rights_status"])
        self.assertIn("not proofread", ia["inspection_and_limitations"])
        self.assertIn("United States", ia["inspection_and_limitations"])
        self.assertIn("43 chapters in four of five", ia["inspection_and_limitations"])
        self.assertIn("All 43 detected headings were visually collated", ia["inspection_and_limitations"])
        self.assertIn("structured audit is stored locally", ia["inspection_and_limitations"])
        self.assertEqual(harden_biography["url"], "https://arquivo.igreja-lusitana.org/e1izg")
        self.assertEqual(harden_biography["rights_classification"], "unknown")
        self.assertIn("1871–1931", harden_biography["inspection_and_limitations"])
        self.assertIn("does not establish that identity", harden_biography["inspection_and_limitations"])
        self.assertIn("SRC-429", edition["source_ids"])
        self.assertIn("worldwide legal determination", ia["rights_status"])
        self.assertIn("204 pages", google_books["inspection_and_limitations"])
        self.assertEqual(edition["mapping_state"], "uncertain")
        self.assertFalse(edition["text_bundled"])
        self.assertEqual(edition["language_tag"], "en")
        self.assertIn("43 main-text heading occurrences", edition["scope_description"])
        self.assertIn("all 43 headings were visually checked", edition["scope_description"])
        self.assertIn("Complete text accuracy, scan completeness", edition["review_status"])
        self.assertIn("SRC-376", edition["source_ids"])
        canon = next(item for item in self.archive["canon_registry"]["books"] if item["canon_id"] == "eotc-nt-35")
        self.assertIsNone(canon["reader_id"])
        self.assertNotIn("Bundled:", canon["reader_status"])
        catalogue = next(item for item in self.archive["catalogue"] if item["catalogue_id"] == "eotc-089")
        self.assertIn("Harden's 1920 Introduction reports 43 chapters", catalogue["chapter_count"])
        self.assertIn("not interchangeable", catalogue["chapter_count"])

        audit = self.heading_audit
        self.assertEqual(audit["chapter_heading_count"], 43)
        self.assertEqual(audit["visually_collated_heading_count"], 43)
        self.assertEqual([item["chapter_number"] for item in audit["entries"]], list(range(1, 44)))
        corrections = [item for item in audit["entries"] if not item["ocr_matches_scan"]]
        self.assertEqual(
            [(item["chapter_number"], item["scan_pdf_page"], item["ocr_label"], item["visually_confirmed_label"])
             for item in corrections],
            [(10, 87, "xX", "X"), (31, 165, "XXXII", "XXXI")],
        )
        xml = ROOT / audit["ocr_xml_path"]
        self.assertEqual(hashlib.sha256(xml.read_bytes()).hexdigest(), audit["ocr_xml_sha256"])
        self.assertFalse(audit["body_text_proofread"])
        self.assertFalse(audit["scan_completeness_reviewed"])
        self.assertFalse(audit["church_list_identity_verified"])
        schema = json.loads((ROOT / "schemas" / "didascalia-heading-audit.schema.json").read_text(encoding="utf-8"))
        self.assertEqual(schema["properties"]["chapter_heading_count"]["const"], 43)


if __name__ == "__main__":
    unittest.main()
