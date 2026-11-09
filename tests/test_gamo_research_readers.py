import json
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
        cls.corpora_by_reader = {row["reader_id"]: row for row in cls.corpora}

    def test_source_html_snapshot_hash_and_menu_scope(self):
        self.assertEqual(len(self.readers), 66)
        self.assertEqual(len(self.corpora), 66)
        self.assertEqual(sum(row["chapter_count"] for row in self.readers), 1189)
        self.assertEqual(sum(row["unit_count"] for row in self.readers), 30906)

    def test_all_standard_new_testament_entries_have_scoped_reviewed_title_matches(self):
        self.assertEqual(len(gamo.REVIEWED_NT_CODES), 27)
        for code, canon_id in gamo.REVIEWED_NT_CODES.items():
            reader = self.by_code[code.lower()]
            corpus = self.corpora_by_reader[reader["reader_id"]]
            self.assertEqual(corpus["canon_mapping_state"], "reviewed_match")
            self.assertEqual(corpus["candidate_canon_id"], canon_id)
            self.assertEqual(reader["reader_scope"], "research_witness_reviewed_title_match")
            self.assertIsNone(reader.get("canon_id"))
            self.assertIn("work/title crosswalk only", corpus["canon_mapping_note"])
            self.assertIn("SRC-029", corpus["source_ids"])
            self.assertIn("SRC-396", corpus["source_ids"])
            self.assertIn("does not establish EOTC", corpus["canon_mapping_note"])

    def test_chronicles_modules_have_reviewed_title_matches_but_remain_research_only(self):
        self.assertEqual(gamo.REVIEWED_CHRONICLES_CODES, {"1CH": "eotc-ot-11", "2CH": "eotc-ot-12"})
        for code, canon_id in gamo.REVIEWED_CHRONICLES_CODES.items():
            reader = self.by_code[code.lower()]
            corpus = self.corpora_by_reader[reader["reader_id"]]
            self.assertEqual(corpus["canon_mapping_state"], "reviewed_match")
            self.assertEqual(corpus["candidate_canon_id"], canon_id)
            self.assertEqual(reader["reader_scope"], "research_witness_reviewed_title_match")
            self.assertIsNone(reader.get("canon_id"))
            self.assertIn("Orthodox alternative title", corpus["canon_mapping_note"])
            self.assertIn("SRC-029", corpus["source_ids"])
            self.assertIn("SRC-396", corpus["source_ids"])
            self.assertIn("does not make this research reader canon-linked coverage", corpus["canon_mapping_note"])

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

    def test_agency_project_history_is_not_misused_as_edition_or_translation_path_evidence(self):
        archive = json.loads((gamo.ROOT / "archive.json").read_text(encoding="utf-8"))
        source = next(item for item in archive["sources"] if item["source_id"] == "SRC-375")
        self.assertIn("2022-10-03", source["inspection_and_limitations"])
        self.assertIn("specify a source language or relay path", source["inspection_and_limitations"])
        language = json.loads((gamo.ROOT / "translation-registry.json").read_text(encoding="utf-8"))
        profile = next(item for item in language["languages"] if item["language_tag"] == "gmv")
        self.assertIn("SRC-375", profile["source_ids"])
        self.assertTrue(all(reader["translation_basis_status"] == "unknown" for reader in self.readers))

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
            expected_scope = (
                "research_witness_reviewed_title_match"
                if code in gamo.REVIEWED_TITLE_CODES
                else "research_witness_unmapped"
            )
            self.assertEqual(reader["reader_scope"], expected_scope)
            self.assertEqual(reader["license_id"], "CC-BY-SA-4.0")


def hashlib_for(payload):
    import hashlib
    return hashlib.sha256(payload).hexdigest()


if __name__ == "__main__":
    unittest.main()
