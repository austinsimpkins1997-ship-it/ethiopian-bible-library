import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


@unittest.skip("Mixed-rights scripture and source XML are withheld from the public package.")
class EcclesiastesDiscoveryTests(unittest.TestCase):
    def test_scoped_reader_does_not_claim_unresolved_print_rights(self):
        archive = json.loads((ROOT / "archive.json").read_text(encoding="utf-8"))
        registry = json.loads((ROOT / "translation-registry.json").read_text(encoding="utf-8"))
        source = next(x for x in archive["sources"] if x["source_id"] == "SRC-279")
        lead = next(x for x in registry["edition_leads"] if x["edition_id"] == "betamasaheft-ecclesiastes-tei-2026")
        reader_lead = next(x for x in registry["edition_leads"] if x["edition_id"] == "betamasaheft-ecclesiastes-eotced")
        catalogue = next(x for x in archive["catalogue"] if x["display_name"] == "Ecclesiastes")
        reader = next(x for x in archive["readers"] if x["reader_id"] == "ecclesiastes-geez-betamasaheft-eotced")

        self.assertFalse(lead["text_bundled"])
        self.assertEqual(lead["candidate_canon_id"], "eotc-ot-27")
        self.assertEqual(lead["rights_classification"], "mixed")
        self.assertIn("noncommercial", lead["rights_status"])
        self.assertIn("are not established", lead["rights_status"])
        self.assertIn("226 line elements", lead["scope_description"])
        self.assertIn("14–17", lead["scope_description"])
        self.assertTrue(reader_lead["text_bundled"] is False)
        self.assertEqual(reader_lead["bundled_reader_id"], reader["reader_id"])
        self.assertEqual(reader_lead["mapping_state"], "asserted_by_source")
        self.assertIn("underlying print rights remain unresolved", catalogue["text_availability_status"])
        self.assertIn("EOTCed-only", source["inspection_and_limitations"])
        self.assertIn("Mercer", source["inspection_and_limitations"])
        self.assertIn("152,281 bytes", source["inspection_and_limitations"])
        self.assertEqual(catalogue["source_id"], "SRC-000")
        self.assertIn("SRC-279", catalogue["evidence_source_ids"])
        self.assertFalse((ROOT / "readers/source/ecclesiastes/LIT1320Eccles.xml").exists())
        self.assertIn("SRC-279", reader["source_ids"])
        self.assertIn("SRC-294", reader["source_ids"])


if __name__ == "__main__":
    unittest.main()
