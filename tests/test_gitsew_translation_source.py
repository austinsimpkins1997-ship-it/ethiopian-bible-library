import json
import hashlib
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class GitsewTranslationSourceTests(unittest.TestCase):
    def test_source_pair_is_bundled_without_claiming_a_verified_reader(self):
        archive = json.loads((ROOT / "archive.json").read_text(encoding="utf-8"))
        canon_registry = json.loads((ROOT / "canon-registry.json").read_text(encoding="utf-8"))
        registry = json.loads((ROOT / "translation-registry.json").read_text(encoding="utf-8"))
        source = next(item for item in archive["sources"] if item["source_id"] == "SRC-433")
        fell = next(item for item in archive["sources"] if item["source_id"] == "SRC-214")
        lead = next(
            item for item in registry["edition_leads"]
            if item["edition_id"] == "gitsew-ethiopic-apostolic-canons-schodde-1885"
        )
        catalogue = next(item for item in archive["catalogue"] if item["catalogue_id"] == "eotc-084")
        book = next(item for item in archive["canon_registry"]["books"] if item["canon_id"] == "eotc-nt-30")

        self.assertEqual(source["rights_classification"], "public_domain_claimed")
        self.assertEqual(source["local_review_url"], "research/gitsew-fell-schodde-translation.html")
        self.assertIn("pp. 61–72", source["inspection_and_limitations"])
        self.assertIn("Fell’s 1871", source["inspection_and_limitations"])
        self.assertIn("No Known Copyright", fell["inspection_and_limitations"])
        self.assertTrue((ROOT / "readers/source/gitsew/Canones-Apostolorum-Aethiopice-Fell-1871.pdf").is_file())
        self.assertTrue((ROOT / "readers/source/gitsew/The-Apostolic-Canons-Schodde-1885.pdf").is_file())
        self.assertTrue((ROOT / source["local_review_url"]).is_file())
        progress_path = ROOT / source["local_proofread_progress_url"]
        progress = json.loads(progress_path.read_text(encoding="utf-8"))
        self.assertEqual(progress["status"], "partial_working_transcription_not_reader")
        self.assertEqual(progress["scope_completed"]["canon_number_range_seen"], [1, 57])
        self.assertEqual(progress["scope_completed"]["fully_proofread_canon_ranges"], [[1, 19], [21, 57]])
        self.assertEqual(progress["scope_completed"]["incomplete_canons"], [20])
        self.assertEqual(
            [unit["number"] for unit in progress["units"] if "number" in unit],
            list(range(1, 58)),
        )
        canon_20 = next(unit for unit in progress["units"] if unit.get("number") == 20)
        self.assertEqual(canon_20["status"], "incomplete_scan_extent")
        self.assertTrue(canon_20["text"].endswith("from me,"))
        self.assertNotIn("I Peter", canon_20["text"])
        self.assertIn("I Peter", canon_20["lacuna_note"])
        canon_26 = next(unit for unit in progress["units"] if unit.get("number") == 26)
        self.assertEqual(canon_26["printed_pages"], [66, 67])
        self.assertIn("given to him", canon_26["text"])
        canon_30 = next(unit for unit in progress["units"] if unit.get("number") == 30)
        self.assertEqual(canon_30["printed_pages"], [67])
        self.assertIn("famine and curse", canon_30["text"])
        canon_32 = next(unit for unit in progress["units"] if unit.get("number") == 32)
        self.assertEqual(canon_32["printed_pages"], [68])
        self.assertIn("theatre", canon_32["text"])
        canon_37 = next(unit for unit in progress["units"] if unit.get("number") == 37)
        self.assertTrue(canon_37["text"].endswith("if he does this."))
        canon_31 = next(unit for unit in progress["units"] if unit.get("number") == 31)
        self.assertEqual(canon_31["printed_pages"], [67, 68])
        self.assertTrue(canon_31["text"].endswith("supporting themselves."))
        canon_37 = next(unit for unit in progress["units"] if unit.get("number") == 37)
        self.assertEqual(canon_37["printed_pages"], [68, 69])
        self.assertIn("deformed at his feet", canon_37["text"])
        canon_38 = next(unit for unit in progress["units"] if unit.get("number") == 38)
        self.assertEqual(canon_38["printed_pages"], [69])
        canon_45 = next(unit for unit in progress["units"] if unit.get("number") == 45)
        self.assertTrue(canon_45["text"].endswith("the layman be expelled."))
        canon_46 = next(unit for unit in progress["units"] if unit.get("number") == 46)
        self.assertEqual(canon_46["printed_pages"], [69, 70])
        canon_51 = next(unit for unit in progress["units"] if unit.get("number") == 51)
        self.assertEqual(canon_51["printed_pages"], [70, 71])
        self.assertTrue(canon_51["text"].endswith("fled from judgment."))
        canon_56 = next(unit for unit in progress["units"] if unit.get("number") == 56)
        self.assertIn("three books of Kufa’e [Book of Jubilees]", canon_56["text"])
        canon_57 = next(unit for unit in progress["units"] if unit.get("number") == 57)
        self.assertTrue(canon_57["text"].endswith("Amen."))
        self.assertNotIn(58, [unit.get("number") for unit in progress["units"]])
        self.assertEqual(source["comparison_copy_sha256"], progress["comparison_copy"]["sha256"])
        self.assertIn("not an independent witness", source["comparison_copy_result"])
        self.assertEqual(progress["source_sha256"], lead["raw_extraction"]["source_sha256"])
        self.assertEqual(
            hashlib.sha256(progress_path.read_bytes()).hexdigest(),
            source["local_proofread_progress_sha256"],
        )
        self.assertIn("not a reader", source["proofread_progress_status"])
        self.assertFalse(lead["text_bundled"])
        self.assertEqual(lead["mapping_state"], "asserted_by_source")
        self.assertEqual(lead["rights_classification"], "public_domain_claimed")
        self.assertEqual(catalogue["chapter_count"], "Schodde prints Canons I–LVII; a visual heading inventory is bundled; scholarship reports 56 or 57, depending on segmentation")
        self.assertIsNone(book.get("reader_id"))
        self.assertEqual(archive["canon_registry"]["reader_count"], 19)
        canon_book = next(item for item in canon_registry["books"] if item["canon_id"] == "eotc-nt-30")
        self.assertIn("no complete reader is bundled", canon_book["reader_status"])

    def test_facsimiles_are_cached_on_demand_for_offline_access(self):
        sw = (ROOT / "sw.js").read_text(encoding="utf-8")
        for path in (
            "research/gitsew-fell-schodde-translation.html",
            "readers/source/gitsew/Canones-Apostolorum-Aethiopice-Fell-1871.pdf",
            "readers/source/gitsew/The-Apostolic-Canons-Schodde-1885.pdf",
        ):
            self.assertTrue((ROOT / path).is_file())
        self.assertIn("if (relativePath)", sw)

    def test_fell_latin_parallel_is_provenanced_and_not_mixed_into_schodde(self):
        record = json.loads((ROOT / "research/gitsew-fell-latin-canon20.json").read_text(encoding="utf-8"))
        page = (ROOT / "research/gitsew-fell-schodde-translation.html").read_text(encoding="utf-8")
        source_bytes = (ROOT / record["source_path"]).read_bytes()
        self.assertEqual(hashlib.sha256(source_bytes).hexdigest(), record["source_sha256"])
        self.assertEqual(record["source_location"], {"pdf_page": 39, "printed_page": 37, "canon": "XX"})
        self.assertEqual(record["same_edition_geez_locator"]["printed_page"], 28)
        self.assertIn("Can. XX.", record["same_edition_geez_locator"]["evidence"])
        self.assertIn("ego Petrus.", record["latin_text"])
        self.assertIn("I, Peter.", record["english_translation"]["text"])
        self.assertIn("does not make the ending visible in the 1885 English scan", page)
        progress = json.loads((ROOT / "research/gitsew-schodde-proofread-progress.json").read_text(encoding="utf-8"))
        canon20 = next(unit for unit in progress["units"] if unit.get("number") == 20)
        self.assertTrue(canon20["text"].endswith("from me,"))
        self.assertEqual(canon20["status"], "incomplete_scan_extent")

    def test_ia_ethiopic_ocr_is_rejected_as_transcription_input(self):
        audit = json.loads((ROOT / "research/gitsew-fell-internet-archive-ocr-audit.json").read_text(encoding="utf-8"))
        self.assertEqual(audit["ethiopic_unicode_codepoints"], 0)
        self.assertEqual(audit["status"], "rejected_as_geez_transcription")
        self.assertEqual(len(audit["downloaded_sha256"]), 64)
        self.assertIn("Not bundled or used", audit["decision"])


if __name__ == "__main__":
    unittest.main()
