import json
import unittest
from pathlib import Path

from build_reigns_readers import SOURCE_ID, build


ROOT = Path(__file__).resolve().parents[1]


class SamuelReignsReaderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.readers, cls.corpora, cls.sources = build()
        cls.capture_root = ROOT / "readers/source/reigns-tau-dillmann"
        cls.capture = json.loads((cls.capture_root / "SOURCE-CAPTURE.json").read_text(encoding="utf-8"))

    def test_two_components_cover_the_reviewed_grouped_work_title_only(self):
        archive = json.loads((ROOT / "archive.json").read_text(encoding="utf-8"))
        book = next(item for item in archive["canon_registry"]["books"] if item["canon_id"] == "eotc-ot-09")
        self.assertEqual(book["display_name"], "I and II Samuel")
        self.assertEqual(len(self.readers), 2)
        self.assertEqual(len(self.corpora), 2)
        self.assertEqual(len(self.sources), 1)
        self.assertEqual(self.sources[0]["local_review_url"], "research/reigns-title-crosswalk-review.md")
        self.assertTrue((ROOT / self.sources[0]["local_review_url"]).is_file())

        expected = {
            "samuel-i-geez-research": ("I", 31, 805, "1sa"),
            "samuel-ii-geez-research": ("II", 24, 691, "2sa"),
        }
        files_by_url = {item["url"]: item for item in self.capture["files"]}
        self.assertIn("that is, Samuel I-II and Kings I-II", (self.capture_root / "regum-information.html").read_text(encoding="ascii"))
        for reader, corpus in zip(self.readers, self.corpora, strict=True):
            with self.subTest(reader=reader["reader_id"]):
                roman, chapters, units, target_book = expected[reader["reader_id"]]
                self.assertEqual((reader["chapter_count"], len(reader["chapters"])), (chapters, chapters))
                self.assertEqual(reader["unit_count"], units)
                self.assertEqual(reader["chapters"][0]["source_marker"], f"Regum {roman} 1")
                self.assertEqual(reader["chapters"][-1]["source_marker"], f"Regum {roman} {chapters}")
                target_books = {
                    unit["source_link_target_book"]
                    for chapter in reader["chapters"] for unit in chapter["verses"]
                }
                self.assertIn(target_book, target_books)
                self.assertTrue(target_books <= {"1sa", "2sa"})
                if roman == "I":
                    boundary_spans = [
                        (chapter["source_marker"], unit["source_link_target_book"],
                         unit["source_link_target_chapter"], unit["number"])
                        for chapter in reader["chapters"] for unit in chapter["verses"]
                        if unit["source_link_target_book"] != target_book
                    ]
                    self.assertEqual(boundary_spans, [("Regum I 31", "2sa", 1, 1)])
                self.assertIsNone(reader.get("canon_id"))
                self.assertEqual(reader["research_corpus_id"], corpus["corpus_id"])
                self.assertEqual(corpus["candidate_canon_id"], "eotc-ot-09")
                self.assertEqual(corpus["canon_mapping_state"], "reviewed_match")
                self.assertIn("work/title crosswalk", corpus["canon_mapping_note"])
                self.assertIn("does not establish identity with a current EOTC edition", corpus["canon_mapping_note"])
                self.assertEqual(reader["rights_classification"], "permission_limited")
                self.assertIn("NONCOMMERCIAL", reader["copyright_notice"])
                self.assertIn(SOURCE_ID, reader["source_ids"])
                for chapter in reader["chapters"]:
                    source_file = files_by_url[chapter["source_url"]]
                    self.assertEqual(chapter["source_sha256"], source_file["sha256"])
                    self.assertTrue(all(unit["text"] for unit in chapter["verses"]))


if __name__ == "__main__":
    unittest.main()
