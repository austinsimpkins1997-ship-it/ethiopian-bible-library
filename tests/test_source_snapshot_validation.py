import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from build_standalone import validate_local_source_snapshots


class LocalSourceSnapshotValidationTests(unittest.TestCase):
    def make_package(self, root: Path, *, include_manifest: bool = True):
        snapshot = root / "readers" / "capture" / "source.html"
        snapshot.parent.mkdir(parents=True)
        content = b"<p>captured source bytes</p>\x80"
        snapshot.write_bytes(content)
        digest = hashlib.sha256(content).hexdigest()
        source = {
            "source_id": "SRC-999",
            "local_snapshot_path": "readers/capture/source.html",
            "local_snapshot_sha256": digest,
            "local_snapshot_status": "byte-exact captured metadata; not scripture text",
            "local_snapshot_note": "Captured from an identified source URL; exact bytes retained.",
        }
        if include_manifest:
            manifest = snapshot.parent / "capture.json"
            manifest.write_text(json.dumps({"files": [{
                "path": "source.html",
                "size_bytes": len(content),
                "sha256": digest,
            }]}), encoding="utf-8")
            source["local_capture_manifest_url"] = "readers/capture/capture.json"
        return source, snapshot, digest

    def test_snapshot_hash_and_manifest_link_are_verified(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, _, _ = self.make_package(root)
            with patch("build_standalone.ROOT", root):
                validate_local_source_snapshots([source])

    def test_changed_snapshot_bytes_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, snapshot, _ = self.make_package(root)
            snapshot.write_bytes(b"modified")
            with patch("build_standalone.ROOT", root):
                with self.assertRaisesRegex(ValueError, "local snapshot hash mismatch"):
                    validate_local_source_snapshots([source])

    def test_capture_manifest_must_match_exact_snapshot_hash_and_size(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, _, _ = self.make_package(root)
            manifest = root / source["local_capture_manifest_url"]
            data = json.loads(manifest.read_text(encoding="utf-8"))
            data["files"][0]["sha256"] = "0" * 64
            manifest.write_text(json.dumps(data), encoding="utf-8")
            with patch("build_standalone.ROOT", root):
                with self.assertRaisesRegex(ValueError, "does not authenticate retained bytes"):
                    validate_local_source_snapshots([source])

    def test_traversal_path_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, _, _ = self.make_package(root, include_manifest=False)
            source["local_snapshot_path"] = "../outside.html"
            with patch("build_standalone.ROOT", root):
                with self.assertRaisesRegex(ValueError, "safe package-relative path"):
                    validate_local_source_snapshots([source])

    def test_existing_snapshot_without_manifest_is_supported(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, _, _ = self.make_package(root, include_manifest=False)
            with patch("build_standalone.ROOT", root):
                validate_local_source_snapshots([source])

    def test_partial_snapshot_provenance_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, _, _ = self.make_package(root)
            source.pop("local_snapshot_note")
            with patch("build_standalone.ROOT", root):
                with self.assertRaisesRegex(ValueError, "incomplete source snapshot provenance"):
                    validate_local_source_snapshots([source])


if __name__ == "__main__":
    unittest.main()
