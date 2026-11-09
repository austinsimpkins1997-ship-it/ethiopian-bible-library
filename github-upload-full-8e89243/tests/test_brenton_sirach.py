import hashlib
import json
import unittest
import zipfile
from pathlib import Path

from build_brenton_sirach import MEMBER, READER_ID, parse_sirach_member
import build_brenton_octateuch as brenton

ROOT = Path(__file__).resolve().parents[1]


class BrentonSirachTests(unittest.TestCase):
    def test_reader_preserves_observed_boundaries_and_candidate_mapping(self):
        source_dir = ROOT / "readers" / "source" / "brenton-septuagint"
        package = source_dir / "eng-Brenton_usfm.zip"
        manifest = json.loads((source_dir / "capture-manifest.json").read_text(encoding="utf-8"))
        package_bytes = package.read_bytes()
        package_hash = hashlib.sha256(package_bytes).hexdigest()
        self.assertEqual(package_hash, manifest["archive_sha256"])
        with zipfile.ZipFile(package) as archive:
            raw = archive.read(MEMBER)
        member = manifest["selected_members"][MEMBER]
        self.assertEqual((len(raw), hashlib.sha256(raw).hexdigest()), (member["byte_length"], member["sha256"]))

        observed = parse_sirach_member(raw, package_hash)
        reader = json.loads((ROOT / "readers" / "sirach-brenton-lxx-1851.json").read_text(encoding="utf-8"))
        self.assertEqual((reader["reader_id"], reader["chapter_count"], reader["unit_count"]), (READER_ID, 51, 1368))
        self.assertEqual(reader["source_member_sha256"], member["sha256"])
        self.assertEqual(reader["chapters"], observed["chapters"])
        self.assertEqual(reader["chapters"][0]["heading"], ["⟦The Prologue to the Wisdom of⟧ Jesus ⟦the son of⟧ Sirach"])
        labels = [verse["number"] for verse in reader["chapters"][0]["verses"]]
        self.assertEqual(labels[:8], ["1", "1a", "1b", "1c", "1d", "1e", "1f", "1g"])
        self.assertEqual(labels[8], "1h")
        self.assertIn("b", reader["chapters"][0]["verses"][8]["source_markers_before"])
        self.assertEqual(sum(len(chapter["verses"]) for chapter in reader["chapters"]), 1368)
        self.assertEqual(sum(len(verse.get("continuations", [])) for chapter in reader["chapters"] for verse in chapter["verses"]), 1)
        self.assertNotIn("canon_id", reader)
        self.assertEqual(reader["translation_path"], ["grc", "en"])
        self.assertEqual(reader["research_corpus_id"], "brenton-sirach-lxx-1851")

        archive = json.loads((ROOT / "archive.json").read_text(encoding="utf-8"))
        entry = next(item for item in archive["catalogue"] if item["catalogue_id"] == "eotc-053")
        self.assertIn("title-level uncertain crosswalk", entry["reviewer_notes"])
        registry = json.loads((ROOT / "translation-registry.json").read_text(encoding="utf-8"))
        corpus = next(item for item in registry["research_corpora"] if item["corpus_id"] == "brenton-sirach-lxx-1851")
        self.assertEqual(corpus["canon_mapping_state"], "uncertain")
        self.assertEqual(corpus["candidate_canon_id"], "eotc-ot-45")
        self.assertIn("11 currently link to bundled source-text readers", registry["coverage_statement"])
        layer = next(item for item in registry["languages"] if item["language_tag"] == "en")["records"]
        layer = next(item for item in layer if item["reader_id"] == READER_ID)
        self.assertEqual(layer["layer_role"], "historical_companion_translation")

        portable = json.loads((ROOT / "examples" / "portable-text-layers.json").read_text(encoding="utf-8"))
        self.assertEqual(len(portable["records"]), 24)
        layer = next(item for item in portable["records"] if item["record_id"].endswith("/layer/sirach-english-brenton-lxx-1851"))
        self.assertEqual(layer["coverage"]["unit_count"], 1368)
        self.assertEqual(layer["content_package"]["json_pointer"], "")
        self.assertEqual(layer["tradition_assertions"][0]["mapping_state"], "uncertain")

    def test_shared_parser_retains_source_headings_and_break_markers(self):
        self.assertIn("mt2", brenton.NONVERSE_MARKERS)
        self.assertIn("b", brenton.NONVERSE_MARKERS)


if __name__ == "__main__":
    unittest.main()
