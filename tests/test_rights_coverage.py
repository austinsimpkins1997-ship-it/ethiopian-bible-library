import json
from pathlib import Path
import unittest

from build_rights_coverage import build_summary, render_html
from build_standalone import apply_source_rights_scope_notes, mark_unassessed_source_rights


ROOT = Path(__file__).resolve().parents[1]


class RightsCoverageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.archive = json.loads((ROOT / "archive.json").read_text(encoding="utf-8"))
        cls.summary = build_summary(cls.archive)

    def test_source_and_reader_denominators_are_separate_and_complete(self):
        source_summary = self.summary["sources"]
        reader_summary = self.summary["readers"]
        self.assertEqual(source_summary["record_count"], len(self.archive["sources"]))
        self.assertEqual(sum(source_summary["rights_class_counts"].values()), len(self.archive["sources"]))
        basis_count = sum(bool(source.get("rights_basis", "").strip()) for source in self.archive["sources"])
        self.assertEqual(source_summary["rights_basis_record_count"], basis_count)
        self.assertEqual(basis_count, len(self.archive["sources"]))
        self.assertEqual(source_summary["rights_class_counts"]["unknown"], 404)
        self.assertEqual(source_summary["rights_class_counts"]["mixed"], 12)
        self.assertEqual(source_summary["rights_class_counts"]["permission_limited"], 17)
        self.assertEqual(reader_summary["record_count"], len(self.archive["readers"]))
        self.assertEqual(
            reader_summary["canon_linked_record_count"] + reader_summary["research_only_record_count"],
            len(self.archive["readers"]),
        )
        self.assertEqual(sum(reader_summary["rights_class_counts"].values()), len(self.archive["readers"]))

    def test_text_license_is_separated_from_webpage_and_aggregate_package_rights(self):
        sources = {source["source_id"]: source for source in self.archive["sources"]}
        for source_id in ("SRC-387", "SRC-393", "SRC-414"):
            source = sources[source_id]
            self.assertEqual(source["rights_classification"], "unknown")
            self.assertIn("CC BY-SA 4.0", source["rights_status"])
            self.assertIn("not reuse rights in the webpage", source["rights_status"])
            self.assertIn("scoped to the webpage resource", source["rights_basis"])
        for source_id, usfm_count in (("SRC-388", 66), ("SRC-394", 66), ("SRC-415", 27)):
            source = sources[source_id]
            self.assertEqual(source["rights_classification"], "mixed")
            self.assertIn(f"{usfm_count} USFM scripture-text members", source["rights_status"])
            self.assertIn("aggregate package", source["rights_status"])
            self.assertIn("ancillary", source["rights_basis"])
        som_page = sources["SRC-390"]
        self.assertEqual(som_page["rights_classification"], "unknown")
        self.assertIn("both CC BY-NC-ND 3.0 and 4.0 references", som_page["rights_status"])
        self.assertIn("scoped to the webpage resource", som_page["rights_basis"])
        som_package = sources["SRC-391"]
        self.assertEqual(som_package["rights_classification"], "mixed")
        self.assertIn("expressly allows file-format conversion", som_package["rights_status"])
        self.assertIn("not adjudicated", som_package["rights_status"])
        for source_id in ("SRC-400", "SRC-404", "SRC-407", "SRC-410", "SRC-412"):
            source = sources[source_id]
            self.assertEqual(source["rights_classification"], "unknown")
            self.assertIn("CC BY-SA 4.0", source["rights_status"])
            self.assertIn("not reuse rights in the webpage", source["rights_status"])
        for source_id, usfm_count in (("SRC-401", 27), ("SRC-405", 66), ("SRC-408", 27), ("SRC-411", 16), ("SRC-413", 27)):
            source = sources[source_id]
            self.assertEqual(source["rights_classification"], "mixed")
            self.assertIn(f"{usfm_count} USFM scripture-text members", source["rights_status"])
            self.assertIn("aggregate package", source["rights_status"])
            self.assertIn("ancillary", source["rights_basis"])

    def test_tau_page_copyright_and_transcriber_permission_stay_distinct_from_page_reuse(self):
        sources = [
            {"source_id": "SRC-151", "rights_classification": "unknown"},
            {"source_id": "SRC-318", "rights_classification": "unknown"},
        ]
        apply_source_rights_scope_notes(sources)
        for source in sources:
            self.assertEqual(source["rights_classification"], "unknown")
            self.assertIn("reuse rights in this information page", source["rights_status"])
            self.assertIn("Unknown is scoped to the", source["rights_basis"])
        self.assertIn("Kefela Ghebre", sources[0]["rights_status"])
        self.assertIn("Ran HaCohen, February 2026", sources[1]["rights_status"])

    def test_archival_site_reuse_restriction_is_recorded_without_overstating_page_ownership(self):
        source = {"source_id": "SRC-429", "rights_classification": "unknown"}
        apply_source_rights_scope_notes([source])
        self.assertEqual(source["rights_classification"], "unknown")
        self.assertIn("commercially or noncommercially", source["rights_status"])
        self.assertIn("ownership of this specific authority-page text", source["rights_status"])
        self.assertIn("without the archive's express authorization", source["rights_status"])
        self.assertIn("informationobject/browse?collection=9104", source["rights_basis"])

    def test_tau_retained_text_sources_use_the_recorded_noncommercial_permission(self):
        ids = (
            "SRC-061", "SRC-064", "SRC-069", "SRC-186", "SRC-187", "SRC-188", "SRC-189",
            "SRC-190", "SRC-191", "SRC-192", "SRC-193", "SRC-195", "SRC-336", "SRC-337",
        )
        source_records = {source["source_id"]: source for source in self.archive["sources"]}
        for source_id in ids:
            source = source_records[source_id]
            self.assertEqual(source["rights_classification"], "permission_limited", source_id)
            self.assertIn("noncommercial", source["rights_status"], source_id)
            self.assertIn("notices accompany every copy", source["rights_status"], source_id)
            matching_readers = [reader for reader in self.archive["readers"] if source_id in reader.get("source_ids", [])]
            self.assertTrue(matching_readers, source_id)
            self.assertTrue(all(reader["rights_classification"] == "permission_limited" for reader in matching_readers), source_id)

    def test_crosswire_geez_module_notice_is_scoped_to_permission_limited_text(self):
        sources = {source["source_id"]: source for source in self.archive["sources"]}
        module = sources["SRC-059"]
        self.assertEqual(module["rights_classification"], "permission_limited")
        self.assertIn("CrossWire Geez 1.0.1", module["rights_status"])
        self.assertIn("noncommercial purposes only", module["rights_status"])
        self.assertIn("not an open or commercial license", module["rights_status"])
        self.assertIn("module-structure-audit.json", module["rights_basis"])
        linked_readers = [reader for reader in self.archive["readers"] if "SRC-059" in reader.get("source_ids", [])]
        self.assertTrue(linked_readers)
        self.assertTrue(all(reader["rights_classification"] == "permission_limited" for reader in linked_readers))

    def test_unknown_rights_are_not_misrepresented_as_permission_or_prohibition(self):
        html = render_html(self.summary)
        source_counts = self.summary["sources"]
        expected_basis_text = (
            f"Source rights-basis fields are populated for "
            f"{source_counts['rights_basis_record_count']} of {source_counts['record_count']} records"
        )
        self.assertIn("Unknown is neither permission nor a finding that reuse is forbidden", self.summary["classification_limits"]["unknown"])
        self.assertIn("Unknown / not established", html)
        self.assertIn("A source record may describe a catalogue", html)
        self.assertIn(expected_basis_text, html)
        self.assertIn("worldwide rights determination", html)

    def test_open_reader_licenses_are_counted_by_exact_machine_readable_terms(self):
        open_count = self.summary["readers"]["rights_class_counts"]["open_license"]
        terms = self.summary["readers"]["open_license_terms"]
        self.assertEqual(sum(item["reader_record_count"] for item in terms), open_count)
        for item in terms:
            self.assertTrue(item["license_id"])
            self.assertTrue(item["license_url"].startswith("https://"))
        self.assertIn("CC-BY-SA-4.0", render_html(self.summary))

    def test_built_json_html_and_offline_homepage_are_connected(self):
        saved = json.loads((ROOT / "examples" / "rights-coverage.json").read_text(encoding="utf-8"))
        inventory = json.loads((ROOT / "package-inventory.json").read_text(encoding="utf-8"))
        page = (ROOT / "research" / "rights-coverage.html").read_text(encoding="utf-8")
        homepage = (ROOT / "index.html").read_text(encoding="utf-8")
        worker = (ROOT / "sw.js").read_text(encoding="utf-8")
        self.assertEqual(saved, self.summary)
        self.assertEqual(saved["sources"]["record_count"], inventory["source_record_count"])
        self.assertEqual(saved["sources"]["rights_class_counts"], {
            key: inventory["source_rights_class_counts"].get(key, 0)
            for key in saved["sources"]["rights_class_counts"]
        })
        self.assertEqual(saved["readers"]["record_count"], inventory["reader_records"]["total"])
        self.assertEqual(saved["readers"]["canon_linked_record_count"], inventory["reader_records"]["canon_linked"])
        self.assertEqual(saved["readers"]["research_only_record_count"], inventory["reader_records"]["research_only"])
        self.assertEqual(saved["readers"]["rights_class_counts"], {
            key: inventory["reader_records"]["rights_class_counts"].get(key, 0)
            for key in saved["readers"]["rights_class_counts"]
        })
        self.assertEqual(page, render_html(self.summary))
        self.assertIn('href="research/rights-coverage.html"', homepage)
        self.assertIn('href="examples/rights-coverage.json"', homepage)
        self.assertIn("research/rights-coverage.html", worker)
        self.assertIn("examples/rights-coverage.json", worker)

    def test_missing_rights_classification_is_rejected(self):
        archive = {"sources": [{"source_id": "SRC-x", "rights_status": "unknown"}], "readers": []}
        with self.assertRaisesRegex(ValueError, "invalid or missing rights category"):
            build_summary(archive)

    def test_missing_source_rights_basis_states_the_evidence_gap_without_inference(self):
        sources = [
            {"source_id": "SRC-TEST-UNKNOWN", "rights_classification": "unknown"},
            {"source_id": "SRC-TEST-CLAIM", "rights_classification": "public_domain_claimed", "rights_status": "Provider claim, US only."},
        ]
        mark_unassessed_source_rights(sources)
        self.assertIn("does not establish permission or prohibition", sources[0]["rights_basis"])
        self.assertIn("evidence gap", sources[0]["rights_basis"])
        self.assertIn("See rights_status", sources[1]["rights_basis"])
        self.assertIn("not independently", sources[1]["rights_basis"])

    def test_open_license_without_specific_license_reference_is_rejected(self):
        archive = {
            "sources": [],
            "readers": [{
                "reader_id": "reader-without-license",
                "research_corpus_id": "example",
                "rights_classification": "open_license",
                "rights_status": "License stated by source.",
            }],
        }
        with self.assertRaisesRegex(ValueError, "specific license ID and HTTPS URL"):
            build_summary(archive)


if __name__ == "__main__":
    unittest.main()
