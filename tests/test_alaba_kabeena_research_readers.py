"""Verify the Alaba-K’abeena research readers against their retained source ZIP."""

from __future__ import annotations

import json
import hashlib
import unittest
import zipfile
from pathlib import Path

import build_maale_research_readers as maale
from build_alaba_kabeena_research_readers import (
    ARC_2015_PAGE,
    ARC_2015_SHA256,
    ARC_2015_SOURCE_ID,
    EXPECTED_CODES,
    EXPECTED_PACKAGE_SHA256,
    SOURCE,
    SOURCE_DIR,
    build,
)

ROOT = Path(__file__).resolve().parents[1]


class AlabaKabeenaResearchReaderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.readers, cls.corpora, cls.sources, cls.manifest = build()

    def test_signed_source_archive_and_complete_module_inventory(self):
        self.assertEqual(self.manifest["archive_sha256"], EXPECTED_PACKAGE_SHA256)
        self.assertEqual(self.manifest["usfm_book_count"], 27)
        self.assertEqual([row["book_code"] for row in self.manifest["usfm_members"]], EXPECTED_CODES)
        self.assertEqual(self.manifest["member_count"], 31)
        self.assertEqual(self.manifest["zip_crc_check"], "passed")
        with zipfile.ZipFile(SOURCE) as package:
            self.assertIsNone(package.testzip())
            signature = maale.verify_checksum_signature(package.read("keys.asc"), package.read("signature.txt.asc"))
        self.assertTrue(signature["valid"])
        self.assertEqual(signature["signer_fingerprint"], "54D714D76956DA6673DC1EEA5F62009D93505F26")

    def test_each_source_member_reproduces_reader_text_and_labels(self):
        with zipfile.ZipFile(SOURCE) as package:
            for reader, code in zip(self.readers, EXPECTED_CODES):
                member = next(name for name in package.namelist() if name.endswith(f"-{code}alw.usfm"))
                parsed = maale.parse_book(package.read(member), member)
                self.assertEqual(reader["chapter_count"], parsed["chapter_count"], code)
                self.assertEqual(reader["unit_count"], parsed["unit_count"], code)
                for observed, source in zip(reader["chapters"], parsed["chapters"]):
                    self.assertEqual(str(observed["chapter"]), str(source["chapter"]), code)
                    self.assertEqual(observed["verses"], source["verses"], f"{code} chapter {source['chapter']}")

    def test_rights_language_script_and_canon_scope_are_explicit(self):
        self.assertEqual(len(self.readers), 27)
        self.assertEqual(sum(reader["chapter_count"] for reader in self.readers), 260)
        self.assertEqual(sum(reader["unit_count"] for reader in self.readers), 7917)
        self.assertTrue(all(reader["language_tag"] == "alw" and reader["script_code"] == "Ethi" for reader in self.readers))
        self.assertTrue(all(reader["canon_id"] is None and reader["rights_classification"] == "open_license" for reader in self.readers))
        self.assertTrue(all(reader["license_id"] == "CC-BY-SA-4.0" and reader["source_ids"] == ["SRC-414", "SRC-415"] for reader in self.readers))
        self.assertTrue(all(reader["translation_basis_status"] == "unknown" for reader in self.readers))
        self.assertTrue(all(reader["translator"].startswith("Not named") for reader in self.readers))
        registry = json.loads((ROOT / "translation-registry.json").read_text(encoding="utf-8"))
        by_corpus = {item["corpus_id"]: item for item in registry["research_corpora"]}
        self.assertTrue(all(
            by_corpus[reader["research_corpus_id"]]["canon_mapping_state"] == "reviewed_match"
            and by_corpus[reader["research_corpus_id"]]["candidate_canon_id"]
            and reader["canon_id"] is None
            for reader in self.readers
        ))

    def test_menu_notices_registry_and_source_records_are_connected(self):
        menu = json.loads((ROOT / "research/alaba-kabeena-menu.json").read_text(encoding="utf-8"))
        self.assertEqual([item["book_code"] for item in menu["entries"]], EXPECTED_CODES)
        self.assertEqual(menu["canon_mapping_state"], "reviewed_match")
        self.assertEqual(menu["canon_crosswalk_source_ids"], ["SRC-029", "SRC-396"])
        self.assertEqual(len({item["candidate_canon_id"] for item in menu["entries"]}), 27)
        html_menu = (ROOT / "research/alaba-kabeena-menu.html").read_text(encoding="utf-8")
        self.assertIn("alaba-kabeena-mat-research", html_menu)
        self.assertIn("Title match: Matthew · MAT", html_menu)
        notice = (SOURCE_DIR / "SOURCE-NOTICE.txt").read_text(encoding="utf-8")
        self.assertIn("no individual translator", notice)
        registry = json.loads((ROOT / "translation-registry.json").read_text(encoding="utf-8"))
        profile = next(item for item in registry["languages"] if item["language_tag"] == "alw")
        self.assertEqual(profile["script_codes"], ["Ethi"])
        self.assertEqual(profile["availability_survey"]["result_count"], 1)
        self.assertIn("not a language-wide", profile["availability_survey"]["scope"])
        self.assertTrue({reader["research_corpus_id"] for reader in self.readers} <= {item["corpus_id"] for item in registry["research_corpora"]})
        archive_sources = {item["source_id"] for item in json.loads((ROOT / "archive.json").read_text(encoding="utf-8"))["sources"]}
        archive = json.loads((ROOT / "archive.json").read_text(encoding="utf-8"))
        self.assertTrue({"SRC-414", "SRC-415", "SRC-077", "SRC-078", ARC_2015_SOURCE_ID} <= archive_sources)
        self.assertTrue(all(ARC_2015_SOURCE_ID not in reader["source_ids"] for reader in self.readers))
        source = next(item for item in archive["sources"] if item["source_id"] == ARC_2015_SOURCE_ID)
        self.assertEqual(source["local_copy_url"], "readers/source/alaba-kabeena/arc-2015.html")
        self.assertEqual(hashlib.sha256((ROOT / source["local_copy_url"]).read_bytes()).hexdigest(), ARC_2015_SHA256)
        self.assertEqual(source["rights_classification"], "unknown")
        self.assertIn("relationship between this 2015", source["inspection_and_limitations"])
        self.assertIn(ARC_2015_SOURCE_ID, profile["source_ids"])
        self.assertNotIn(ARC_2015_SOURCE_ID, profile["availability_survey"]["source_ids"])
        historical = next(item for item in registry["corpus_leads"] if item["corpus_id"] == "alw-2015-halaba-new-testament-metadata")
        self.assertFalse(historical["text_bundled"])
        self.assertEqual(historical["source_ids"], [ARC_2015_SOURCE_ID])
        self.assertEqual(historical["basis_language_tag"], "und")
        self.assertIsNone(historical["translation_path"])
        self.assertEqual(historical["rights_classification"], "unknown")
        self.assertIn("do not establish that it is an earlier edition", historical["notes"])


if __name__ == "__main__":
    unittest.main()
