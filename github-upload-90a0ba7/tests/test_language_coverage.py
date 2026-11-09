import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class LanguageCoverageTests(unittest.TestCase):
    def test_ethiopic_joel_lead_stays_unbundled_and_rights_limited(self):
        archive = json.loads((ROOT / "archive.json").read_text(encoding="utf-8"))
        registry = archive["translation_registry"]
        lead = next(item for item in registry["edition_leads"] if item["edition_id"] == "hacohen-joel-dillmann-1879-online-text-2024")
        sources = {source["source_id"]: source for source in archive["sources"]}
        self.assertEqual(lead["candidate_canon_id"], "eotc-ot-36")
        self.assertEqual(lead["mapping_state"], "uncertain")
        self.assertIs(lead["text_bundled"], False)
        self.assertEqual(lead["rights_classification"], "permission_limited")
        self.assertEqual(set(lead["source_ids"]), {"SRC-029", "SRC-036", "SRC-149"})
        self.assertIn("noncommercial", lead["rights_status"])
        self.assertIn("1879", lead["edition_statement"])
        self.assertIn("2024", lead["edition_statement"])
        self.assertEqual(sources["SRC-149"]["url"], "https://www.tau.ac.il/~hacohen/Joel/Information.html")
        self.assertNotIn("joel", " ".join(reader["reader_id"].lower() for reader in archive["readers"]))

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

    def test_ethiopic_amos_lead_preserves_layer_specific_rights_uncertainty(self):
        archive = json.loads((ROOT / "archive.json").read_text(encoding="utf-8"))
        lead = next(item for item in archive["translation_registry"]["edition_leads"] if item["edition_id"] == "hacohen-amos-pereira-1917-online-text")
        sources = {source["source_id"]: source for source in archive["sources"]}
        self.assertEqual(lead["candidate_canon_id"], "eotc-ot-34")
        self.assertEqual(lead["mapping_state"], "uncertain")
        self.assertIs(lead["text_bundled"], False)
        self.assertEqual(lead["rights_classification"], "unknown")
        self.assertIn("SRC-151", lead["source_ids"])
        self.assertIn("Kefela Ghebre", lead["edition_statement"])
        self.assertIn("scope for that transcription", lead["rights_status"])
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
            "tau-obadiah-bachmann-1892": ("eotc-ot-37", "SRC-153", "Obadia"),
            "tau-micah-fuhs-1968": ("eotc-ot-35", "SRC-154", "Micha"),
            "tau-nahum-lofgren-1930": ("eotc-ot-39", "SRC-155", "Nahum"),
            "tau-jonah-lofgren-1930": ("eotc-ot-38", "SRC-156", "Jona"),
            "tau-habakkuk-lofgren-1930": ("eotc-ot-40", "SRC-157", "Habakuk"),
            "tau-zephaniah-lofgren-1930": ("eotc-ot-41", "SRC-158", "Zephanja"),
            "tau-zechariah-lofgren-1930": ("eotc-ot-43", "SRC-159", "Sacharja"),
            "tau-haggai-lofgren-1930": ("eotc-ot-42", "SRC-160", "Haggai"),
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
        self.assertEqual(len(bundled), 23)
        for language_tag, record in bundled:
            with self.subTest(language=language_tag, reader=record.get("reader_id")):
                reader = readers.get(record.get("reader_id"))
                self.assertIsNotNone(reader, "bundled language record must reference an archived reader")
                layer = reader
                if record.get("translation_id"):
                    layer = reader.get("parallel_translation") or reader
                    self.assertEqual(layer.get("translation_id"), record["translation_id"])
                self.assertEqual(layer.get("language_tag"), language_tag)

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
        self.assertEqual((len(bundled), len(canon_linked), len(research)), (23, 20, 3))
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
        self.assertIn("researchLayerCount", app)
        self.assertIn("Research candidate:", app)
        self.assertIn("not canon-linked coverage", app)
        self.assertIn("two-language translation paths recorded", app)
        self.assertNotIn("bundledLayers.length} canon-linked text layers", app)

    def test_dawro_and_maale_language_leads_preserve_scope_rights_and_unknowns(self):
        archive = json.loads((ROOT / "archive.json").read_text(encoding="utf-8"))
        registry = archive["translation_registry"]
        profiles = {item["language_tag"]: item for item in registry["languages"]}
        sources = {item["source_id"]: item for item in archive["sources"]}
        self.assertEqual(profiles["dwr"]["script_code"], "Zzzz")
        self.assertIn("script", profiles["dwr"]["script_profile_note"].lower())
        self.assertEqual(profiles["dwr"]["availability_survey"]["result_count"], 2)
        self.assertEqual(profiles["mdy"]["script_code"], "Ethi")
        self.assertEqual(profiles["mdy"]["availability_survey"]["result_count"], 2)
        leads = {item["corpus_id"]: item for item in registry["corpus_leads"]}
        dawro = leads["ethiopia-dawro-ebible-resources"]
        self.assertEqual(dawro["rights_classification"], "mixed")
        self.assertFalse(dawro["text_bundled"])
        self.assertIn("does not map", dawro["scope_description"])
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
        self.assertEqual(profile["script_code"], "Ethi")
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
        menu_page = (ROOT / "research" / "gamo-menu.html").read_text(encoding="utf-8")
        self.assertEqual(menu_page.count('<li class="source-label">'), 66)
        page_labels = re.findall(r'<li class="source-label">(.*?)</li>', menu_page)
        self.assertEqual(page_labels, [item["source_title_label"] for item in menu["entries"]])
        self.assertIn("not the scripture text", menu_page)
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
            "wal": ("Wolaytta", "wolaytta-bible-sim-2004", "Zzzz", "SRC-172"),
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
