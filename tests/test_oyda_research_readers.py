import json
import re
import unittest
import zipfile
from pathlib import Path

from build_oyda_research_readers import (
    EXPECTED_CODES,
    EXPECTED_PACKAGE_SHA256,
    SOURCE,
    build,
)
from build_brenton_octateuch import clean_usfm


ROOT = Path(__file__).resolve().parents[1]


class OydaResearchReaderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.readers, cls.corpora, cls.sources, cls.manifest = build()

    def test_source_package_crc_signed_hashes_and_book_inventory(self):
        self.assertEqual(self.manifest["archive_sha256"], EXPECTED_PACKAGE_SHA256)
        self.assertEqual(self.manifest["usfm_book_count"], 27)
        self.assertEqual(self.manifest["member_count"], 31)
        self.assertEqual(self.manifest["signed_member_count"], 29)
        self.assertTrue(self.manifest["signature"]["valid"])
        self.assertEqual(self.manifest["signature"]["signer_fingerprint"], "54D714D76956DA6673DC1EEA5F62009D93505F26")
        self.assertEqual([item["book_code"] for item in self.manifest["usfm_members"]], EXPECTED_CODES)
        with zipfile.ZipFile(SOURCE) as archive:
            self.assertIsNone(archive.testzip())

    def test_every_publisher_verse_label_is_retained_in_order(self):
        with zipfile.ZipFile(SOURCE) as package:
            for reader, code in zip(self.readers, EXPECTED_CODES):
                member_name = next(name for name in package.namelist() if name.endswith(f"-{code}oyde.usfm"))
                source_text = package.read(member_name).decode("utf-8-sig")
                expected = [match.group(1) for match in re.finditer(r"^\\v\s+(\S+)", source_text, re.M)]
                observed = [verse["number"] for chapter in reader["chapters"] for verse in chapter["verses"]]
                self.assertEqual(observed, expected, code)
                self.assertEqual(reader["unit_count"], len(expected), code)
                self.assertEqual(
                    [chapter["chapter"] for chapter in reader["chapters"]],
                    list(range(1, reader["chapter_count"] + 1)),
                    code,
                )

    def test_records_are_research_only_and_preserve_source_language_context(self):
        self.assertEqual(len(self.readers), 27)
        self.assertEqual(len(self.corpora), 27)
        self.assertEqual([source["source_id"] for source in self.sources], ["SRC-400", "SRC-401", "SRC-402"])
        self.assertEqual(sum(reader["chapter_count"] for reader in self.readers), 260)
        self.assertEqual(sum(reader["unit_count"] for reader in self.readers), 7931)
        self.assertTrue(all(reader["canon_id"] is None for reader in self.readers))
        self.assertTrue(all(item["canon_mapping_state"] == "not_mapped" for item in self.corpora))
        self.assertTrue(all(item["candidate_canon_id"] is None for item in self.corpora))
        self.assertTrue(all(reader["language_tag"] == "oyd" and reader["script_code"] == "Ethi" for reader in self.readers))
        self.assertTrue(all(reader["translation_basis_status"] == "unknown" for reader in self.readers))
        self.assertTrue(all(reader["rights_classification"] == "open_license" for reader in self.readers))
        self.assertTrue(all(reader["license_id"] == "CC-BY-SA-4.0" for reader in self.readers))

    def test_retained_provenance_menu_and_language_profile(self):
        menu = json.loads((ROOT / "research" / "oyda-menu.json").read_text(encoding="utf-8"))
        self.assertEqual([entry["book_code"] for entry in menu["entries"]], EXPECTED_CODES)
        self.assertEqual(menu["canon_mapping_state"], "not_mapped")
        self.assertTrue((ROOT / "research" / "oyda-menu.html").is_file())
        self.assertTrue((ROOT / "readers" / "source" / "oyda" / "SOURCE-NOTICE.txt").is_file())
        registry = json.loads((ROOT / "translation-registry.json").read_text(encoding="utf-8"))
        profile = next(item for item in registry["languages"] if item["language_tag"] == "oyd")
        self.assertIn("Ethi", profile["script_codes"])
        self.assertEqual(profile["availability_survey"]["status"], "completed")
        self.assertIn("not a language-wide census", profile["availability_survey"]["scope"])
        source_ids = {item["source_id"] for item in json.loads((ROOT / "archive.json").read_text(encoding="utf-8"))["sources"]}
        self.assertTrue(set(profile["source_ids"]) <= source_ids)

    def test_introduction_outline_reference_marker_text_is_rendered_without_rewriting_source(self):
        self.assertEqual(clean_usfm(r"\ior An outline label\ior*"), "An outline label")
        with zipfile.ZipFile(SOURCE) as package:
            raw = package.read("46-MAToyde.usfm").decode("utf-8-sig")
        self.assertIn(r"\ior", raw)
        reader = next(item for item in self.readers if item["reader_id"] == "oyda-mat-research")
        display_strings = [item.get("text", "") for item in reader["front_matter"]]
        self.assertTrue(any("1:1—2:23" in item for item in display_strings))


if __name__ == "__main__":
    unittest.main()
