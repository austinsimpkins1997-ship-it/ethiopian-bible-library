import json
import unittest
from pathlib import Path

from build_brenton_research_readers import RESEARCH_CODES, build_records

ROOT = Path(__file__).resolve().parents[1]


class BrentonResearchReaderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.readers, cls.corpora, _ = build_records()
        cls.archive = json.loads((ROOT / "archive.json").read_text(encoding="utf-8"))
        cls.manifest = json.loads((ROOT / "readers/source/brenton-septuagint/capture-manifest.json").read_text(encoding="utf-8"))

    def test_all_selected_members_have_research_readers_without_canon_claims(self):
        self.assertEqual(len(self.readers), 38)
        self.assertEqual(len(self.corpora), 38)
        for reader, corpus in zip(self.readers, self.corpora, strict=True):
            with self.subTest(reader=reader["reader_id"]):
                self.assertIsNone(reader.get("canon_id"))
                self.assertEqual(reader["reader_scope"], "research_witness_not_mapped_to_eotc_canon")
                self.assertEqual(corpus["canon_mapping_state"], "not_mapped")
                self.assertIsNone(corpus["candidate_canon_id"])
                self.assertEqual(reader["translation_path"], ["grc", "en"])
                self.assertEqual(reader["unit_count"], sum(len(chapter["verses"]) for chapter in reader["chapters"]))
                self.assertIn("not canon-linked", reader["verification_status"])
                self.assertIn("not proof of completeness", reader["chapter_structure_note"])

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
                reader = next(item for item in readers if name in item.get("source_pages", ""))
                self.assertEqual(reader["source_member_sha256"], meta["sha256"])
                self.assertEqual(reader["source_pages"].split("/")[-1].split(" ")[0], name)
                self.assertTrue(all(verse.get("text") or verse.get("source_text_state") == "marker_only"
                                    for chapter in reader["chapters"] for verse in chapter["verses"]))

    def test_empty_source_markers_and_pre_verse_headings_are_retained_without_invention(self):
        readers = self.archive["readers"]
        by_member = {reader["source_pages"].split("/")[-1].split(" ")[0]: reader for reader in readers if reader.get("source_pages")}
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
