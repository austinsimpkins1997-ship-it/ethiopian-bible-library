import json
import unittest
from pathlib import Path

from build_brenton_research_readers import CANDIDATE_CANON_LINKS, RESEARCH_CODES, build_records

ROOT = Path(__file__).resolve().parents[1]


class BrentonResearchReaderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.readers, cls.corpora, _ = build_records()
        cls.archive = json.loads((ROOT / "archive.json").read_text(encoding="utf-8"))
        cls.manifest = json.loads((ROOT / "readers/source/brenton-septuagint/capture-manifest.json").read_text(encoding="utf-8"))

    def test_all_selected_members_have_research_readers_without_canon_claims(self):
        self.assertEqual(len(self.readers), len(RESEARCH_CODES))
        self.assertEqual(len(self.corpora), len(RESEARCH_CODES))
        for reader, corpus in zip(self.readers, self.corpora, strict=True):
            with self.subTest(reader=reader["reader_id"]):
                self.assertIsNone(reader.get("canon_id"))
                self.assertEqual(reader["reader_scope"], "research_witness_not_mapped_to_eotc_canon")
                if reader["reader_id"] == "brenton-lxx-jdt-research":
                    self.assertEqual(corpus["canon_mapping_state"], "uncertain")
                    self.assertEqual(corpus["candidate_canon_id"], "eotc-ot-18")
                    self.assertIn("shared title supports a research-only candidate", corpus["canon_mapping_note"])
                    self.assertIn("SRC-029", corpus["source_ids"])
                elif reader["reader_id"] == "brenton-lxx-esg-research":
                    self.assertEqual(corpus["canon_mapping_state"], "uncertain")
                    self.assertEqual(corpus["candidate_canon_id"], "eotc-ot-19")
                    self.assertIn("explicitly titled ‘Esther (Greek)’", corpus["canon_mapping_note"])
                    self.assertIn("SRC-029", corpus["source_ids"])
                    self.assertEqual(reader["chapter_count"], 10)
                    self.assertEqual(reader["unit_count"], 252)
                    self.assertIn("1b", [verse["number"] for verse in reader["chapters"][0]["verses"]])
                elif reader["reader_id"] in {
                    "brenton-lxx-first-ma-research",
                    "brenton-lxx-second-ma-research",
                    "brenton-lxx-third-ma-research",
                }:
                    expected_candidate = (
                        "eotc-ot-20" if reader["reader_id"] == "brenton-lxx-first-ma-research"
                        else "eotc-ot-21"
                    )
                    self.assertEqual(corpus["canon_mapping_state"], "uncertain")
                    self.assertEqual(corpus["candidate_canon_id"], expected_candidate)
                    self.assertIn("title-level", corpus["canon_mapping_note"])
                    self.assertIn("SRC-029", corpus["source_ids"])
                else:
                    source_pages = reader.get("source_pages", "")
                    code = next((code for code in RESEARCH_CODES if f"-{code}eng-Brenton.usfm" in source_pages), None)
                    self.assertIsNotNone(code)
                    candidate = CANDIDATE_CANON_LINKS.get(code)
                    if candidate:
                        self.assertEqual(corpus["canon_mapping_state"], "uncertain")
                        self.assertEqual(corpus["candidate_canon_id"], candidate[0])
                        self.assertEqual(corpus["canon_mapping_note"], candidate[1])
                        self.assertIn("SRC-029", corpus["source_ids"])
                    else:
                        self.assertEqual(corpus["canon_mapping_state"], "not_mapped")
                        self.assertIsNone(corpus["candidate_canon_id"])
                self.assertEqual(reader["translation_path"], ["grc", "en"])
                self.assertEqual(reader["translation_basis_status"], "established")
                self.assertEqual(corpus["translation_basis_status"], "established")
                self.assertEqual(reader["translation_basis_note"], corpus["translation_basis_note"])
                self.assertEqual(reader["unit_count"], sum(len(chapter["verses"]) for chapter in reader["chapters"]))
                self.assertIn("not canon-linked", reader["verification_status"])
                self.assertIn("not proof of completeness", reader["chapter_structure_note"])

    def test_judith_title_candidate_does_not_replace_withheld_geez_text_or_count_as_canon_coverage(self):
        corpus = next(item for item in self.corpora if item["reader_id"] == "brenton-lxx-jdt-research")
        reader = next(item for item in self.readers if item["reader_id"] == "brenton-lxx-jdt-research")
        canon_entry = next(item for item in self.archive["canon_registry"]["books"] if item["canon_id"] == "eotc-ot-18")
        embedded_corpus = next(
            item for item in self.archive["translation_registry"]["research_corpora"]
            if item["reader_id"] == "brenton-lxx-jdt-research"
        )
        self.assertIsNone(reader.get("canon_id"))
        self.assertEqual(corpus["candidate_canon_id"], canon_entry["canon_id"])
        self.assertIn("Not bundled: source text withheld pending rights clarification", canon_entry["reader_status"])
        self.assertIn("does not establish", corpus["canon_mapping_note"])
        self.assertEqual(embedded_corpus["canon_mapping_state"], "uncertain")
        self.assertEqual(embedded_corpus["candidate_canon_id"], canon_entry["canon_id"])

    def test_esther_greek_candidate_preserves_lettered_source_labels_and_withheld_canon_text(self):
        corpus = next(item for item in self.corpora if item["reader_id"] == "brenton-lxx-esg-research")
        reader = next(item for item in self.readers if item["reader_id"] == "brenton-lxx-esg-research")
        canon_entry = next(item for item in self.archive["canon_registry"]["books"] if item["canon_id"] == "eotc-ot-19")
        chapter_one_labels = [verse["number"] for verse in reader["chapters"][0]["verses"]]

        self.assertIsNone(reader.get("canon_id"))
        self.assertEqual(corpus["canon_mapping_state"], "uncertain")
        self.assertEqual(corpus["candidate_canon_id"], "eotc-ot-19")
        self.assertIn("does not establish identity", corpus["canon_mapping_note"])
        self.assertEqual(reader["chapter_count"], 10)
        self.assertEqual(reader["unit_count"], 252)
        self.assertIn("1b", chapter_one_labels)
        self.assertIn("1s", chapter_one_labels)
        self.assertIn("lettered labels", reader["chapter_structure_note"])
        self.assertEqual(canon_entry["reader_status"], "Not bundled: source text withheld pending rights clarification.")

    def test_wisdom_is_surfaced_as_one_uncertain_component_candidate_only(self):
        reader = next(item for item in self.readers if item["reader_id"] == "brenton-lxx-wis-research")
        corpus = next(item for item in self.corpora if item["reader_id"] == reader["reader_id"])
        coverage = json.loads((ROOT / "book-coverage.json").read_text(encoding="utf-8"))
        entry = next(item for item in coverage["entries"] if item["canon_id"] == "eotc-ot-26")

        self.assertIsNone(reader.get("canon_id"))
        self.assertEqual(corpus["canon_mapping_state"], "uncertain")
        self.assertEqual(corpus["candidate_canon_id"], "eotc-ot-26")
        self.assertTrue({"SRC-029", "SRC-384"} <= set(corpus["source_ids"]))
        self.assertIn("possible single-work discovery link", corpus["canon_mapping_note"])
        self.assertIn("does not establish that it is identical", corpus["canon_mapping_note"])
        self.assertEqual((reader["chapter_count"], reader["unit_count"]), (19, 436))
        self.assertEqual(reader["translation_path"], ["grc", "en"])
        self.assertEqual(entry["reader_availability"], "research_candidate_reader_only")
        self.assertFalse(entry["canon_linked_readers"])
        self.assertEqual([item["reader_id"] for item in entry["research_reader_candidates"]], [reader["reader_id"]])

    def test_maccabees_titles_are_provisional_and_preserve_eotc_grouping(self):
        expected = {
            "brenton-lxx-first-ma-research": ("eotc-ot-20", "Maccabees I"),
            "brenton-lxx-second-ma-research": ("eotc-ot-21", "Maccabees II"),
            "brenton-lxx-third-ma-research": ("eotc-ot-21", "Maccabees III"),
        }
        canon_entries = {item["canon_id"]: item for item in self.archive["canon_registry"]["books"]}
        for reader_id, (canon_id, source_title) in expected.items():
            with self.subTest(reader_id=reader_id):
                reader = next(item for item in self.readers if item["reader_id"] == reader_id)
                corpus = next(item for item in self.corpora if item["reader_id"] == reader_id)
                self.assertIsNone(reader.get("canon_id"))
                self.assertIn(source_title, reader["title"])
                self.assertEqual(corpus["canon_mapping_state"], "uncertain")
                self.assertEqual(corpus["candidate_canon_id"], canon_id)
                self.assertTrue("only" in corpus["canon_mapping_note"] or "does not establish" in corpus["canon_mapping_note"])
                self.assertEqual(canon_entries[canon_id]["reader_status"], "No reader bundled here; external availability not assessed")

    def test_selected_usfm_members_are_checksums_pinned_and_built_offline(self):
        expected = {code for code in RESEARCH_CODES}
        selected = self.manifest["selected_members"]
        members = {code: (name, meta) for name, meta in selected.items()
                   for code in RESEARCH_CODES if f"-{code}eng-Brenton.usfm" in name}
        self.assertEqual(set(members), expected)
        readers = self.archive["readers"]
        for code in expected:
            with self.subTest(code=code):
                name, meta = members[code]
                reader = next(item for item in readers if name in " ".join(
                    item.get("source_pages", []) if isinstance(item.get("source_pages"), list)
                    else [str(item.get("source_pages", ""))]
                ))
                self.assertEqual(reader["source_member_sha256"], meta["sha256"])
                self.assertEqual(reader["source_pages"].split("/")[-1].split(" ")[0], name)
                self.assertTrue(all(verse.get("text") or verse.get("source_text_state") == "marker_only"
                                    for chapter in reader["chapters"] for verse in chapter["verses"]))

    def test_empty_source_markers_and_pre_verse_headings_are_retained_without_invention(self):
        readers = self.archive["readers"]
        by_member = {
            reader["source_pages"].split("/")[-1].split(" ")[0]: reader
            for reader in readers
            if isinstance(reader.get("source_pages"), str) and reader.get("source_pages")
        }
        kings = by_member["12-1KIeng-Brenton.usfm"]
        self.assertTrue(any(note.get("note_type") == "source_note_marker_without_text"
                            and note.get("source_reference") == "6:1"
                            and note.get("text") is None
                            for chapter in kings["chapters"] for note in chapter.get("notes", [])))
        proverbs = by_member["21-PROeng-Brenton.usfm"]
        chapter30 = next(chapter for chapter in proverbs["chapters"] if chapter["chapter"] == 30)
        empty_label = next(verse for verse in chapter30["verses"] if verse["number"] == "1")
        self.assertEqual(empty_label["source_text_state"], "marker_only")
        self.assertFalse(empty_label["text"])
        self.assertTrue(any(note.get("verse") == "1" and note.get("text") == "See chapter 24 for the content of chapter 30."
                            for note in chapter30["notes"]))
        lamentations = by_member["26-LAMeng-Brenton.usfm"]
        self.assertTrue(lamentations["chapters"][0]["heading"])
        self.assertEqual(lamentations["chapters"][0]["heading_markers"], ["p"])


if __name__ == "__main__":
    unittest.main()
