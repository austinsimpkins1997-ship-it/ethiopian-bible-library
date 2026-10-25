import json
import re
import unittest
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]


class OfflineBundleTests(unittest.TestCase):
    def test_index_embeds_the_complete_local_archive_object(self):
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        matches = re.findall(r'<script\s+id="archive-data"\s+type="application/json">(.*?)</script>', html, re.DOTALL)
        self.assertEqual(len(matches), 1)
        embedded = json.loads(matches[0])
        archive = json.loads((ROOT / "archive.json").read_text(encoding="utf-8"))
        self.assertEqual(embedded, archive)
        self.assertEqual(sum(bool(reader.get("canon_id")) for reader in embedded["readers"]), 11)
        research_count = len(embedded["translation_registry"]["research_corpora"])
        self.assertEqual(sum(bool(reader.get("research_corpus_id")) for reader in embedded["readers"]), research_count)
        for reader in embedded["readers"]:
            with self.subTest(reader=reader["reader_id"]):
                self.assertTrue(reader.get("chapters"))
                actual_units = 0
                for chapter in reader["chapters"]:
                    units = chapter.get("units", chapter.get("verses", []))
                    self.assertTrue(units)
                    for unit in units:
                        if unit.get("text"):
                            continue
                        self.assertEqual(unit.get("source_text_state"), "marker_only")
                        self.assertTrue(any(note.get("verse") == unit.get("number") and note.get("text")
                                            for note in chapter.get("notes", [])))
                    actual_units += len(units)
                self.assertEqual(reader.get("unit_count"), actual_units)
                if reader.get("research_corpus_id"):
                    self.assertIsNone(reader.get("canon_id"))
                    self.assertIn("not counted as an EOTC canon reader", reader["verification_status"])
                companion = reader.get("parallel_translation")
                if companion:
                    companion_units = sum(len(chapter.get("verses", [])) for chapter in companion["chapters"])
                    self.assertEqual(companion.get("unit_count"), companion_units)

    def test_mark_research_reader_preserves_unlabeled_lines_without_canon_count(self):
        archive = json.loads((ROOT / "archive.json").read_text(encoding="utf-8"))
        reader = next(item for item in archive["readers"] if item["reader_id"] == "mark-betamasaheft-tei-research")
        corpus = next(item for item in archive["translation_registry"]["research_corpora"] if item["reader_id"] == reader["reader_id"])
        units = [unit for chapter in reader["chapters"] for unit in chapter["units"]]
        self.assertEqual((len(reader["chapters"]), len(units)), (16, 765))
        self.assertEqual(sum(unit["source_marker"] is not None for unit in units), 678)
        self.assertEqual(sum(unit["source_marker"] is None for unit in units), 87)
        self.assertEqual(reader["language_tag"], "und")
        self.assertEqual(reader["language_assignment_status"], "unknown_due_to_conflicting_source_metadata")
        self.assertEqual(reader["script_code"], "Ethi")
        self.assertEqual(reader["unit_count"], 765)
        self.assertIn("not verified scripture", reader["verification_status"].casefold())
        portable = json.loads((ROOT / "examples" / "portable-text-layers.json").read_text(encoding="utf-8"))
        layer = next(item for item in portable["records"] if item["record_id"].endswith("/layer/mark-betamasaheft-tei-research"))
        self.assertEqual((layer["language_tag"], layer["script_code"], layer["basis_path"]), ("und", "Ethi", None))
        self.assertEqual((layer["coverage"]["extent_state"], layer["coverage"]["unit_count"]), ("unknown", 765))
        self.assertIn("completeness of the intended printed work is unknown", layer["coverage"]["structure_description"])
        self.assertEqual(layer["text_origin"], "source_transcription")
        self.assertEqual(layer["publication_state"], "bundled")
        self.assertEqual(corpus["canon_mapping_state"], "uncertain")
        self.assertIsNone(reader.get("canon_id"))
        self.assertEqual(corpus["license_id"], "CC-BY-SA-4.0")
        self.assertEqual(corpus["license_url"], "https://creativecommons.org/licenses/by-sa/4.0/")
        self.assertEqual(archive["canon_registry"]["reader_count"], 11)
        self.assertIn(f"{len(archive['translation_registry']['research_corpora'])} separately scoped related research readers;", archive["translation_registry"]["coverage_statement"])
        self.assertIn("not linked to or counted as Church-list book coverage", archive["translation_registry"]["coverage_statement"])

    def test_brenton_job_is_a_separate_published_translation_research_reader(self):
        archive = json.loads((ROOT / "archive.json").read_text(encoding="utf-8"))
        reader = next(item for item in archive["readers"] if item["reader_id"] == "job-brenton-lxx-1851-research")
        corpus = next(item for item in archive["translation_registry"]["research_corpora"] if item["reader_id"] == reader["reader_id"])
        labels = [verse for chapter in reader["chapters"] for verse in chapter["verses"]]
        continuations = [segment for chapter in reader["chapters"] for verse in chapter["verses"] for segment in verse.get("continuations", [])]
        self.assertEqual((len(reader["chapters"]), len(labels), len(continuations)), (42, 1082, 2))
        self.assertEqual(reader["text_origin"], "published_translation")
        self.assertEqual((reader["basis_language_tag"], reader["language_tag"], reader["translation_path"]), ("grc", "en", ["grc", "en"]))
        self.assertIsNone(reader.get("canon_id"))
        self.assertEqual(corpus["canon_mapping_state"], "uncertain")
        self.assertIn("not counted as an EOTC canon reader", reader["verification_status"])
        self.assertIn("SRC-143", reader["source_ids"])

    def test_mark_research_view_matches_each_retained_tei_line_and_chapter_label(self):
        archive = json.loads((ROOT / "archive.json").read_text(encoding="utf-8"))
        reader = next(item for item in archive["readers"] if item["reader_id"] == "mark-betamasaheft-tei-research")
        source = ET.parse(ROOT / "readers" / "source" / "mark" / "LIT2711Mark-original.xml").getroot()
        ns = {"tei": "http://www.tei-c.org/ns/1.0"}
        body = source.find(".//tei:body", ns)
        divisions = body.findall(".//tei:div[@subtype='chapter']", ns)
        self.assertEqual(len(divisions), len(reader["chapters"]))
        for division, chapter in zip(divisions, reader["chapters"], strict=True):
            self.assertEqual(chapter["source_chapter_label"], division.get("n"))
            source_label = division.find("tei:label", ns)
            expected_heading = " ".join("".join(source_label.itertext()).split()) if source_label is not None else ""
            self.assertEqual(chapter.get("heading", []), [expected_heading] if expected_heading else [])
            source_lines = division.findall(".//tei:l", ns)
            self.assertEqual(len(source_lines), len(chapter["units"]))
            for original, extracted in zip(source_lines, chapter["units"], strict=True):
                expected_text = " ".join("".join(original.itertext()).split())
                self.assertEqual(extracted["text"], expected_text)
                self.assertEqual(extracted["source_marker"], original.get("n"))
                self.assertEqual(extracted["source_refs"], [node.get("target") for node in original.findall(".//tei:ref", ns) if node.get("target")])

    def test_service_worker_caches_the_offline_page_and_fallback(self):
        service_worker = (ROOT / "sw.js").read_text(encoding="utf-8")
        self.assertIn("'index.html'", service_worker)
        self.assertIn("'reader-package.js'", service_worker)
        self.assertIn("'schemas/reader-package.schema.json'", service_worker)
        self.assertIn("cache.addAll(APP_FILES)", service_worker)
        self.assertIn("cache.match(new URL('index.html', SITE_BASE).href)", service_worker)
        self.assertIn("request.mode === 'navigate'", service_worker)

    def test_reader_code_never_fetches_text_at_runtime(self):
        app = (ROOT / "app.js").read_text(encoding="utf-8")
        self.assertNotRegex(app, r"\bfetch\s*\(|\bXMLHttpRequest\b|\bWebSocket\b")
        self.assertIn("Related research texts · not canon coverage", app)
        self.assertIn("Open this research reader", app)
        self.assertIn("not counted as Church-list book coverage", app)
        self.assertIn("No canon-linked reader is bundled for this catalogue title", app)
        self.assertIn("source label absent", app)
        self.assertIn("Source notes and cross-references", app)
        self.assertIn("its source note is retained below", app)

    def test_selected_reader_export_is_local_and_has_a_downloadable_schema(self):
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        app = (ROOT / "app.js").read_text(encoding="utf-8")
        schema = json.loads((ROOT / "schemas" / "reader-package.schema.json").read_text(encoding="utf-8"))
        self.assertIn('id="reader-download"', html)
        self.assertIn('href="schemas/reader-package.schema.json"', html)
        self.assertIn("window.ReaderPackage.createReaderPackage", app)
        self.assertNotRegex(app, r"\bfetch\s*\(")
        self.assertEqual(schema["$schema"], "https://json-schema.org/draft/2020-12/schema")


if __name__ == "__main__":
    unittest.main()
