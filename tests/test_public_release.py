"""Public exports must omit private captures and stale delivery copies."""
from pathlib import Path
import tempfile
import unittest

from archive_manifest import build_manifest, is_package_path
from build_upload_package import site_path


class PublicReleaseTests(unittest.TestCase):
    def test_private_and_legacy_paths_never_enter_public_manifest(self):
        for name in ("source-captures/private.zip", "github-upload-old/readers/text.json",
                     "github-docs-upload/index.html", "github-runtime-repair-old/archive.json",
                     "dist/site/index.html", "site/archive.json", "EthiopianBibleLibrary_GitHub_Upload.zip"):
            self.assertFalse(is_package_path(Path(name)), name)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "index.html").write_text("public", encoding="utf-8")
            (root / "source-captures").mkdir()
            (root / "source-captures/private.txt").write_text("private", encoding="utf-8")
            self.assertEqual([r["path"] for r in build_manifest(root)["files"]], ["index.html"])

    def test_site_keeps_evidence_and_readers_but_not_automation(self):
        for name in ("readers/source/brenton-septuagint/eng-Brenton_usfm.zip",
                     "research/review.html", "readers/ruth-geez.json", ".nojekyll"):
            self.assertTrue(site_path(Path(name)), name)
        for name in (".github/workflows/pages.yml", "tests/test_release.py", "build_release.py"):
            self.assertFalse(site_path(Path(name)), name)


if __name__ == "__main__":
    unittest.main()
