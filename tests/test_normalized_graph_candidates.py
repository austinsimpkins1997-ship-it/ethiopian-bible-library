import json
import unittest
from pathlib import Path

from build_normalized_graph import build_graph


ROOT = Path(__file__).resolve().parents[1]


class NormalizedGraphCandidateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.archive = json.loads((ROOT / "archive.json").read_text(encoding="utf-8"))
        cls.portable = json.loads((ROOT / "examples" / "portable-text-layers.json").read_text(encoding="utf-8"))
        cls.graph = build_graph(ROOT, cls.archive, cls.portable["records"])
        cls.work_id_by_reader = {}
        for record in cls.portable["records"]:
            package_path = ROOT / record["content_package"]["uri"].removeprefix("../")
            package = json.loads(package_path.read_text(encoding="utf-8"))
            if package.get("reader_id"):
                cls.work_id_by_reader[package["reader_id"]] = record["work_id"]
        cls.assertions_by_target = {
            entry["id"].rsplit("/", 1)[-1]: entry["work_assertions"]
            for canon in cls.graph["canons"]
            for entry in canon["entries"]
        }

    def test_amharic_and_gamo_candidate_assertions_preserve_recorded_evidence_states(self):
        corpora = [
            item for item in self.archive["translation_registry"]["research_corpora"]
            if item.get("language_tag") in {"am", "gmv"} and item.get("candidate_canon_id")
        ]
        self.assertEqual(len(corpora), 92)
        for corpus in corpora:
            with self.subTest(reader=corpus["reader_id"]):
                target_assertions = self.assertions_by_target[corpus["candidate_canon_id"]]
                expected_work = self.work_id_by_reader.get(corpus["reader_id"])
                if expected_work is None:
                    expected_work = f"https://austinsimpkins1997-ship-it.github.io/ethiopian-bible-library/id/work/reader-{corpus['reader_id']}"
                match = next(item for item in target_assertions if item["work_id"] == expected_work)
                self.assertEqual(match["state"], corpus["canon_mapping_state"])
                self.assertEqual(match["notes"], corpus["canon_mapping_note"])
                self.assertTrue(set(corpus["source_ids"]).issubset(match["evidence_source_ids"]))

    def test_lamentations_candidate_is_not_invented(self):
        corpus = next(
            item for item in self.archive["translation_registry"]["research_corpora"]
            if item["reader_id"] == "gamo-lam-research"
        )
        self.assertIsNone(corpus["candidate_canon_id"])
        self.assertFalse(any(
            assertion["work_id"].endswith("/reader-gamo-lam-research")
            for entries in self.assertions_by_target.values()
            for assertion in entries
        ))

    def test_reigns_title_equivalences_are_reviewed_as_work_titles_not_edition_identity(self):
        corpora = [
            item for item in self.archive["translation_registry"]["research_corpora"]
            if item.get("reader_id") in {
                "samuel-i-geez-research", "samuel-ii-geez-research",
                "kings-i-geez-research", "kings-ii-geez-research",
            }
        ]
        self.assertEqual(len(corpora), 4)
        for corpus in corpora:
            with self.subTest(reader=corpus["reader_id"]):
                self.assertEqual(corpus["canon_mapping_state"], "reviewed_match")
                self.assertIn("Archive-reviewed work/title crosswalk", corpus["canon_mapping_note"])
                self.assertIn("does not establish identity with a current EOTC edition", corpus["canon_mapping_note"])
                assertions = self.assertions_by_target[corpus["candidate_canon_id"]]
                work_id = f"https://austinsimpkins1997-ship-it.github.io/ethiopian-bible-library/id/work/reader-{corpus['reader_id']}"
                match = next(item for item in assertions if item["work_id"] == work_id)
                self.assertEqual(match["state"], "reviewed_match")
                self.assertEqual(match["notes"], corpus["canon_mapping_note"])
                self.assertTrue(set(corpus["source_ids"]).issubset(match["evidence_source_ids"]))

    def test_dawro_reviewed_title_matches_reach_graph_with_real_scope_provenance(self):
        for code in (
            "mat", "mrk", "luk", "jhn", "act", "rom", "1co", "2co", "gal", "eph", "php", "col",
            "1th", "2th", "1ti", "2ti", "tit", "phm", "heb", "1pe", "2pe", "1jn", "2jn", "3jn",
            "jas", "jud", "rev",
        ):
            reader_id = f"dawro-latin-{code}-research"
            corpus = next(item for item in self.archive["translation_registry"]["research_corpora"]
                          if item["reader_id"] == reader_id)
            work_id = self.work_id_by_reader.get(
                reader_id,
                f"https://austinsimpkins1997-ship-it.github.io/ethiopian-bible-library/id/work/reader-{reader_id}",
            )
            match = next(item for item in self.assertions_by_target[corpus["candidate_canon_id"]]
                         if item["work_id"] == work_id)
            self.assertEqual(match["state"], "reviewed_match")
            self.assertTrue({"SRC-029", "SRC-396", "SRC-404", "SRC-405"} <= set(match["evidence_source_ids"]))
            work = next(item for item in self.graph["works"] if item["id"] == work_id)
            self.assertIn("One of 66 USFM book members", work["notes"])
            self.assertNotIn("scope: None", work["notes"])

    def test_oyda_yemsa_and_baiso_reviewed_matches_reach_the_graph(self):
        packages = {
            "oyda-": "One of 27 USFM book members",
            "yemsa-": "One of 27 USFM book members",
            "baiso-ethiopic-": "One of 27 USFM book members",
        }
        for prefix, expected_scope in packages.items():
            for code in (
                "mat", "mrk", "luk", "jhn", "act", "rom", "1co", "2co", "gal", "eph", "php", "col",
                "1th", "2th", "1ti", "2ti", "tit", "phm", "heb", "1pe", "2pe", "1jn", "2jn", "3jn",
                "jas", "jud", "rev",
            ):
                reader_id = f"{prefix}{code}-research"
                corpus = next(item for item in self.archive["translation_registry"]["research_corpora"]
                              if item["reader_id"] == reader_id)
                work_id = self.work_id_by_reader.get(
                    reader_id,
                    f"https://austinsimpkins1997-ship-it.github.io/ethiopian-bible-library/id/work/reader-{reader_id}",
                )
                match = next(item for item in self.assertions_by_target[corpus["candidate_canon_id"]]
                             if item["work_id"] == work_id)
                self.assertEqual(match["state"], "reviewed_match")
                self.assertTrue({"SRC-029", "SRC-396"} <= set(match["evidence_source_ids"]))
                work = next(item for item in self.graph["works"] if item["id"] == work_id)
                self.assertIn(expected_scope, work["notes"])
                self.assertNotIn("scope: None", work["notes"])

    def test_arabic_van_dyck_crosswalk_reaches_graph_without_claiming_translation_basis(self):
        for code in (
            "mat", "mrk", "luk", "jhn", "act", "rom", "1co", "2co", "gal", "eph", "php", "col",
            "1th", "2th", "1ti", "2ti", "tit", "phm", "heb", "1pe", "2pe", "1jn", "2jn", "3jn",
            "jas", "jud", "rev",
        ):
            reader_id = f"arb-vd-{code}-research"
            corpus = next(item for item in self.archive["translation_registry"]["research_corpora"]
                          if item["reader_id"] == reader_id)
            self.assertIsNone(corpus.get("translation_path"))
            work_id = self.work_id_by_reader.get(
                reader_id,
                f"https://austinsimpkins1997-ship-it.github.io/ethiopian-bible-library/id/work/reader-{reader_id}",
            )
            match = next(item for item in self.assertions_by_target[corpus["candidate_canon_id"]]
                         if item["work_id"] == work_id)
            self.assertEqual(match["state"], "reviewed_match")
            self.assertTrue({"SRC-029", "SRC-396", "SRC-329", "SRC-330"}
                            <= set(match["evidence_source_ids"]))
            work = next(item for item in self.graph["works"] if item["id"] == work_id)
            self.assertIn("One separate book from a 66-book standard-Arabic package", work["notes"])
            self.assertNotIn("scope: None", work["notes"])

    def test_somali_lingala_and_maale_crosswalks_are_present_in_the_normalized_graph(self):
        packages = {
            "som-1979-2008-": "One of 66 conventional USFM modules",
            "lin-2020-": "One of 66 conventional USFM modules",
            "maale-": "one of 66 USFM book members",
        }
        for prefix, expected_scope in packages.items():
            for code in (
                "mat", "mrk", "luk", "jhn", "act", "rom", "1co", "2co", "gal", "eph", "php", "col",
                "1th", "2th", "1ti", "2ti", "tit", "phm", "heb", "1pe", "2pe", "1jn", "2jn", "3jn",
                "jas", "jud", "rev",
            ):
                reader_id = f"{prefix}{code}-research"
                corpus = next(item for item in self.archive["translation_registry"]["research_corpora"]
                              if item["reader_id"] == reader_id)
                work_id = self.work_id_by_reader.get(
                    reader_id,
                    f"https://austinsimpkins1997-ship-it.github.io/ethiopian-bible-library/id/work/reader-{reader_id}",
                )
                match = next(item for item in self.assertions_by_target[corpus["candidate_canon_id"]]
                             if item["work_id"] == work_id)
                self.assertEqual(match["state"], "reviewed_match")
                self.assertTrue({"SRC-029", "SRC-396"} <= set(match["evidence_source_ids"]))
                work = next(item for item in self.graph["works"] if item["id"] == work_id)
                self.assertIn(expected_scope, work["notes"])
                self.assertNotIn("scope: None", work["notes"])


if __name__ == "__main__":
    unittest.main()
