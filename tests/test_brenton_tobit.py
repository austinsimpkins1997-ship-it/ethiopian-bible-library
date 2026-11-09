import hashlib
import json
import unittest
import zipfile
from pathlib import Path

from build_brenton_tobit import parse_tobit_member


ROOT = Path(__file__).resolve().parents[1]
MEMBER = "41-TOBeng-Brenton.usfm"


class BrentonTobitTests(unittest.TestCase):
    def test_reader_matches_the_pinned_member_and_keeps_its_scope_separate(self):
        source_dir = ROOT / "readers" / "source" / "brenton-septuagint"
        package = source_dir / "eng-Brenton_usfm.zip"
        manifest = json.loads((source_dir / "capture-manifest.json").read_text(encoding="utf-8"))
        package_bytes = package.read_bytes()
        package_hash = hashlib.sha256(package_bytes).hexdigest()
        self.assertEqual(package_hash, manifest["archive_sha256"])
        self.assertIn(MEMBER, manifest["selected_members"])
        with zipfile.ZipFile(package) as archive:
            raw = archive.read(MEMBER)
        member = manifest["selected_members"][MEMBER]
        self.assertEqual((len(raw), hashlib.sha256(raw).hexdigest()), (member["byte_length"], member["sha256"]))

        expected = parse_tobit_member(raw, package_hash)
        reader = json.loads((ROOT / "readers" / "tobit-brenton-lxx-1851.json").read_text(encoding="utf-8"))
        self.assertEqual((reader["chapter_count"], reader["unit_count"]), (14, 245))
        self.assertEqual(reader["source_member_sha256"], member["sha256"])
        self.assertEqual(reader["chapters"], expected["chapters"])
        self.assertEqual(sum(len(chapter["verses"]) for chapter in reader["chapters"]), 245)
        self.assertEqual(sum(len(verse.get("continuations", [])) for chapter in reader["chapters"] for verse in chapter["verses"]), 2)
        self.assertNotIn("canon_id", reader)
        self.assertEqual(reader["translation_path"], ["grc", "en"])
        self.assertEqual(reader["translation_basis_status"], "established")
        self.assertIn("edition-stated Greek-to-English basis", reader["translation_basis_note"])
        portable = json.loads((ROOT / "examples" / "portable-text-layers.json").read_text(encoding="utf-8"))
        tobit_layer = next(item for item in portable["records"] if item["record_id"].endswith("/layer/tobit-brenton-english-1851"))
        self.assertEqual(tobit_layer["coverage"]["unit_count"], 245)
        self.assertEqual(tobit_layer["content_package"]["json_pointer"], "")


if __name__ == "__main__":
    unittest.main()
