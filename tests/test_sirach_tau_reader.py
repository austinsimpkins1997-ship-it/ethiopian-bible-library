"""Integrity checks for the captured TAU Geʽez Sirach reader."""
from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path

from build_sirach_reader import CAPTURE, READER_ID, SirachPageParser

ROOT = Path(__file__).resolve().parents[1]


class SirachTauReaderTests(unittest.TestCase):
    def setUp(self):
        self.reader = json.loads((ROOT / "readers" / f"{READER_ID}.json").read_text(encoding="utf-8"))
        self.layer = json.loads((ROOT / "examples" / f"{READER_ID}-layer.json").read_text(encoding="utf-8"))
        self.manifest = json.loads((CAPTURE / "SOURCE-CAPTURE.json").read_text(encoding="utf-8"))

    def test_all_menu_pages_are_retained_and_hash_checked(self):
        self.assertEqual(self.reader["chapter_count"], 51)
        chapter_pages = [item for item in self.manifest["files"] if item["path"].startswith("sirach-chapter-")]
        self.assertEqual(len(chapter_pages), 51)
        for item in self.manifest["files"]:
            raw = (CAPTURE / item["path"]).read_bytes()
            self.assertEqual(item["http_status"], 200)
            self.assertEqual(len(raw), item["size_bytes"])
            self.assertEqual(hashlib.sha256(raw).hexdigest(), item["sha256"])
        for chapter in range(1, 52):
            raw = (CAPTURE / f"sirach-chapter-{chapter}.html").read_text(encoding="utf-8")
            self.assertIn(f"<title>Sirach {chapter}</title>", raw)

    def test_reader_units_match_source_labels_and_keep_source_gaps(self):
        self.assertEqual(len(self.reader["chapters"]), 51)
        total = 0
        for chapter in self.reader["chapters"]:
            parser = SirachPageParser()
            raw = (CAPTURE / f"sirach-chapter-{chapter['chapter']}.html").read_text(encoding="utf-8")
            parser.feed(raw)
            parser.close()
            observed = [(unit["source_marker"], unit["text"]) for unit in chapter["verses"]]
            self.assertEqual(observed, parser.rows)
            self.assertTrue(all(label.isdecimal() and text for label, text in observed))
            total += len(observed)
        self.assertEqual(total, self.reader["unit_count"])
        chapter_1 = self.reader["chapters"][0]
        self.assertEqual([v["number"] for v in chapter_1["verses"]],
                         [1, 2, 3, 4, 6, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 29, 30])
        gaps = {item["chapter"]: item["unobserved_source_markers"] for item in self.reader["source_label_gaps"]}
        self.assertEqual(gaps[1], ["5", "7", "28"])
        self.assertEqual(gaps[2], ["3", "13"])
        self.assertEqual(gaps[21], ["20"])
        anomalies = {item["chapter"]: item["reversals"] for item in self.reader["source_label_order_anomalies"]}
        self.assertEqual(anomalies[13], [{"source_order": 18, "previous_label": 30, "label": 21}])
        self.assertIn("not treated as proof of textual lacunae", self.reader["chapter_structure_note"])

    def test_rights_and_scoped_reviewed_title_mapping_are_visible(self):
        self.assertEqual(self.reader["canon_id"], "eotc-ot-45")
        self.assertEqual(self.reader["language_tag"], "gez")
        self.assertEqual(self.reader["text_origin"], "source_transcription")
        self.assertEqual(self.reader["rights_classification"], "permission_limited")
        self.assertIn("NONCOMMERCIAL", self.reader["copyright_notice"])
        self.assertIn("does not translate", self.reader["transcription_note"])
        self.assertIn("No English translation is included", self.reader["additional_notes"])
        self.assertEqual(self.layer["tradition_assertions"][0]["mapping_state"], "reviewed_match")
        self.assertIn("bounded title/work-family match only", self.layer["tradition_assertions"][0]["notes"])
        self.assertIn("does not establish recension", self.layer["tradition_assertions"][0]["notes"])
        self.assertEqual(self.layer["rights"]["status"], "permission_limited")
        package = (ROOT / "readers" / f"{READER_ID}.json").read_bytes()
        self.assertEqual(hashlib.sha256(package).hexdigest(), self.layer["content_package"]["sha256"])

    def test_catalogue_and_language_registry_link_only_to_this_limited_reader(self):
        canon = json.loads((ROOT / "canon-registry.json").read_text(encoding="utf-8"))
        entry = next(item for item in canon["books"] if item["canon_id"] == "eotc-ot-45")
        self.assertEqual(entry["reader_id"], READER_ID)
        self.assertIn("does not establish recension", entry["mapping_note"])
        self.assertIn("completeness", entry["mapping_note"])
        registry = json.loads((ROOT / "translation-registry.json").read_text(encoding="utf-8"))
        language = next(item for item in registry["languages"] if item["language_tag"] == "gez")
        record = next(item for item in language["records"] if item.get("reader_id") == READER_ID)
        self.assertEqual(record["rights_classification"], "permission_limited")
        sources = {item["source_id"]: item for item in json.loads((ROOT / "archive.json").read_text(encoding="utf-8"))["sources"]}
        self.assertIn("51 corresponding chapter pages", sources["SRC-318"]["inspection_and_limitations"])
        self.assertIn("accuracy", sources["SRC-318"]["archive_status"])


if __name__ == "__main__":
    unittest.main()
