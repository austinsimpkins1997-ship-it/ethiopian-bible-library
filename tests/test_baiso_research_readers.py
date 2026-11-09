"""Check the Baiso editions against their retained, signed USFM packages."""

from __future__ import annotations

import json
import re
import unittest
import zipfile
from pathlib import Path

from build_baiso_research_readers import EDITION_CONFIG, BOOK_ORDER, SOURCE_DIR, build
import build_maale_research_readers as maale

ROOT = Path(__file__).resolve().parents[1]


class BaisoResearchReaderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.readers, cls.corpora, cls.sources, cls.manifests = build()

    def test_both_provider_packages_and_signed_hash_lists(self):
        self.assertEqual(len(self.manifests), 2)
        for config, manifest in zip(EDITION_CONFIG, self.manifests):
            package = SOURCE_DIR / f"{config['edition_id']}_usfm.zip"
            with zipfile.ZipFile(package) as archive:
                self.assertIsNone(archive.testzip())
                self.assertEqual(archive.read("signature.txt.asc") is not None, True)
                signature = maale.verify_checksum_signature(archive.read("keys.asc"), archive.read("signature.txt.asc"))
                self.assertTrue(signature["valid"])
                self.assertEqual(signature["signer_fingerprint"], "54D714D76956DA6673DC1EEA5F62009D93505F26")
            self.assertEqual(manifest["archive_sha256"], config["expected_sha256"])
            self.assertEqual(manifest["usfm_book_count"], len(config["expected_codes"]))
            self.assertEqual([row["book_code"] for row in manifest["usfm_members"]], config["expected_codes"])
            self.assertEqual(manifest["zip_crc_check"], "passed")
            self.assertTrue(all(reader["source_package_sha256"] == manifest["archive_sha256"] for reader in self.readers if reader["source_pages"].startswith(f"readers/source/baiso/{config['edition_id']}_")))

    def test_exact_source_chapter_and_verse_labels_match_reader(self):
        for config in EDITION_CONFIG:
            with zipfile.ZipFile(SOURCE_DIR / f"{config['edition_id']}_usfm.zip") as package:
                for source_name in package.namelist():
                    if not source_name.lower().endswith(".usfm"):
                        continue
                    parsed = maale.parse_book(package.read(source_name), source_name)
                    reader_id = f"baiso-{config['key']}-{parsed['code'].lower()}-research"
                    reader = next(item for item in self.readers if item["reader_id"] == reader_id)
                    self.assertEqual(len(reader["chapters"]), parsed["chapter_count"], source_name)
                    for observed, source in zip(reader["chapters"], parsed["chapters"]):
                        self.assertEqual(str(observed["chapter"]), str(source["chapter"]), source_name)
                        self.assertEqual(
                            [verse["number"] for verse in observed["verses"]],
                            [verse["number"] for verse in source["verses"]],
                            f"{source_name} chapter {source['chapter']}",
                        )
                    self.assertEqual(reader["unit_count"], parsed["unit_count"], source_name)

    def test_latin_package_gaps_remain_explicit_and_unfilled(self):
        latin, ethiopic = self.manifests
        self.assertEqual(latin["usfm_book_count"], 16)
        self.assertEqual(ethiopic["usfm_book_count"], 27)
        self.assertEqual(latin["absent_conventional_module_codes"], [code for code in BOOK_ORDER if code not in EDITION_CONFIG[0]["expected_codes"]])
        self.assertEqual(ethiopic["absent_conventional_module_codes"], [])
        latin_readers = [reader for reader in self.readers if reader["script_code"] == "Latn"]
        self.assertEqual(len(latin_readers), 16)
        self.assertTrue(all(reader["canon_id"] is None and reader["language_tag"] == "bsw" for reader in self.readers))
        self.assertTrue(all(reader["rights_classification"] == "open_license" and reader["license_id"] == "CC-BY-SA-4.0" for reader in self.readers))

    def test_intro_list_marker_is_preserved_as_source_structure(self):
        readers = [reader for reader in self.readers if reader["script_code"] == "Latn"]
        self.assertTrue(any(item["marker"] == "ili1" for reader in readers for item in reader["front_matter"]))

    def test_language_registry_and_notices_keep_scope_and_provenance(self):
        registry = json.loads((ROOT / "translation-registry.json").read_text(encoding="utf-8"))
        profile = next(item for item in registry["languages"] if item["language_tag"] == "bsw")
        self.assertEqual(set(profile["script_codes"]), {"Ethi", "Latn"})
        self.assertEqual(profile["availability_survey"]["result_count"], 2)
        self.assertIn("not a language-wide", profile["availability_survey"]["scope"])
        corpus_ids = {item["corpus_id"] for item in registry["research_corpora"]}
        self.assertTrue({reader["research_corpus_id"] for reader in self.readers} <= corpus_ids)
        source_ids = {item["source_id"] for item in json.loads((ROOT / "archive.json").read_text(encoding="utf-8"))["sources"]}
        self.assertTrue({"SRC-410", "SRC-411", "SRC-412", "SRC-413", "SRC-077", "SRC-078"} <= source_ids)
        notice = (SOURCE_DIR / "SOURCE-NOTICE.txt").read_text(encoding="utf-8")
        self.assertIn("The Latin-script package's missing conventional module codes are recorded", notice)
        self.assertIn("No individual translator", notice)


if __name__ == "__main__":
    unittest.main()
