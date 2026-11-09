import json
import unittest
from pathlib import Path

from build_bilen_mark_facsimile import CAPTURE_DIR, validate_capture


ROOT = Path(__file__).resolve().parents[1]


class BilenMarkFacsimileTests(unittest.TestCase):
    def test_captured_scan_metadata_and_ocr_diagnostic_are_hash_pinned(self):
        manifest = validate_capture()
        self.assertEqual(manifest["physical_page_count"], 80)
        self.assertEqual(manifest["script_observation"]["code"], "Ethi")
        self.assertIn("Latin", manifest["script_observation"]["conflict"])
        self.assertEqual(manifest["ocr_assessment"]["detected_language"], "kk")
        self.assertEqual(manifest["ocr_assessment"]["invalid_source_language"], "byn")
        self.assertEqual(manifest["ocr_assessment"]["use"], "Diagnostic only; not a transcription or reader layer")
        self.assertEqual(len(manifest["files"]), 4)

    def test_facsimile_is_presented_with_scope_rights_and_script_conflict(self):
        page = (ROOT / "research" / "bilin-mark-1890.html").read_text(encoding="utf-8")
        self.assertIn("Stored facsimile · no transcription", page)
        self.assertIn("not reader text", page)
        self.assertIn("Script metadata conflict", page)
        self.assertIn("Public Domain / OPEN", page)
        self.assertIn("not a worldwide legal determination", page)
        self.assertIn("Bilin-1890-Mark.pdf#view=FitH", page)

    def test_bundled_source_link_does_not_claim_bilin_text_or_canon_coverage(self):
        archive = json.loads((ROOT / "archive.json").read_text(encoding="utf-8"))
        source = next(item for item in archive["sources"] if item["source_id"] == "SRC-305")
        self.assertEqual(source["local_copy_url"], "research/bilin-mark-1890.html")
        self.assertEqual(source["rights_classification"], "public_domain_claimed")
        self.assertIn("provider claims", source["rights_status"])
        self.assertIn("not an independent worldwide", source["rights_status"])
        self.assertIn("Latin script field", source["inspection_and_limitations"])
        profile = next(item for item in archive["translation_registry"]["languages"] if item["language_tag"] == "byn")
        self.assertIn("SRC-339", profile["source_ids"])
        self.assertIn("Ethiopic script", profile["script_profile_note"])
        self.assertIn("Kazakh/Cyrillic", profile["availability_survey"]["notes"])
        self.assertFalse(any(reader.get("language_tag") == "byn" for reader in archive["readers"]))
        self.assertEqual(sum(bool(reader.get("canon_id")) for reader in archive["readers"]), archive["canon_registry"]["reader_count"])
        license_doc = (ROOT / "CONTENT-LICENSES.md").read_text(encoding="utf-8")
        self.assertIn("Bilin (1890) Gospel of Mark facsimile only", license_doc)
        self.assertIn("not as a worldwide legal determination", license_doc)
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("DBS-linked Bilin (1890) Mark scan as an offline facsimile", readme)


if __name__ == "__main__":
    unittest.main()
