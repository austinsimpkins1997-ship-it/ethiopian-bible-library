import hashlib
import json
import unittest

import build_habakkuk_reader as habakkuk


class HabakkukTauReaderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reader, cls.layer = habakkuk.build()

    def test_captured_source_bytes_and_page_labels_are_pinned(self):
        manifest = json.loads((habakkuk.CAPTURE / "SOURCE-CAPTURE.json").read_text(encoding="utf-8"))
        self.assertEqual(len(manifest["files"]), 6)
        for item in manifest["files"]:
            raw = (habakkuk.CAPTURE / item["path"]).read_bytes()
            self.assertEqual(len(raw), item["size_bytes"])
            self.assertEqual(hashlib.sha256(raw).hexdigest(), item["sha256"])
            self.assertEqual(item["http_status"], 200)

        expected = {1: (17, "Hab"), 2: (20, "Nah"), 3: (19, "Hab")}
        self.assertEqual(self.reader["chapter_count"], 3)
        self.assertEqual(self.reader["unit_count"], 56)
        for chapter in self.reader["chapters"]:
            count, expected_link_book = expected[chapter["chapter"]]
            self.assertEqual(len(chapter["verses"]), count)
            self.assertEqual(
                [unit["source_marker"] for unit in chapter["verses"]],
                [str(number) for number in range(1, count + 1)],
            )
            self.assertEqual({unit["source_link_target_book"] for unit in chapter["verses"]}, {expected_link_book})
            self.assertTrue(all(unit["text"].strip() for unit in chapter["verses"]))

    def test_preserves_the_habakkuk_2_to_nahum_2_link_anomaly(self):
        page = (habakkuk.CAPTURE / "habakkuk-chapter-2.html").read_text(encoding="utf-8")
        self.assertIn("<title>Habacuc 2</title>", page)
        self.assertIn("Habakuk/Hab 2.html", (habakkuk.CAPTURE / "tau-ethiopic-index.html").read_text(encoding="utf-8"))
        chapter_two = self.reader["chapters"][1]
        self.assertEqual(len(chapter_two["verses"]), 20)
        self.assertTrue(all(unit["source_link_target_book"] == "Nah" for unit in chapter_two["verses"]))
        self.assertIn("links target Nahum 2", self.reader["edition_scope"])
        self.assertEqual(self.reader["text_origin"], "source_transcription")
        self.assertEqual(self.reader["language_tag"], "gez")
        self.assertEqual(self.reader["rights_classification"], "permission_limited")
        self.assertIn("NONCOMMERCIAL", self.reader["copyright_notice"])
        self.assertIsNone(self.reader["license_id"])
        self.assertIn("noncommercial", self.layer["rights"]["territory_or_term_limits"])


if __name__ == "__main__":
    unittest.main()
