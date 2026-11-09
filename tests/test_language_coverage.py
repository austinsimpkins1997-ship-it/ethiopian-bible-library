import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class LanguageCoverageTests(unittest.TestCase):
    def test_standard_old_testament_module_candidates_are_discoverable_without_canon_promotion(self):
        archive = json.loads((ROOT / "archive.json").read_text(encoding="utf-8"))
        coverage = json.loads((ROOT / "book-coverage.json").read_text(encoding="utf-8"))
        books_by_number = {
            int(book["canon_id"].rsplit("-", 1)[1]): book
            for book in archive["canon_registry"]["books"]
            if book["canon_id"].startswith("eotc-ot-")
        }
        code_to_number = {
            "GEN": 1, "EXO": 2, "LEV": 3, "NUM": 4, "DEU": 5, "JOS": 6, "JDG": 7, "RUT": 8,
            "1SA": 9, "2SA": 9, "1KI": 10, "2KI": 10, "1CH": 11, "2CH": 12,
            "EZR": 15, "NEH": 15, "TOB": 17, "JDT": 18, "EST": 19, "ESG": 19,
            "1MA": 20, "2MA": 21, "3MA": 21, "JOB": 22, "PSA": 23, "PRO": 24,
            "ECC": 27, "SNG": 28, "ISA": 29, "JER": 30, "EZK": 31, "DAN": 32,
            "DAG": 32, "HOS": 33, "AMO": 34, "MIC": 35, "JOL": 36, "OBA": 37,
            "JON": 38, "NAM": 39, "HAB": 40, "ZEP": 41, "HAG": 42, "ZEC": 43,
            "MAL": 44, "SIR": 45,
        }
        readers = {reader["reader_id"]: reader for reader in archive["readers"]}
        pattern = re.compile(r"(?:::|[/#])\d+-(" + "|".join(sorted(code_to_number, key=len, reverse=True)) + r")")
        candidates = []
        for corpus in archive["translation_registry"]["research_corpora"]:
            if not {"SRC-029", "SRC-384"}.issubset(set(corpus.get("source_ids", []))):
                continue
            reader = readers.get(corpus.get("reader_id"), {})
            match = pattern.search(str(reader.get("source_pages", "")))
            if match is None:
                continue
            candidates.append((corpus, reader, match.group(1)))
        self.assertEqual(len(candidates), 307)
        for corpus, reader, code in candidates:
            with self.subTest(corpus=corpus["corpus_id"]):
                target = f"eotc-ot-{code_to_number[code]:02d}"
                self.assertEqual(corpus["candidate_canon_id"], target)
                expected_state = "reviewed_match" if code in {"JOB", "1CH", "2CH"} else "uncertain"
                self.assertEqual(corpus["canon_mapping_state"], expected_state)
                if code in {"1CH", "2CH"}:
                    title = "I Chronicles" if code == "1CH" else "II Chronicles"
                    self.assertIn("reviewed work/title match only", corpus["canon_mapping_note"].lower())
                    self.assertIn(title, corpus["canon_mapping_note"])
                    self.assertIn("SRC-396", corpus["source_ids"])
                    self.assertIn("Orthodox alternative title", corpus["canon_mapping_note"])
                    self.assertIn("excluded from canon-linked coverage", corpus["canon_mapping_note"])
                elif code == "JOB":
                    self.assertIn("reviewed work/title match only", corpus["canon_mapping_note"].lower())
                    self.assertIn("SRC-396", corpus["source_ids"])
                self.assertIn("does not establish", corpus["canon_mapping_note"])
                self.assertIsNone(reader.get("canon_id"))
        self.assertEqual(sum(corpus["canon_mapping_state"] == "reviewed_match" for corpus, _, _ in candidates), 24)
        self.assertEqual(sum(corpus["canon_mapping_state"] == "uncertain" for corpus, _, _ in candidates), 283)
        sources = {source["source_id"]: source for source in archive["sources"]}
        for source_id in ("SRC-029", "SRC-396"):
            self.assertEqual(sources[source_id]["local_review_url"], "research/chronicles-title-crosswalk-review.md")
        self.assertTrue((ROOT / "research" / "chronicles-title-crosswalk-review.md").is_file())
        for canon_id in ("eotc-ot-11", "eotc-ot-12"):
            entry = next(item for item in coverage["entries"] if item["canon_id"] == canon_id)
            self.assertEqual(len(entry["canon_linked_readers"]), 0)
            self.assertEqual(len(entry["research_reader_candidates"]), 9)
            self.assertTrue(all(item["mapping_state"] == "reviewed_match" for item in entry["research_reader_candidates"]))
        self.assertEqual(sum(len(entry["canon_linked_readers"]) for entry in coverage["entries"]), 19)
        genesis = next(item for item in coverage["entries"] if item["canon_id"] == "eotc-ot-01")
        genesis_book = books_by_number[1]
        self.assertEqual(genesis_book.get("reader_id"), "genesis-geez-dillmann-hacohen")
        self.assertEqual(genesis["reader_availability"], "canon_linked_reader")
        self.assertEqual(len(genesis["canon_linked_readers"]), 1)
        self.assertEqual(len(genesis["research_reader_candidates"]), 8)
        self.assertIn("SRC-384", genesis["related_source_ids"])

    def test_job_research_candidates_are_discoverable_without_canon_promotion(self):
        archive = json.loads((ROOT / "archive.json").read_text(encoding="utf-8"))
        coverage = json.loads((ROOT / "book-coverage.json").read_text(encoding="utf-8"))
        job = next(item for item in archive["canon_registry"]["books"] if item["canon_id"] == "eotc-ot-22")
        entry = next(item for item in coverage["entries"] if item["canon_id"] == "eotc-ot-22")
        corpora = {
            item["corpus_id"]: item
            for item in archive["translation_registry"]["research_corpora"]
        }
        expected = {
            "dawro-dwrl-2024-job",
            "gazbib-2022-job",
            "linbibo-2020-job",
            "maale-mdytwf-2008-job",
            "somsim-1979-2008-job",
            "webbe-2020-job",
        }
        job_candidates = [item for item in corpora.values() if item.get("candidate_canon_id") == "eotc-ot-22"]
        self.assertEqual(len(job_candidates), 9)
        for corpus_id in expected:
            corpus = corpora[corpus_id]
            self.assertEqual(corpus["candidate_canon_id"], "eotc-ot-22")
            self.assertEqual(corpus["canon_mapping_state"], "reviewed_match")
            self.assertIn("SRC-029", corpus["source_ids"])
            self.assertIn("SRC-396", corpus["source_ids"])
            self.assertIn("does not establish Ethiopian or Eritrean Orthodox affiliation", corpus["canon_mapping_note"])
        self.assertEqual(sum(item["canon_mapping_state"] == "reviewed_match" for item in job_candidates), 8)
        self.assertEqual(
            {item["corpus_id"] for item in job_candidates if item["canon_mapping_state"] == "uncertain"},
            {"gmvetw-job-research"},
        )
        gamo = corpora["gmvetw-job-research"]
        self.assertEqual(gamo["canon_mapping_state"], "uncertain")
        self.assertNotIn("SRC-396", gamo["source_ids"])
        self.assertIsNone(job.get("reader_id"))
        self.assertEqual(entry["reader_availability"], "reviewed_title_match_research_reader_only")
        self.assertEqual(entry["canon_linked_readers"], [])
        self.assertEqual(len(entry["research_reader_candidates"]), 9)
        self.assertEqual(len({item["language_tag"] for item in entry["research_reader_candidates"]}), 8)
        self.assertIn("9 separately scoped Job title-candidate research readers", job["reader_status"])

    def test_iana_language_count_in_source_note_matches_audited_tags(self):
        archive = json.loads((ROOT / "archive.json").read_text(encoding="utf-8"))
        audit = json.loads((ROOT / "language-script-code-audit.json").read_text(encoding="utf-8"))
        source = next(item for item in archive["sources"] if item["source_id"] == "SRC-077")
        audited_count = len(audit["language_subtags"]["codes"])
        self.assertEqual(audit["latest_authority_check"]["iana_language_or_extlang_codes_checked"], audited_count)
        self.assertIn(f"All {audited_count} language-tag subtags", source["inspection_and_limitations"])
        self.assertIn(f"{audited_count} locally used tags resolved", source["archive_status"])

    def test_standard_arabic_tag_is_separate_from_eritrea_filtered_arabic_survey(self):
        archive = json.loads((ROOT / "archive.json").read_text(encoding="utf-8"))
        profiles = {item["language_tag"]: item for item in archive["translation_registry"]["languages"]}
        self.assertEqual(profiles["ar"]["language_name"], "Arabic")
        self.assertIn("filtered by Eritrea", profiles["ar"]["script_profile_note"])
        self.assertEqual(profiles["arb"]["language_name"], "Standard Arabic")
        self.assertEqual(profiles["arb"]["availability_survey"]["result_count"], 1)
        self.assertNotIn("SRC-329", profiles["ar"]["source_ids"])
        van_dyck = [item for item in archive["translation_registry"]["research_corpora"] if item.get("corpus_id", "").startswith("arb-vd-")]
        self.assertEqual(len(van_dyck), 66)
        self.assertTrue(all(item["language_tag"] == "arb" for item in van_dyck))
        candidates = [item for item in van_dyck if item["canon_mapping_state"] == "uncertain"]
        reviewed = [item for item in van_dyck if item["canon_mapping_state"] == "reviewed_match"]
        unmapped = [item for item in van_dyck if item["canon_mapping_state"] == "not_mapped"]
        self.assertEqual(len(candidates), 35)
        self.assertEqual(len(reviewed), 30)
        self.assertTrue(all(item.get("candidate_canon_id") for item in candidates + reviewed))
        self.assertTrue(all("SRC-029" in item["source_ids"] and "SRC-196" in item["source_ids"] for item in candidates))
        self.assertTrue(all({"SRC-029", "SRC-329", "SRC-330", "SRC-396"} <= set(item["source_ids"])
                            for item in reviewed))
        self.assertEqual(len(unmapped), 1)
        self.assertTrue(all(item.get("candidate_canon_id") is None for item in unmapped))
        self.assertIn("Lamentations", next(reader["title"] for reader in archive["readers"] if reader["reader_id"] == unmapped[0]["reader_id"]))

    def test_kunama_catalog_text_link_and_translation_project_stay_distinct(self):
        archive = json.loads((ROOT / "archive.json").read_text(encoding="utf-8"))
        registry = archive["translation_registry"]
        profile = next(item for item in registry["languages"] if item["language_tag"] == "kun")
        leads = {item["corpus_id"]: item for item in registry["corpus_leads"]}
        full_bible = leads["eritrea-kunama-complete-bible-2012"]
        bible_film = leads["kunama-scriptureearth-jesus-film-resource"]
        project = leads["kunama-wycliffe-ethiopia-project-page"]
        sources = {item["source_id"]: item for item in archive["sources"]}

        self.assertEqual(profile["availability_survey"]["result_count"], 2)
        self.assertIn("does not count Bible editions or books", profile["availability_survey"]["scope"])
        self.assertIn("2009 Easy Kunama Gospel of John PDF", full_bible["scope_description"])
        self.assertIn("does not provide the 2012 full text", full_bible["scope_description"])
        self.assertEqual(full_bible["rights_classification"], "unknown")
        self.assertIs(bible_film["text_bundled"], False)
        self.assertIn("not a Bible text", bible_film["scope_description"])
        self.assertIn("two teams", project["scope_description"])
        self.assertIn("relationship to the Eritrea-published 2012 Bible", project["scope_description"])
        self.assertIn("Copyright 2009 Eritrean easyBibles team", sources["SRC-309"]["inspection_and_limitations"])
        self.assertIn("no open reuse license", full_bible["rights_status"].lower())

    def test_blin_resources_keep_1890_mark_distinct_from_2018_new_testament(self):
        archive = json.loads((ROOT / "archive.json").read_text(encoding="utf-8"))
        registry = archive["translation_registry"]
        profile = next(item for item in registry["languages"] if item["language_tag"] == "byn")
        leads = {item["corpus_id"]: item for item in registry["corpus_leads"]}
        historic = leads["blin-mark-1890-archive-scan"]
        modern = leads["eritrea-blin-new-testament-2018"]
        sources = {item["source_id"]: item for item in archive["sources"]}

        self.assertEqual(profile["availability_survey"]["result_count"], 2)
        self.assertIn("not two translations", profile["availability_survey"]["scope"])
        self.assertIs(historic["text_bundled"], False)
        self.assertEqual(historic["rights_classification"], "public_domain_claimed")
        self.assertEqual(historic["script_code"], "Latn")
        self.assertIn("New Testament portions", historic["scope_description"])
        self.assertIn("Gospel of Mark", historic["scope_description"])
        self.assertIn("2018", modern["scope_description"])
        self.assertIn("not a digital edition", modern["scope_description"])
        self.assertIn("PDF retrieval failed", historic["review_status"])
        self.assertIn("Public Domain", sources["SRC-304"]["inspection_and_limitations"])
        self.assertIn("PDF", sources["SRC-305"]["inspection_and_limitations"])

    def test_tigre_barih_discovery_stays_bounded_unbundled_and_rights_unknown(self):
        archive = json.loads((ROOT / "archive.json").read_text(encoding="utf-8"))
        registry = archive["translation_registry"]
        profile = next(item for item in registry["languages"] if item["language_tag"] == "tig")
        lead = next(item for item in registry["corpus_leads"] if item["corpus_id"] == "barih-tigre-scripture-media-discovery-2026")
        sources = {item["source_id"]: item for item in archive["sources"]}

        self.assertEqual(profile["availability_survey"]["result_count"], 1)
        self.assertIn("one provider website/resource collection", profile["availability_survey"]["scope"])
        self.assertEqual(set(lead["source_ids"]), {"SRC-298", "SRC-299", "SRC-300", "SRC-301", "SRC-302"})
        self.assertIs(lead["text_bundled"], False)
        self.assertEqual(lead["rights_classification"], "unknown")
        self.assertEqual(lead["script_code"], "Zzzz")
        self.assertIn("Arabic script", lead["scope_description"])
        self.assertIn("Tigrinya", lead["notes"])
        self.assertIn("no readable terms", sources["SRC-302"]["inspection_and_limitations"])
        self.assertIn("not evidence that the displayed scripture is Tigre", sources["SRC-301"]["inspection_and_limitations"])

    def test_ethiopic_joel_lead_matches_bundled_reader_and_retains_rights_limit(self):
        archive = json.loads((ROOT / "archive.json").read_text(encoding="utf-8"))
        registry = archive["translation_registry"]
        lead = next(item for item in registry["edition_leads"] if item["edition_id"] == "hacohen-joel-dillmann-1879-online-text-2024")
        sources = {source["source_id"]: source for source in archive["sources"]}
        self.assertEqual(lead["candidate_canon_id"], "eotc-ot-36")
        self.assertEqual(lead["mapping_state"], "uncertain")
        self.assertIs(lead["text_bundled"], False)
        self.assertEqual(lead["bundled_reader_id"], "joel-geez-dillmann-hacohen-tau")
        self.assertEqual(lead["rights_classification"], "permission_limited")
        self.assertTrue({"SRC-029", "SRC-036", "SRC-149", "SRC-192"}.issubset(set(lead["source_ids"])))
        self.assertIn("noncommercial", lead["rights_status"])
        self.assertIn("1879", lead["edition_statement"])
        self.assertIn("2024", lead["edition_statement"])
        self.assertEqual(sources["SRC-149"]["url"], "https://www.tau.ac.il/~hacohen/Joel/Information.html")
        self.assertIn("joel-geez-dillmann-hacohen-tau", {reader["reader_id"] for reader in archive["readers"]})

    def test_ethiopic_daniel_lead_keeps_mapping_and_rights_unresolved(self):
        archive = json.loads((ROOT / "archive.json").read_text(encoding="utf-8"))
        lead = next(item for item in archive["translation_registry"]["edition_leads"] if item["edition_id"] == "lofgren-ethiopic-daniel-1927")
        sources = {source["source_id"]: source for source in archive["sources"]}
        self.assertEqual(lead["candidate_canon_id"], "eotc-ot-32")
        self.assertEqual(lead["mapping_state"], "uncertain")
        self.assertIs(lead["text_bundled"], False)
        self.assertEqual(lead["rights_classification"], "unknown")
        self.assertIn("SRC-150", lead["source_ids"])
        self.assertIn("1927", lead["edition_statement"])
        self.assertIn("reuse rights", sources["SRC-150"]["inspection_and_limitations"])

    def test_ethiopic_amos_lead_matches_bundled_reader_and_retains_rights_limit(self):
        archive = json.loads((ROOT / "archive.json").read_text(encoding="utf-8"))
        lead = next(item for item in archive["translation_registry"]["edition_leads"] if item["edition_id"] == "hacohen-amos-pereira-1917-online-text")
        sources = {source["source_id"]: source for source in archive["sources"]}
        self.assertEqual(lead["candidate_canon_id"], "eotc-ot-34")
        self.assertEqual(lead["mapping_state"], "uncertain")
        self.assertIs(lead["text_bundled"], False)
        self.assertEqual(lead["bundled_reader_id"], "amos-geez-pereira-ghebre-tau")
        self.assertEqual(lead["rights_classification"], "permission_limited")
        self.assertIn("SRC-151", lead["source_ids"])
        self.assertIn("Kefela Ghebre", lead["edition_statement"])
        self.assertIn("No open-content or commercial license", lead["rights_status"])
        self.assertEqual(sources["SRC-151"]["url"], "https://www.tau.ac.il/~hacohen/Amos/Information.html")

    def test_ethiopic_hosea_lead_keeps_provider_claims_and_rights_unverified(self):
        archive = json.loads((ROOT / "archive.json").read_text(encoding="utf-8"))
        lead = next(item for item in archive["translation_registry"]["edition_leads"] if item["edition_id"] == "hacohen-hosea-fuhs-1971-image-edition")
        sources = {source["source_id"]: source for source in archive["sources"]}
        self.assertEqual(lead["candidate_canon_id"], "eotc-ot-33")
        self.assertEqual(lead["mapping_state"], "uncertain")
        self.assertIs(lead["text_bundled"], False)
        self.assertEqual(lead["rights_classification"], "unknown")
        self.assertIn("1971", lead["edition_statement"])
        self.assertEqual(set(lead["source_ids"]), {"SRC-152", "SRC-034", "SRC-029"})
        self.assertIn("does not establish permission", lead["rights_status"])
        self.assertEqual(sources["SRC-152"]["url"], "https://www.tau.ac.il/~hacohen/Hosea/Information.html")
        self.assertIn("with Prof. Fuhs’s permission", sources["SRC-152"]["inspection_and_limitations"])
        self.assertIn("not independent verification", sources["SRC-152"]["inspection_and_limitations"])

    def test_ta_u_prophet_edition_leads_are_metadata_only_and_cited(self):
        archive = json.loads((ROOT / "archive.json").read_text(encoding="utf-8"))
        leads = {item["edition_id"]: item for item in archive["translation_registry"]["edition_leads"]}
        sources = {source["source_id"]: source for source in archive["sources"]}
        expected = {
            "tau-micah-fuhs-1968": ("eotc-ot-35", "SRC-154", "Micha"),
            "tau-zechariah-lofgren-1930": ("eotc-ot-43", "SRC-159", "Sacharja"),
            "tau-malachi-lofgren-1930": ("eotc-ot-44", "SRC-161", "Maleachi"),
        }
        for edition_id, (canon_id, source_id, source_path) in expected.items():
            with self.subTest(edition=edition_id):
                lead = leads[edition_id]
                self.assertEqual(lead["candidate_canon_id"], canon_id)
                self.assertEqual(lead["mapping_state"], "uncertain")
                self.assertIs(lead["text_bundled"], False)
                self.assertEqual(lead["rights_classification"], "permission_limited")
                self.assertIn(source_id, lead["source_ids"])
                self.assertIn("not", lead["scope_description"].lower())
                self.assertEqual(sources[source_id]["url"], f"https://www.tau.ac.il/~hacohen/{source_path}/Information.html")
                self.assertIn("not", sources[source_id]["inspection_and_limitations"].lower())
        self.assertIn("cannot be stored in another repository", leads["tau-micah-fuhs-1968"]["rights_status"])
        self.assertIn("cannot be stored in another repository", leads["tau-zechariah-lofgren-1930"]["rights_status"])
        for edition_id, canon_id, reader_id, source_id in (
            ("tau-haggai-lofgren-1930", "eotc-ot-42", "haggai-geez-lofgren-ghebre-tau", "SRC-191"),
            ("tau-zephaniah-lofgren-1930", "eotc-ot-41", "zephaniah-geez-lofgren-hacohen-tau", "SRC-190"),
            ("tau-obadiah-bachmann-1892", "eotc-ot-37", "obadiah-geez-bachmann-theot", "SRC-186"),
            ("tau-jonah-lofgren-1930", "eotc-ot-38", "jonah-geez-lofgren-ghebre-tau", "SRC-187"),
            ("tau-nahum-lofgren-1930", "eotc-ot-39", "nahum-geez-lofgren-ghebre-tau", "SRC-188"),
            ("tau-habakkuk-lofgren-1930", "eotc-ot-40", "habakkuk-geez-lofgren-ghebre-tau", "SRC-189"),
        ):
            with self.subTest(bundled_reader=reader_id):
                self.assertNotIn(edition_id, leads)
                entry = next(book for book in archive["canon_registry"]["books"] if book["canon_id"] == canon_id)
                reader = next(item for item in archive["readers"] if item["reader_id"] == reader_id)
                self.assertEqual(entry["reader_id"], reader_id)
                self.assertEqual(reader["canon_id"], canon_id)
                self.assertIn(source_id, reader["source_ids"])

    def test_ethiopic_ezra_nehemia_candidate_crosswalk_stays_unverified(self):
        archive = json.loads((ROOT / "archive.json").read_text(encoding="utf-8"))
        lead = next(item for item in archive["translation_registry"]["edition_leads"] if item["edition_id"] == "pereira-ezra-nehemiah-ethiopic-1919")
        self.assertEqual(lead["candidate_canon_id"], "eotc-ot-15")
        self.assertEqual(lead["mapping_state"], "uncertain")
        self.assertIs(lead["text_bundled"], False)
        self.assertIn("Ezrâ III", lead["scope_description"])
        self.assertIn("SRC-097", lead["source_ids"])
        self.assertIn("French translation", lead["rights_status"])

    def test_language_and_basis_profiles_have_cited_evidence(self):
        archive = json.loads((ROOT / "archive.json").read_text(encoding="utf-8"))
        registry = archive["translation_registry"]
        schema = json.loads((ROOT / "translation-registry.schema.json").read_text(encoding="utf-8"))
        self.assertIn("source_ids", schema["$defs"]["language"]["required"])
        self.assertIn("source_ids", schema["properties"]["basis_languages"]["items"]["required"])
        source_ids = {source["source_id"] for source in archive["sources"]}
        self.assertTrue(registry["basis_languages"])
        self.assertTrue(registry["languages"])
        for profile in registry["basis_languages"] + registry["languages"]:
            with self.subTest(language=profile["language_tag"]):
                self.assertTrue(profile["source_ids"])
                self.assertEqual(set(profile["source_ids"]) - source_ids, set())

    def test_tme15_evidence_is_version_specific_and_keeps_rights_unknown(self):
        archive = json.loads((ROOT / "archive.json").read_text(encoding="utf-8"))
        registry = archive["translation_registry"]
        lead = next(
            item for item in registry["corpus_leads"]
            if item["corpus_id"] == "tigrinya-tme15-bible-society-ethiopia"
        )
        sources = {source["source_id"]: source for source in archive["sources"]}
        self.assertEqual(lead["source_ids"], ["SRC-087", "SRC-147", "SRC-148"])
        self.assertNotIn("SRC-089", lead["source_ids"])  # SRC-089 is a TIG24 copyright sample.
        self.assertEqual(lead["rights_classification"], "unknown")
        self.assertIn("no deuterocanonical heading is visible", lead["scope_description"])
        self.assertIn("not a complete contents", lead["scope_description"])
        self.assertIn("GEN.1", sources["SRC-148"]["url"])
        self.assertIn("not copied into the archive", sources["SRC-148"]["inspection_and_limitations"])

    def test_bundled_language_records_resolve_to_the_declared_reader_layer(self):
        archive = json.loads((ROOT / "archive.json").read_text(encoding="utf-8"))
        readers = {reader["reader_id"]: reader for reader in archive["readers"]}
        bundled = [
            (language["language_tag"], record)
            for language in archive["translation_registry"]["languages"]
            for record in language.get("records", [])
            if record.get("status") == "bundled"
        ]
        self.assertEqual(len(bundled), 33)
        for language_tag, record in bundled:
            with self.subTest(language=language_tag, reader=record.get("reader_id")):
                reader = readers.get(record.get("reader_id"))
                self.assertIsNotNone(reader, "bundled language record must reference an archived reader")
                layer = reader
                if record.get("translation_id"):
                    layer = reader.get("parallel_translation") or reader
                    self.assertEqual(layer.get("translation_id"), record["translation_id"])
                self.assertEqual(layer.get("language_tag"), language_tag)

    def test_reader_scripts_are_supported_by_their_language_profile(self):
        archive = json.loads((ROOT / "archive.json").read_text(encoding="utf-8"))
        profiles = {
            profile["language_tag"]: profile
            for profile in archive["translation_registry"]["languages"]
        }
        for tag, profile in profiles.items():
            codes = profile.get("script_codes")
            with self.subTest(language=tag):
                self.assertTrue(codes, "script_codes must preserve known or explicitly unknown script evidence")
                self.assertEqual(len(codes), len(set(codes)))
                default_script = profile.get("script_code")
                if default_script != "Zzzz":
                    self.assertIn(default_script, codes)
                else:
                    self.assertTrue(profile.get("script_profile_note", "").strip())

        for reader in archive["readers"]:
            tag = reader.get("language_tag")
            script = reader.get("script_code")
            if tag not in profiles or not script:
                continue
            with self.subTest(reader=reader["reader_id"], language=tag, script=script):
                self.assertIn(script, profiles[tag]["script_codes"])

    def test_research_translation_layers_are_not_counted_as_canon_linked(self):
        archive = json.loads((ROOT / "archive.json").read_text(encoding="utf-8"))
        registry = archive["translation_registry"]
        readers = {reader["reader_id"]: reader for reader in archive["readers"]}
        bundled = [
            (language["language_tag"], record)
            for language in registry["languages"]
            for record in language.get("records", [])
            if record.get("status") == "bundled"
        ]
        canon_linked = [
            (language_tag, record)
            for language_tag, record in bundled
            if (reader := readers.get(record.get("reader_id")))
            and reader.get("canon_id")
            and not reader.get("research_corpus_id")
            and reader.get("canon_id") == record.get("canon_id")
        ]
        research = [
            (language_tag, record)
            for language_tag, record in bundled
            if (reader := readers.get(record.get("reader_id")))
            and reader.get("research_corpus_id")
        ]
        self.assertEqual((len(bundled), len(canon_linked), len(research)), (33, 30, 3))
        self.assertEqual(
            {record["reader_id"] for _, record in research},
            {
                "job-brenton-lxx-1851-research",
                "sirach-brenton-lxx-1851-research",
                "tobit-brenton-lxx-1851-research",
            },
        )
        self.assertTrue(all(language_tag == "en" for language_tag, _ in research))

    def test_language_coverage_ui_labels_candidates_and_research_layers(self):
        app = (ROOT / "app.js").read_text(encoding="utf-8")
        self.assertIn("canonLinkedLayerCount", app)
        self.assertIn("researchOnlyEntryCount", app)
        self.assertIn("have canon-linked source-text readers", app)
        self.assertIn("have neither type of reader bundled here", app)
        self.assertIn("researchLanguageCount", app)
        self.assertIn("languageResearchCorpora", app)
        self.assertIn("Open stored text", app)
        self.assertIn("separately scoped research reader", app)
        self.assertIn("reviewed work/title match", app)
        self.assertIn("provisional title candidate", app)
        self.assertIn("not canon-linked", app)
        self.assertIn("Registered source/translation layers: ${readerLanguages.length} of ${languages.length} language/script profiles", app)
        self.assertIn("separately scoped ${researchReaderLabel} across ${researchLanguageCount} profiles (not canon-linked)", app)
        self.assertIn("two-language paths in registered layers", app)
        self.assertIn("researchTranslationsWithKnownPath", app)
        self.assertIn("researchTranslationsWithUnknownPath", app)
        self.assertIn("have unknown basis", app)
        self.assertNotIn("bundledLayers.length} canon-linked text layers", app)

    def test_dawro_and_maale_language_leads_preserve_scope_rights_and_unknowns(self):
        archive = json.loads((ROOT / "archive.json").read_text(encoding="utf-8"))
        registry = archive["translation_registry"]
        profiles = {item["language_tag"]: item for item in registry["languages"]}
        sources = {item["source_id"]: item for item in archive["sources"]}
        self.assertEqual(profiles["dwr"]["script_code"], "Zzzz")
        self.assertIn("script", profiles["dwr"]["script_profile_note"].lower())
        self.assertEqual(profiles["dwr"]["availability_survey"]["result_count"], 3)
        self.assertEqual(profiles["dwr"]["script_codes"], ["Ethi", "Latn"])
        self.assertEqual(profiles["mdy"]["script_code"], "Ethi")
        self.assertEqual(profiles["mdy"]["availability_survey"]["result_count"], 2)
        leads = {item["corpus_id"]: item for item in registry["corpus_leads"]}
        dawro = leads["ethiopia-dawro-ebible-resources"]
        self.assertEqual(dawro["rights_classification"], "mixed")
        self.assertFalse(dawro["text_bundled"])
        self.assertIn("not silently mapped", dawro["scope_description"])
        self.assertIn("CC BY-NC-ND 3.0", dawro["rights_status"])
        self.assertIn("CC BY-SA 4.0", dawro["rights_status"])
        maale = leads["ethiopia-maale-mdyeth-nt-pdf"]
        self.assertEqual(maale["rights_classification"], "open_license")
        self.assertFalse(maale["text_bundled"])
        self.assertIn("27 New Testament books", maale["scope_description"])
        self.assertIn("do not align", maale["scope_description"])
        self.assertEqual(sources["SRC-167"]["url"], "https://ebible.org/pdf/mdyeth/mdyeth_nt.pdf")
        audit = json.loads((ROOT / "language-script-code-audit.json").read_text(encoding="utf-8"))
        self.assertIn("dwr", audit["language_subtags"]["codes"])
        self.assertIn("mdy", audit["language_subtags"]["codes"])
        self.assertIn("dwr", sources["SRC-077"]["inspection_and_limitations"])

    def test_gamo_edition_lead_preserves_license_and_unverified_book_scope(self):
        archive = json.loads((ROOT / "archive.json").read_text(encoding="utf-8"))
        registry = archive["translation_registry"]
        profiles = {item["language_tag"]: item for item in registry["languages"]}
        sources = {item["source_id"]: item for item in archive["sources"]}
        profile = profiles["gmv"]
        self.assertEqual(profile["script_code"], "Zzzz")
        self.assertEqual(profile["script_codes"], ["Ethi", "Latn"])
        self.assertIn("do not establish a language-wide default", profile["script_profile_note"])
        self.assertEqual(profile["availability_survey"]["result_count"], 4)
        self.assertEqual(profile["records"], [])
        leads = {item["corpus_id"]: item for item in registry["corpus_leads"]}
        gamo = leads["ethiopia-gamo-gmve-bible"]
        self.assertFalse(gamo["text_bundled"])
        self.assertEqual(gamo["rights_classification"], "open_license")
        self.assertIn("66 title links", gamo["scope_description"])
        self.assertIn("not an audit", gamo["scope_description"])
        self.assertIn("CC BY-SA 4.0", gamo["rights_status"])
        self.assertNotIn("canon_id", gamo)
        self.assertEqual(sources["SRC-168"]["url"], "https://ebible.org/Bible/details.php?id=gmve")
        self.assertEqual(sources["SRC-169"]["url"], "https://ebible.org/gmve/")
        self.assertEqual(sources["SRC-170"]["url"], "https://ebible.org/pdf/")
        self.assertEqual(sources["SRC-171"]["url"], "research/gamo-menu.html")
        menu = json.loads((ROOT / "research" / "gamo-menu.json").read_text(encoding="utf-8"))
        self.assertEqual(len(menu["entries"]), 66)
        self.assertEqual([item["position"] for item in menu["entries"]], list(range(1, 67)))
        self.assertFalse(menu["raw_html_retained"])
        self.assertFalse(menu["scripture_text_retained"])
        self.assertEqual(len([item for item in menu["entries"] if item.get("reader_id")]), 66)
        menu_page = (ROOT / "research" / "gamo-menu.html").read_text(encoding="utf-8")
        self.assertEqual(menu_page.count('<li class="source-label">'), 66)
        reader_links = re.findall(r'<li class="source-label"><span>.*?</span> <a href="\.\./index\.html\?reader=([^"]+)#reader">', menu_page)
        self.assertEqual(reader_links, [item["reader_id"] for item in menu["entries"]])
        page_labels = re.findall(r'<li class="source-label"><span>(.*?)</span>', menu_page)
        self.assertEqual(page_labels, [item["source_title_label"] for item in menu["entries"]])
        self.assertIn("original online landing-page response is not retained", menu_page)
        audit = json.loads((ROOT / "language-script-code-audit.json").read_text(encoding="utf-8"))
        self.assertIn("gmv", audit["language_subtags"]["codes"])

    def test_repository_language_claims_remain_unverified_and_unbundled(self):
        archive = json.loads((ROOT / "archive.json").read_text(encoding="utf-8"))
        registry = archive["translation_registry"]
        profiles = {item["language_tag"]: item for item in registry["languages"]}
        leads = {item["corpus_id"]: item for item in registry["corpus_leads"]}
        expected = {
            "hdy": ("Hadiyya", "hadiyya-bible-bse-1992", "Ethi", "SRC-173"),
            "nus": ("Nuer", "nuer-bible-bss-1998", "Latn", "SRC-175"),
            "wal": ("Wolaytta", "wolaytta-bible-sim-2004", "Latn", "SRC-172"),
        }
        for tag, (name, corpus_id, script, source_id) in expected.items():
            with self.subTest(language=tag):
                profile = profiles[tag]
                self.assertEqual(profile["language_name"], name)
                self.assertEqual(profile["script_code"], script)
                self.assertEqual(profile["availability_survey"]["status"], "completed")
                self.assertEqual(profile["records"], [])
                lead = leads[corpus_id]
                self.assertFalse(lead["text_bundled"])
                self.assertIn(lead["rights_classification"], {"unknown", "all_rights_reserved", "permission_limited"})
                if tag == "wal":
                    self.assertEqual(lead["script_code"], "Latn")
                    self.assertEqual(lead["script_status"], "identified")
                    self.assertIn("inline sample", lead["review_status"])
                self.assertIsNone(lead["translation_path"])
                self.assertIn("not", lead["review_status"].lower())
                self.assertIn(source_id, lead["source_ids"])
        self.assertIn("license or permission grant", leads["hadiyya-bible-bse-1992"]["rights_status"])
        self.assertIn("RESERVED", leads["nuer-bible-bss-1998"]["rights_status"])
        self.assertIn("CC BY-NC-ND", leads["wolaytta-bible-sim-2004"]["rights_status"])
        audit = json.loads((ROOT / "language-script-code-audit.json").read_text(encoding="utf-8"))
        for tag in expected:
            self.assertIn(tag, audit["language_subtags"]["codes"])


if __name__ == "__main__":
    unittest.main()
