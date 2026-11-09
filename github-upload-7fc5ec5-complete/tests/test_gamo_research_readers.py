import unittest
import zipfile

import build_gamo_research_readers as gamo


class GamoResearchReadersTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.readers, cls.corpora, cls.coverage = gamo.build_readers()
        cls.by_code = {
            row["reader_id"].removeprefix("gamo-").removesuffix("-research"): row
            for row in cls.readers
        }

    def test_source_html_snapshot_hash_and_menu_scope(self):
        self.assertEqual(len(self.readers), 66)
        self.assertEqual(len(self.corpora), 66)
        self.assertEqual(sum(row["chapter_count"] for row in self.readers), 1189)
        self.assertEqual(sum(row["unit_count"] for row in self.readers), 30906)

    def test_genesis_source_labels_notes_and_text_are_retained(self):
        genesis = self.by_code["gen"]
        self.assertEqual(genesis["language_tag"], "gmv")
        self.assertEqual(genesis["script_code"], "Ethi")
        self.assertEqual(genesis.get("canon_id"), None)
        self.assertEqual(genesis["translation_basis_status"], "unknown")
        self.assertNotIn("basis_language_tag", genesis)
        self.assertNotIn("translation_path", genesis)
        self.assertIn("does not identify the source language", genesis["translation_basis_note"])
        chapter_one = genesis["chapters"][0]
        self.assertEqual(chapter_one["chapter"], 1)
        self.assertEqual(chapter_one["units"][0]["text"], "ጾሲ ኮይሮ ሳሎኔ ሳኣ ሜꬊዴስ።")
        combined = next(unit for unit in chapter_one["units"] if unit["source_marker"] == "6-7")
        self.assertEqual(combined["source_element_id"], "V6")
        self.assertIn("2ቆሮ 4፡6", [note["text"] for note in chapter_one["notes"]])

    def test_chapter_pages_and_source_labels_are_unique_and_present(self):
        with zipfile.ZipFile(gamo.SOURCE_ZIP) as source:
            self.assertFalse(any(name.lower().endswith((".png", ".jpg", ".jpeg", ".css", ".ttf", ".woff")) for name in source.namelist()))
        for reader in self.readers:
            self.assertEqual(len(reader["chapters"]), reader["chapter_count"])
            self.assertEqual([chapter["chapter"] for chapter in reader["chapters"]], list(range(1, reader["chapter_count"] + 1)))
            self.assertEqual(sum(len(chapter["units"]) for chapter in reader["chapters"]), reader["unit_count"])
            self.assertTrue(all(unit["text"].strip() and unit["source_marker"] for chapter in reader["chapters"] for unit in chapter["units"]))
            page_hashes = {item["page"]: item["sha256"] for item in reader["source_page_hashes"]}
            self.assertEqual(len(page_hashes), reader["chapter_count"])
            code = reader["reader_id"].removeprefix("gamo-").removesuffix("-research").upper()
            with zipfile.ZipFile(gamo.SOURCE_ZIP) as source:
                for chapter, page_info in zip(reader["chapters"], reader["source_page_hashes"]):
                    page = page_info["page"]
                    page_bytes = source.read(page)
                    self.assertEqual(hashlib_for(page_bytes), page_hashes[page])
                    number = chapter["chapter"]
                    source_page_title, source_headings, source_units, source_notes = gamo.extract_chapter(page_bytes, code, number)
                    self.assertEqual(chapter["source_page_title"], source_page_title)
                    self.assertEqual(chapter["heading"], source_headings)
                    self.assertEqual(chapter["units"], source_units)
                    self.assertEqual(chapter["notes"], source_notes)
            self.assertEqual(reader["reader_scope"], "research_witness_unmapped")
            self.assertEqual(reader["license_id"], "CC-BY-SA-4.0")


def hashlib_for(payload):
    import hashlib
    return hashlib.sha256(payload).hexdigest()


if __name__ == "__main__":
    unittest.main()
