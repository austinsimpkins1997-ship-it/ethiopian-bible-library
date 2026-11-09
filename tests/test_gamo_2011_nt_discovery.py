import json
import unittest
from pathlib import Path

from build_gamo_2011_nt_discovery import CORPUS_LEAD, SOURCE, apply
from build_standalone import validate_closed_schema_objects


ROOT = Path(__file__).resolve().parents[1]


class Gamo2011NtDiscoveryTests(unittest.TestCase):
    def test_adds_distinct_unbundled_record_with_unknown_basis_and_mixed_terms(self):
        archive = {"sources": [], "translation_registry": {"corpus_leads": []}}
        apply(archive)
        source = next(item for item in archive["sources"] if item["source_id"] == "SRC-397")
        lead = next(item for item in archive["translation_registry"]["corpus_leads"] if item["corpus_id"] == "gmv-gmvwbt-2011-nt")
        self.assertEqual(source, SOURCE)
        self.assertEqual(lead, CORPUS_LEAD)
        self.assertIsNone(lead["translation_path"])
        self.assertEqual(lead["basis_language_tag"], "und")
        self.assertFalse(lead["text_bundled"])
        self.assertEqual(lead["rights_classification"], "mixed")
        self.assertNotIn("candidate_canon_id", lead)

    def test_apply_is_idempotent_and_rejects_conflicts(self):
        archive = {"sources": [], "translation_registry": {"corpus_leads": []}}
        apply(archive)
        apply(archive)
        self.assertEqual(len(archive["sources"]), 1)
        self.assertEqual(len(archive["translation_registry"]["corpus_leads"]), 1)
        archive["sources"][0]["url"] = "https://example.invalid/"
        with self.assertRaises(ValueError):
            apply(archive)

    def test_registry_schema_accepts_the_metadata_only_record(self):
        schema = json.loads((ROOT / "translation-registry.schema.json").read_text(encoding="utf-8"))
        registry = json.loads((ROOT / "translation-registry.json").read_text(encoding="utf-8"))
        registry["corpus_leads"] = [CORPUS_LEAD]
        validate_closed_schema_objects(registry, schema, schema, "translation-registry.json")


if __name__ == "__main__":
    unittest.main()
