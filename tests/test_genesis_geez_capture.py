"""Genesis' stored Geʽez reader must reproduce its retained source captures."""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

from build_genesis_geez import INDEX, OUTPUT, SOURCE_DIR, parse_chapter


ROOT = Path(__file__).resolve().parents[1]


class GenesisGeezCaptureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reader = json.loads(OUTPUT.read_text(encoding="utf-8"))
        cls.index = INDEX.read_text(encoding="utf-8-sig")

    def test_archived_index_lists_all_fifty_chapters_in_order(self):
        chapters = [int(value) for value in re.findall(r"Octateuch/Genesis (\d+)\.html", self.index)]
        self.assertEqual(chapters, list(range(1, 51)))
        self.assertEqual(self.reader["chapter_count"], 50)

    def test_all_fifty_retained_pages_reproduce_the_stored_reader_records(self):
        self.assertEqual(len(self.reader["chapters"]), 50)
        total_verses = 0
        for chapter_number, stored in enumerate(self.reader["chapters"], start=1):
            with self.subTest(chapter=chapter_number):
                raw_path = SOURCE_DIR / f"Genesis_{chapter_number:02d}.html"
                self.assertTrue(raw_path.is_file(), raw_path)
                reproduced = parse_chapter(chapter_number)
                self.assertEqual(stored, reproduced)
                self.assertEqual(stored["chapter"], chapter_number)
                self.assertTrue(stored["verses"])
                total_verses += len(stored["verses"])
        self.assertEqual(total_verses, self.reader["unit_count"])
        self.assertIn("re-parsing all 50 retained HTML pages reproduces", self.reader["verification_status"])
        self.assertIn("not HaCohen's transcription", self.reader["verification_status"])

    def test_observed_verse_label_gaps_are_preserved_and_disclosed(self):
        expected_gaps = {6: [20], 10: [12], 19: [23], 22: [4], 35: [21], 40: [4]}
        observed_gaps = {}
        for chapter in self.reader["chapters"]:
            labels = [verse["number"] for verse in chapter["verses"]]
            missing = [number for number in range(labels[0], labels[-1] + 1) if number not in labels]
            if missing:
                observed_gaps[chapter["chapter"]] = missing
        self.assertEqual(observed_gaps, expected_gaps)
        note = self.reader["chapter_structure_note"]
        for chapter, labels in expected_gaps.items():
            with self.subTest(chapter=chapter):
                self.assertIn(f"{chapter} ({labels[0]})", note)
        self.assertIn("not independently verified textual lacunae", note)
        self.assertIn("without regularizing or filling them", note)


if __name__ == "__main__":
    unittest.main()
