import hashlib
import json
import re
import unittest
from copy import deepcopy
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit
import xml.etree.ElementTree as ET
from build_standalone import validate_source_record_metadata

ROOT = Path(__file__).resolve().parents[1]


class OfflineBundleTests(unittest.TestCase):
    def test_static_app_shell_does_not_load_runtime_assets_from_external_hosts(self):
        class RuntimeResourceParser(HTMLParser):
            def __init__(self):
                super().__init__()
                self.resources = []

            def handle_starttag(self, tag, attrs):
                attrs = dict(attrs)
                if tag == "script" and attrs.get("src"):
                    self.resources.append((tag, attrs["src"]))
                elif tag == "link" and attrs.get("href"):
                    self.resources.append((tag, attrs["href"]))

        parser = RuntimeResourceParser()
        parser.feed((ROOT / "index.html").read_text(encoding="utf-8"))
        self.assertTrue(parser.resources)
        external = [
            (tag, url) for tag, url in parser.resources
            if url.startswith("//") or urlsplit(url).scheme in {"http", "https"}
        ]
        self.assertEqual(external, [])
        styles = (ROOT / "styles.css").read_text(encoding="utf-8")
        self.assertNotRegex(styles, r"(?i)@import\s+[^;]*(?:https?:)?//")
        self.assertNotRegex(styles, r"(?i)url\(\s*['\"]?(?:https?:)?//")

    def test_mobile_first_install_does_not_precache_redundant_metadata_exports(self):
        service_worker = (ROOT / "sw.js").read_text(encoding="utf-8")
        precache_match = re.search(r"const PRECACHE_PATHS = \[(.*?)\];", service_worker, re.DOTALL)
        self.assertIsNotNone(precache_match)
        precache = set(re.findall(r"'([^']+)'", precache_match.group(1)))
        redundant_exports = {
            "examples/portable-text-layers.json",
            "translation-registry.json",
            "book-coverage.json",
        }
        self.assertFalse(redundant_exports & precache)
        self.assertIn("if (relativePath)", service_worker)
        self.assertIn("await cache.put(request, response.clone())", service_worker)

        manifest = json.loads((ROOT / "archive-manifest.json").read_text(encoding="utf-8"))
        sizes = {item["path"]: item["size_bytes"] for item in manifest["files"]}
        # The self-checksum manifest is intentionally excluded from its own
        # inventory, so account for its installed size from disk.
        sizes["archive-manifest.json"] = (ROOT / "archive-manifest.json").stat().st_size
        precache_bytes = sum(sizes[path] for path in precache)
        self.assertLessEqual(precache_bytes, 10 * 1024 * 1024)

    def test_every_local_source_url_field_is_validated(self):
        archive = json.loads((ROOT / "archive.json").read_text(encoding="utf-8"))
        source_by_id = {item["source_id"]: item for item in archive["sources"]}
        validate_source_record_metadata(archive["sources"])

        for source_id, field in (
            ("SRC-376", "local_heading_audit_url"),
            ("SRC-414", "local_rights_copy_url"),
        ):
            invalid = deepcopy(source_by_id[source_id])
            invalid[field] = "research/missing-local-source-file.json"
            with self.subTest(source_id=source_id, field=field):
                with self.assertRaisesRegex(ValueError, field):
                    validate_source_record_metadata([invalid])

    def test_optional_bulk_reader_cache_is_cancellable_sized_and_precached(self):
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        app = (ROOT / "app.js").read_text(encoding="utf-8")
        service_worker = (ROOT / "sw.js").read_text(encoding="utf-8")
        self.assertIn('id="save-all-readers"', html)
        self.assertIn('id="cancel-save-all-readers"', html)
        self.assertIn('id="save-all-readers-progress"', html)
        self.assertIn('<script src="offline-reader-cache.js" defer></script>', html)
        self.assertIn("OfflineReaderCache.createPlan", app)
        self.assertIn("bulkReaderSaveController?.abort()", app)
        self.assertIn("X-Archive-Bulk-Cache", service_worker)
        self.assertIn("offline-reader-cache.js", service_worker)
        self.assertIn("isBulkReaderRequest", service_worker)
        embedded = json.loads(re.search(
            r'<script\s+id="archive-data"\s+type="application/json">(.*?)</script>', html, re.DOTALL
        ).group(1))
        manifest = json.loads((ROOT / "archive-manifest.json").read_text(encoding="utf-8"))
        sizes = {item["path"]: item["size_bytes"] for item in manifest["files"]}
        paths = [reader["reader_data_url"] for reader in embedded["readers"]]
        self.assertEqual(len(paths), len(set(paths)))
        self.assertTrue(all(path in sizes for path in paths))
        total_bytes = sum(sizes[path] for path in paths)
        self.assertGreater(total_bytes, 100 * 1024 * 1024)

    def test_index_embeds_metadata_and_every_reader_is_in_the_local_package(self):
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        matches = re.findall(r'<script\s+id="archive-data"\s+type="application/json">(.*?)</script>', html, re.DOTALL)
        self.assertEqual(len(matches), 1)
        embedded = json.loads(matches[0])
        archive = json.loads((ROOT / "archive.json").read_text(encoding="utf-8"))
        complete_embedded = deepcopy(embedded)
        full_readers = []
        reader_urls = set()
        for metadata in complete_embedded["readers"]:
            reader_url = metadata.pop("reader_data_url")
            self.assertRegex(reader_url, r"^readers/[a-z0-9-]+\.json$")
            self.assertNotIn("..", reader_url.split("/"))
            self.assertNotIn(reader_url, reader_urls)
            reader_urls.add(reader_url)
            self.assertNotIn("chapters", metadata)
            if metadata.get("parallel_translation"):
                self.assertNotIn("chapters", metadata["parallel_translation"])
            reader = json.loads((ROOT / reader_url).read_text(encoding="utf-8"))
            self.assertEqual(reader["reader_id"], metadata["reader_id"])
            for key, value in metadata.items():
                reader_value = reader.get(key)
                if key == "parallel_translation" and reader_value:
                    reader_value = deepcopy(reader_value)
                    reader_value.pop("chapters", None)
                self.assertEqual(reader_value, value, f"Metadata mismatch for {reader['reader_id']}: {key}")
            self.assertTrue(reader.get("chapters"))
            full_readers.append(reader)
        complete_embedded["readers"] = full_readers
        self.assertEqual(complete_embedded, archive)
        canon_count = sum(bool(reader.get("canon_id")) for reader in embedded["readers"])
        self.assertEqual(canon_count, embedded["canon_registry"]["reader_count"])
        research_count = len(embedded["translation_registry"]["research_corpora"])
        research_corpus_ids = {
            corpus["corpus_id"] for corpus in embedded["translation_registry"]["research_corpora"]
        }
        self.assertEqual(sum(bool(reader.get("research_corpus_id")) for reader in embedded["readers"]), research_count)
        for reader in full_readers:
            with self.subTest(reader=reader["reader_id"]):
                self.assertTrue(reader.get("chapters"))
                actual_units = 0
                for chapter in reader["chapters"]:
                    units = chapter.get("units", chapter.get("verses", []))
                    self.assertTrue(units)
                    for unit in units:
                        if unit.get("text"):
                            continue
                        self.assertIn(unit.get("source_text_state"), {"marker_only", "empty_source_element"})
                        self.assertTrue(any(note.get("verse") == unit.get("number") and note.get("text")
                                            for note in chapter.get("notes", [])))
                        if unit.get("source_text_state") == "empty_source_element":
                            self.assertIsNotNone(unit.get("source_marker"))
                    actual_units += len(units)
                self.assertEqual(reader.get("unit_count"), actual_units)
                if reader.get("research_corpus_id"):
                    self.assertIsNone(reader.get("canon_id"))
                    self.assertIn(reader["research_corpus_id"], research_corpus_ids)
                companion = reader.get("parallel_translation")
                if companion:
                    companion_units = sum(len(chapter.get("verses", [])) for chapter in companion["chapters"])
                    self.assertEqual(companion.get("unit_count"), companion_units)

    def test_reader_and_rights_documentation_matches_current_metadata(self):
        archive = json.loads((ROOT / "archive.json").read_text(encoding="utf-8"))
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        rights = (ROOT / "CONTENT-LICENSES.md").read_text(encoding="utf-8")
        canon_count = sum(bool(reader.get("canon_id")) for reader in archive["readers"])
        research_count = sum(bool(reader.get("research_corpus_id")) for reader in archive["readers"])
        language_count = len(archive["translation_registry"]["languages"])
        self.assertIn(f"| Canon-linked reader records | {canon_count} |", readme)
        self.assertIn(f"| Research-only reader records | {research_count} |", readme)
        self.assertIn(f"| Reader records total | {len(archive['readers'])} |", readme)
        self.assertIn("separately scoped research readers remain outside canon-linked coverage.", readme)
        self.assertIn("Every registered language profile has a bounded provider-page survey record", readme)
        self.assertIn("This snapshot documents all", readme)
        self.assertNotIn("The current package has 22", readme)
        plan = (ROOT / "GLOBAL-ARCHIVE-PLAN.md").read_text(encoding="utf-8")
        source_count = len(archive["sources"])
        catalogue_count = len(archive["catalogue"])
        self.assertIn(f"the local standalone build has {len(archive['readers'])} reader records ({canon_count} canon-linked and {research_count} research-only), {catalogue_count} catalogue entries, {source_count} source records", plan)
        self.assertIn(f"Current package inventory: {catalogue_count} catalogue rows, {source_count} source records", plan)
        package_inventory = json.loads((ROOT / "package-inventory.json").read_text(encoding="utf-8"))
        standard_nt = package_inventory["standard_nt_research"]
        standard_nt_ids = {
            book["canon_id"] for book in archive["canon_registry"]["books"]
            if book.get("section") == "New Testament"
        }
        standard_nt_ids = set(sorted(standard_nt_ids)[:27])
        standard_nt_corpora = [
            item for item in archive["translation_registry"]["research_corpora"]
            if item.get("reader_status") == "bundled_research_reader"
            and item.get("candidate_canon_id") in standard_nt_ids
        ]
        standard_nt_states = {}
        for item in standard_nt_corpora:
            state = item.get("canon_mapping_state", "unrecorded")
            standard_nt_states[state] = standard_nt_states.get(state, 0) + 1
        self.assertEqual(standard_nt["candidate_reader_record_count"], len(standard_nt_corpora))
        self.assertEqual(standard_nt["mapping_state_counts"], standard_nt_states)
        self.assertEqual(standard_nt["language_tag_count"], len({item["language_tag"] for item in standard_nt_corpora}))
        summary = (
            f"Across the {standard_nt['entry_count']} standard New Testament work titles, "
            f"{standard_nt['candidate_reader_record_count']} bundled research-reader records are indexed as work/title candidates "
            f"({standard_nt_states.get('reviewed_match', 0)} reviewed title matches, "
            f"{standard_nt_states.get('uncertain', 0)} provisional candidates, "
            f"{standard_nt['language_tag_count']} language tags)."
        )
        self.assertIn(summary, plan)
        self.assertNotIn("340 individual research-reader records", plan)
        self.assertIn("42 Beta maṣāḥǝft Works scripture records with unresolved mixed notices", rights)
        self.assertIn("scripture payloads from this source are withheld pending clarification", rights)
        self.assertNotIn("Language unresolved (`und`)", rights)
        self.assertIn("node tests/test_service_worker.js", readme)
        self.assertIn("node tests/test_offline_reader_cache.js", readme)
        self.assertIn("embeds catalogue, source, canon, and translation metadata for the current reader records", readme)
        self.assertNotIn("all 492 current reader records", readme)
        self.assertNotIn("492 corresponding reader packages", readme)
        self.assertIn("local source builders do not fetch source content over the network", readme)

    def test_portable_layer_counts_are_in_manifest_not_duplicated_in_prose(self):
        portable = json.loads((ROOT / "examples" / "portable-text-layers.json").read_text(encoding="utf-8"))
        records = portable["records"]
        source_count = sum(record.get("text_origin") == "source_transcription" for record in records)
        translation_count = sum(record.get("text_origin") == "published_translation" for record in records)
        readme = (ROOT / "README.md").read_text(encoding="utf-8")

        self.assertEqual(source_count + translation_count, len(records))
        self.assertIn(f"| Portable text layers | {len(records)} |", readme)
        self.assertIn("Selected layers; not complete canon or language coverage.", readme)
        self.assertIn(f"This manifest includes portable metadata for {len(records)} selected text layers", portable["coverage_statement"])

    def test_didascalia_manifest_is_offline_metadata_and_not_a_text_reader(self):
        archive = json.loads((ROOT / "archive.json").read_text(encoding="utf-8"))
        source = next(item for item in archive["sources"] if item["source_id"] == "SRC-346")
        capture_path = ROOT / "readers" / "source" / "didascalia-platt1834" / "capture-manifest.json"
        manifest_path = capture_path.with_name("iiif-manifest.json")
        capture = json.loads(capture_path.read_text(encoding="utf-8"))
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        canvases = manifest["sequences"][0]["canvases"]

        self.assertEqual(source["local_metadata_url"], "readers/source/didascalia-platt1834/capture-manifest.json")
        self.assertIn("source.local_metadata_url", (ROOT / "app.js").read_text(encoding="utf-8"))
        self.assertEqual(capture["sha256"], hashlib.sha256(manifest_path.read_bytes()).hexdigest())
        self.assertEqual(capture["byte_length"], manifest_path.stat().st_size)
        self.assertEqual(capture["manifest_rights_statement"], "https://rightsstatements.org/vocab/NoC-NC/1.0/")
        self.assertEqual((capture["declared_canvas_count"], len(canvases)), (178, 178))
        self.assertEqual((canvases[0]["label"], canvases[-1]["label"]), ("(0001)", "(0178)"))
        self.assertIn("no scan images, OCR, or transcription were downloaded", capture["capture_method"])
        self.assertNotIn("chapters", manifest)
        self.assertNotIn("verses", manifest)

    def test_tegsats_iiif_metadata_and_review_are_pre_cached_for_offline_use(self):
        archive = json.loads((ROOT / "archive.json").read_text(encoding="utf-8"))
        source = next(item for item in archive["sources"] if item["source_id"] == "SRC-385")
        self.assertEqual(source["local_metadata_url"], "readers/source/tegsats-bl-add-ms-16186/capture-manifest.json")
        self.assertEqual(source["local_review_url"], "research/tegsats-source-review.md")
        sw = (ROOT / "sw.js").read_text(encoding="utf-8")
        self.assertIn("readers/source/tegsats-bl-add-ms-16186/capture-manifest.json", sw)
        self.assertIn("readers/source/tegsats-bl-add-ms-16186/iiif-manifest.json", sw)
        self.assertIn("research/tegsats-source-review.md", sw)

    def test_didascalia_internet_archive_ocr_is_offline_research_data_not_reader_text(self):
        archive = json.loads((ROOT / "archive.json").read_text(encoding="utf-8"))
        source = next(item for item in archive["sources"] if item.get("local_ocr_url") == "readers/source/didascalia-platt1834/internet-archive-djvu.txt")
        base = ROOT / "readers" / "source" / "didascalia-platt1834"
        capture = json.loads((base / "internet-archive-capture-manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(source["local_ocr_url"], "readers/source/didascalia-platt1834/internet-archive-djvu.txt")
        self.assertEqual(source["local_metadata_url"], "readers/source/didascalia-platt1834/internet-archive-capture-manifest.json")
        self.assertIn("source.local_ocr_url", (ROOT / "app.js").read_text(encoding="utf-8"))
        self.assertEqual(source["rights_classification"], "public_domain_claimed")
        self.assertIn("US only", source["inspection_and_limitations"])
        self.assertIn("not reader text", source["archive_status"])
        self.assertEqual(capture["rights_classification"], "public_domain_claimed")
        self.assertIn("worldwide legal determination", capture["rights_scope"].casefold())
        self.assertEqual(capture["observed_limits"]["internet_archive_page_count"], 190)
        self.assertEqual(capture["observed_limits"]["xml_page_object_count"], 186)
        self.assertEqual(capture["observed_limits"]["ethiopic_unicode_codepoint_count"], 0)
        for item in capture["files"]:
            data = (base / item["path"]).read_bytes()
            self.assertEqual(len(data), item["byte_length"])
            self.assertEqual(hashlib.md5(data).hexdigest(), item["md5"])
            self.assertEqual(hashlib.sha1(data).hexdigest(), item["sha1"])
            self.assertEqual(hashlib.sha256(data).hexdigest(), item["sha256"])
        text = (base / "internet-archive-djvu.txt").read_text(encoding="utf-8")
        self.assertFalse(any("\u1200" <= char <= "\u137f" for char in text))
        xml_root = ET.parse(base / "internet-archive-djvu.xml").getroot()
        self.assertEqual(sum(1 for node in xml_root.iter() if node.tag.upper() == "OBJECT"), 186)
        canon = next(item for item in archive["canon_registry"]["books"] if item["canon_id"] == "eotc-nt-35")
        self.assertIsNone(canon["reader_id"])
        self.assertIn("no reader or canon-linked coverage added", source["archive_status"])
        sw = (ROOT / "sw.js").read_text(encoding="utf-8")
        self.assertRegex(sw, r"CACHE_NAME = `\$\{CACHE_PREFIX\}shell-v\d+`")
        self.assertIn("if (relativePath)", sw)

    def test_mark_candidate_is_metadata_only_pending_rights_clarification(self):
        archive = json.loads((ROOT / "archive.json").read_text(encoding="utf-8"))
        reader_id = "mark-betamasaheft-tei-research"
        self.assertFalse(any(item["reader_id"] == reader_id for item in archive["readers"]))
        withheld = next(item for item in archive["rights_withheld_texts"] if item["reader_id"] == reader_id)
        self.assertEqual((withheld["chapter_count"], withheld["unit_count"]), (16, 765))
        self.assertEqual(withheld["rights_classification"], "mixed")
        self.assertFalse(withheld["public_text_included"])
        self.assertFalse((ROOT / "readers/mark-research-tei.json").exists())
        self.assertFalse((ROOT / "readers/source/mark/LIT2711Mark-original.xml").exists())
        self.assertTrue((ROOT / "readers/source/mark/structure-audit.json").is_file())
        audit = json.loads((ROOT / "readers/source/mark/structure-audit.json").read_text(encoding="utf-8"))
        self.assertEqual(audit["language_context"]["chapter_divisions_in_scope"], 16)
        self.assertEqual(audit["language_context"]["line_elements_in_scope"], 765)
        portable = json.loads((ROOT / "examples/portable-text-layers.json").read_text(encoding="utf-8"))
        self.assertFalse(any(reader_id in item.get("record_id", "") for item in portable["records"]))
    def test_wisdom_ed2_reader_is_metadata_only_pending_rights_clarification(self):
        archive = json.loads((ROOT / "archive.json").read_text(encoding="utf-8"))
        reader_id = "wisdom-solomon-betamasaheft-tei-research"
        self.assertFalse(any(item["reader_id"] == reader_id for item in archive["readers"]))
        withheld = next(item for item in archive["rights_withheld_texts"] if item["reader_id"] == reader_id)
        self.assertFalse(withheld["public_text_included"])
        self.assertEqual(withheld["rights_classification"], "mixed")
        lead = next(item for item in archive["translation_registry"]["corpus_leads"] if item["corpus_id"] == "betamasaheft-wisdom-solomon-ed2-research")
        self.assertFalse(lead["text_bundled"])
        self.assertIn("withheld", lead["review_status"].lower())
        extract = ROOT / "readers/source/wisdom-of-solomon-LIT2516Wisdom-ed2-only.xml"
        self.assertFalse(extract.exists(), "Withheld TEI wording must not be web-accessible from the package tree.")
        manifest = json.loads((ROOT / "archive-manifest.json").read_text(encoding="utf-8"))
        self.assertNotIn("readers/source/wisdom-of-solomon-LIT2516Wisdom-ed2-only.xml", {item["path"] for item in manifest["files"]})
        from build_wisdom_solomon_research_reader import build as build_withheld_wisdom
        with self.assertRaisesRegex(RuntimeError, "Publication blocked"):
            build_withheld_wisdom()

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
        self.assertEqual(corpus["canon_mapping_state"], "reviewed_match")
        self.assertIn("Reviewed work/title match only", corpus["canon_mapping_note"])
        self.assertIn("excluded from canon-linked coverage", corpus["canon_mapping_note"])
        self.assertIn("not counted as an EOTC canon reader", reader["verification_status"])
        self.assertIn("SRC-143", reader["source_ids"])

    def test_mark_source_text_is_absent_from_public_manifest(self):
        manifest = json.loads((ROOT / "archive-manifest.json").read_text(encoding="utf-8"))
        paths = {item["path"] for item in manifest["files"]}
        self.assertNotIn("readers/mark-research-tei.json", paths)
        self.assertNotIn("readers/source/mark/LIT2711Mark-original.xml", paths)
        self.assertNotIn("examples/mark-research-tei-layer.json", paths)
        self.assertIn("readers/source/mark/structure-audit.json", paths)
    def test_service_worker_caches_the_offline_page_and_fallback(self):
        service_worker = (ROOT / "sw.js").read_text(encoding="utf-8")
        self.assertIn("'index.html'", service_worker)
        self.assertIn("'reader-package.js'", service_worker)
        self.assertIn("'schemas/source-record.schema.json'", service_worker)
        self.assertIn("'schemas/reader-package.schema.json'", service_worker)
        self.assertIn("'offline.html'", service_worker)
        self.assertIn("await cache.addAll(smallShellFiles)", service_worker)
        self.assertIn("const smallShellFiles = PRECACHE_FILES.filter(url => url !== INDEX_URL)", service_worker)
        self.assertIn("request.mode === 'navigate'", service_worker)
        self.assertIn("matchAcrossCaches(INDEX_URL)", service_worker)
        self.assertIn("matchAcrossCaches(OFFLINE_URL)", service_worker)
        self.assertIn("OFFLINE_READER_STATUS", service_worker)
        self.assertRegex(service_worker, r"const CACHE_NAME = `\$\{CACHE_PREFIX\}shell-v\d+`;")
        self.assertIn("schemas/eotc-canon-registry.schema.json", service_worker)
        self.assertIn("schemas/textual-lens.schema.json", service_worker)
        self.assertIn("research/genesis-1-divine-person-lens.json", service_worker)
        self.assertIn("/^readers\\/[a-z0-9-]+\\.json$/", service_worker)
        self.assertIn("if (relativePath)", service_worker)

    def test_reader_loads_only_selected_text_from_the_local_package(self):
        app = (ROOT / "app.js").read_text(encoding="utf-8")
        self.assertRegex(app, r"fetch\(path,\s*\{\s*credentials:\s*'same-origin'\s*\}\)")
        self.assertIn("readerMetadata.reader_data_url", app)
        self.assertIn("state.activeReaderData", app)
        self.assertIn("renderReader({ loadText: false })", app)
        self.assertIn("reader-open", app)
        self.assertNotRegex(app, r"\bXMLHttpRequest\b|\bWebSocket\b")
        self.assertIn("Related research readers · not counted as Church-list book coverage", app)
        self.assertIn("Open this research reader", app)
        self.assertIn("not counted as Church-list book coverage", app)
        self.assertIn("No canon-linked reader is bundled for this catalogue title", app)
        self.assertIn("source label absent", app)
        self.assertIn("Source notes and cross-references", app)
        self.assertIn("its source note is retained below", app)

    def test_source_builders_use_retained_inputs_without_network_fetches(self):
        source_files = sorted(
            path
            for pattern in ("build_*.py", "audit_*.py", "integrate_*.py")
            for path in ROOT.glob(pattern)
        )
        self.assertTrue(source_files)
        forbidden_network_calls = r"\b(?:urlopen|urlretrieve|requests\.(?:get|post|put)|httpx\.(?:get|post)|urllib\.request|curl|wget)\b"
        for path in source_files:
            with self.subTest(builder=path.name):
                self.assertNotRegex(path.read_text(encoding="utf-8"), forbidden_network_calls)

    def test_selected_reader_export_is_local_and_has_a_downloadable_schema(self):
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        app = (ROOT / "app.js").read_text(encoding="utf-8")
        schema = json.loads((ROOT / "schemas" / "reader-package.schema.json").read_text(encoding="utf-8"))
        self.assertIn('id="reader-download"', html)
        self.assertIn('href="schemas/reader-package.schema.json"', html)
        self.assertIn("window.ReaderPackage.createReaderPackage", app)
        self.assertIn("window.ReaderPackage.createReaderPackage", app)
        self.assertEqual(schema["$schema"], "https://json-schema.org/draft/2020-12/schema")


if __name__ == "__main__":
    unittest.main()
