import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ChroniclesDiscoveryTests(unittest.TestCase):
    def test_grebaut_chronicles_are_two_cited_unbundled_candidates(self):
        archive = json.loads((ROOT / "archive.json").read_text(encoding="utf-8"))
        registry = json.loads((ROOT / "translation-registry.json").read_text(encoding="utf-8"))
        sources = {s["source_id"]: s for s in archive["sources"]}
        leads = {x["edition_id"]: x for x in registry["edition_leads"]}

        self.assertIn("Paralipomena", sources["SRC-034"]["inspection_and_limitations"])
        self.assertIn("SRC-338", sources["SRC-034"]["inspection_and_limitations"])
        self.assertIn("CiNii identifies Sylvain Grébaut", sources["SRC-275"]["inspection_and_limitations"])
        self.assertIn("rights", sources["SRC-275"]["inspection_and_limitations"])
        capture = sources["SRC-338"]["inspection_and_limitations"]
        self.assertIn("29 for Paralipomena I", capture)
        self.assertIn("36 for II", capture)
        self.assertIn("neither the PNG scans nor a text transcription", capture)
        for part, canon_id in (("i", "eotc-ot-11"), ("ii", "eotc-ot-12")):
            lead = leads[f"grebaut-ethiopic-chronicles-{part}-1932"]
            self.assertEqual(lead["candidate_canon_id"], canon_id)
            self.assertEqual(lead["mapping_state"], "uncertain")
            self.assertFalse(lead["text_bundled"])
            self.assertEqual(lead["rights_classification"], "mixed")
            self.assertIn("SRC-275", lead["source_ids"])
            self.assertIn("SRC-338", lead["source_ids"])
            self.assertIn("bibliographic candidate", lead["scope_description"])
            self.assertIn("unverified", lead["scope_description"])
            self.assertIn("PNG scan", lead["scope_description"])


if __name__ == "__main__":
    unittest.main()
