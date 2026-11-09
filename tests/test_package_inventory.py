"""The public snapshot inventory must be generated from archive records."""
from __future__ import annotations

import json
import copy
import re
import unittest
from pathlib import Path

from build_standalone import (
    apply_standard_ot_research_crosswalks,
    build_package_inventory,
    render_package_inventory,
)

ROOT = Path(__file__).resolve().parents[1]


class PackageInventoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.archive = json.loads((ROOT / "archive.json").read_text(encoding="utf-8"))
        portable = json.loads((ROOT / "examples/portable-text-layers.json").read_text(encoding="utf-8"))
        cls.inventory = build_package_inventory(cls.archive, portable["records"])
        cls.portable_records = portable["records"]

    def test_counts_derive_from_authoritative_records(self):
        inventory = self.inventory
        self.assertEqual(inventory["catalogue_row_count"], len(self.archive["catalogue"]))
        self.assertEqual(inventory["source_record_count"], len(self.archive["sources"]))
        self.assertEqual(inventory["related_work_record_count"], len(self.archive["related_texts"]))
        self.assertEqual(inventory["reader_records"]["total"], len(self.archive["readers"]))
        self.assertEqual(
            inventory["reader_records"]["total"],
            inventory["reader_records"]["canon_linked"] + inventory["reader_records"]["research_only"],
        )
        canon = inventory["church_list"]
        self.assertEqual(canon["entry_count"], canon["canon_linked_reader_entry_count"] + canon["research_candidate_entry_count"] + canon["entries_with_neither_local_reader_count"])
        self.assertEqual(canon["canon_linked_reader_entry_count"], inventory["reader_records"]["canon_linked"])
        ot_candidates = inventory["standard_ot_research"]
        self.assertEqual(ot_candidates["candidate_reader_record_count"], 307)
        self.assertEqual(ot_candidates["entry_count"], 40)
        self.assertEqual(ot_candidates["module_code_count"], 46)
        self.assertEqual(ot_candidates["language_tag_count"], 7)
        self.assertEqual(ot_candidates["mapping_state_counts"], {"reviewed_match": 24, "uncertain": 283})
        self.assertEqual(ot_candidates["source_ids"], ["SRC-029", "SRC-384", "SRC-396"])
        self.assertIn("Reviewed title matches do not establish EOTC/Eritrean affiliation", ot_candidates["scope_note"])
        self.assertEqual(canon["canon_linked_reader_entry_count"], 19)
        self.assertEqual(
            inventory["rights_withheld_text_record_count"],
            len(self.archive.get("rights_withheld_texts", [])),
        )
        expected_rights = {}
        for reader in self.archive["readers"]:
            key = reader.get("rights_classification", "unknown")
            expected_rights[key] = expected_rights.get(key, 0) + 1
        self.assertEqual(inventory["reader_records"]["rights_class_counts"], dict(sorted(expected_rights.items())))
        self.assertEqual(sum(expected_rights.values()), inventory["reader_records"]["total"])
        translation_registry = self.archive["translation_registry"]
        profiles = {item["language_tag"]: item for item in translation_registry["languages"]}
        bundled_research = [
            item for item in translation_registry["research_corpora"]
            if item.get("reader_status") == "bundled_research_reader"
        ]
        script_names = {"Arab": "Arabic script", "Ethi": "Ethiopic script", "Latn": "Latin script"}
        expected_labels = sorted({
            f"{profiles[item['language_tag']]['language_name']} "
            f"({script_names.get(item['script_code'], item['script_code'])})"
            for item in bundled_research
        })
        self.assertEqual(
            inventory["language_profile_content_counts"]["bundled_research_language_script_labels"],
            expected_labels,
        )
        self.assertEqual(
            inventory["language_profile_content_counts"]["bundled_research_language_script_pair_count"],
            len(expected_labels),
        )
        self.assertEqual(inventory["language_profile_content_counts"]["with_bundled_research_readers"], 14)
        self.assertEqual(len(expected_labels), 15)
        research_provenance = inventory["research_translation_provenance"]
        self.assertEqual(
            research_provenance["text_origin_counts"],
            {"published_translation": 736, "source_transcription": 4},
        )
        self.assertEqual(
            research_provenance["published_translation_basis_counts"],
            {"established": 42, "unknown": 694},
        )
        self.assertIn("not that no translation exists", research_provenance["scope_note"])
        self.assertIn("Dawro (Latin script)", expected_labels)
        self.assertIn("Oyda (Ethiopic script)", expected_labels)
        expected_linked_rights = {}
        canon_ids = {book["canon_id"] for book in self.archive["canon_registry"]["books"]}
        for reader in self.archive["readers"]:
            if reader.get("canon_id") in canon_ids:
                key = reader.get("rights_classification", "unknown")
                expected_linked_rights[key] = expected_linked_rights.get(key, 0) + 1
        self.assertEqual(
            inventory["reader_records"]["canon_linked_rights_class_counts"],
            dict(sorted(expected_linked_rights.items())),
        )
        self.assertEqual(sum(expected_linked_rights.values()), inventory["reader_records"]["canon_linked"])
        self.assertEqual(expected_linked_rights.get("open_license", 0), 0)
        self.assertEqual(expected_linked_rights.get("permission_limited"), 19)

    def test_generated_json_and_readme_table_match_current_snapshot(self):
        saved = json.loads((ROOT / "package-inventory.json").read_text(encoding="utf-8"))
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertEqual(saved, self.inventory)
        self.assertEqual(readme.count("<!-- GENERATED PACKAGE INVENTORY: START -->"), 1)
        self.assertEqual(readme.count("<!-- GENERATED PACKAGE INVENTORY: END -->"), 1)
        self.assertIn(render_package_inventory(self.inventory), readme)
        self.assertNotIn("Inventory is generated from the current archive records during each standalone build.", readme)

    def test_readme_does_not_duplicate_live_coverage_counts_outside_generated_inventory(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        manual_copy = readme.replace(render_package_inventory(self.inventory), "")
        self.assertNotRegex(
            manual_copy,
            re.compile(r"(?i)\b\d+\s+(?:of\s+81|church-list\s+entries?)\s+have\s+canon-linked\s+readers?"),
        )
        self.assertNotRegex(
            manual_copy,
            re.compile(r"(?i)\b\d+\s+separately scoped research readers?\s+remain"),
        )
        self.assertNotRegex(manual_copy, re.compile(r"(?i)all\s+\d+\s+links have a scoped"))

    def test_ot_candidate_catalogue_notes_remain_idempotent_across_rebuilds(self):
        archive = copy.deepcopy(self.archive)
        apply_standard_ot_research_crosswalks(archive)
        apply_standard_ot_research_crosswalks(archive)
        catalogue = next(item for item in archive["catalogue"] if item["catalogue_id"] == "eotc-001")
        status = catalogue["text_availability_status"]
        self.assertEqual(status.count("8 separately scoped Genesis title-candidate research readers"), 1)
        self.assertEqual(status.count("Per-reader source, rights, and review limits remain attached individually."), 1)

    def test_source_records_require_provenance_and_explicit_rights_assessments(self):
        schema = json.loads((ROOT / "schemas/source-record.schema.json").read_text(encoding="utf-8"))
        self.assertTrue({
            "source_id", "source_name", "url", "inspection_and_limitations", "archive_status",
            "rights_classification", "rights_status",
        }.issubset(set(schema["required"])))
        self.assertIn("unknown", schema["properties"]["rights_classification"]["enum"])

        archive = copy.deepcopy(self.archive)
        archive["sources"][0]["rights_status"] = "   "
        with self.assertRaisesRegex(ValueError, "rights_status"):
            build_package_inventory(archive, self.portable_records)

        archive = copy.deepcopy(self.archive)
        archive["sources"][0]["rights_classification"] = "open_license"
        with self.assertRaisesRegex(ValueError, "license_id"):
            build_package_inventory(archive, self.portable_records)


if __name__ == "__main__":
    unittest.main()
