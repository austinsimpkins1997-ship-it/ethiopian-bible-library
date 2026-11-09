import hashlib
import json
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class GazResearchReaderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.archive = json.loads((ROOT / "archive.json").read_text(encoding="utf-8"))
        cls.registry = cls.archive["translation_registry"]
        cls.readers = [reader for reader in cls.archive["readers"] if reader.get("language_tag") == "gaz"]
        cls.corpora = [corpus for corpus in cls.registry["research_corpora"] if corpus.get("language_tag") == "gaz"]

    def test_all_66_package_members_remain_research_only_with_scoped_nt_title_candidates(self):
        self.assertEqual(len(self.readers), 66)
        self.assertEqual(len(self.corpora), 66)
        self.assertTrue(all(reader.get("canon_id") is None for reader in self.readers))
        candidates = [corpus for corpus in self.corpora if corpus.get("candidate_canon_id")]
        nt_candidates = [corpus for corpus in candidates if corpus["candidate_canon_id"].startswith("eotc-nt-")]
        ot_candidates = [corpus for corpus in candidates if corpus["candidate_canon_id"].startswith("eotc-ot-")]
        self.assertEqual(len(nt_candidates), 27)
        self.assertEqual({corpus["candidate_canon_id"] for corpus in nt_candidates},
                         {f"eotc-nt-{number:02d}" for number in range(1, 28)})
        self.assertTrue(all(corpus["canon_mapping_state"] == "uncertain" for corpus in nt_candidates))
        self.assertEqual(len(ot_candidates), 38)
        gaz_job = next(corpus for corpus in ot_candidates if corpus["corpus_id"] == "gazbib-2022-job")
        self.assertEqual(gaz_job["canon_mapping_state"], "reviewed_match")
        self.assertIn("SRC-396", gaz_job["source_ids"])
        for code in ("1ch", "2ch"):
            chronicles = next(corpus for corpus in ot_candidates if corpus["corpus_id"] == f"gazbib-2022-{code}")
            self.assertEqual(chronicles["canon_mapping_state"], "reviewed_match")
        self.assertTrue(all(
            corpus["canon_mapping_state"] == "uncertain"
            for corpus in ot_candidates if corpus["corpus_id"] not in {"gazbib-2022-job", "gazbib-2022-1ch", "gazbib-2022-2ch"}
        ))
        self.assertTrue(all({"SRC-029", "SRC-384"}.issubset(set(corpus["source_ids"])) for corpus in ot_candidates))
        self.assertTrue(all(
            corpus["canon_mapping_state"] == "not_mapped" and corpus["candidate_canon_id"] is None
            for corpus in self.corpora if corpus not in candidates
        ))
        self.assertEqual(sum(reader["chapter_count"] for reader in self.readers), 1189)
        self.assertEqual(sum(reader["unit_count"] for reader in self.readers), 31102)

    def test_source_license_attribution_and_original_package_are_visible(self):
        source = next(item for item in self.archive["sources"] if item["source_id"] == "SRC-388")
        self.assertEqual(source["local_source_package_url"], "readers/source/gaz/gaz_usfm.zip")
        self.assertEqual(source["license_id"] if "license_id" in source else "CC-BY-SA-4.0", "CC-BY-SA-4.0")
        reader = next(reader for reader in self.readers if reader["reader_id"] == "gaz-gen-research")
        self.assertEqual(reader["rights_classification"], "open_license")
        self.assertIn("www.biblica.com and open.bible", reader["copyright_notice"])
        self.assertIn("Biblica® mark is removed", reader["copyright_notice"])
        self.assertIn("gaz_usfm.zip::02-GENgaz.usfm", reader["source_pages"])

    def test_every_reader_member_hash_matches_retained_signed_list(self):
        manifest = json.loads((ROOT / "research/gaz-usfm-source-manifest.json").read_text(encoding="utf-8"))
        package = ROOT / "readers/source/gaz/gaz_usfm.zip"
        self.assertEqual(hashlib.sha256(package.read_bytes()).hexdigest(), manifest["archive_sha256"])
        with zipfile.ZipFile(package) as archive:
            self.assertIsNone(archive.testzip())
            signed = archive.read("signature.txt.asc").decode("utf-8")
            declared = {row[1]: row[0] for row in (line.split() for line in signed.splitlines()) if len(row) == 2 and len(row[0]) == 64}
            members = [name for name in archive.namelist() if name.endswith(".usfm")]
            self.assertEqual(len(members), 66)
            self.assertTrue(all(hashlib.sha256(archive.read(name)).hexdigest() == declared[name] for name in members))
        self.assertEqual(manifest["signature"]["signer_fingerprint"], "54D714D76956DA6673DC1EEA5F62009D93505F26")

    def test_language_survey_and_local_package_download_are_scoped(self):
        gaz = next(language for language in self.registry["languages"] if language["language_tag"] == "gaz")
        self.assertEqual(gaz["availability_survey"]["result_count"], 4)
        self.assertIn("not four proven unique translations", gaz["availability_survey"]["scope"])
        app = (ROOT / "app.js").read_text(encoding="utf-8")
        service_worker = (ROOT / "sw.js").read_text(encoding="utf-8")
        self.assertIn("Download archived source package", app)
        self.assertIn("Every successful same-origin file under this static site", service_worker)
        self.assertIn("if (relativePath)", service_worker)


if __name__ == "__main__":
    unittest.main()
