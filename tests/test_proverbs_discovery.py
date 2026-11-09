import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ProverbsDiscoveryTests(unittest.TestCase):
    def test_rights_and_chapter_crosswalk_uncertainty_keep_source_unbundled(self):
        archive = json.loads((ROOT / "archive.json").read_text(encoding="utf-8"))
        registry = json.loads((ROOT / "translation-registry.json").read_text(encoding="utf-8"))
        canon = json.loads((ROOT / "canon-registry.json").read_text(encoding="utf-8"))
        source = next(x for x in archive["sources"] if x["source_id"] == "SRC-280")
        scholarship = next(x for x in archive["sources"] if x["source_id"] == "SRC-281")
        license_context = next(x for x in archive["sources"] if x["source_id"] == "SRC-295")
        lead = next(x for x in registry["edition_leads"] if x["edition_id"] == "betamasaheft-proverbs-of-solomon-tei-2026")
        catalogue = next(x for x in archive["catalogue"] if x["catalogue_id"] == "eotc-029")
        book = next(x for x in canon["books"] if x["canon_id"] == "eotc-ot-24")

        self.assertFalse(lead["text_bundled"])
        self.assertEqual((lead["candidate_canon_id"], lead["mapping_state"]), ("eotc-ot-24", "uncertain"))
        self.assertEqual(lead["rights_classification"], "mixed")
        self.assertIn("CC BY-NC-SA 4.0", lead["rights_status"])
        self.assertIn("766 labeled lines", lead["scope_description"])
        self.assertIn("Proverbs 1–24", scholarship["inspection_and_limitations"])
        self.assertIn("Proverbs 25–29", scholarship["inspection_and_limitations"])
        review = (ROOT / "research/proverbs-source-review.md").read_text(encoding="utf-8")
        self.assertIn(f"]({scholarship['url']})", review)
        self.assertNotIn("{SCHOLARLY_URL}", review)
        self.assertIn("26 ordered chapter divisions", source["inspection_and_limitations"])
        self.assertIn("No scripture wording is copied", source["inspection_and_limitations"])
        self.assertEqual(license_context["url"], "https://www.fdm.uni-hamburg.de/en/uhh-data-notes/data-notes/issue-2020/dano-01-001.html")
        self.assertIn("each file contains a specific license statement", license_context["inspection_and_limitations"])
        self.assertIn("does not explain the current Beta maṣāḥǝft Guidelines", license_context["inspection_and_limitations"])
        self.assertIn("underlying print rights unresolved", license_context["archive_status"])
        self.assertIn("SRC-295", catalogue["evidence_source_ids"])
        self.assertIn("SRC-295", lead["source_ids"])
        self.assertEqual(catalogue["source_id"], "SRC-000")
        self.assertIn("SRC-280", catalogue["evidence_source_ids"])
        self.assertIn("not bundled", catalogue["text_availability_status"])
        self.assertEqual(book["reader_status"], "No reader bundled here; external availability not assessed")
        self.assertEqual(canon["reader_count"], 19)

        self.assertFalse((ROOT / "readers/source/proverbs/LIT3927Messale.xml").exists())
        self.assertFalse((ROOT / "readers/proverbs-of-solomon-betamasaheft-tei-research.json").exists())
        self.assertFalse(any(x.get("reader_id") == "proverbs-of-solomon-betamasaheft-tei-research" for x in archive["readers"]))
        self.assertFalse(any(x.get("corpus_id") == "betamasaheft-proverbs-of-solomon-tei-research" for x in registry["research_corpora"]))


if __name__ == "__main__":
    unittest.main()
