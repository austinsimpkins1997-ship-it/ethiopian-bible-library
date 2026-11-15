"""Run the complete archive suite with identical generated-file bytes on all OSes."""
import unittest
import sys

from archive_manifest import enable_atomic_path_writes


if __name__ == "__main__":
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    enable_atomic_path_writes()
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.discover("tests"))
    raise SystemExit(not result.wasSuccessful())
