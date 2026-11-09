import json
import unittest
from pathlib import Path

from coverage_summary import build_coverage_statement
from build_standalone import validate_closed_schema_objects


ROOT = Path(__file__).resolve().parents[1]


class IntegrityPrinciplesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.archive = json.loads((ROOT / "archive.json").read_text(encoding="utf-8"))
        cls.app = (ROOT / "app.js").read_text(encoding="utf-8")
        cls.index = (ROOT / "index.html").read_text(encoding="utf-8")

    def test_displayed_coverage_is_derived_from_the_actual_bundled_records(self):
        registry = self.archive["translation_registry"]
        canon = self.archive["canon_registry"]
        statement = build_coverage_statement(registry, canon)
        bundled_ids = {
            record.get("canon_id")
            for language in registry["languages"]
            for record in language.get("records", [])
            if record.get("status") == "bundled"
            and record.get("layer_role") in {"source_text_transcription", "source_text_edition"}
            and record.get("canon_id")
        }
        listed_ids = {book["canon_id"] for book in canon["books"]}
        actual_count = len(bundled_ids & listed_ids)
        self.assertIn(f"{actual_count} currently link to bundled source-text readers", statement)
        self.assertIn(f"{len(listed_ids) - actual_count} have no reader bundled in this archive", statement)
        self.assertIn("not a claim that no edition exists elsewhere", statement)
        self.assertIn("not surveyed or unknown, never zero by default", statement)

    def test_visible_copy_keeps_unbundled_unknown_and_generated_text_distinct(self):
        self.assertIn("not worldwide availability", self.app)
        self.assertIn("not surveyed", self.app)
        self.assertIn("unknown", self.app)
        self.assertIn("Machine-generated wording may appear only as a labeled draft", self.app)
        self.assertIn("never counted or presented as verified scripture or translation", self.app)

    def test_reader_header_reports_observed_units_per_active_witness(self):
        self.assertIn("unit count unknown for", self.app)
        self.assertIn("${layer.unit_count.toLocaleString()} ${layer.unit_label || 'source units'} observed", self.app)
        self.assertIn("mode === 'parallel' && companion ? [reader, companion]", self.app)
        self.assertIn("Observed source units are structural counts, not completeness or accuracy claims.", self.index)
        self.assertIn("Measured from the actual reader records", self.app)
        self.assertIn("never contributes to coverage counts", self.app)

    def test_brenton_companions_preserve_source_scope_and_markup(self):
        from build_brenton_octateuch import BOOKS, READER_FILE, validate
        expected_units = {"PSA": 2535, "LEV": 859, "NUM": 1288, "DEU": 958, "JOS": 659, "JDG": 618}
        expected_notes = {"PSA": 311, "LEV": 0, "NUM": 151, "DEU": 155, "JOS": 124, "JDG": 160}
        validate()
        for code, (slug, _number, title, chapter_count) in BOOKS.items():
            with self.subTest(book=title):
                reader_file = READER_FILE.get(code, f"{slug}-geez.json")
                reader = json.loads((ROOT / "readers" / reader_file).read_text(encoding="utf-8"))
                companion = reader["parallel_translation"]
                self.assertEqual(companion["chapter_count"], chapter_count)
                self.assertEqual(len(companion["chapters"]), chapter_count)
                self.assertEqual(companion["unit_count"], expected_units[code])
                self.assertEqual(companion["note_count"], expected_notes[code])
                self.assertEqual(companion["basis_language_tag"], "grc")
                self.assertIn("not a direct", companion["translation_basis"])
                self.assertIn("no independent collation", companion["verification_status"])
                self.assertTrue(all(chapter["verses"] for chapter in companion["chapters"]))
                self.assertTrue(all(note.get("text") for chapter in companion["chapters"] for note in chapter.get("notes", [])))
                self.assertIn("SRC-142", companion["source_ids"])
                if code == "PSA":
                    self.assertEqual(companion["structural_marker_counts"], {"p": 520, "d": 150, "p_inline_text_segments": 88})
                    self.assertEqual(companion["continuation_segment_count"], 88)
        source = next(item for item in self.archive["sources"] if item["source_id"] == "SRC-142")
        self.assertIn("USFM zip", source["inspection_and_limitations"])
        self.assertEqual(source["url"], "https://ebible.org/details.php?id=eng-Brenton")
        self.assertEqual(self.archive["translation_registry"]["languages"][1]["language_tag"], "en")
        leviticus = json.loads((ROOT / "readers" / "leviticus-geez.json").read_text(encoding="utf-8"))["parallel_translation"]
        self.assertIn("⟦any⟧", leviticus["chapters"][0]["verses"][1]["text"])
        numbers = json.loads((ROOT / "readers" / "numbers-geez.json").read_text(encoding="utf-8"))["parallel_translation"]
        notes = numbers["chapters"][0]["notes"]
        self.assertTrue(notes)
        self.assertEqual(notes[0]["verse"], "3")
        self.assertNotIn("Source note reference 1:3.", notes[0]["text"])
        self.assertIn("Gr. force.", notes[0]["text"])

    def test_ethiopicbible_job_page_is_discovery_evidence_only(self):
        sources = {source["source_id"]: source for source in self.archive["sources"]}
        homepage = sources["SRC-136"]
        job_page = sources["SRC-137"]
        self.assertIn("not a Church-issued canon authority", homepage["inspection_and_limitations"])
        self.assertIn("all rights reserved", homepage["inspection_and_limitations"])
        self.assertIn("numbered Geʽez and English lines 1–22", job_page["inspection_and_limitations"])
        self.assertIn("does not establish the rest of Job", job_page["inspection_and_limitations"])
        self.assertIn("No scripture text copied", job_page["inspection_and_limitations"])
        self.assertEqual(len(self.archive["readers"]), 53)
        self.assertNotIn("SRC-137", {
            source_id
            for reader in self.archive["readers"]
            for source_id in reader.get("source_ids", [])
        })

    def test_internet_archive_job_scan_metadata_is_not_treated_as_a_license_or_text(self):
        source = next(item for item in self.archive["sources"] if item["source_id"] == "SRC-109")
        lead = next(
            item for item in self.archive["translation_registry"]["edition_leads"]
            if item["edition_id"] == "pereira-job-ethiopic-1907"
        )
        self.assertIn("710 pages", source["inspection_and_limitations"])
        self.assertIn("OCR-detected language French", source["inspection_and_limitations"])
        self.assertIn("NOT_IN_COPYRIGHT", source["inspection_and_limitations"])
        self.assertIn("not a license", source["inspection_and_limitations"])
        self.assertIn("not a license", lead["rights_status"])
        self.assertIn("French OCR detection", lead["review_status"])

    def test_cpradmin_geez_corpus_claim_is_recorded_as_unverified_discovery_only(self):
        sources = {source["source_id"]: source for source in self.archive["sources"]}
        lead = next(
            item for item in self.archive["translation_registry"]["corpus_leads"]
            if item["corpus_id"] == "cpradmin-ethiopian-bible-geez-text-lead"
        )
        self.assertIn("later, broader metadata inspection SRC-141", sources["SRC-039"]["inspection_and_limitations"])
        self.assertIn("not independent witnesses", sources["SRC-039"]["inspection_and_limitations"])
        self.assertIn("data/canon.json", sources["SRC-141"]["inspection_and_limitations"])
        self.assertIn("six category counts total 91", sources["SRC-141"]["inspection_and_limitations"])
        self.assertIn("item-level", sources["SRC-141"]["inspection_and_limitations"])
        self.assertIn("no reader coverage added", sources["SRC-141"]["inspection_and_limitations"])
        self.assertIn("SRC-141", lead["source_ids"])
        self.assertFalse(lead["text_bundled"])
        self.assertEqual(lead["rights_classification"], "unknown")
        self.assertIsNone(lead["translation_path"])
        self.assertIn("chapter payload and Geʽez text were not downloaded or audited", lead["scope_description"])
        self.assertIn("have not been independently audited", lead["review_status"])
        self.assertIn("not counted as reader coverage", lead["review_status"])
        self.assertIn("not adopted as canon", lead["notes"])

    def test_user_flagged_pdf_source_is_retained_but_outbound_link_is_withheld(self):
        sources = {source["source_id"]: source for source in self.archive["sources"]}
        source = sources["SRC-004"]
        app = (ROOT / "app.js").read_text(encoding="utf-8")
        self.assertEqual(source["link_status"], "withheld")
        self.assertIn("browser screenshot supplied with this project", source["link_warning"])
        self.assertIn("not an independent malware analysis", source["inspection_and_limitations"])
        self.assertNotIn("wsimg.com", source["url"])
        self.assertIn("if (source.link_status === 'withheld')", app)
        self.assertIn("sourceLinkHTML(source)", app)
        self.assertIn("External source link withheld", app)

    def test_multilingual_github_repositories_are_unbundled_rights_cautious_leads(self):
        registry = self.archive["translation_registry"]
        leads = {
            lead["corpus_id"]: lead
            for lead in registry["corpus_leads"]
        }
        expected = {
            "biniama-ethiopic-bible-data-amharic-66book-lead": "am",
            "biniama-ethiopic-bible-data-english-kjv-66book-lead": "en",
            "biniama-ethiopic-bible-data-geez-partial-lead": "gez",
        }
        sources = {source["source_id"]: source for source in self.archive["sources"]}
        source_ids = {source["source_id"] for source in self.archive["sources"]}
        for corpus_id, language_tag in expected.items():
            with self.subTest(corpus_id=corpus_id):
                lead = leads[corpus_id]
                self.assertEqual(lead["language_tag"], language_tag)
                self.assertFalse(lead["text_bundled"])
                self.assertEqual(lead["rights_classification"], "unknown")
                self.assertTrue(set(lead["source_ids"]) <= source_ids)
                self.assertIn("remains unresolved", lead["rights_status"])
        self.assertIn("1,189 chapters", sources["SRC-139"]["inspection_and_limitations"])
        self.assertIn("Apache-2.0", sources["SRC-139"]["inspection_and_limitations"])
        self.assertIn("does not by itself establish rights", sources["SRC-140"]["inspection_and_limitations"])
        for corpus_id in expected:
            self.assertIn("No reader text is bundled.", leads[corpus_id]["scope_description"])

    def test_unknown_external_availability_is_not_a_zero_result(self):
        registry = self.archive["translation_registry"]
        self.assertTrue(registry["languages"])
        for language in registry["languages"]:
            with self.subTest(language=language["language_tag"]):
                survey = language["availability_survey"]
                if survey["status"] == "not_surveyed":
                    self.assertNotIn("result_count", survey)
                    self.assertNotIn("result", survey)

    def test_amharic_provider_inventory_stays_bounded_and_unbundled(self):
        registry = self.archive["translation_registry"]
        language = next(x for x in registry["languages"] if x["language_tag"] == "am")
        survey = language["availability_survey"]
        lead = next(
            x for x in registry["corpus_leads"]
            if x["corpus_id"] == "amharic-amh2000-biblecom-provider-record"
        )
        source_ids = {source["source_id"] for source in self.archive["sources"]}
        self.assertEqual(survey["result_count"], 5)
        self.assertEqual(survey["result"], "records_found")
        self.assertIn("not a census", survey["scope"])
        self.assertTrue(set(survey["source_ids"]) <= source_ids)
        self.assertFalse(lead["text_bundled"])
        self.assertEqual(lead["rights_classification"], "unknown")
        self.assertIsNone(lead["translation_path"])
        self.assertIn("not prove an exact EOTC", lead["scope_description"])
        self.assertEqual(len(registry["languages"]), 22)
        self.assertIn("11 currently link to bundled source-text readers", registry["coverage_statement"])

    def test_oromo_catalogue_evidence_keeps_copyright_and_mapping_limits(self):
        registry = self.archive["translation_registry"]
        language = next(x for x in registry["languages"] if x["language_tag"] == "gaz")
        survey = language["availability_survey"]
        lead = next(
            x for x in registry["corpus_leads"]
            if x["corpus_id"] == "west-central-oromo-macqul-biblecom-provider-record"
        )
        source_ids = {source["source_id"] for source in self.archive["sources"]}
        self.assertEqual(language["language_name"], "West Central Oromo (Afaan Oromoo)")
        self.assertEqual(survey["result_count"], 3)
        self.assertTrue(set(survey["source_ids"]) <= source_ids)
        self.assertFalse(lead["text_bundled"])
        self.assertEqual(lead["rights_classification"], "unknown")
        self.assertIn("1997", lead["rights_status"])
        self.assertIsNone(lead["translation_path"])
        self.assertIn("No exact Ethiopian Orthodox Tewahedo canon crosswalk", lead["scope_description"])

    def test_somali_catalogue_count_does_not_claim_full_text_or_clear_rights(self):
        registry = self.archive["translation_registry"]
        language = next(x for x in registry["languages"] if x["language_tag"] == "so")
        survey = language["availability_survey"]
        lead = next(
            x for x in registry["corpus_leads"]
            if x["corpus_id"] == "somali-som08-biblecom-provider-record"
        )
        source_ids = {source["source_id"] for source in self.archive["sources"]}
        self.assertEqual(survey["result_count"], 4)
        self.assertTrue(set(survey["source_ids"]) <= source_ids)
        self.assertFalse(lead["text_bundled"])
        self.assertEqual(lead["rights_classification"], "unknown")
        self.assertEqual(lead["publication_year"], "2008 (provider-stated publication year)")
        self.assertIsNone(lead["translation_path"])
        self.assertIn("not audited all listed destinations", lead["scope_description"])

    def test_afar_visible_listing_preserves_unresolved_additional_record(self):
        registry = self.archive["translation_registry"]
        language = next(x for x in registry["languages"] if x["language_tag"] == "aa")
        survey = language["availability_survey"]
        lead = next(
            x for x in registry["corpus_leads"]
            if x["corpus_id"] == "afar-qafar-nkm-biblecom-provider-record"
        )
        source_ids = {source["source_id"] for source in self.archive["sources"]}
        self.assertEqual(survey["result_count"], 1)
        self.assertIn("additional Qafar text Bible", survey["notes"])
        self.assertTrue(set(survey["source_ids"]) <= source_ids)
        self.assertFalse(lead["text_bundled"])
        self.assertEqual(lead["rights_classification"], "unknown")
        self.assertIn("no New Testament section is visible", lead["scope_description"])
        self.assertIn("not resolved by this survey", lead["notes"])

    def test_saho_survey_measures_distinct_observed_resources_without_claiming_completeness(self):
        registry = self.archive["translation_registry"]
        language = next(x for x in registry["languages"] if x["language_tag"] == "ssy")
        survey = language["availability_survey"]
        lead = next(
            x for x in registry["corpus_leads"]
            if x["corpus_id"] == "eritrea-saho-scc-biblecom-listing"
        )
        self.assertEqual(survey["result_count"], 2)
        self.assertIn("Two distinct Saho text resources", survey["scope"])
        self.assertIn("not a Saho scripture census", survey["scope"])
        self.assertFalse(lead["text_bundled"])
        self.assertEqual(lead["rights_classification"], "unknown")
        self.assertIn("sampled page proves a text page is accessible", lead["notes"])
        gospels = next(x for x in registry["corpus_leads"] if x["corpus_id"] == "eritrea-saho-four-gospels")
        self.assertEqual(gospels["script_code"], "Latn")
        self.assertEqual(gospels["publication_year"].split()[0], "2020")
        self.assertFalse(gospels["text_bundled"])
        self.assertIn("format conversion", gospels["rights_status"])


    def test_bundled_exodus_companion_is_not_duplicated_as_an_unbundled_lead(self):
        registry = self.archive["translation_registry"]
        exodus_layers = [
            x for x in registry["languages"]
            if x["language_tag"] == "en"
        ][0]["records"]
        companion = next(
            x for x in exodus_layers
            if x.get("translation_id") == "exodus-english-brenton-lxx-1851"
        )
        duplicate_leads = [
            x for x in registry["translation_leads"]
            if x["canon_id"] == "eotc-ot-02"
            and x["language_tag"] == "en"
            and x["translator"] == "Sir Lancelot Charles Lee Brenton"
        ]
        self.assertEqual(companion["status"], "bundled")
        self.assertFalse(duplicate_leads)
        self.assertEqual(companion["translation_path"], ["grc", "en"])

    def test_charles_enoch_english_path_is_supported_but_not_mistaken_for_aligned_text(self):
        registry = self.archive["translation_registry"]
        lead = next(
            x for x in registry["translation_leads"]
            if x["canon_id"] == "eotc-ot-14"
            and x["language_tag"] == "en"
            and x["translator"].startswith("R. H. Charles")
        )
        sources = {source["source_id"]: source for source in self.archive["sources"]}
        self.assertEqual(lead["translation_path"], ["gez", "en"])
        self.assertIn("SRC-133", lead["source_ids"])
        self.assertIn("editor’s Ethiopic text", sources["SRC-133"]["inspection_and_limitations"])
        self.assertFalse(lead["text_bundled"])
        self.assertEqual(lead["rights_classification"], "mixed")
        self.assertIn("does not prove Charles used the same Ethiopic recension", lead["notes"])

    def test_sidamo_profile_keeps_observed_script_and_rights_separate(self):
        registry = self.archive["translation_registry"]
        language = next(x for x in registry["languages"] if x["language_tag"] == "sid")
        lead = next(
            x for x in registry["corpus_leads"]
            if x["corpus_id"] == "sidamo-qulmax-biblecom-provider-record"
        )
        self.assertEqual(language["script_code"], "Zzzz")
        self.assertEqual(language["script_codes"], ["Latn"])
        self.assertIn("not as an exhaustive", language["script_profile_note"])
        self.assertFalse(lead["text_bundled"])
        self.assertEqual(lead["rights_classification"], "unknown")
        self.assertIsNone(lead["translation_path"])
        self.assertIn("2014", lead["rights_status"])

    def test_beja_new_testament_stays_a_bounded_unbundled_lead(self):
        registry = self.archive["translation_registry"]
        language = next(x for x in registry["languages"] if x["language_tag"] == "bej")
        survey = language["availability_survey"]
        lead = next(
            x for x in registry["corpus_leads"]
            if x["corpus_id"] == "beja-ugalad-ugayi-new-testament"
        )
        source_ids = {source["source_id"] for source in self.archive["sources"]}
        self.assertEqual(survey["result_count"], 1)
        self.assertTrue(set(survey["source_ids"]) <= source_ids)
        self.assertFalse(lead["text_bundled"])
        self.assertEqual(lead["rights_classification"], "unknown")
        self.assertEqual(lead["basis_language_tag"], "und")
        self.assertIsNone(lead["translation_path"])
        self.assertIn("No claim of a complete Bible", lead["scope_description"])
        self.assertIn("not establish the orthography", lead["notes"])

    def test_nalca_bible_is_not_misattributed_to_eritrean_nara(self):
        registry = self.archive["translation_registry"]
        language = next(x for x in registry["languages"] if x["language_tag"] == "nrb")
        survey = language["availability_survey"]
        source = next(x for x in self.archive["sources"] if x["source_id"] == "SRC-128")
        self.assertEqual(survey["status"], "not_surveyed")
        self.assertNotIn("result_count", survey)
        self.assertIn("Nalca (nlc), not Eritrean Nara", survey["notes"])
        self.assertIn("not an Eritrean Nara source", source["archive_status"])

    def test_dillmann_scan_discovery_lead_does_not_become_book_coverage(self):
        registry = self.archive["translation_registry"]
        lead = next(
            item for item in registry["corpus_leads"]
            if item["corpus_id"] == "dillmann-ethiopic-historical-books-1861-1871"
        )
        source_ids = {source["source_id"] for source in self.archive["sources"]}
        self.assertFalse(lead["text_bundled"])
        self.assertEqual(lead["rights_classification"], "unknown")
        self.assertTrue(set(lead["source_ids"]) <= source_ids)
        self.assertIn("not been audited", lead["scope_description"])
        self.assertNotIn("reader_id", lead)
        canon_ids = {
            reader.get("canon_id") for reader in self.archive["readers"]
            if reader.get("canon_id")
        }
        self.assertEqual(len(canon_ids), 11)

    def test_book_level_source_editions_have_a_separate_v2_record_and_visible_card(self):
        registry = self.archive["translation_registry"]
        schema = json.loads((ROOT / "translation-registry.schema.json").read_text(encoding="utf-8"))
        lead = next(
            item for item in registry["edition_leads"]
            if item["edition_id"] == "pilkington-proverbs-ethiopic-1978"
        )
        self.assertEqual(registry["schema_version"], 2)
        self.assertEqual(schema["properties"]["schema_version"]["const"], 2)
        self.assertIn("edition_leads", schema["required"])
        self.assertFalse(schema["$defs"]["editionLead"]["additionalProperties"])
        self.assertIn("rights_classification", schema["$defs"]["editionLead"]["required"])
        self.assertFalse(lead["text_bundled"])
        self.assertEqual(lead["mapping_state"], "uncertain")
        self.assertEqual(lead["rights_classification"], "unknown")
        self.assertIn("Source edition leads · not bundled as reader text", self.app)
        self.assertIn("editionLeads.map", self.app)

    def test_translation_registry_schema_covers_the_bundled_research_reader_records(self):
        registry = json.loads((ROOT / "translation-registry.json").read_text(encoding="utf-8"))
        schema = json.loads((ROOT / "translation-registry.schema.json").read_text(encoding="utf-8"))
        validate_closed_schema_objects(registry, schema, schema, "translation-registry.json")
        self.assertIn("research_corpora", schema["required"])
        self.assertIn("researchCorpus", schema["$defs"])
        self.assertEqual(len(registry["research_corpora"]), 42)
        job = next(item for item in registry["research_corpora"] if item["corpus_id"] == "brenton-job-lxx-1851")
        self.assertEqual(job["text_origin"], "published_translation")
        self.assertEqual(job["translation_path"], ["grc", "en"])
        tobit = next(item for item in registry["research_corpora"] if item["corpus_id"] == "brenton-tobit-lxx-1851")
        self.assertEqual(tobit["candidate_canon_id"], "eotc-ot-17")
        self.assertEqual(tobit["canon_mapping_state"], "uncertain")
        self.assertIn("provisional", tobit["canon_mapping_note"])
        self.assertIn("245 English verse labels", tobit["unit_summary"])

    def test_coverage_summary_counts_edition_leads_separately_from_readers(self):
        registry = self.archive["translation_registry"]
        statement = registry["coverage_statement"]
        expected_leads = sum(
            len(registry.get(key, []))
            for key in ("translation_leads", "edition_leads", "corpus_leads")
        )
        self.assertIn("11 currently link to bundled source-text readers", statement)
        self.assertIn("70 have no reader bundled in this archive", statement)
        self.assertIn(f"{expected_leads} unbundled translation, source-edition, or corpus leads", statement)

    def test_job_edition_lead_preserves_catalog_scope_and_unknown_reuse_rights(self):
        registry = self.archive["translation_registry"]
        lead = next(
            item for item in registry["edition_leads"]
            if item["edition_id"] == "pereira-job-ethiopic-1907"
        )
        self.assertEqual(lead["candidate_canon_id"], "eotc-ot-22")
        self.assertEqual(lead["mapping_state"], "uncertain")
        self.assertFalse(lead["text_bundled"])
        self.assertEqual(lead["rights_classification"], "unknown")
        self.assertIn("not establish the exact boundaries or completeness", lead["scope_description"])
        total_leads = sum(len(registry.get(key, [])) for key in ("translation_leads", "edition_leads", "corpus_leads"))
        self.assertIn(f"{total_leads} unbundled translation, source-edition, or corpus leads", registry["coverage_statement"])

    def test_esther_lead_preserves_fragment_and_rights_limits(self):
        registry = self.archive["translation_registry"]
        lead = next(
            item for item in registry["edition_leads"]
            if item["edition_id"] == "pereira-esther-ethiopic-1913"
        )
        self.assertEqual(lead["candidate_canon_id"], "eotc-ot-19")
        self.assertFalse(lead["text_bundled"])
        self.assertEqual(lead["rights_classification"], "permission_limited")
        self.assertIn("A–F", lead["scope_description"])
        self.assertIn("repeats 3 and 8", lead["scope_description"])
        self.assertIn("noncommercial purposes", lead["rights_status"])

    def test_tobit_dillmann_lead_is_supported_but_not_admitted_as_reader_text(self):
        registry = self.archive["translation_registry"]
        lead = next(
            item for item in registry["edition_leads"]
            if item["edition_id"] == "dillmann-tobit-ethiopic-1894"
        )
        source_ids = {source["source_id"] for source in self.archive["sources"]}
        self.assertEqual(lead["candidate_canon_id"], "eotc-ot-17")
        self.assertEqual(lead["mapping_state"], "uncertain")
        self.assertFalse(lead["text_bundled"])
        self.assertEqual(lead["rights_classification"], "permission_limited")
        self.assertTrue(set(lead["source_ids"]) <= source_ids)
        self.assertIn("SRC-134", lead["source_ids"])
        self.assertIn("pages 11–27", lead["scope_description"])
        self.assertIn("page range is bibliographic", lead["scope_description"])
        self.assertIn("not been retrieved or audited", lead["scope_description"])
        self.assertIn("Public Domain Mark 1.0", lead["rights_status"])
        self.assertIn("noncommercial copying", lead["rights_status"])
        self.assertIn("does not by itself resolve rights", lead["rights_status"])
        self.assertIn("20 manuscript-record attestations", lead["scope_description"])
        witness = next(
            item for item in registry["edition_leads"]
            if item["edition_id"] == "emip-mekane-yesus-4-tobit-20c"
        )
        self.assertEqual(witness["candidate_canon_id"], "eotc-ot-17")
        self.assertEqual(witness["mapping_state"], "uncertain")
        self.assertFalse(witness["text_bundled"])
        self.assertEqual(witness["language_tag"], "mul")
        self.assertEqual(witness["language_name"], "Multiple languages")
        self.assertEqual(witness["language_tags"], ["gez", "am"])
        self.assertEqual(witness["script_code"], "Zzzz")
        self.assertIn("folios 100r–103v", witness["scope_description"])
        self.assertEqual(witness["rights_classification"], "unknown")
        self.assertIn("SRC-135", witness["source_ids"])
        self.assertIn("SRC-077", witness["source_ids"])
        identifier_audit = json.loads((ROOT / "language-script-code-audit.json").read_text(encoding="utf-8"))
        self.assertIn("mul", identifier_audit["language_subtags"]["codes"])
        self.assertIn("11 currently link to bundled source-text readers", registry["coverage_statement"])
        canon_linked_readers = {
            record.get("canon_id")
            for language in registry["languages"]
            for record in language.get("records", [])
            if record.get("status") == "bundled"
            and record.get("layer_role") in {"source_text_transcription", "source_text_edition"}
            and record.get("canon_id")
        }
        self.assertNotIn("eotc-ot-17", canon_linked_readers)
        self.assertIn("11 currently link to bundled source-text readers", registry["coverage_statement"])

    def test_related_dillmann_leads_keep_titles_rights_and_uncertain_crosswalks(self):
        registry = self.archive["translation_registry"]
        expected = {
            "dillmann-judith-ethiopic-1894": "eotc-ot-18",
            "dillmann-sirac-ethiopic-1894": "eotc-ot-45",
            "dillmann-wisdom-solomon-ethiopic-1894": "eotc-ot-26",
        }
        leads = {item["edition_id"]: item for item in registry["edition_leads"]}
        for edition_id, canon_id in expected.items():
            with self.subTest(edition_id=edition_id):
                lead = leads[edition_id]
                self.assertEqual(lead["candidate_canon_id"], canon_id)
                self.assertEqual(lead["mapping_state"], "uncertain")
                self.assertFalse(lead["text_bundled"])
                self.assertEqual(lead["rights_classification"], "permission_limited")
                self.assertIn("SRC-112", lead["source_ids"])
                self.assertIn("not been audited", lead["review_status"])


if __name__ == "__main__":
    unittest.main()
