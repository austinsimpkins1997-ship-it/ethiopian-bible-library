import hashlib
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CAPTURE = ROOT / "readers" / "source" / "haggai-tau-2018"


class HaggaiTauReaderTests(unittest.TestCase):
    def test_captured_pages_and_reader_labels_match_checksums(self):
        manifest = json.loads((CAPTURE / "SOURCE-CAPTURE.json").read_text(encoding="utf-8"))
        for item in manifest["files"]:
            raw = (CAPTURE / item["path"]).read_bytes()
            self.assertEqual(item["http_status"], 200)
            self.assertEqual(len(raw), item["size_bytes"])
            self.assertEqual(hashlib.sha256(raw).hexdigest(), item["sha256"])

        reader = json.loads((ROOT / "readers" / "haggai-geez-lofgren-ghebre-tau.json").read_text(encoding="utf-8"))
        self.assertEqual(reader["canon_id"], "eotc-ot-42")
        self.assertEqual([len(chapter["verses"]) for chapter in reader["chapters"]], [14, 23])
        self.assertEqual(reader["unit_count"], 37)
        for index, chapter in enumerate(reader["chapters"], 1):
            self.assertEqual([verse["number"] for verse in chapter["verses"]], list(range(1, len(chapter["verses"]) + 1)))
            self.assertTrue(all(verse["source_link_target_book"] == "Hag" for verse in chapter["verses"]))
            page = (CAPTURE / f"haggai-chapter-{index}.html").read_text(encoding="utf-8")
            self.assertIn(f"Aggaeus {index}", page)

    def test_reader_scopes_attribution_rights_and_translation_status(self):
        reader = json.loads((ROOT / "readers" / "haggai-geez-lofgren-ghebre-tau.json").read_text(encoding="utf-8"))
        self.assertEqual(reader["text_origin"], "source_transcription")
        self.assertEqual(reader["language_tag"], "gez")
        self.assertIn("Kefela Ghebre", reader["edition"])
        self.assertIn("Ran HaCohen", reader["edition"])
        self.assertIn("no English translation", reader["additional_notes"])
        self.assertEqual(reader["rights_classification"], "permission_limited")
        self.assertIn("NONCOMMERCIAL", reader["copyright_notice"])
        self.assertIn("No collation", reader["verification_status"])


if __name__ == "__main__":
    unittest.main()

