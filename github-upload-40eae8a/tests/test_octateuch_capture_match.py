import json
import unittest
from pathlib import Path

from build_octateuch_readers import BOOKS, SOURCE_ROOT, load_capture, parse_chapter


ROOT = Path(__file__).resolve().parents[1]


class OctateuchCaptureMatchTests(unittest.TestCase):
    def test_all_eight_reader_notes_describe_the_digitizer_numbering(self):
        reader_ids = [
            "genesis-geez-dillmann-hacohen",
            "exodus-geez-dillmann-hacohen",
            *(f"{book['slug']}-geez-dillmann-hacohen" for book in BOOKS),
        ]
        archive = json.loads((ROOT / "archive.json").read_text(encoding="utf-8"))
        readers = {reader["reader_id"]: reader for reader in archive["readers"]}
        for reader_id in reader_ids:
            with self.subTest(reader=reader_id):
                note = readers[reader_id]["chapter_structure_note"]
                self.assertIn("replaces Dillmann's Ethiopic verse numerals with Arabic numerals", note)
                self.assertIn("follows the Septuagint", note)
                self.assertIn("may be discontinuous", note)
                self.assertIn("without regularizing", note)
                self.assertNotIn("retained as published", note)

    def test_all_146_archived_pages_reproduce_the_bundled_chapter_records(self):
        capture = load_capture()
        page_total = 0
        for book in BOOKS:
            reader_path = ROOT / "readers" / f"{book['slug']}-geez.json"
            reader = json.loads(reader_path.read_text(encoding="utf-8"))
            self.assertEqual(reader["chapter_count"], book["count"], book["name"])
            for chapter_number in range(1, book["count"] + 1):
                with self.subTest(book=book["name"], chapter=chapter_number):
                    page = capture[(book["source"], chapter_number)]
                    raw_page_path = SOURCE_ROOT / book["slug"] / f"{book['source']}_{chapter_number:02d}.html"
                    raw_bytes = page["html"].encode("utf-8")
                    self.assertEqual(raw_page_path.read_bytes(), raw_bytes)
                    parsed = parse_chapter(book, page)
                    stored = reader["chapters"][chapter_number - 1]
                    self.assertEqual(stored, parsed)
                page_total += 1
        self.assertEqual(page_total, 146)


if __name__ == "__main__":
    unittest.main()
