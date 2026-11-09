import json
import unittest
from pathlib import Path

from build_maale_strategy_example import PROCESS_EVIDENCE, SOURCE, apply
from build_standalone import validate_closed_schema_objects


ROOT = Path(__file__).resolve().parents[1]


class MaaleStrategyExampleTests(unittest.TestCase):
    def test_source_and_record_preserve_unknown_edition_and_translation_path(self):
        archive = {"sources": [], "translation_registry": {"translation_process_evidence": []}}
        apply(archive)
        self.assertEqual(archive["sources"], [SOURCE])
        self.assertEqual(archive["translation_registry"]["translation_process_evidence"], [PROCESS_EVIDENCE])
        self.assertEqual(PROCESS_EVIDENCE["edition_link_status"], "not_established")
        self.assertEqual(PROCESS_EVIDENCE["edition_ids"], [])
        self.assertEqual(PROCESS_EVIDENCE["translation_path_status"], "not_stated")
        self.assertNotIn("translation_path", PROCESS_EVIDENCE)
        self.assertIn("cannot be used to claim", PROCESS_EVIDENCE["limitations"])

    def test_apply_is_idempotent_and_rejects_conflicting_source(self):
        archive = {"sources": [], "translation_registry": {"translation_process_evidence": []}}
        apply(archive)
        apply(archive)
        self.assertEqual(len(archive["sources"]), 1)
        self.assertEqual(len(archive["translation_registry"]["translation_process_evidence"]), 1)
        archive["sources"][0]["url"] = "https://example.invalid/"
        with self.assertRaises(ValueError):
            apply(archive)

    def test_closed_registry_schema_accepts_attributed_example(self):
        schema = json.loads((ROOT / "translation-registry.schema.json").read_text(encoding="utf-8"))
        registry = json.loads((ROOT / "translation-registry.json").read_text(encoding="utf-8"))
        registry["translation_process_evidence"] = [PROCESS_EVIDENCE]
        validate_closed_schema_objects(registry, schema, schema, "translation-registry.json")

    def test_research_page_labels_example_and_edition_limit(self):
        page = (ROOT / "research" / "gamo-maale-provenance.html").read_text(encoding="utf-8")
        app = (ROOT / "app.js").read_text(encoding="utf-8")
        self.assertIn("Maale Revelation 3:20 translation example", page)
        self.assertIn("not an independent linguistic or community review", page)
        self.assertIn("does <strong>not</strong> establish that this wording appears in the bundled 2008", page)
        self.assertIn("source-src-398", page)
        self.assertIn('id="source-${escapeHTML(source.source_id.toLowerCase())}"', app)


if __name__ == "__main__":
    unittest.main()
