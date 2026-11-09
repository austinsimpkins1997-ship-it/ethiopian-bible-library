import hashlib
import json
import unittest

import build_jonah_reader as jonah


class JonahTauReaderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reader, cls.layer = jonah.build()

    def test_capture_hashes_and_source_labels_are_exactly_bounded(self):
        manifest = json.loads((jonah.CAPTURE / "SOURCE-CAPTURE.json").read_text(encoding="utf-8"))
        self.assertEqual(len(manifest["files"]), 7)
        for item in manifest["files"]:
            raw = (jonah.CAPTURE / item["path"]).read_bytes()
            self.assertEqual(len(raw), item["size_bytes"])
            self.assertEqual(hashlib.sha256(raw).hexdigest(), item["sha256"])

        expected = {1: 16, 2: 11, 3: 10, 4: 11}
        self.assertEqual(self.reader["chapter_count"], 4)
        self.assertEqual(self.reader["unit_count"], sum(expected.values()))
        for chapter in self.reader["chapters"]:
            self.assertEqual(len(chapter["verses"]), expected[chapter["chapter"]])
            self.assertEqual([v["source_marker"] for v in chapter["verses"]], [str(n) for n in range(1, expected[chapter["chapter"]] + 1)])
            self.assertTrue(all(v["text"].strip() for v in chapter["verses"]))

    def test_reader_is_source_transcription_not_translation_or_collation_claim(self):
        self.assertEqual(self.reader["text_origin"], "source_transcription")
        self.assertEqual(self.reader["language_tag"], "gez")
        self.assertEqual(self.reader["rights_classification"], "permission_limited")
        self.assertIn("NONCOMMERCIAL", self.reader["copyright_notice"])
        self.assertIsNone(self.reader["license_id"])
        self.assertIn("No wording was translated", self.reader["transcription_note"])
        self.assertIn("No collation", self.reader["verification_status"])
        self.assertEqual(self.layer["publication_state"], "bundled")
        self.assertIn("noncommercial", self.layer["rights"]["territory_or_term_limits"])


if __name__ == "__main__":
    unittest.main()
