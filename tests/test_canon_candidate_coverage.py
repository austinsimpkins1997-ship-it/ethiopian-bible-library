import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class CanonCandidateCoverageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.archive = json.loads((ROOT / "archive.json").read_text(encoding="utf-8"))
        cls.app = (ROOT / "app.js").read_text(encoding="utf-8")
        cls.books = cls.archive["canon_registry"]["books"]
        cls.readers = cls.archive["readers"]
        cls.translation_registry = cls.archive["translation_registry"]

    def test_candidate_records_do_not_inflate_bundled_reader_count(self):
        reader_canon_ids = {reader.get("canon_id") for reader in self.readers if reader.get("canon_id")}
        candidate_canon_ids = {
            record.get("candidate_canon_id")
            for group in ("translation_leads", "edition_leads", "corpus_leads", "research_corpora")
            for record in self.translation_registry.get(group, [])
            if record.get("candidate_canon_id") and record.get("mapping_state") not in {"related_work", "not_mapped"}
        }
        bundled = [book for book in self.books if book["canon_id"] in reader_canon_ids]
        unbundled = [book for book in self.books if book["canon_id"] not in reader_canon_ids]
        candidates = [book for book in unbundled if book["canon_id"] in candidate_canon_ids]

        self.assertEqual((len(bundled), len(unbundled), len(candidates), len(unbundled) - len(candidates)), (19, 62, 60, 2))
        self.assertIn("const candidateEntryCount = state.canonBooks.filter(book => !readerForCanon(book)", self.app)
        self.assertIn("Church-listed entries have canon-linked reader text", self.app)
        self.assertIn("candidate records are research or bibliographic leads", self.app.lower())
        self.assertIn("have no canon-linked reader here", self.app.lower())
        self.assertIn("separately bundled research reader surfaced from the catalogue", self.app.lower())
        self.assertIn("Related research text available; canon link unverified — see its reader button", self.app)
        self.assertIn("related church-list entry (not a crosswalk)", self.app.lower())
        self.assertIn("no church-list crosswalk assigned", self.app.lower())
        self.assertIn("No candidate recorded here does not mean no source exists elsewhere.", self.app)

    def test_philemon_research_layers_are_discoverable_but_not_canon_linked(self):
        candidates = [
            item for item in self.translation_registry["research_corpora"]
            if item.get("candidate_canon_id") == "eotc-nt-18"
        ]
        reader_ids = {item["reader_id"] for item in candidates}
        self.assertEqual(len(candidates), 14)
        self.assertEqual(len({item["language_tag"] for item in candidates}), 13)
        self.assertEqual(sum(item["canon_mapping_state"] == "reviewed_match" for item in candidates), 11)
        self.assertEqual(sum(item["canon_mapping_state"] == "uncertain" for item in candidates), 3)
        self.assertTrue(all(
            next(reader for reader in self.readers if reader["reader_id"] == reader_id).get("canon_id") is None
            for reader_id in reader_ids
        ))
        philemon = next(book for book in self.books if book["canon_id"] == "eotc-nt-18")
        self.assertIsNone(philemon["reader_id"])
        self.assertEqual(self.archive["canon_registry"]["reader_count"], 19)
        self.assertIn("Fourteen separately scoped Philemon research readers", philemon["reader_status"])

    def test_standard_nt_research_members_are_indexed_without_claiming_edition_equivalence(self):
        corpora = self.translation_registry["research_corpora"]
        expected_codes = [
            "mat", "mrk", "luk", "jhn", "act", "rom", "1co", "2co", "gal", "eph", "php", "col",
            "1th", "2th", "1ti", "2ti", "tit", "phm", "heb", "1pe", "2pe", "1jn", "2jn", "3jn", "jas", "jud", "rev",
        ]
        readers_by_id = {reader["reader_id"]: reader for reader in self.readers}
        for number, code in enumerate(expected_codes, 1):
            candidates = [item for item in corpora if item.get("candidate_canon_id") == f"eotc-nt-{number:02d}"
                          and item.get("reader_id", "").endswith(f"-{code}-research")]
            self.assertIn(len(candidates), {13, 14}, code)
            self.assertEqual(sum(item["canon_mapping_state"] == "reviewed_match" for item in candidates), 11, code)
            self.assertTrue(all(item["canon_mapping_state"] in {"reviewed_match", "uncertain"} for item in candidates), code)
            self.assertTrue(all(readers_by_id[item["reader_id"]].get("canon_id") is None for item in candidates), code)
            self.assertTrue(all({"SRC-029", "SRC-384", "SRC-396"} <= set(item["source_ids"])
                                for item in candidates), code)
            self.assertEqual(sum(item["reader_id"].startswith("webbe-2020-") for item in candidates), 1, code)
        self.assertEqual(self.archive["canon_registry"]["reader_count"], 19)

    def test_research_corpus_provenance_stays_off_the_canon_mapping_record(self):
        genesis = next(book for book in self.books if book["canon_id"] == "eotc-ot-01")
        candidates = [
            corpus for corpus in self.translation_registry["research_corpora"]
            if corpus.get("candidate_canon_id") == genesis["canon_id"]
        ]
        candidate_sources = set().union(*(set(item["source_ids"]) for item in candidates))
        catalogue = next(
            row for row in self.archive["catalogue"]
            if row["catalogue_id"] in genesis["catalogue_ids"]
        )

        # IANA language-tag and ISO script-code references describe research
        # corpus metadata. They are not evidence for Genesis' canon mapping.
        self.assertNotIn("SRC-077", genesis["source_ids"])
        self.assertNotIn("SRC-078", genesis["source_ids"])
        self.assertIn("SRC-077", candidate_sources)
        self.assertIn("SRC-078", candidate_sources)
        self.assertTrue({"SRC-077", "SRC-078"} <= set(catalogue["evidence_source_ids"]))

    def test_canon_linked_cards_expose_reader_scope_and_verification_details(self):
        linked = [reader for reader in self.readers if reader.get("canon_id")]
        self.assertEqual(len(linked), 19)
        self.assertTrue(all(reader.get("verification_status") for reader in linked))
        self.assertIn("const verificationDetails = hasReader && reader.verification_status", self.app)
        self.assertIn('<details class="canon-entry-verification"><summary>Extent and checks</summary>', self.app)
        self.assertIn("${escapeHTML(reader.verification_status)}", self.app)
        self.assertIn("${verificationDetails}${researchActions}", self.app)

    def test_clement_candidate_availability_is_documented_without_counting_as_reader_coverage(self):
        book = next(item for item in self.books if item["canon_id"] == "eotc-nt-34")
        source = next(item for item in self.archive["sources"] if item["source_id"] == "SRC-207")
        lead = next(item for item in self.translation_registry["edition_leads"] if item["edition_id"] == "bausi-2024-eritrean-qalementos-witness")
        beta_source = next(item for item in self.archive["sources"] if item["source_id"] == "SRC-424")
        beta_lead = next(item for item in self.translation_registry["edition_leads"] if item["edition_id"] == "betamasaheft-qalementos-cae1957-metadata")
        capture_path = ROOT / "readers" / "source" / "clement-betamasaheft" / "capture-manifest.json"
        capture = json.loads(capture_path.read_text(encoding="utf-8"))
        self.assertIsNone(book["reader_id"])
        self.assertEqual(book["mapping_state"], "uncertain")
        self.assertIn("SRC-207", book["source_ids"])
        self.assertIn("complementary French/Italian translations", book["reader_status"])
        self.assertIn("exact identity", book["reader_status"])
        self.assertIn("does not establish this exact list crosswalk", book["mapping_note"])
        self.assertEqual(source["rights_classification"], "permission_limited")
        self.assertIn("CC BY-NC-ND 4.0", source["rights_status"])
        self.assertEqual(source["local_review_url"], "research/clement-source-review.md")
        self.assertIn("local_review_url", self.app)
        self.assertIn("Read local source review", self.app)
        self.assertEqual(lead["mapping_state"], "uncertain")
        self.assertFalse(lead["text_bundled"])
        self.assertEqual(lead["rights_classification"], "unknown")
        self.assertIn("SRC-424", book["source_ids"])
        self.assertEqual(beta_source["rights_classification"], "mixed")
        self.assertEqual(beta_source["local_metadata_url"], "readers/source/clement-betamasaheft/capture-manifest.json")
        self.assertEqual(capture["sha256"], "db5f90e9b78079a7befae9a7a081ec72c10c1bedfaef79ef847d3f466796dd6e")
        self.assertEqual(capture["byte_length"], 16865)
        self.assertEqual(capture["validation"]["text_divisions"]["numbered_book_textparts"], 7)
        self.assertEqual(capture["validation"]["text_divisions"]["chapter_or_verse_divisions_found"], 0)
        self.assertEqual(beta_lead["mapping_state"], "related_work")
        self.assertEqual(beta_lead["candidate_canon_id"], "eotc-nt-34")
        self.assertFalse(beta_lead["text_bundled"])
        self.assertEqual(beta_lead["rights_classification"], "mixed")
        self.assertIn("no continuous, chaptered full-text reader", beta_lead["scope_description"])
        self.assertEqual(self.archive["canon_registry"]["reader_count"], 19)

    def test_ethiopic_maccabees_is_related_work_not_a_crosswalk(self):
        lead = next(
            record for record in self.translation_registry["edition_leads"]
            if record["edition_id"] == "bl-or506-first-ethiopian-maccabees"
        )
        self.assertEqual(lead["candidate_canon_id"], "eotc-ot-20")
        self.assertEqual(lead["mapping_state"], "related_work")
        self.assertFalse(lead["text_bundled"])
        self.assertEqual(lead["rights_classification"], "unknown")
        self.assertIn("not a crosswalk", lead["scope_description"])

    def test_unmapped_edition_lead_can_be_preserved_without_inventing_a_book_link(self):
        lead = next(
            record for record in self.translation_registry["edition_leads"]
            if record["edition_id"] == "bl-eap704-2-8-synodos"
        )
        self.assertIsNone(lead["candidate_canon_id"])
        self.assertEqual(lead["mapping_state"], "not_mapped")
        self.assertFalse(lead["text_bundled"])
        self.assertEqual(lead["rights_classification"], "unknown")
        self.assertIn("does not enumerate the four separate Church-list titles", lead["scope_description"])

    def test_tegsats_candidate_remains_provisional_and_unbundled(self):
        lead = next(
            record for record in self.translation_registry["edition_leads"]
            if record["edition_id"] == "pilkington-tegsats-reproof-1978"
        )
        self.assertEqual(lead["candidate_canon_id"], "eotc-ot-25")
        self.assertEqual(lead["mapping_state"], "uncertain")
        self.assertFalse(lead["text_bundled"])
        self.assertEqual(lead["rights_classification"], "unknown")
        self.assertIn("not verify that the thesis section is the Church-listed work", lead["scope_description"])

    def test_zena_ayhud_candidate_does_not_claim_verified_josippon_crosswalk(self):
        lead = next(
            record for record in self.translation_registry["edition_leads"]
            if record["edition_id"] == "bl-eap704-2-3-zena-ayhud"
        )
        self.assertEqual(lead["candidate_canon_id"], "eotc-ot-46")
        self.assertEqual(lead["mapping_state"], "uncertain")
        self.assertFalse(lead["text_bundled"])
        self.assertEqual(lead["rights_classification"], "unknown")
        self.assertIn("does not make that identification", lead["scope_description"])

    def test_amharic_nt_book_code_crosswalks_are_reviewed_without_canon_promotion(self):
        corpora = [
            corpus for corpus in self.translation_registry["research_corpora"]
            if corpus.get("language_tag") == "am"
        ]
        self.assertEqual(len(corpora), 27)
        expected = {f"eotc-nt-{number:02d}" for number in range(1, 28)}
        self.assertEqual({corpus["candidate_canon_id"] for corpus in corpora}, expected)
        self.assertTrue(all(corpus["canon_mapping_state"] == "reviewed_match" for corpus in corpora))
        self.assertTrue(all({"SRC-029", "SRC-396"} <= set(corpus["source_ids"]) for corpus in corpora))
        self.assertTrue(all("does not establish EOTC" in corpus["canon_mapping_note"] for corpus in corpora))
        self.assertTrue(all(corpus["rights_classification"] == "permission_limited" for corpus in corpora))
        self.assertTrue(all(corpus.get("license_id") is None for corpus in corpora))
        self.assertTrue(all("Commercial use requires written permission" in corpus["rights_status"] for corpus in corpora))
        self.assertTrue(all(
            next(reader for reader in self.readers if reader["reader_id"] == corpus["reader_id"]).get("canon_id") is None
            for corpus in corpora
        ))
        self.assertTrue(all(
            next(reader for reader in self.readers if reader["reader_id"] == corpus["reader_id"])
            ["title_normalization"]["canon_mapping"] == "reviewed_work_title_match"
            for corpus in corpora
        ))

    def test_dawro_nt_modules_have_reviewed_title_crosswalks_without_canon_promotion(self):
        codes = [
            "mat", "mrk", "luk", "jhn", "act", "rom", "1co", "2co", "gal", "eph", "php", "col",
            "1th", "2th", "1ti", "2ti", "tit", "phm", "heb", "1pe", "2pe", "1jn", "2jn", "3jn",
            "jas", "jud", "rev",
        ]
        corpora = [
            corpus for corpus in self.translation_registry["research_corpora"]
            if corpus.get("reader_id", "").startswith("dawro-latin-")
            and isinstance(corpus.get("candidate_canon_id"), str)
            and corpus["candidate_canon_id"].startswith("eotc-nt-")
        ]
        self.assertEqual(len(corpora), 27)
        by_reader = {reader["reader_id"]: reader for reader in self.readers}
        for number, code in enumerate(codes, 1):
            corpus = next(item for item in corpora if item["reader_id"] == f"dawro-latin-{code}-research")
            reader = by_reader[corpus["reader_id"]]
            self.assertEqual(corpus["candidate_canon_id"], f"eotc-nt-{number:02d}")
            self.assertEqual(corpus["canon_mapping_state"], "reviewed_match")
            self.assertTrue({"SRC-029", "SRC-396", "SRC-404", "SRC-405"} <= set(corpus["source_ids"]))
            self.assertIn(f"-{code.upper()}dwrl.usfm", reader["source_pages"])
            self.assertIn("title-level crosswalk only", corpus["canon_mapping_note"])
            self.assertEqual(corpus["translation_basis_status"], "unknown")
            self.assertEqual(corpus["rights_classification"], "open_license")
            self.assertIsNone(reader.get("canon_id"))
        self.assertEqual(self.archive["canon_registry"]["reader_count"], 19)

    def test_oyda_yemsa_and_baiso_nt_modules_have_scoped_title_matches(self):
        packages = {
            "oyd": ("oyda-", "oyde", "SRC-400", "SRC-401"),
            "jnj": ("yemsa-", "jnje", "SRC-407", "SRC-408"),
            "bsw": ("baiso-ethiopic-", "bswe", "SRC-412", "SRC-413"),
        }
        codes = [
            "mat", "mrk", "luk", "jhn", "act", "rom", "1co", "2co", "gal", "eph", "php", "col",
            "1th", "2th", "1ti", "2ti", "tit", "phm", "heb", "1pe", "2pe", "1jn", "2jn", "3jn",
            "jas", "jud", "rev",
        ]
        readers_by_id = {reader["reader_id"]: reader for reader in self.readers}
        for language_tag, (prefix, package_code, edition_source_id, package_source_id) in packages.items():
            with self.subTest(language=language_tag):
                corpora = [item for item in self.translation_registry["research_corpora"]
                           if item.get("language_tag") == language_tag
                           and item.get("reader_id", "").startswith(prefix)]
                self.assertEqual(len(corpora), 27)
                for number, code in enumerate(codes, 1):
                    corpus = next(item for item in corpora if item["reader_id"] == f"{prefix}{code}-research")
                    reader = readers_by_id[corpus["reader_id"]]
                    self.assertEqual(corpus["candidate_canon_id"], f"eotc-nt-{number:02d}")
                    self.assertEqual(corpus["canon_mapping_state"], "reviewed_match")
                    self.assertTrue({"SRC-029", "SRC-396", edition_source_id, package_source_id}
                                    <= set(corpus["source_ids"]))
                    self.assertIn(f"-{code.upper()}{package_code}.usfm", reader["source_pages"])
                    self.assertIn("title-level crosswalk only", corpus["canon_mapping_note"])
                    self.assertEqual(corpus["translation_basis_status"], "unknown")
                    self.assertEqual(corpus["rights_classification"], "open_license")
                    self.assertIsNone(reader.get("canon_id"))
        self.assertEqual(self.archive["canon_registry"]["reader_count"], 19)

    def test_arabic_van_dyck_nt_modules_have_reviewed_title_matches_only(self):
        codes = [
            "mat", "mrk", "luk", "jhn", "act", "rom", "1co", "2co", "gal", "eph", "php", "col",
            "1th", "2th", "1ti", "2ti", "tit", "phm", "heb", "1pe", "2pe", "1jn", "2jn", "3jn",
            "jas", "jud", "rev",
        ]
        corpora = [item for item in self.translation_registry["research_corpora"]
                   if item.get("language_tag") == "arb" and item.get("reader_id", "").startswith("arb-vd-")
                   and isinstance(item.get("candidate_canon_id"), str)
                   and item["candidate_canon_id"].startswith("eotc-nt-")]
        self.assertEqual(len(corpora), 27)
        readers_by_id = {reader["reader_id"]: reader for reader in self.readers}
        for number, code in enumerate(codes, 1):
            corpus = next(item for item in corpora if item["reader_id"] == f"arb-vd-{code}-research")
            reader = readers_by_id[corpus["reader_id"]]
            self.assertEqual(corpus["candidate_canon_id"], f"eotc-nt-{number:02d}")
            self.assertEqual(corpus["canon_mapping_state"], "reviewed_match")
            self.assertTrue({"SRC-029", "SRC-396", "SRC-329", "SRC-330"} <= set(corpus["source_ids"]))
            self.assertIn(f"-{code.upper()}arb-vd.usfm", reader["source_pages"])
            self.assertIn("title-level crosswalk only", corpus["canon_mapping_note"])
            self.assertEqual(corpus["translation_basis_status"], "unknown")
            self.assertIsNone(corpus.get("translation_path"))
            self.assertEqual(corpus["rights_classification"], "public_domain_claimed")
            self.assertIsNone(corpus.get("license_id"))
            self.assertIsNone(reader.get("canon_id"))
        self.assertEqual(self.archive["canon_registry"]["reader_count"], 19)

    def test_somali_lingala_and_maale_nt_crosswalks_preserve_each_editions_rights(self):
        packages = {
            "so": ("som-1979-2008-", "som", "SRC-390", "SRC-391", "permission_limited"),
            "ln": ("lin-2020-", "lin", "SRC-393", "SRC-394", "open_license"),
            "mdy": ("maale-", "mdyeth", "SRC-363", "SRC-364", "open_license"),
        }
        codes = [
            "mat", "mrk", "luk", "jhn", "act", "rom", "1co", "2co", "gal", "eph", "php", "col",
            "1th", "2th", "1ti", "2ti", "tit", "phm", "heb", "1pe", "2pe", "1jn", "2jn", "3jn",
            "jas", "jud", "rev",
        ]
        readers_by_id = {reader["reader_id"]: reader for reader in self.readers}
        for language_tag, (prefix, package_code, edition_source_id, package_source_id, rights) in packages.items():
            with self.subTest(language=language_tag):
                corpora = [item for item in self.translation_registry["research_corpora"]
                           if item.get("language_tag") == language_tag
                           and item.get("reader_id", "").startswith(prefix)
                           and isinstance(item.get("candidate_canon_id"), str)
                           and item["candidate_canon_id"].startswith("eotc-nt-")]
                self.assertEqual(len(corpora), 27)
                for number, code in enumerate(codes, 1):
                    corpus = next(item for item in corpora if item["reader_id"] == f"{prefix}{code}-research")
                    reader = readers_by_id[corpus["reader_id"]]
                    self.assertEqual(corpus["candidate_canon_id"], f"eotc-nt-{number:02d}")
                    self.assertEqual(corpus["canon_mapping_state"], "reviewed_match")
                    self.assertTrue({"SRC-029", "SRC-396", edition_source_id, package_source_id}
                                    <= set(corpus["source_ids"]))
                    self.assertIn(f"-{code.upper()}{package_code}.usfm", reader["source_pages"])
                    self.assertIn("title-level crosswalk only", corpus["canon_mapping_note"])
                    self.assertEqual(corpus["translation_basis_status"], "unknown")
                    self.assertIsNone(corpus.get("translation_path"))
                    self.assertEqual(corpus["rights_classification"], rights)
                    self.assertEqual(reader["rights_classification"], rights)
                    self.assertIsNone(reader.get("canon_id"))
        self.assertEqual(self.archive["canon_registry"]["reader_count"], 19)

    def test_teezaz_horner_image_lead_is_provisional_and_discloses_missing_pages(self):
        lead = next(
            record for record in self.translation_registry["edition_leads"]
            if record["edition_id"] == "tau-horner-teezaz-image-edition-1904"
        )
        self.assertEqual((lead["candidate_canon_id"], lead["mapping_state"]), ("eotc-nt-29", "uncertain"))
        self.assertFalse(lead["text_bundled"])
        self.assertEqual(lead["rights_classification"], "unknown")
        self.assertIn("pages 5, 9, 17", lead["scope_description"])
        self.assertIn("not an authoritative crosswalk", lead["scope_description"])
        self.assertIn("broader Statutes volume", lead["scope_description"])
        catalogue = next(item for item in self.archive["catalogue"] if item["catalogue_id"] == "eotc-083")
        self.assertIn("TAU-hosted Ge'ez page images", catalogue["edition_or_translation"])
        self.assertIn("separate English-language digitization", catalogue["edition_or_translation"])
        archive_source = next(source for source in self.archive["sources"] if source["source_id"] == "SRC-368")
        self.assertIn("without the Ethiopic and Arabic texts", archive_source["inspection_and_limitations"])
        self.assertIn("NOT_IN_COPYRIGHT", archive_source["inspection_and_limitations"])
        self.assertIn("pp. 127-232", archive_source["inspection_and_limitations"])
        self.assertIn("SRC-368", lead["source_ids"])
        self.assertIn("not worldwide clearance", lead["rights_status"])
        self.assertIn("pp. 127-232", lead["scope_description"])
        self.assertIn("boundaries", lead["scope_description"])
        self.assertFalse(lead["text_bundled"])

    def test_sinodos_fell_edition_and_emml_witness_stay_unmapped(self):
        for edition_id in (
            "fell-canones-apostolorum-aethiopice-1871",
            "vhmml-emml677-sinodos-manuscript",
        ):
            lead = next(
                record for record in self.translation_registry["edition_leads"]
                if record["edition_id"] == edition_id
            )
            self.assertIsNone(lead["candidate_canon_id"])
            self.assertEqual(lead["mapping_state"], "not_mapped")
            self.assertFalse(lead["text_bundled"])
            self.assertEqual(lead["rights_classification"], "unknown" if edition_id.startswith("fell-") else "permission_limited")

    def test_gamo_standard_code_candidates_preserve_unmapped_lamentations(self):
        corpora = [
            corpus for corpus in self.translation_registry["research_corpora"]
            if corpus.get("language_tag") == "gmv"
        ]
        self.assertEqual(len(corpora), 66)
        mapped = [corpus for corpus in corpora if corpus.get("candidate_canon_id")]
        self.assertEqual(len(mapped), 65)
        lam = next(corpus for corpus in corpora if corpus["reader_id"] == "gamo-lam-research")
        self.assertEqual((lam["canon_mapping_state"], lam["candidate_canon_id"]), ("not_mapped", None))
        for code in ("1sa", "2sa", "1ki", "2ki", "ezr", "neh"):
            corpus = next(item for item in mapped if item["reader_id"] == f"gamo-{code}-research")
            self.assertIn("one named component of a grouped catalogue entry", corpus["canon_mapping_note"])
        states = {state: sum(item["canon_mapping_state"] == state for item in mapped)
                  for state in ("reviewed_match", "uncertain")}
        self.assertEqual(states, {"reviewed_match": 29, "uncertain": 36})
        self.assertTrue(all(item["canon_mapping_state"] in states for item in mapped))
        self.assertTrue(all("Reviewed work/title match" in item["canon_mapping_note"]
                            for item in mapped if item["canon_mapping_state"] == "reviewed_match"))
        self.assertTrue(all(
            "canon-linked coverage" in item["canon_mapping_note"]
            for item in mapped if item["canon_mapping_state"] == "reviewed_match"
        ))


if __name__ == "__main__":
    unittest.main()
