import json
import unittest
from pathlib import Path

from availability_survey import validate_availability_survey
from build_standalone import validate_closed_schema_objects
from build_tigrinya_ebible_index_check import SOURCE, apply
from rights_metadata import same_source_identity, validate_rights_classification

ROOT = Path(__file__).resolve().parents[1]


class TigrinyaEbibleIndexCheckTests(unittest.TestCase):
    def setUp(self):
        self.archive = json.loads((ROOT / "archive.json").read_text(encoding="utf-8"))
        apply(self.archive)

    def test_records_bounded_negative_search_without_claiming_absence(self):
        source = next(item for item in self.archive["sources"] if item["source_id"] == "SRC-399")
        language = next(item for item in self.archive["translation_registry"]["languages"] if item["language_tag"] == "ti")
        survey = language["availability_survey"]
        self.assertTrue(same_source_identity(source, SOURCE))
        self.assertTrue(same_source_identity(source, {**source, "rights_basis": "Updated evidence note."}))
        self.assertFalse(same_source_identity(source, {**source, "url": "https://example.org/changed"}))
        self.assertEqual(source["rights_classification"], "unknown")
        self.assertTrue(source["rights_status"])
        validate_rights_classification(source, "Tigrinya discovery source")
        self.assertEqual(survey["result_count"], 2)
        self.assertEqual(survey["result"], "records_found")
        self.assertIn("bounded negative finding only", survey["notes"])
        self.assertIn("no Tigrinya material exists", survey["notes"])
        self.assertIn("SRC-399", survey["source_ids"])

    def test_survey_remains_schema_valid_and_source_referenced(self):
        language = next(item for item in self.archive["translation_registry"]["languages"] if item["language_tag"] == "ti")
        validate_availability_survey(language["availability_survey"], "Tigrinya availability survey", {item["source_id"] for item in self.archive["sources"]})
        schema = json.loads((ROOT / "translation-registry.schema.json").read_text(encoding="utf-8"))
        validate_closed_schema_objects(self.archive["translation_registry"], schema, schema, "translation-registry.json")

    def test_apply_is_idempotent_and_does_not_bundle_a_tigrinya_reader(self):
        before = next(item for item in self.archive["translation_registry"]["languages"] if item["language_tag"] == "ti")["availability_survey"].copy()
        apply(self.archive)
        after = next(item for item in self.archive["translation_registry"]["languages"] if item["language_tag"] == "ti")["availability_survey"]
        self.assertEqual(after, before)
        self.assertFalse(any(item.get("language_tag") == "ti" for item in self.archive["readers"]))
        self.assertFalse(any(item.get("candidate_canon_id") for item in self.archive["readers"] if item.get("language_tag") == "ti"))


if __name__ == "__main__":
    unittest.main()
