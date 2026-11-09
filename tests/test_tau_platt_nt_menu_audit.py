from pathlib import Path
import unittest

from build_tau_platt_nt_menu_audit import apply, build_report
from archive_helpers import read_embedded_archive


ROOT = Path(__file__).resolve().parents[1]


class TauPlattNTMenuAuditTests(unittest.TestCase):
    def test_captured_menu_separates_grouped_forms_and_display_classes(self):
        report = build_report()
        self.assertEqual(report["menu_form_count"], 21)
        self.assertEqual(len(report["other_menu_forms"]), 4)
        self.assertEqual(
            report["grey_form_titles"],
            ["Colossians", "Ephesians", "John", "Luke", "Mark", "Matthew", "Philippians", "Romans"],
        )
        self.assertEqual(len(report["green_form_titles"]), 8)
        self.assertTrue(any("grouped labels" in note for note in report["limits"]))
        self.assertTrue(any("not verified chapter counts" in note for note in report["limits"]))

    def test_only_sampled_wrappers_are_described_as_image_references(self):
        report = build_report()
        self.assertEqual([row["menu_title"] for row in report["sample_wrappers"]], ["Acts", "Romans"])
        for row in report["sample_wrappers"]:
            self.assertEqual(row["image_count_in_wrapper"], 1)
            self.assertIn("not fetched or copied", row["evidence_limit"])

    def test_registry_keeps_tau_corpus_unbundled_and_surfaces_local_evidence(self):
        archive = read_embedded_archive(ROOT)
        apply(archive)
        source = next(item for item in archive["sources"] if item["source_id"] == "SRC-086")
        corpus = next(
            item for item in archive["translation_registry"]["corpus_leads"]
            if item["corpus_id"] == "ethiopic-new-testament-platt-1830-tau"
        )
        self.assertFalse(corpus["text_bundled"])
        self.assertEqual(corpus["rights_classification"], "permission_limited")
        self.assertEqual(source["local_metadata_url"], "readers/source/tau-platt-nt-menu/SOURCE-CAPTURE.json")
        self.assertEqual(source["local_review_url"], "research/tau-platt-nt-menu-audit.html")
        self.assertIn("no image or scripture text bundled", source["archive_status"].lower())
        self.assertTrue((ROOT / source["local_review_url"]).is_file())


if __name__ == "__main__":
    unittest.main()
