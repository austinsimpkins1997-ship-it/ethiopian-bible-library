import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class JosephasDiscoveryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.archive = json.loads((ROOT / "archive.json").read_text(encoding="utf-8"))
        cls.registry = json.loads((ROOT / "translation-registry.json").read_text(encoding="utf-8"))
        cls.canon = json.loads((ROOT / "canon-registry.json").read_text(encoding="utf-8"))

    def test_title_related_sources_are_recorded_as_separate_metadata_leads(self):
        sources = {item["source_id"]: item for item in self.archive["sources"]}
        leads = {item["edition_id"]: item for item in self.registry["edition_leads"]}
        beta = leads["betamasaheft-josippon-cae2598"]
        bl = leads["bl-or824-joseph-ben-goryon"]
        bl_older = leads["bl-or822-joseph-ben-goryon"]
        oebp = leads["oebp-zena-ayhud-2017-acquisition"]
        morwen = leads["morwen-josippon-epitome-1722"]
        reconstruction = leads["ethiopian-canon-josippon-reconstruction"]
        self.assertNotIn("ethiopian-canon-josippon-reconstruction-2026", leads)

        self.assertIn("Zenā ʾAyhud", sources["SRC-343"]["inspection_and_limitations"])
        self.assertIn("error in one of the work's sources", sources["SRC-343"]["inspection_and_limitations"])
        self.assertIn("ff. 3r–136v", sources["SRC-344"]["inspection_and_limitations"])
        self.assertIn("ff. 2r–136v", sources["SRC-386"]["inspection_and_limitations"])
        self.assertIn("17th century", sources["SRC-386"]["inspection_and_limitations"])
        self.assertIn("Zëna Ayhud in Amharic", sources["SRC-422"]["inspection_and_limitations"])
        self.assertIn("not an EOTC-issued catalogue record", sources["SRC-422"]["inspection_and_limitations"])
        self.assertEqual(sources["SRC-422"]["local_review_url"], "research/josephas-source-review.md")
        self.assertIn("not a full English translation", sources["SRC-430"]["inspection_and_limitations"])
        self.assertIn("University of Pennsylvania", sources["SRC-431"]["source_name"])
        self.assertIn("not a direct Geʽez translation", sources["SRC-432"]["inspection_and_limitations"])
        self.assertIn("© 2026", sources["SRC-432"]["inspection_and_limitations"])
        self.assertEqual((beta["candidate_canon_id"], beta["mapping_state"]), ("eotc-ot-46", "uncertain"))
        self.assertEqual((bl["candidate_canon_id"], bl["mapping_state"]), ("eotc-ot-46", "uncertain"))
        self.assertEqual((bl_older["candidate_canon_id"], bl_older["mapping_state"]), ("eotc-ot-46", "uncertain"))
        self.assertEqual((oebp["candidate_canon_id"], oebp["mapping_state"]), ("eotc-ot-46", "asserted_by_source"))
        self.assertEqual(oebp["source_ids"], ["SRC-029", "SRC-422"])
        self.assertEqual(oebp["language_tag"], "und")
        self.assertEqual(oebp["language_name"], "Undetermined")
        self.assertEqual(oebp["script_code"], "Zzzz")
        self.assertEqual((morwen["candidate_canon_id"], morwen["mapping_state"]), ("eotc-ot-46", "related_work"))
        self.assertEqual((morwen["language_tag"], morwen["script_code"]), ("en", "Latn"))
        self.assertIn("abridged account", morwen["scope_description"])
        self.assertEqual((reconstruction["candidate_canon_id"], reconstruction["mapping_state"]), ("eotc-ot-46", "asserted_by_source"))
        self.assertIn("explicitly says it is not a direct Geʽez translation", reconstruction["scope_description"])
        self.assertIn("not an independently verified crosswalk", reconstruction["scope_description"])
        self.assertEqual(beta["witness_type"], "unknown")
        self.assertEqual(bl["witness_type"], "manuscript")
        self.assertIn("must not be silently merged with Or 824", bl_older["scope_description"])
        self.assertEqual(bl_older["source_ids"], ["SRC-029", "SRC-386"])
        for lead in (beta, bl, bl_older, oebp, morwen, reconstruction):
            self.assertFalse(lead["text_bundled"])
            self.assertEqual(lead["rights_classification"], "unknown")
            self.assertNotIn("bundled_reader_id", lead)

    def test_catalogue_preserves_unknown_identity_and_does_not_inflate_reader_coverage(self):
        catalogue = next(item for item in self.archive["catalogue"] if item["catalogue_id"] == "eotc-054")
        book = next(item for item in self.canon["books"] if item["canon_id"] == "eotc-ot-46")
        eap = next(item for item in self.registry["edition_leads"] if item["edition_id"] == "bl-eap704-2-3-zena-ayhud")
        self.assertIn("unverified", catalogue["identity_status"])
        self.assertIn("no text or images are bundled", catalogue["text_availability_status"])
        self.assertIn("do not infer a complete text", catalogue["reviewer_notes"])
        self.assertIsNone(book.get("reader_id"))
        self.assertIn("related Geʽez catalogue records located", book["reader_status"])
        self.assertEqual(eap["edition_id"], "bl-eap704-2-3-zena-ayhud")
        self.assertIn("does not make that identification", eap["scope_description"])
        self.assertEqual(self.canon["reader_count"], 19)
        self.assertEqual(len(self.canon["books"]), 81)
        self.assertIn("SRC-386", catalogue["evidence_source_ids"])
        self.assertIn("SRC-422", catalogue["evidence_source_ids"])


if __name__ == "__main__":
    unittest.main()
