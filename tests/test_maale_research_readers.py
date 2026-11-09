import json
import re
import unittest
import zipfile
from pathlib import Path

from build_maale_research_readers import BOOK_NAMES, SOURCE, build


ROOT = Path(__file__).resolve().parents[1]


class MaaleResearchReaderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.readers, cls.corpora, cls.sources, cls.manifest = build()

    def test_publisher_package_inventory_and_member_hashes_are_verified(self):
        self.assertEqual(len(BOOK_NAMES), 66)
        self.assertEqual(self.manifest["usfm_book_count"], 66)
        self.assertEqual(self.manifest["member_count"], 66)
        self.assertTrue(self.manifest["signature"]["valid"])
        self.assertEqual(self.manifest["signature"]["signer_fingerprint"], "54D714D76956DA6673DC1EEA5F62009D93505F26")
        self.assertIn("legacy", self.manifest["signature"]["signature_hash_algorithm"])
        self.assertIn("not independently establish identity", self.manifest["signature"]["key_identity_limit"])
        self.assertIn("GnuPG verified", self.manifest["verification"])
        with zipfile.ZipFile(SOURCE) as package:
            self.assertIsNone(package.testzip())

    def test_every_publisher_verse_label_is_preserved_in_order(self):
        with zipfile.ZipFile(SOURCE) as package:
            for reader in self.readers:
                code = reader["reader_id"].removeprefix("maale-").removesuffix("-research").upper()
                member_name = next(name for name in package.namelist() if name.endswith(f"-{code}mdyeth.usfm"))
                source_text = package.read(member_name).decode("utf-8-sig")
                source_labels = [match.group(1) for match in re.finditer(r"^\\v\s+(\S+)", source_text, re.M)]
                reader_labels = [
                    verse["number"]
                    for chapter in reader["chapters"]
                    for verse in chapter["verses"]
                ]
                self.assertEqual(reader_labels, source_labels, code)
                self.assertEqual(reader["unit_count"], len(source_labels), code)
                self.assertEqual([item["chapter"] for item in reader["chapters"]], list(range(1, reader["chapter_count"] + 1)), code)

    def test_notes_figures_and_front_matter_are_retained_as_bounded_records(self):
        with zipfile.ZipFile(SOURCE) as package:
            expected_note_openers = 0
            expected_figures = 0
            for name in package.namelist():
                if not name.endswith(".usfm"):
                    continue
                text = package.read(name).decode("utf-8-sig")
                expected_note_openers += len(re.findall(r"\\[fx]\b(?!\*)", text))
                expected_figures += len(re.findall(r"\\fig\b(?!\*)", text))
        actual_notes = sum(len(chapter.get("notes", [])) for reader in self.readers for chapter in reader["chapters"])
        actual_figures = sum(
            note.get("note_type") == "source_asset_omitted"
            for reader in self.readers for chapter in reader["chapters"] for note in chapter.get("notes", [])
        )
        self.assertEqual(actual_notes, expected_note_openers + expected_figures)
        self.assertEqual(actual_figures, expected_figures)
        self.assertTrue(any(reader["front_matter"] for reader in self.readers))

    def test_all_maale_records_remain_separate_from_the_eotc_and_eritrean_canons(self):
        self.assertEqual(len(self.readers), 66)
        self.assertEqual(len(self.corpora), 66)
        self.assertEqual(len(self.sources), 6)
        self.assertEqual([source["source_id"] for source in self.sources[-3:]], ["SRC-372", "SRC-373", "SRC-374"])
        self.assertTrue(all(reader["canon_id"] is None for reader in self.readers))
        self.assertTrue(all(item["canon_mapping_state"] == "not_mapped" for item in self.corpora))
        self.assertTrue(all(item["candidate_canon_id"] is None for item in self.corpora))
        self.assertTrue(all(reader["language_tag"] == "mdy" and reader["script_code"] == "Ethi" for reader in self.readers))
        self.assertEqual(sum(reader["unit_count"] for reader in self.readers), 30506)
        self.assertTrue(all(reader["rights_classification"] == "open_license" for reader in self.readers))
        self.assertTrue(all("Change made:" in reader["copyright_notice"] for reader in self.readers))

    def test_original_source_is_retained_with_language_and_rights_provenance(self):
        source_path = ROOT / "readers" / "source" / "maale" / "mdyeth_usfm.zip"
        self.assertTrue(source_path.is_file())
        language = json.loads((ROOT / "translation-registry.json").read_text(encoding="utf-8"))
        profile = next(item for item in language["languages"] if item["language_tag"] == "mdy")
        self.assertIn("Ethi", profile["script_codes"])
        self.assertIn("SRC-363", profile["source_ids"])
        self.assertIn("SRC-364", profile["source_ids"])
        self.assertIn("SRC-372", profile["source_ids"])
        self.assertIn("SRC-373", profile["source_ids"])
        self.assertIn("SRC-374", profile["source_ids"])

    def test_maale_rights_history_and_distinct_product_identity_are_disclosed(self):
        sources = {item["source_id"]: item for item in self.sources}
        self.assertIn("CC BY-ND 4.0", sources["SRC-372"]["inspection_and_limitations"])
        self.assertIn("2024-02-21", sources["SRC-372"]["inspection_and_limitations"])
        self.assertIn("SRC-373", sources["SRC-363"]["inspection_and_limitations"])
        self.assertIn("RESERVED", sources["SRC-373"]["inspection_and_limitations"])
        self.assertIn("Tamene Lale Gego", sources["SRC-374"]["inspection_and_limitations"])
        self.assertIn("does not date the translation", sources["SRC-374"]["inspection_and_limitations"])
        notice = (ROOT / "readers" / "source" / "maale" / "SOURCE-NOTICE.txt").read_text(encoding="utf-8")
        self.assertIn("No legal conclusion about license history", notice)
        self.assertTrue((ROOT / "research" / "gamo-maale-provenance.html").is_file())
        index = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn('href="research/gamo-maale-provenance.html"', index)


if __name__ == "__main__":
    unittest.main()
