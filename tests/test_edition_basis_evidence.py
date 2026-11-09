import json
import unittest
from pathlib import Path

from build_standalone import validate_closed_schema_objects


ROOT = Path(__file__).resolve().parents[1]


class EditionBasisEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = json.loads((ROOT / "translation-registry.json").read_text(encoding="utf-8"))
        cls.archive = json.loads((ROOT / "archive.json").read_text(encoding="utf-8"))
        cls.schema = json.loads((ROOT / "translation-registry.schema.json").read_text(encoding="utf-8"))
        cls.app = (ROOT / "app.js").read_text(encoding="utf-8")

    def test_registry_schema_accepts_attributed_family_level_basis_claims(self):
        validate_closed_schema_objects(self.registry, self.schema, self.schema, "translation-registry.json")
        evidence = next(item for item in self.registry["edition_basis_evidence"] if item["family_id"] == "arabic-van-dyck-standard")
        self.assertEqual(evidence["witness_relation"], "family_level_not_collated")
        self.assertEqual([claim["source_language_tags"] for claim in evidence["claims"]], [["hbo", "arc"], ["grc"]])
        self.assertEqual(evidence["claim_type"], "historical_secondary_report")

    def test_historical_policy_does_not_promote_digital_witness_paths(self):
        arabic = [item for item in self.registry["research_corpora"] if item.get("translation_id") == "arabic-van-dyck-standard"]
        self.assertEqual(len(arabic), 66)
        self.assertTrue(all(item["translation_basis_status"] == "unknown" for item in arabic))
        self.assertTrue(all(item.get("translation_path") is None for item in arabic))

    def test_webbe_publisher_claim_is_family_scoped_and_keeps_module_paths_unknown(self):
        evidence = next(item for item in self.registry["edition_basis_evidence"] if item["family_id"] == "webbe-2020-english")
        self.assertEqual(evidence["claim_type"], "publisher_statement")
        self.assertEqual(evidence["witness_relation"], "family_level_not_collated")
        self.assertEqual([claim["scope"] for claim in evidence["claims"]], ["old_testament", "new_testament"])
        self.assertEqual([claim["source_language_tags"] for claim in evidence["claims"]], [["hbo", "arc"], ["grc"]])
        webbe = [item for item in self.registry["research_corpora"] if item.get("translation_id") == "webbe-2020-english"]
        self.assertEqual(len(webbe), 81)
        self.assertTrue(all(item["translation_basis_status"] == "unknown" for item in webbe))
        self.assertTrue(all(item.get("translation_path") is None for item in webbe))
        self.assertIn("English", evidence["limitations"])

    def test_reader_language_lens_displays_edition_family_evidence_with_scope_warning(self):
        self.assertIn("edition_basis_evidence", self.app)
        self.assertIn("Attributed edition-family basis report (not checked against this digital witness)", self.app)
        self.assertIn("editionBasis.source_ids", self.app)

    def test_downloadable_and_embedded_registries_share_evidence_and_citations(self):
        embedded = self.archive["translation_registry"]
        self.assertEqual(self.registry, embedded)
        source_urls = {source["source_id"]: source["url"] for source in self.archive["sources"]}
        webbe_evidence = next(item for item in embedded["edition_basis_evidence"] if item["family_id"] == "webbe-2020-english")
        self.assertEqual(
            {source_urls[source_id] for source_id in webbe_evidence["source_ids"]},
            {"https://ebible.org/eng-web/webfaq.htm", "https://worldenglish.bible/"},
        )
        webbe = [item for item in embedded["research_corpora"] if item.get("translation_id") == "webbe-2020-english"]
        self.assertEqual(len(webbe), 81)
        self.assertEqual(source_urls.get("SRC-435"), "https://worldenglish.bible/")
        self.assertTrue(all("SRC-435" in item["source_ids"] for item in webbe))
        webbe_readers = [item for item in self.archive["readers"] if item.get("translation_id") == "webbe-2020-english"]
        self.assertEqual(len(webbe_readers), 81)
        self.assertTrue(all("SRC-435" in item["source_ids"] for item in webbe_readers))


if __name__ == "__main__":
    unittest.main()
