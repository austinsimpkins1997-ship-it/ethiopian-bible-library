import hashlib
import json
import unittest

import build_nahum_reader as nahum


class NahumTauReaderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reader, cls.layer = nahum.build()

    def test_captured_source_bytes_and_observed_labels_are_pinned(self):
        manifest = json.loads((nahum.CAPTURE / "SOURCE-CAPTURE.json").read_text(encoding="utf-8"))
        self.assertEqual(len(manifest["files"]), 6)
        for item in manifest["files"]:
            raw = (nahum.CAPTURE / item["path"]).read_bytes()
            self.assertEqual(len(raw), item["size_bytes"])
            self.assertEqual(hashlib.sha256(raw).hexdigest(), item["sha256"])
            self.assertEqual(item["http_status"], 200)

        expected = {1: 15, 2: 14, 3: 19}
        self.assertEqual(self.reader["chapter_count"], 3)
        self.assertEqual(self.reader["unit_count"], 48)
        for chapter in self.reader["chapters"]:
            self.assertEqual(len(chapter["verses"]), expected[chapter["chapter"]])
            self.assertEqual(
                [unit["source_marker"] for unit in chapter["verses"]],
                [str(number) for number in range(1, expected[chapter["chapter"]] + 1)],
            )
            self.assertTrue(all(unit["text"].strip() for unit in chapter["verses"]))

    def test_is_labeled_as_permission_limited_geez_transcription(self):
        self.assertEqual(self.reader["canon_id"], "eotc-ot-39")
        self.assertEqual(self.reader["text_origin"], "source_transcription")
        self.assertEqual(self.reader["language_tag"], "gez")
        self.assertEqual(self.reader["script_code"], "Ethi")
        self.assertEqual(self.reader["rights_classification"], "permission_limited")
        self.assertIn("NONCOMMERCIAL", self.reader["copyright_notice"])
        self.assertIsNone(self.reader["license_id"])
        self.assertIn("No wording was translated", self.reader["transcription_note"])
        self.assertIn("No collation", self.reader["verification_status"])
        self.assertEqual(self.layer["publication_state"], "bundled")
        self.assertIn("noncommercial", self.layer["rights"]["territory_or_term_limits"])


if __name__ == "__main__":
    unittest.main()
