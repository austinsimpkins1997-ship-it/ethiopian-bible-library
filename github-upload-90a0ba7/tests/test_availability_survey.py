import json
import unittest
from pathlib import Path

from availability_survey import validate_availability_survey


ROOT = Path(__file__).resolve().parents[1]


class AvailabilitySurveyTests(unittest.TestCase):
    def test_each_language_profile_has_explicit_bounded_survey_state(self):
        registry = json.loads((ROOT / "translation-registry.json").read_text(encoding="utf-8"))
        archive = json.loads((ROOT / "archive.json").read_text(encoding="utf-8"))
        known_source_ids = {source["source_id"] for source in archive["sources"]}
        self.assertTrue(registry["languages"])
        for language in registry["languages"]:
            with self.subTest(language=language["language_tag"]):
                validate_availability_survey(
                    language.get("availability_survey"),
                    known_source_ids=known_source_ids,
                )
        completed = {x["language_tag"]: x["availability_survey"] for x in registry["languages"]
                     if x["availability_survey"]["status"] == "completed"}
        self.assertEqual(set(completed), {"ti", "am", "gaz", "so", "aa", "ssy", "sid", "bej", "dwr", "mdy", "gmv", "hdy", "nus", "wal"})
        self.assertEqual(completed["ti"]["result_count"], 2)
        self.assertIn("not a census", completed["ti"]["scope"])
        self.assertEqual(completed["am"]["result_count"], 5)
        self.assertIn("Bible.com", completed["am"]["scope"])
        self.assertIn("not a census", completed["am"]["scope"])
        self.assertEqual(completed["gaz"]["result_count"], 3)
        self.assertIn("not a census", completed["gaz"]["scope"])
        self.assertEqual(completed["so"]["result_count"], 4)
        self.assertIn("not a Somali scripture census", completed["so"]["scope"])
        self.assertEqual(completed["aa"]["result_count"], 1)
        self.assertIn("not a complete provider inventory", completed["aa"]["scope"])
        self.assertIn("additional Qafar text Bible", completed["aa"]["notes"])
        self.assertEqual(completed["ssy"]["result_count"], 2)
        self.assertIn("Two distinct Saho text resources", completed["ssy"]["scope"])
        self.assertIn("not a Saho scripture census", completed["ssy"]["scope"])
        self.assertEqual(completed["sid"]["result_count"], 1)
        self.assertIn("not a language-wide census", completed["sid"]["scope"])
        self.assertEqual(completed["bej"]["result_count"], 1)
        self.assertIn("single-provider discovery check", completed["bej"]["scope"])
        self.assertEqual(set(completed["bej"]["source_ids"]), {"SRC-126", "SRC-127"})
        self.assertEqual(completed["gmv"]["result_count"], 4)
        self.assertIn("66 visible title links", completed["gmv"]["scope"])
        self.assertIn("not a language-wide census", completed["gmv"]["scope"])
        self.assertEqual(completed["hdy"]["result_count"], 1)
        self.assertIn("One KeesKita/KEESAMMI KITAABA version listing", completed["hdy"]["scope"])
        self.assertEqual(completed["nus"]["result_count"], 1)
        self.assertIn("license marked RESERVED", completed["nus"]["scope"])
        self.assertEqual(completed["wal"]["result_count"], 1)
        self.assertIn("noncommercial/no-derivatives", completed["wal"]["scope"])
        self.assertEqual(
            sum(x["availability_survey"]["status"] == "not_surveyed" for x in registry["languages"]),
            len(registry["languages"]) - 14,
        )

    def test_unbounded_none_found_cannot_be_recorded_as_a_zero(self):
        with self.assertRaisesRegex(ValueError, "cannot report survey scope"):
            validate_availability_survey({"status": "not_surveyed", "result": "none_found", "result_count": 0})

    def test_completed_zero_requires_scope_date_and_sources(self):
        with self.assertRaisesRegex(ValueError, "bounded scope and cited source IDs"):
            validate_availability_survey({
                "status": "completed", "result": "none_found", "result_count": 0,
                "searched_at": "2026-10-25",
            })

    def test_cited_bounded_completed_zero_is_valid(self):
        validate_availability_survey({
            "status": "completed", "scope": "Catalogues A and B, searched for Tigrinya New Testament editions",
            "searched_at": "2026-10-25", "result": "none_found", "result_count": 0,
            "source_ids": ["SRC-001"],
        }, known_source_ids={"SRC-001"})

    def test_records_found_requires_positive_observed_count(self):
        with self.assertRaisesRegex(ValueError, "positive result_count"):
            validate_availability_survey({
                "status": "completed", "scope": "A bounded catalogue search", "searched_at": "2026-10-25",
                "result": "records_found", "result_count": 0, "source_ids": ["SRC-001"],
            })

    def test_survey_sources_must_exist_in_archive(self):
        with self.assertRaisesRegex(ValueError, "unknown source IDs"):
            validate_availability_survey({
                "status": "in_progress", "scope": "A bounded catalogue search", "source_ids": ["SRC-999"],
            }, known_source_ids={"SRC-001"})

    def test_in_progress_survey_cannot_report_a_result(self):
        with self.assertRaisesRegex(ValueError, "cannot report a result"):
            validate_availability_survey({
                "status": "in_progress", "scope": "A bounded catalogue search", "source_ids": ["SRC-001"],
                "result": "none_found", "result_count": 0,
            }, known_source_ids={"SRC-001"})


if __name__ == "__main__":
    unittest.main()
