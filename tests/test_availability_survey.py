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
        self.assertEqual(set(completed), {"ti", "am", "gaz", "so", "aa", "ssy", "sid", "bej", "dwr", "mdy", "gmv", "hdy", "nus", "wal", "tig", "byn", "kun", "nrb", "dlk", "gez", "en", "ar", "arb", "ln", "oyd", "jnj", "bsw", "alw"})
        self.assertEqual(completed["gez"]["result_count"], 2)
        self.assertIn("not a global corpus census", completed["gez"]["scope"])
        self.assertEqual(set(completed["gez"]["source_ids"]), {"SRC-316", "SRC-317", "SRC-058"})
        self.assertEqual(completed["en"]["result_count"], 3)
        self.assertIn("not the number of distinct translations", completed["en"]["scope"])
        self.assertEqual(set(completed["en"]["source_ids"]), {"SRC-319", "SRC-320", "SRC-321"})
        self.assertIn("not a global or exhaustive census", completed["en"]["scope"])
        self.assertEqual(completed["ar"]["result_count"], 3)
        self.assertIn("not a count of Eritrean-specific translations", completed["ar"]["scope"])
        self.assertIn("Arabic varieties", completed["ar"]["scope"])
        self.assertEqual(completed["ln"]["result_count"], 1)
        self.assertIn("not a Lingala scripture census", completed["ln"]["scope"])
        self.assertIn("SRC-394", completed["ln"]["source_ids"])
        self.assertEqual(set(completed["ar"]["source_ids"]), {"SRC-322", "SRC-323", "SRC-324", "SRC-325", "SRC-326", "SRC-327", "SRC-328"})
        self.assertIn("discrepancy remains unresolved", completed["ar"]["scope"])
        self.assertEqual(completed["arb"]["result_count"], 1)
        self.assertIn("66 separate book members", completed["arb"]["scope"])
        self.assertEqual(set(completed["arb"]["source_ids"]), {"SRC-329", "SRC-330", "SRC-335"})
        geez_leads = {x["corpus_id"]: x for x in registry["corpus_leads"]
                      if x["corpus_id"] in {"stepbible-geez-version-catalogue-2026", "biblecom-geez-new-testament-bse-version-3177"}}
        self.assertEqual(set(geez_leads), {"stepbible-geez-version-catalogue-2026", "biblecom-geez-new-testament-bse-version-3177"})
        self.assertFalse(any(x["text_bundled"] for x in geez_leads.values()))
        self.assertIn("unresolved", geez_leads["stepbible-geez-version-catalogue-2026"]["scope_description"])
        self.assertIn("No text-reuse", geez_leads["biblecom-geez-new-testament-bse-version-3177"]["rights_status"])
        self.assertEqual(completed["ti"]["result_count"], 2)
        self.assertIn("not a census", completed["ti"]["scope"])
        self.assertEqual(completed["am"]["result_count"], 5)
        self.assertIn("Bible.com", completed["am"]["scope"])
        self.assertIn("not a census", completed["am"]["scope"])
        self.assertEqual(completed["gaz"]["result_count"], 4)
        self.assertIn("not a census", completed["gaz"]["scope"])
        self.assertEqual(completed["so"]["result_count"], 4)
        self.assertIn("not a Somali scripture census", completed["so"]["scope"])
        self.assertEqual(completed["aa"]["result_count"], 1)
        self.assertIn("not a complete provider inventory", completed["aa"]["scope"])
        self.assertIn("additional Qafar text Bible", completed["aa"]["notes"])
        self.assertEqual(completed["ssy"]["result_count"], 2)
        self.assertIn("Two distinct Saho text resources", completed["ssy"]["scope"])
        self.assertIn("not a Saho scripture census", completed["ssy"]["scope"])
        self.assertIn("SRC-216", completed["ssy"]["source_ids"])
        saho = next(x for x in registry["languages"] if x["language_tag"] == "ssy")
        scc = next(x for x in registry["corpus_leads"]
                   if x["corpus_id"] == "eritrea-saho-scc-biblecom-listing")
        self.assertIn("SRC-216", scc["source_ids"])
        self.assertIn("27 named book menus", scc["scope_description"])
        self.assertIn("260 chapter links", scc["scope_description"])
        self.assertIn("no reuse license", scc["rights_status"])
        self.assertFalse(scc["text_bundled"])
        self.assertIn("SRC-216", saho["source_ids"])
        self.assertEqual(completed["sid"]["result_count"], 1)
        self.assertIn("not a language-wide census", completed["sid"]["scope"])
        self.assertEqual(completed["bej"]["result_count"], 1)
        self.assertIn("single-provider discovery check", completed["bej"]["scope"])
        self.assertEqual(set(completed["bej"]["source_ids"]), {"SRC-126", "SRC-127"})
        self.assertEqual(completed["gmv"]["result_count"], 4)
        self.assertIn("66 visible title links", completed["gmv"]["scope"])
        self.assertIn("not a language-wide census", completed["gmv"]["scope"])
        self.assertEqual(completed["hdy"]["result_count"], 3)
        self.assertIn("Three provider resource records/interfaces", completed["hdy"]["scope"])
        self.assertEqual(set(completed["hdy"]["source_ids"]), {"SRC-173", "SRC-174", "SRC-418", "SRC-419", "SRC-420"})
        self.assertEqual(completed["nus"]["result_count"], 1)
        self.assertIn("license marked RESERVED", completed["nus"]["scope"])
        self.assertEqual(completed["wal"]["result_count"], 1)
        self.assertIn("noncommercial/no-derivatives", completed["wal"]["scope"])
        self.assertEqual(completed["nrb"]["result"], "none_found")
        self.assertEqual(completed["nrb"]["result_count"], 0)
        self.assertEqual(set(completed["nrb"]["source_ids"]), {"SRC-312", "SRC-313", "SRC-322", "SRC-416"})
        self.assertIn("not a language-wide census", completed["nrb"]["scope"])
        self.assertIn("Bible translation", completed["nrb"]["notes"])
        self.assertIn("None Reported", completed["nrb"]["notes"])
        self.assertEqual(completed["dlk"]["result"], "none_found")
        self.assertEqual(completed["dlk"]["result_count"], 0)
        self.assertEqual(set(completed["dlk"]["source_ids"]), {"SRC-314", "SRC-315"})
        self.assertIn("not a language-wide census", completed["dlk"]["scope"])
        self.assertIn("not independent evidence", completed["dlk"]["notes"])
        self.assertEqual(
            sum(x["availability_survey"]["status"] == "not_surveyed" for x in registry["languages"]),
            0,
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
