"""Exodus' stored Geʽez reader must reproduce its retained source captures."""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

from build_exodus_geez import CAPTURE, INDEX, OUTPUT, SOURCE_DIR, load_capture, parse_chapter
from build_brenton_exodus import EXODUS_COMPANION_NOTE, ensure_note_once


class ExodusGeezCaptureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reader = json.loads(OUTPUT.read_text(encoding="utf-8"))
        cls.capture = json.loads(CAPTURE.read_text(encoding="utf-8"))
        cls.index = INDEX.read_text(encoding="utf-8-sig")

    def test_archived_index_and_capture_cover_all_forty_chapters_in_order(self):
        chapters = [int(value) for value in re.findall(r"Octateuch/Exodus (\d+)\.html", self.index)]
        self.assertEqual(chapters, list(range(1, 41)))
        rows = load_capture()
        self.assertEqual([row["chapter"] for row in rows], list(range(1, 41)))
        self.assertEqual(self.reader["chapter_count"], 40)
        self.assertEqual(
            self.reader["parallel_translation"]["translation_id"],
            "exodus-english-brenton-lxx-1851",
        )

    def test_all_forty_retained_pages_reproduce_the_stored_reader_records(self):
        rows = {row["chapter"]: row for row in load_capture()}
        self.assertEqual(len(self.reader["chapters"]), 40)
        total_verses = 0
        for chapter_number, stored in enumerate(self.reader["chapters"], start=1):
            with self.subTest(chapter=chapter_number):
                row = rows[chapter_number]
                raw_path = SOURCE_DIR / f"Exodus_{chapter_number:02d}.html"
                self.assertTrue(raw_path.is_file(), raw_path)
                self.assertEqual(raw_path.read_bytes(), row["html"].encode("utf-8"))
                reproduced = parse_chapter(row)
                self.assertEqual(stored, reproduced)
                self.assertEqual(stored["chapter"], chapter_number)
                self.assertTrue(stored["verses"])
                total_verses += len(stored["verses"])
        self.assertEqual(total_verses, self.reader["unit_count"])
        self.assertIn("re-parsing all 40 retained HTML pages reproduces", self.reader["verification_status"])
        self.assertIn("not HaCohen's transcription", self.reader["verification_status"])

    def test_generated_companion_note_is_idempotent(self):
        note = EXODUS_COMPANION_NOTE
        value = ensure_note_once(f"Base note. {note} {note}", note)
        self.assertEqual(value.count(note), 1)
        self.assertEqual(ensure_note_once(value, note), value)
        self.assertEqual(self.reader["chapter_structure_note"].count(note), 1)


if __name__ == "__main__":
    unittest.main()
