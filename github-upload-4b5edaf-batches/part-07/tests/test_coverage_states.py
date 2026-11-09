import unittest

from coverage_summary import validate_unit_coverage


class ZeroCoverageTests(unittest.TestCase):
    def test_unknown_extent_cannot_be_zero(self):
        coverage = {
            "unit_count": 0,
            "extent_state": "unknown",
            "extent_basis": "source_inventory",
            "structure_description": "Chapter labels inspected",
        }
        with self.assertRaisesRegex(ValueError, "extent is unknown"):
            validate_unit_coverage(coverage)

    def test_unknown_basis_cannot_be_zero(self):
        coverage = {
            "unit_count": 0,
            "extent_state": "partial",
            "extent_basis": "unknown",
            "structure_description": "Chapter labels inspected",
        }
        with self.assertRaisesRegex(ValueError, "completed source inventory"):
            validate_unit_coverage(coverage)

    def test_zero_requires_a_named_scope(self):
        coverage = {
            "unit_count": 0,
            "extent_state": "partial",
            "extent_basis": "source_inventory",
            "structure_description": "",
        }
        with self.assertRaisesRegex(ValueError, "bounded scope"):
            validate_unit_coverage(coverage)

    def test_bounded_inventory_can_report_zero(self):
        coverage = {
            "unit_count": 0,
            "extent_state": "partial",
            "extent_basis": "source_inventory",
            "structure_description": "Survey of chapters 1–3 in the cited edition; none contained numbered units.",
        }
        validate_unit_coverage(coverage)

    def test_unknown_count_remains_null(self):
        coverage = {
            "unit_count": None,
            "extent_state": "unknown",
            "extent_basis": "unknown",
        }
        validate_unit_coverage(coverage)

    def test_boolean_is_not_an_integer_count(self):
        with self.assertRaisesRegex(ValueError, "nonnegative integer or null"):
            validate_unit_coverage({"unit_count": False})

    def test_negative_count_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "nonnegative integer or null"):
            validate_unit_coverage({"unit_count": -1})

    def test_nonnumeric_count_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "nonnegative integer or null"):
            validate_unit_coverage({"unit_count": "3"})


if __name__ == "__main__":
    unittest.main()
