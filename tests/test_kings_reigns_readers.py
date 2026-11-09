import json
import unittest
from pathlib import Path

from build_kings_research_readers import SOURCE_ID, build
from capture_kings_sources import EXPECTED_MENU

ROOT = Path(__file__).resolve().parents[1]


class KingsReignsReaderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.readers, cls.corpora, cls.sources = build()
        cls.capture = json.loads(
            (ROOT / "readers/source/reigns-kings-tau-dillmann/SOURCE-CAPTURE.json").read_text(encoding="utf-8")
        )

    def test_both_components_are_separately_bundled_as_research_not_canon_readers(self):
        self.assertEqual(len(self.readers), 2)
        self.assertEqual(len(self.corpora), 2)
        self.assertEqual(len(self.sources), 1)
        for reader, corpus in zip(self.readers, self.corpora, strict=True):
            with self.subTest(reader=reader["reader_id"]):
                self.assertIsNone(reader.get("canon_id"))
                self.assertEqual(reader["research_corpus_id"], corpus["corpus_id"])
                self.assertEqual(corpus["canon_mapping_state"], "reviewed_match")
                self.assertEqual(corpus["candidate_canon_id"], "eotc-ot-10")
                self.assertIn("Archive-reviewed work/title crosswalk", corpus["canon_mapping_note"])
                self.assertIn("does not establish identity with a current EOTC edition", corpus["canon_mapping_note"])
                self.assertEqual(reader["rights_classification"], "permission_limited")
                self.assertIn("NONCOMMERCIAL", reader["copyright_notice"])
                self.assertEqual(reader["source_ids"][-1], SOURCE_ID)
                self.assertTrue(all(unit["text"] for chapter in reader["chapters"] for unit in chapter["verses"]))

    def test_ta_u_menu_page_labels_and_order_are_preserved(self):
        by_roman = {"III": self.readers[0], "IV": self.readers[1]}
        for roman, reader in by_roman.items():
            with self.subTest(regum=roman):
                self.assertEqual(
                    [chapter["source_page_label"] for chapter in reader["chapters"]],
                    EXPECTED_MENU[roman],
                )
                self.assertEqual(reader["chapter_count"], len(EXPECTED_MENU[roman]))
                self.assertEqual(reader["chapter_count"], len(reader["chapters"]))
                self.assertEqual(reader["unit_count"], sum(len(chapter["verses"]) for chapter in reader["chapters"]))

        third_regum = by_roman["III"]["chapters"]
        labels = [chapter["source_page_label"] for chapter in third_regum]
        self.assertEqual(labels[2:4], ["3a", "3b"])
        self.assertEqual(labels.index("21") + 1, 21)
        self.assertEqual(labels.index("20") + 1, 22)
        self.assertIn("navigation positions are not claims", by_roman["III"]["chapter_structure_note"])

    def test_every_captured_source_page_matches_its_hash_record(self):
        files = {item["path"]: item for item in self.capture["files"]}
        text_pages = [item for item in self.capture["files"] if item.get("menu_label") is not None]
        self.assertEqual(len(text_pages), sum(map(len, EXPECTED_MENU.values())))
        for reader in self.readers:
            for chapter in reader["chapters"]:
                path = next(
                    name for name, item in files.items()
                    if item["url"] == chapter["source_url"]
                )
                record = files[path]
                self.assertEqual(chapter["source_sha256"], record["sha256"])
                self.assertTrue(all(unit["source_link_target_book"] in {"1ki", "2ki"}
                                    for unit in chapter["verses"]))


if __name__ == "__main__":
    unittest.main()
