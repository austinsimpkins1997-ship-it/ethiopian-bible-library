import json
import hashlib
import unittest
from pathlib import Path

from build_octateuch_readers import BOOKS, SOURCE_ROOT, SourcePage, load_capture, parse_chapter


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

    def test_leviticus_18_raw_response_and_narrow_marker_normalization_are_pinned(self):
        book = next(item for item in BOOKS if item["slug"] == "leviticus")
        page = load_capture()[(book["source"], 18)]
        parsed = parse_chapter(book, page)
        labels = [verse["number"] for verse in parsed["verses"]]
        self.assertEqual(labels[0], 1)
        self.assertEqual(labels[-1], 30)
        self.assertEqual(len(labels), 30)
        self.assertTrue(parsed["verses"][0]["text"])
        self.assertNotIn("\ufffd", "".join(item["text"] for item in parsed["verses"]))
        self.assertEqual(page["html"].count("\u00a0"), 6)
        self.assertNotIn("\ufffd", page["html"])
        self.assertIn("source_label_observations", parsed)
        self.assertIn("three nonbreaking spaces", parsed["source_label_observations"][0])

        capture_data = json.loads((SOURCE_ROOT / "capture.json").read_text(encoding="utf-8"))
        audit = capture_data["http_response_captures"][0]
        raw_path = ROOT / audit["local_raw_response_path"]
        raw_response = raw_path.read_bytes()
        self.assertEqual(len(raw_response), audit["response_bytes"])
        self.assertEqual(hashlib.sha256(raw_response).hexdigest(), audit["response_sha256"])
        self.assertEqual(raw_response.count(b"\xa0"), 6)
        self.assertEqual(raw_response.replace(b"\xa0", b"\xc2\xa0").decode("utf-8"), page["html"])

        archive = json.loads((ROOT / "archive.json").read_text(encoding="utf-8"))
        source = next(item for item in archive["sources"] if item["source_id"] == "SRC-064")
        self.assertEqual(source["local_copy_url"], audit["local_raw_response_path"])
        self.assertEqual(source["local_metadata_url"], "readers/source/octateuch-additional/capture.json")
        self.assertIn("reader recognizes the trailing displayed numeral as verse 1", source["inspection_and_limitations"])

    def test_malformed_expected_verse_link_cannot_be_silently_skipped(self):
        parser = SourcePage(18, "Lev")
        with self.assertRaisesRegex(ValueError, "Malformed expected verse reference"):
            parser.feed(
                '<p><a href="https://www.biblegateway.com/passage/?search=Lev+18%3Axx">x</a> Text.</p>'
            )


if __name__ == "__main__":
    unittest.main()
