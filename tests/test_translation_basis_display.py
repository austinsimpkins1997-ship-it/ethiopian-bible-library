"""Reader language cards must keep declared translation paths and unknowns visible."""

import json
import unittest
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class TranslationBasisDisplayTests(unittest.TestCase):
    def test_registry_states_are_coherent_and_have_explicit_reader_card_copy(self):
        registry = json.loads((ROOT / "translation-registry.json").read_text(encoding="utf-8"))
        corpora = [
            record for record in registry["research_corpora"]
            if record.get("reader_status") == "bundled_research_reader"
        ]
        translated = [record for record in corpora if record.get("text_origin") == "published_translation"]
        states = Counter(record["translation_basis_status"] for record in translated)
        self.assertEqual(states, {"established": 42, "unknown": 694})
        source_records = {
            source["source_id"]: source for source in json.loads(
                (ROOT / "archive.json").read_text(encoding="utf-8")
            )["sources"]
        }
        for record in translated:
            if record["translation_basis_status"] == "established":
                self.assertGreaterEqual(len(record.get("translation_path", [])), 2)
                self.assertEqual(record["basis_language_tag"], record["translation_path"][0])
                self.assertEqual(record["language_tag"], record["translation_path"][-1])
                evidence_ids = record.get("translation_basis_source_ids", [])
                self.assertTrue(evidence_ids)
                self.assertEqual(evidence_ids, ["SRC-142"])
                self.assertTrue(set(evidence_ids) <= set(record["source_ids"]))
                self.assertTrue(set(evidence_ids) <= set(source_records))
                self.assertIn("English translation from Greek", source_records[evidence_ids[0]]["inspection_and_limitations"])
                self.assertEqual(record["translation_path"], ["grc", "en"])
            else:
                self.assertNotIn("translation_path", record)
                self.assertNotIn("basis_language_tag", record)
                self.assertNotIn("translation_basis_source_ids", record)

        app = (ROOT / "app.js").read_text(encoding="utf-8")
        self.assertIn("Translation basis: ${basisLabel}.", app)
        self.assertIn("cited evidence identifies a path", app)
        self.assertIn("unknown in this archive", app)
        self.assertIn("No source-language path is established here.", app)
        self.assertIn("Evidence: ${sourceLinks(researchRecord.translation_basis_source_ids)}", app)
        self.assertIn("Text origin: source transcription.", app)


if __name__ == "__main__":
    unittest.main()
