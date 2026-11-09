import tempfile
import unittest
from pathlib import Path

from archive_manifest import verify_manifest, write_manifest


class CopyVerificationTests(unittest.TestCase):
    def test_copy_verification_allows_unrelated_destination_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "index.html").write_text("site", encoding="utf-8")
            write_manifest(root)
            (root / "repository-notes.txt").write_text("keep me", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "Manifest file inventory differs"):
                verify_manifest(root)

            self.assertEqual(verify_manifest(root, allow_extra_files=True), 1)

    def test_copy_verification_still_checks_hashes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "index.html").write_text("site", encoding="utf-8")
            write_manifest(root)
            (root / "index.html").write_text("changed", encoding="utf-8")
            (root / "repository-notes.txt").write_text("keep me", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "Checksum or size mismatch"):
                verify_manifest(root, allow_extra_files=True)


if __name__ == "__main__":
    unittest.main()
