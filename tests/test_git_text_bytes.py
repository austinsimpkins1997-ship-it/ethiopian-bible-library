"""Prevent a Windows-only manifest from reaching Linux CI."""
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from archive_manifest import check_git_text_bytes, write_manifest


@unittest.skipUnless(shutil.which("git"), "Git unavailable")
class GitTextBytesTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.git("init")
        self.git("config", "core.autocrlf", "false")
        self.git("config", "core.safecrlf", "false")
        (self.root / ".gitattributes").write_bytes(
            b"* text=auto eol=lf\nreaders/source/** -text\n"
        )

    def git(self, *args):
        return subprocess.run(["git", "-C", str(self.root), *args], check=True,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def track(self, name, data):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        self.git("add", "--", name)
        return path

    def test_crlf_changelog_rejected_before_manifest_is_replaced(self):
        path = self.track("CHANGELOG.md", b"one\r\ntwo\r\n")
        manifest = self.root / "archive-manifest.json"
        manifest.write_bytes(b"previous manifest")
        with self.assertRaisesRegex(ValueError, "CHANGELOG.md"):
            write_manifest(self.root)
        self.assertEqual(manifest.read_bytes(), b"previous manifest")
        self.assertEqual(path.read_bytes(), b"one\r\ntwo\r\n")

    def test_lf_text_and_byte_preserved_sources_pass(self):
        self.track("CHANGELOG.md", b"one\ntwo\n")
        source = self.track("readers/source/capture.html", b"raw\r\nsource\r\n")
        check_git_text_bytes(self.root)
        self.assertEqual(source.read_bytes(), b"raw\r\nsource\r\n")

    def test_new_untracked_text_is_checked_before_first_commit(self):
        self.git("add", ".gitattributes")
        (self.root / "new-notes.md").write_bytes(b"new\r\n")
        with self.assertRaisesRegex(ValueError, "new-notes.md"):
            check_git_text_bytes(self.root)

    def test_auto_binary_bytes_are_preserved(self):
        self.track("capture.dat", b"\0binary\r\n")
        check_git_text_bytes(self.root)

    def test_lf_repair_passes_without_changing_source_bytes(self):
        text = self.track("notes.md", b"notes\r\n")
        self.track("readers/source/raw.txt", b"retain\r\n")
        with self.assertRaises(ValueError):
            check_git_text_bytes(self.root)
        text.write_bytes(b"notes\n")
        check_git_text_bytes(self.root)

    def test_download_without_git_metadata_is_supported(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "notes.md").write_bytes(b"local\r\n")
            self.assertEqual(len(write_manifest(root)["files"]), 1)


if __name__ == "__main__":
    unittest.main()
