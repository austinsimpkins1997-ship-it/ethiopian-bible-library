import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class JobDiscoveryTests(unittest.TestCase):
    def test_beta_masaheft_job_is_a_separate_unbundled_source_lead(self):
        archive = json.loads((ROOT / "archive.json").read_text(encoding="utf-8"))
        registry = json.loads((ROOT / "translation-registry.json").read_text(encoding="utf-8"))
        source = next(item for item in archive["sources"] if item["source_id"] == "SRC-283")
        lead = next(
            item for item in registry["edition_leads"]
            if item["edition_id"] == "betamasaheft-job-tei-l1688"
        )
        self.assertIn("LIT1688Job", source["source_name"])
        self.assertIn("CC BY-SA 4.0", source["inspection_and_limitations"])
        self.assertIn("CC BY-NC-SA 4.0", source["inspection_and_limitations"])
        self.assertEqual((lead["candidate_canon_id"], lead["mapping_state"]), ("eotc-ot-22", "uncertain"))
        self.assertFalse(lead["text_bundled"])
        self.assertEqual(lead["rights_classification"], "mixed")
        self.assertIn("No text is copied", lead["rights_status"])
        self.assertTrue((ROOT / "research/job-source-review.md").is_file())

    def test_job_lead_does_not_change_reader_coverage(self):
        archive = json.loads((ROOT / "archive.json").read_text(encoding="utf-8"))
        canon = archive["canon_registry"]
        job = next(book for book in canon["books"] if book["canon_id"] == "eotc-ot-22")
        self.assertEqual(canon["reader_count"], 19)
        self.assertIsNone(job.get("reader_id"))
        self.assertTrue(any(
            item.get("candidate_canon_id") == "eotc-ot-22"
            for item in archive["translation_registry"]["edition_leads"]
        ))


if __name__ == "__main__":
    unittest.main()
