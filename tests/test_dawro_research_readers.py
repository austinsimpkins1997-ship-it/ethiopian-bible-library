import json
import re
import unittest
import zipfile
from pathlib import Path

from build_brenton_octateuch import clean_usfm
from build_dawro_research_readers import (
    EXPECTED_PACKAGE_SHA256,
    SOURCE,
    build,
    expected_source_labels,
)


ROOT = Path(__file__).resolve().parents[1]


class DawroResearchReaderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.readers, cls.corpora, cls.sources, cls.manifest = build()

    def test_pinned_zip_signature_crc_and_module_inventory(self):
        self.assertEqual(self.manifest["archive_sha256"], EXPECTED_PACKAGE_SHA256)
        self.assertEqual(self.manifest["zip_member_count"], 70)
        self.assertEqual(self.manifest["signed_member_count"], 68)
        self.assertEqual(self.manifest["usfm_book_count"], 66)
        self.assertTrue(self.manifest["signature"]["valid"])
        self.assertEqual(
            self.manifest["signature"]["signer_fingerprint"],
            "54D714D76956DA6673DC1EEA5F62009D93505F26",
        )
        self.assertIn("not independently", self.manifest["signature"]["key_identity_limit"])
        with zipfile.ZipFile(SOURCE) as package:
            self.assertIsNone(package.testzip())
            self.assertEqual(len(package.namelist()), 70)
            self.assertEqual(sum(name.endswith(".usfm") for name in package.namelist()), 66)

    def test_every_reader_retains_its_source_chapter_and_verse_labels_in_order(self):
        by_code = {item["book_code"]: item for item in self.manifest["usfm_members"]}
        with zipfile.ZipFile(SOURCE) as package:
            for reader in self.readers:
                code = reader["reader_id"].removeprefix("dawro-latin-").removesuffix("-research").upper()
                member = by_code[code]["member_name"]
                raw = package.read(member)
                source_pairs = expected_source_labels(raw, member)
                reader_pairs = [
                    (chapter["chapter"], verse["number"])
                    for chapter in reader["chapters"]
                    for verse in chapter["verses"]
                ]
                self.assertEqual(reader_pairs, source_pairs, code)
                source_chapters = [int(x) for x in re.findall(rb"^\\c\s+(\d+)", raw, re.M)]
                self.assertEqual(source_chapters, list(range(1, reader["chapter_count"] + 1)), code)
                self.assertEqual(reader["unit_count"], len(source_pairs), code)

    def test_readers_are_openly_licensed_research_layers_with_unknowns_preserved(self):
        self.assertEqual((len(self.readers), len(self.corpora)), (66, 66))
        self.assertEqual(self.manifest["totals"], {"chapter_markers": 1189, "observed_verse_labels": 30815})
        self.assertEqual([source["source_id"] for source in self.sources], ["SRC-403", "SRC-404", "SRC-405", "SRC-406"])
        for reader, corpus in zip(self.readers, self.corpora):
            self.assertIsNone(reader["canon_id"])
            self.assertEqual(corpus["canon_mapping_state"], "not_mapped")
            self.assertIsNone(corpus["candidate_canon_id"])
            self.assertEqual((reader["language_tag"], reader["script_code"]), ("dwr", "Latn"))
            self.assertEqual(reader["translation_basis_status"], "unknown")
            self.assertEqual(reader["rights_classification"], "open_license")
            self.assertEqual(reader["license_id"], "CC-BY-SA-4.0")
            self.assertEqual(reader["translator"], "Not identified on the publisher's edition page.")
            self.assertIn("The Word for the World International", reader["contributor"])
            self.assertIn("Change made:", reader["copyright_notice"])
            self.assertTrue(reader["chapters"])
        self.assertIn("not a print completeness audit", self.manifest["limits"])
        self.assertIn("source/relay language", self.manifest["limits"])

    def test_front_matter_and_inline_italics_are_not_silently_rejected(self):
        self.assertTrue(any(
            item["marker"] == "ipi"
            for reader in self.readers
            for item in reader["front_matter"]
        ))
        self.assertEqual(clean_usfm(r"\it italic words\it*"), "italic words")

    def test_profile_index_count_menu_and_source_records_keep_distinct_scope(self):
        registry = json.loads((ROOT / "translation-registry.json").read_text(encoding="utf-8"))
        profile = next(item for item in registry["languages"] if item["language_tag"] == "dwr")
        self.assertEqual(profile["availability_survey"]["result_count"], 3)
        self.assertEqual(profile["script_code"], "Zzzz")
        self.assertEqual(profile["script_codes"], ["Ethi", "Latn"])
        self.assertIn("not three translations", profile["script_profile_note"])
        menu = json.loads((ROOT / "research/dawro-latin-menu.json").read_text(encoding="utf-8"))
        self.assertEqual(len(menu["entries"]), 66)
        self.assertEqual(menu["canon_mapping_state"], "not_mapped")
        self.assertTrue((ROOT / "research/dawro-latin-menu.html").is_file())
        self.assertTrue((ROOT / "readers/source/dawro/SOURCE-NOTICE.txt").is_file())
        archive = json.loads((ROOT / "archive.json").read_text(encoding="utf-8"))
        source_ids = {item["source_id"] for item in archive["sources"]}
        self.assertTrue({"SRC-403", "SRC-404", "SRC-405", "SRC-406"} <= source_ids)
        self.assertEqual(sum(item["language_tag"] == "dwr" for item in archive["translation_registry"]["research_corpora"]), 66)
        lead = next(item for item in archive["translation_registry"]["corpus_leads"] if item["corpus_id"] == "ethiopia-dawro-ebible-resources")
        self.assertFalse(lead["text_bundled"])
        self.assertIn("three Dawro labels", lead["scope_description"])


if __name__ == "__main__":
    unittest.main()
