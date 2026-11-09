import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class PhilemonTauLeadTests(unittest.TestCase):
    def test_research_lead_uses_a_current_non_numeric_coverage_note(self):
        registry = json.loads((ROOT / "translation-registry.json").read_text(encoding="utf-8"))
        archive = json.loads((ROOT / "archive.json").read_text(encoding="utf-8"))
        lead = next(item for item in registry["corpus_leads"]
                    if item["corpus_id"] == "betamasaheft-philemon-tei-research")
        embedded_lead = next(item for item in archive["translation_registry"]["corpus_leads"]
                             if item["corpus_id"] == "betamasaheft-philemon-tei-research")
        self.assertIn("excluded from canon-linked reader coverage", lead["canon_mapping_note"])
        self.assertNotIn("51/81", lead["canon_mapping_note"])
        self.assertNotIn("51/81", lead["notes"])
        self.assertEqual(embedded_lead, lead)
        self.assertIn(lead["canon_mapping_note"], (ROOT / "index.html").read_text(encoding="utf-8"))

    def test_philemon_is_a_cited_rights_limited_lead_not_bundled_text(self):
        archive = json.loads((ROOT / "archive.json").read_text(encoding="utf-8"))
        registry = json.loads((ROOT / "translation-registry.json").read_text(encoding="utf-8"))
        lead = next(item for item in registry["edition_leads"]
                    if item["edition_id"] == "platt-ethiopic-philemon-1830-tau")
        source = next(item for item in archive["sources"] if item["source_id"] == "SRC-162")

        self.assertEqual(lead["candidate_canon_id"], "eotc-nt-18")
        self.assertEqual(lead["mapping_state"], "uncertain")
        self.assertEqual((lead["language_tag"], lead["script_code"]), ("gez", "Ethi"))
        self.assertFalse(lead["text_bundled"])
        self.assertNotIn("bundled_reader_id", lead)
        self.assertEqual(lead["rights_classification"], "permission_limited")
        self.assertIn("written consent", lead["rights_status"])
        self.assertIn("SRC-162", lead["source_ids"])
        self.assertIn("Philemon", source["inspection_and_limitations"])
        self.assertIn("without his written consent", source["inspection_and_limitations"])
        self.assertIn("InformationPa.html", source["url"])


if __name__ == "__main__":
    unittest.main()
