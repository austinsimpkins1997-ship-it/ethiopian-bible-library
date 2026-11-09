"""Tegsats evidence must retain distinct source claims and unresolved scope."""
from __future__ import annotations

import json
import hashlib
import unittest
from pathlib import Path

from archive_helpers import read_embedded_archive

ROOT = Path(__file__).resolve().parents[1]


class TegsatsDiscoveryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.archive = read_embedded_archive(ROOT)
        cls.canon = json.loads((ROOT / "canon-registry.json").read_text(encoding="utf-8"))
        cls.translation = json.loads((ROOT / "translation-registry.json").read_text(encoding="utf-8"))

    def test_church_title_and_historical_boundary_disagreement_are_preserved(self):
        row = next(item for item in self.archive["catalogue"] if item["catalogue_id"] == "eotc-030")
        book = next(item for item in self.canon["books"] if item["canon_id"] == "eotc-ot-25")
        self.assertEqual(row["display_name"], "Tegsats (Reproof)")
        self.assertEqual(book["display_name"], "Tegsats (Reproof)")
        self.assertEqual(row["chapter_count"].split(";")[0], "Not established for this Church-list entry")
        self.assertIn("Proverbs 25–31", row["chapter_order_status"])
        self.assertIn("Proverbs 25–29", row["chapter_order_status"])
        self.assertEqual(row["completeness_status"], "Not assessed; no defined edition or witness has been selected and collated.")
        self.assertIsNone(book["reader_id"])
        self.assertEqual(len(self.canon["books"]), 81)

    def test_claim_sources_are_attributed_and_text_rights_are_not_inferred(self):
        source_ids = {item["source_id"] for item in self.archive["sources"]}
        row = next(item for item in self.archive["catalogue"] if item["catalogue_id"] == "eotc-030")
        self.assertTrue({"SRC-029", "SRC-101", "SRC-108", "SRC-205", "SRC-281"} <= set(row["evidence_source_ids"]))
        self.assertTrue(set(row["evidence_source_ids"]) <= source_ids)
        article = next(item for item in self.archive["sources"] if item["source_id"] == "SRC-101")
        self.assertIn("printed p. 120, note 51", article["inspection_and_limitations"])
        self.assertIn("Tegsas (Proverbs 25–31)", article["inspection_and_limitations"])
        self.assertIn("not an official current ruling", article["inspection_and_limitations"])
        self.assertIn("not been established", row["rights_status"])
        self.assertIn("No text is copied", row["reviewer_notes"])
        self.assertTrue((ROOT / "research/tegsats-source-review.md").is_file())

    def test_british_library_manuscript_lead_is_separate_from_canon_coverage(self):
        row = next(item for item in self.archive["catalogue"] if item["catalogue_id"] == "eotc-030")
        book = next(item for item in self.canon["books"] if item["canon_id"] == "eotc-ot-25")
        source = next(item for item in self.archive["sources"] if item["source_id"] == "SRC-385")
        lead = next(item for item in self.translation["edition_leads"] if item["edition_id"] == "bl-add-ms-16186-tagsasa-solomon")
        self.assertIn("Tagśāṣa Salomon", source["inspection_and_limitations"])
        self.assertIn("Proverbs 25–29", source["inspection_and_limitations"])
        self.assertIn("access restrictions apply", source["inspection_and_limitations"])
        self.assertIn("available under CC BY", source["inspection_and_limitations"])
        self.assertTrue({"SRC-029", "SRC-385"} <= set(row["evidence_source_ids"]))
        self.assertTrue({"SRC-029", "SRC-385"} <= set(book["source_ids"]))
        self.assertEqual(lead["mapping_state"], "uncertain")
        self.assertFalse(lead["text_bundled"])
        self.assertEqual(lead["rights_classification"], "unknown")
        self.assertIn("catalogue text", lead["rights_status"])
        self.assertIn("not presumed to license manuscript images", lead["rights_status"])
        self.assertIn("not proof", lead["scope_description"])
        self.assertIsNone(book.get("reader_id"))
        self.assertEqual(len(self.canon["books"]), 81)

    def test_iiif_manifest_is_offline_metadata_only_and_rights_scoped(self):
        source = next(item for item in self.archive["sources"] if item["source_id"] == "SRC-385")
        base = ROOT / "readers/source/tegsats-bl-add-ms-16186"
        capture = json.loads((base / "capture-manifest.json").read_text(encoding="utf-8"))
        manifest_path = base / "iiif-manifest.json"
        manifest_bytes = manifest_path.read_bytes()
        manifest = json.loads(manifest_bytes)
        canvases = manifest["items"]
        labels = ["".join(item["label"].get("en", [])) for item in canvases]

        self.assertEqual(source["local_metadata_url"], "readers/source/tegsats-bl-add-ms-16186/capture-manifest.json")
        self.assertEqual(source["local_review_url"], "research/tegsats-source-review.md")
        self.assertEqual(capture["sha256"], hashlib.sha256(manifest_bytes).hexdigest())
        self.assertEqual(capture["bytes"], len(manifest_bytes))
        self.assertEqual((capture["observed_canvas_count"], len(canvases)), (159, 159))
        self.assertTrue({"f.22r", "f.22v", "f.23r", "f.24r", "f.25r", "f.26r", "f.26v"} <= set(labels))
        self.assertEqual(manifest.get("rights"), "")
        self.assertIn("No canvas image bytes", capture["scope"])
        self.assertIn("top-level rights field is present but blank", source["inspection_and_limitations"])
        self.assertIn("not presumed to cover manuscript images", source["inspection_and_limitations"])
        lead = next(item for item in self.translation["edition_leads"] if item["edition_id"] == "bl-add-ms-16186-tagsasa-solomon")
        self.assertEqual(lead["rights_classification"], "unknown")
        self.assertFalse(any("image" in key.lower() and isinstance(value, bytes) for key, value in manifest.items()))

    def test_pilkington_abstract_adds_an_attributed_english_lead_not_reader_coverage(self):
        source = next(item for item in self.archive["sources"] if item["source_id"] == "SRC-108")
        edition = next(item for item in self.translation["edition_leads"] if item["edition_id"] == "pilkington-tegsats-reproof-1978")
        translation = next(item for item in self.translation["translation_leads"] if item["translation_id"] == "pilkington-proverbs-ethiopic-en-1978")
        book = next(item for item in self.canon["books"] if item["canon_id"] == "eotc-ot-25")
        self.assertIn("Cambridge University Library Add. 1570", source["inspection_and_limitations"])
        self.assertIn("21 Ethiopic manuscripts", source["inspection_and_limitations"])
        self.assertIn("translated literally", source["inspection_and_limitations"])
        self.assertIn("pp. 318–522", source["inspection_and_limitations"])
        self.assertIn("not been inspected", source["inspection_and_limitations"])
        self.assertFalse(edition["text_bundled"])
        self.assertIn("remain uninspected", edition["scope_description"])
        self.assertEqual(translation["translation_path"], ["gez", "en"])
        self.assertEqual(translation["rights_classification"], "unknown")
        self.assertFalse(translation["text_bundled"])
        self.assertEqual(translation["mapping_state"], "uncertain")
        self.assertIsNone(book["reader_id"])
        self.assertEqual(len(self.canon["books"]), 81)


if __name__ == "__main__":
    unittest.main()
