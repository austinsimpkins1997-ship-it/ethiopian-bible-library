import hashlib
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


@unittest.skip('Mixed-rights scripture and source XML are withheld from the public package.')
class ChroniclesResearchReaderTests(unittest.TestCase):
    def test_pinned_chronicles_text_is_bundled_as_research_only_with_source_labels(self):
        registry = json.loads((ROOT / "translation-registry.json").read_text(encoding="utf-8"))
        corpora = {item["corpus_id"]: item for item in registry["research_corpora"]}
        expected = {
            "first-chronicles-betamasaheft-tei-research": ("betamasaheft-first-chronicles-tei-research", 29, 950, "eotc-ot-11"),
            "second-chronicles-betamasaheft-tei-research": ("betamasaheft-second-chronicles-tei-research", 36, 854, "eotc-ot-12"),
        }
        for reader_id, (corpus_id, chapter_count, unit_count, candidate) in expected.items():
            reader = json.loads((ROOT / "readers" / f"{reader_id}.json").read_text(encoding="utf-8"))
            corpus = corpora[corpus_id]
            digest = hashlib.sha256((ROOT / "readers" / "source" / "chronicles" / ("LIT3499Chroni.xml" if chapter_count == 29 else "LIT3500Chroni.xml")).read_bytes()).hexdigest()
            self.assertEqual(reader["source_snapshot_sha256"], digest)
            self.assertEqual(reader["chapter_count"], chapter_count)
            self.assertEqual(reader["unit_count"], unit_count)
            self.assertEqual(sum(len(chapter["units"]) for chapter in reader["chapters"]), unit_count)
            self.assertEqual(corpus["candidate_canon_id"], candidate)
            self.assertEqual(corpus["canon_mapping_state"], "uncertain")
            self.assertIn("excluded from canon-linked", corpus["canon_mapping_note"])
            self.assertEqual(reader["rights_classification"], "open_license")
            self.assertIn("CC BY-NC-SA 4.0", reader["copyright_notice"])
            self.assertIn("unresolved", reader["copyright_notice"])

    def test_source_line_label_gaps_are_preserved_not_filled(self):
        reader = json.loads((ROOT / "readers" / "first-chronicles-betamasaheft-tei-research.json").read_text(encoding="utf-8"))
        first_labels = [unit["source_marker"] for unit in reader["chapters"][0]["units"]]
        chapter_26_labels = [unit["source_marker"] for unit in reader["chapters"][25]["units"]]
        self.assertNotIn("13", first_labels)
        self.assertNotIn("28", chapter_26_labels)
        self.assertIn("gaps", reader["chapter_structure_note"])


if __name__ == "__main__":
    unittest.main()
