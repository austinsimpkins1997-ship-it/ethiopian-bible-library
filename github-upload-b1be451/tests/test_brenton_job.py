import hashlib
import json
import unittest
import zipfile
from pathlib import Path

from build_brenton_job import parse_job_member


ROOT = Path(__file__).resolve().parents[1]
MEMBER = "19-JOBeng-Brenton.usfm"


class BrentonJobTests(unittest.TestCase):
    def test_reader_matches_the_pinned_member_and_manifest(self):
        package = ROOT / "readers" / "source" / "brenton-septuagint" / "eng-Brenton_usfm.zip"
        manifest_path = ROOT / "readers" / "source" / "brenton-septuagint" / "capture-manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        package_bytes = package.read_bytes()
        package_hash = hashlib.sha256(package_bytes).hexdigest()
        self.assertEqual(package_hash, manifest["archive_sha256"])
        self.assertIn(MEMBER, manifest["selected_members"])
        with zipfile.ZipFile(package) as archive:
            raw = archive.read(MEMBER)
        member = manifest["selected_members"][MEMBER]
        self.assertEqual((len(raw), hashlib.sha256(raw).hexdigest()), (member["byte_length"], member["sha256"]))

        expected = parse_job_member(raw, package_hash)
        reader = json.loads((ROOT / "readers" / "job-brenton-lxx-1851.json").read_text(encoding="utf-8"))
        self.assertEqual((reader["chapter_count"], reader["unit_count"]), (42, 1082))
        self.assertEqual(reader["source_member_sha256"], member["sha256"])
        self.assertEqual(reader["chapters"], expected["chapters"])
        self.assertEqual(sum(len(chapter["verses"]) for chapter in reader["chapters"]), 1082)
        self.assertEqual(sum(len(verse.get("continuations", [])) for chapter in reader["chapters"] for verse in chapter["verses"]), 2)
        self.assertNotIn("canon_id", reader)
        self.assertEqual(reader["translation_path"], ["grc", "en"])

        portable = json.loads((ROOT / "examples" / "portable-text-layers.json").read_text(encoding="utf-8"))
        self.assertEqual(len(portable["records"]), 24)
        layer = next(item for item in portable["records"] if item["record_id"].endswith("/layer/job-english-brenton-lxx-1851"))
        self.assertEqual(layer["coverage"]["unit_count"], 1082)
        self.assertEqual(layer["content_package"]["json_pointer"], "")
        self.assertEqual(layer["tradition_assertions"][0]["mapping_state"], "uncertain")
        archive = json.loads((ROOT / "archive.json").read_text(encoding="utf-8"))
        page_source = next(item for item in archive["sources"] if item["source_id"] == "SRC-146")
        self.assertEqual(page_source["url"], "https://ebible.org/eng-Brenton/JOB.htm")


if __name__ == "__main__":
    unittest.main()
