import unittest

from review_metadata import validate_review_record


class ReviewMetadataTests(unittest.TestCase):
    def test_automated_validation_is_not_a_human_reviewer(self):
        validate_review_record({
            "review_method": "automated_validation",
            "review_process": "chapter sequence validator",
            "reviewer": None,
            "state": "checked_with_limits",
        })

    def test_automated_validation_cannot_claim_fully_reviewed(self):
        with self.assertRaisesRegex(ValueError, "cannot mark automated"):
            validate_review_record({
                "review_method": "automated_validation",
                "review_process": "chapter sequence validator",
                "reviewer": None,
                "state": "reviewed",
            })

    def test_fully_reviewed_requires_named_human_and_date(self):
        record = {"review_method": "scholarly_review", "reviewer": "Reviewer", "reviewed_at": "2026-10-25", "state": "reviewed"}
        validate_review_record(record)
        record["reviewer"] = None
        with self.assertRaisesRegex(ValueError, "cannot mark automated or unattributed"):
            validate_review_record(record)

    def test_unknown_method_is_explicit(self):
        validate_review_record({"review_method": "unknown", "reviewer": None, "review_process": None, "state": "checked_with_limits"})

    def test_bundled_examples_keep_automation_separate_from_reviewers(self):
        import json
        from pathlib import Path
        root = Path(__file__).resolve().parents[1]
        examples = [p for p in (root / "examples").glob("*-layer.json")]
        portable = json.loads((root / "examples" / "portable-text-layers.json").read_text(encoding="utf-8"))
        self.assertEqual(len(examples), len(portable["records"]))
        for path in examples:
            record = json.loads(path.read_text(encoding="utf-8"))
            for index, review in enumerate(record["review_dimensions"]):
                with self.subTest(file=path.name, review=index):
                    validate_review_record(review, path.name)
                    if review["review_method"] in {"automated_validation", "combined_source_and_automated_validation"}:
                        self.assertIsNone(review.get("reviewer"))
                        self.assertNotEqual(review["state"], "reviewed")

    def test_schema_has_matching_review_gate(self):
        import json
        from pathlib import Path
        schema = json.loads((Path(__file__).resolve().parents[1] / "schemas" / "text-layer.schema.json").read_text(encoding="utf-8"))
        item = schema["properties"]["review_dimensions"]["items"]
        self.assertIn("review_method", item["properties"])
        self.assertIn("review_method", item["required"])
        self.assertEqual(len(item["allOf"]), 2)


if __name__ == "__main__":
    unittest.main()
