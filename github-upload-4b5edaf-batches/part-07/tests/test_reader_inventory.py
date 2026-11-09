import json
import unittest
from pathlib import Path

from reader_validation import validate_observed_unit_count

ROOT = Path(__file__).resolve().parents[1]


class ReaderUnitInventoryTests(unittest.TestCase):
    def test_continuation_source_marker_is_rendered_as_data_not_literal_template_code(self):
        app = (ROOT / "app.js").read_text(encoding="utf-8")
        self.assertIn("Unnumbered continuation (source ${escapeHTML(segment.source_marker || 'marker')})", app)
        self.assertNotIn(r"source \${escapeHTML(segment.source_marker", app)

    def test_all_local_reader_and_companion_counts_match_stored_units(self):
        archive = json.loads((ROOT / "archive.json").read_text(encoding="utf-8"))
        for reader in archive["readers"]:
            with self.subTest(record=reader["reader_id"]):
                validate_observed_unit_count(reader, "unit_count", reader["reader_id"])
            companion = reader.get("parallel_translation")
            if companion:
                with self.subTest(record=companion["translation_id"]):
                    validate_observed_unit_count(companion, "unit_count", companion["translation_id"])

    def test_mismatch_is_rejected(self):
        record = {"unit_count": 2, "chapters": [{"verses": [{}, {}, {}]}]}
        with self.assertRaisesRegex(ValueError, "declares 2 units but 3 are stored"):
            validate_observed_unit_count(record, "unit_count", "sample")

    def test_generic_line_elements_are_counted_without_calling_them_verses(self):
        record = {"unit_count": 3, "chapters": [{"units": [
            {"unit_order": 1, "source_marker": None},
            {"unit_order": 2, "source_marker": "1"},
            {"unit_order": 3, "source_marker": "2"},
        ]}]}
        self.assertEqual(validate_observed_unit_count(record, "unit_count", "research witness"), 3)

    def test_empty_research_line_list_cannot_be_given_a_positive_count(self):
        record = {"unit_count": 1, "chapters": [{"units": []}]}
        with self.assertRaisesRegex(ValueError, "no unit list"):
            validate_observed_unit_count(record, "unit_count", "research witness")

    def test_boolean_or_nonnumeric_declared_count_is_rejected(self):
        for count in (True, "3", -1):
            with self.subTest(count=count):
                with self.assertRaisesRegex(ValueError, "nonnegative integer"):
                    validate_observed_unit_count({"unit_count": count, "chapters": [{"verses": [{}]}]}, "unit_count", "sample")


if __name__ == "__main__":
    unittest.main()
