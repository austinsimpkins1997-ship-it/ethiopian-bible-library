import json
import unittest
from pathlib import Path

from rights_metadata import VALID_RIGHTS_CLASSIFICATIONS, validate_rights_classification

ROOT = Path(__file__).resolve().parents[1]


class RightsClassificationTests(unittest.TestCase):
    def test_registry_records_have_controlled_categories_and_detail(self):
        registry = json.loads((ROOT / "translation-registry.json").read_text(encoding="utf-8"))
        records = list(registry["translation_leads"]) + list(registry["corpus_leads"])
        records += [layer for language in registry["languages"] for layer in language["records"]]
        self.assertTrue(records)
        for index, record in enumerate(records):
            with self.subTest(record=index):
                validate_rights_classification(record, f"record {index}")
                self.assertTrue(record.get("rights_status"))

    def test_bundled_reader_and_companion_rights_match_registry(self):
        archive = json.loads((ROOT / "archive.json").read_text(encoding="utf-8"))
        registry = archive["translation_registry"]
        layers = [layer for language in registry["languages"] for layer in language["records"]]
        for reader in archive["readers"]:
            with self.subTest(reader=reader["reader_id"]):
                validate_rights_classification(reader, reader["reader_id"])
                if reader.get("research_corpus_id"):
                    matching = [item for item in registry["research_corpora"] if item["reader_id"] == reader["reader_id"]]
                else:
                    matching = [item for item in layers if item.get("reader_id") == reader["reader_id"] and not item.get("translation_id")]
                self.assertEqual(len(matching), 1)
                self.assertEqual(reader["rights_classification"], matching[0]["rights_classification"])
                companion = reader.get("parallel_translation")
                if companion:
                    validate_rights_classification(companion, companion["translation_id"])
                    translation = [item for item in layers if item.get("translation_id") == companion["translation_id"]]
                    self.assertEqual(len(translation), 1)
                    self.assertEqual(companion["rights_classification"], translation[0]["rights_classification"])

    def test_missing_or_invented_category_rejected(self):
        for value in (None, "clear", "probably public domain"):
            with self.subTest(value=value):
                with self.assertRaisesRegex(ValueError, "controlled rights_classification"):
                    validate_rights_classification({"rights_classification": value}, "test lead")

    def test_unknown_is_a_valid_explicit_state(self):
        self.assertIn("unknown", VALID_RIGHTS_CLASSIFICATIONS)
        validate_rights_classification({"rights_classification": "unknown"}, "test lead")


if __name__ == "__main__":
    unittest.main()
