"""The public 81-entry coverage register is derived and scope-limited."""
from __future__ import annotations

import json
import unittest
from pathlib import Path

from book_coverage import build_book_coverage
from build_standalone import normalize_catalogue_custodians, validate_closed_schema_objects, validate_schema_constraints


ROOT = Path(__file__).resolve().parents[1]


class BookCoverageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.archive = json.loads((ROOT / "archive.json").read_text(encoding="utf-8"))
        cls.reader_urls = {}
        for path in (ROOT / "readers").glob("*.json"):
            record = json.loads(path.read_text(encoding="utf-8"))
            if record.get("reader_id"):
                cls.reader_urls[record["reader_id"]] = path.relative_to(ROOT).as_posix()
        cls.coverage = build_book_coverage(cls.archive, cls.reader_urls)

    def test_catalogue_custodian_is_self_while_prior_sources_remain_evidence(self):
        sources = {"SRC-000", "SRC-029", "SRC-279"}
        records = [{
            "catalogue_id": "test", "display_name": "Test work", "source_id": "SRC-279",
            "evidence_source_ids": ["SRC-029"],
        }]
        normalize_catalogue_custodians(records, sources)
        normalize_catalogue_custodians(records, sources)
        self.assertEqual(records[0]["source_id"], "SRC-000")
        self.assertEqual(records[0]["evidence_source_ids"], ["SRC-029", "SRC-279"])

    def test_built_catalogue_rows_use_self_as_custodian(self):
        self.assertEqual(len(self.archive["catalogue"]), 90)
        for row in self.archive["catalogue"]:
            self.assertEqual(row.get("source_id"), "SRC-000", row["catalogue_id"])
        for evidence_source in ("SRC-041", "SRC-065", "SRC-151", "SRC-279", "SRC-280", "SRC-289", "SRC-433"):
            self.assertTrue(any(evidence_source in row.get("evidence_source_ids", []) for row in self.archive["catalogue"]))

    def test_all_registered_entries_have_one_evidence_scoped_availability_state(self):
        coverage = self.coverage
        self.assertEqual(coverage["entry_count"], len(self.archive["canon_registry"]["books"]))
        self.assertEqual(coverage["entry_count"], 81)
        self.assertEqual(len(coverage["entries"]), len({item["canon_id"] for item in coverage["entries"]}))
        schema = json.loads((ROOT / "schemas" / "book-coverage.schema.json").read_text(encoding="utf-8"))
        validate_closed_schema_objects(coverage, schema, schema, "book-coverage.json")
        validate_schema_constraints(coverage, schema, schema, "book-coverage.json")
        self.assertEqual(
            sum(entry["mapping_state"] == "unrecorded" for entry in coverage["entries"]),
            sum(not book.get("mapping_state") for book in self.archive["canon_registry"]["books"]),
        )
        self.assertEqual(
            coverage["availability_counts"],
            {
                "canon_linked_reader": 19,
                "reviewed_title_match_research_reader_only": 32,
                "source_asserted_research_reader_only": 0,
                "research_candidate_reader_only": 17,
                "no_bundled_reader": 13,
            },
        )
        for entry in coverage["entries"]:
            if entry["reader_availability"] == "canon_linked_reader":
                self.assertTrue(entry["canon_linked_readers"])
            elif entry["reader_availability"] in {
                "reviewed_title_match_research_reader_only",
                "source_asserted_research_reader_only",
                "research_candidate_reader_only",
            }:
                self.assertFalse(entry["canon_linked_readers"])
                self.assertTrue(entry["research_reader_candidates"])
            else:
                self.assertFalse(entry["canon_linked_readers"])
                self.assertFalse(entry["research_reader_candidates"])

    def test_unbundled_leads_remain_distinct_from_reader_coverage(self):
        entries = {item["canon_id"]: item for item in self.coverage["entries"]}
        didascalia = entries["eotc-nt-35"]
        self.assertEqual(didascalia["reader_availability"], "no_bundled_reader")
        self.assertFalse(didascalia["canon_linked_readers"])
        self.assertFalse(didascalia["research_reader_candidates"])
        self.assertTrue(didascalia["unbundled_leads"])
        self.assertTrue(all(not lead["text_bundled"] for lead in didascalia["unbundled_leads"]))
        self.assertEqual(len(didascalia["supplemental_research_views"]), 1)
        didascalia_view = didascalia["supplemental_research_views"][0]
        self.assertEqual(didascalia_view["source_id"], "SRC-376")
        self.assertEqual(didascalia_view["research_view_url"], "research/didascalia-harden1920-ocr-reader.html")
        self.assertIn("no reader text", didascalia_view["archive_status"].lower())
        self.assertTrue((ROOT / didascalia_view["research_view_url"]).is_file())
        enoch = entries["eotc-ot-14"]
        self.assertEqual(enoch["reader_availability"], "no_bundled_reader")
        self.assertFalse(enoch["canon_linked_readers"])
        self.assertFalse(enoch["research_reader_candidates"])
        enoch_view = next(view for view in enoch["supplemental_research_views"] if view["source_id"] == "SRC-125")
        self.assertEqual(enoch_view["research_view_url"], "research/enoch-charles-1917-source.html")
        self.assertIn("not a normalized or verified reader", enoch_view["archive_status"])
        self.assertTrue((ROOT / enoch_view["research_view_url"]).is_file())
        source_ids = {source["source_id"] for source in self.archive["sources"]}
        canon_books = {item["canon_id"]: item for item in self.archive["canon_registry"]["books"]}
        catalogue = {item["catalogue_id"]: item for item in self.archive["catalogue"]}
        for entry in self.coverage["entries"]:
            self.assertTrue(set(entry["related_source_ids"]) <= source_ids, entry["canon_id"])
            book = canon_books[entry["canon_id"]]
            self.assertEqual(entry["canon_entry_source_ids"], sorted(set(book.get("source_ids", []))))
            expected_catalogue_sources = sorted({
                source_id
                for catalogue_id in book.get("catalogue_ids", [])
                if catalogue_id in catalogue
                for source_id in [catalogue[catalogue_id].get("source_id"), *catalogue[catalogue_id].get("evidence_source_ids", [])]
                if source_id
            })
            self.assertEqual(entry["catalogue_source_ids"], expected_catalogue_sources)
            expected_reader_sources = sorted({
                source_id for record in [*entry["canon_linked_readers"], *entry["research_reader_candidates"]]
                for source_id in record.get("source_ids", [])
            })
            expected_lead_sources = sorted({
                source_id for lead in entry["unbundled_leads"] for source_id in lead.get("source_ids", [])
            })
            self.assertEqual(entry["reader_source_ids"], expected_reader_sources)
            self.assertEqual(entry["lead_source_ids"], expected_lead_sources)
            all_groups = set(expected_catalogue_sources + entry["canon_entry_source_ids"] + expected_reader_sources + expected_lead_sources)
            self.assertEqual(entry["related_source_ids"], sorted(all_groups))
            for reader in [*entry["canon_linked_readers"], *entry["research_reader_candidates"]]:
                self.assertTrue((ROOT / reader["reader_data_url"]).is_file())

    def test_generated_file_schema_and_site_links_match_builder(self):
        saved = json.loads((ROOT / "book-coverage.json").read_text(encoding="utf-8"))
        self.assertEqual(saved, self.coverage)
        schema = json.loads((ROOT / "schemas/book-coverage.schema.json").read_text(encoding="utf-8"))
        self.assertIn("supplemental_research_views", schema["properties"]["entries"]["items"]["required"])
        self.assertEqual(schema["properties"]["entries"]["items"]["properties"]["reader_availability"]["enum"], [
            "canon_linked_reader", "reviewed_title_match_research_reader_only",
            "source_asserted_research_reader_only", "research_candidate_reader_only", "no_bundled_reader",
        ])
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn('href="book-coverage.json" download', html)
        self.assertIn('href="schemas/book-coverage.schema.json"', html)
        app = (ROOT / "app.js").read_text(encoding="utf-8")
        self.assertIn("const supplementalViews = state.sources", app)
        self.assertIn("(not a reader)", app)
        service_worker = (ROOT / "sw.js").read_text(encoding="utf-8")
        self.assertIn("'schemas/book-coverage.schema.json'", service_worker)
        self.assertIn("if (relativePath)", service_worker)


if __name__ == "__main__":
    unittest.main()
