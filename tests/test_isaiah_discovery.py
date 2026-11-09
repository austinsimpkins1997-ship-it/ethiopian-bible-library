import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class IsaiahDiscoveryTests(unittest.TestCase):
    def test_isaiah_lead_preserves_source_scope_and_reuse_limits(self):
        archive = json.loads((ROOT / "archive.json").read_text(encoding="utf-8"))
        registry = json.loads((ROOT / "translation-registry.json").read_text(encoding="utf-8"))
        sources = {item["source_id"]: item for item in archive["sources"]}
        lead = next(item for item in registry["edition_leads"]
                    if item["edition_id"] == "bachmann-ethiopic-isaiah-1893-tau")

        self.assertIn("1893", sources["SRC-276"]["inspection_and_limitations"])
        self.assertIn("second part", sources["SRC-276"]["inspection_and_limitations"])
        self.assertEqual(lead["candidate_canon_id"], "eotc-ot-29")
        self.assertEqual(lead["mapping_state"], "uncertain")
        self.assertFalse(lead["text_bundled"])
        self.assertEqual(lead["rights_classification"], "permission_limited")
        self.assertIn("noncommercial", lead["rights_status"])
        self.assertIn("current EOTC edition", lead["scope_description"])
        self.assertIn("chapter count have not been inventoried", lead["scope_description"])


if __name__ == "__main__":
    unittest.main()
