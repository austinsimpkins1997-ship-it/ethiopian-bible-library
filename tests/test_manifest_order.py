"""A Windows-generated manifest must have the same order as a Linux rebuild."""

import tempfile
import unittest
from pathlib import Path, PurePosixPath, PureWindowsPath
from unittest.mock import patch

from archive_manifest import build_manifest


class ManifestOrderTests(unittest.TestCase):
    def test_mixed_case_paths_have_one_portable_order(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            names = ["alpha.txt", "Zebra.txt", "B/alpha.txt", "b-dir/Zeta.txt", "b-dir/éclair.txt"]
            for name in names:
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(b"retained source bytes\r\n")

            self.assertNotEqual(sorted(names, key=PureWindowsPath), sorted(names, key=PurePosixPath))
            expected = ["B/alpha.txt", "Zebra.txt", "alpha.txt", "b-dir/Zeta.txt", "b-dir/éclair.txt"]
            records = build_manifest(root)["files"]
            self.assertEqual([record["path"] for record in records], expected)
            self.assertTrue(all(record["size_bytes"] == len(b"retained source bytes\r\n") for record in records))

    def test_directory_enumeration_order_does_not_change_manifest(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            files = [root / name for name in ("Zebra.txt", "alpha.txt", "Beta.txt")]
            for path in files:
                path.write_bytes(path.name.encode("utf-8"))
            with patch.object(Path, "rglob", return_value=iter(files)):
                first = build_manifest(root)
            with patch.object(Path, "rglob", return_value=iter(reversed(files))):
                second = build_manifest(root)
            self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
