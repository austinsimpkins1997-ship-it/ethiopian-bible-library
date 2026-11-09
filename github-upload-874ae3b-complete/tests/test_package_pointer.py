import json
import unittest
from pathlib import Path

from package_pointer import resolve_json_pointer

ROOT = Path(__file__).resolve().parents[1]


class PackagePointerTests(unittest.TestCase):
    def test_nested_language_layers_select_the_exact_object(self):
        for name in ("exodus-brenton-translation-layer.json", "ruth-brenton-translation-layer.json"):
            record = json.loads((ROOT / "examples" / name).read_text(encoding="utf-8"))
            package = json.loads((ROOT / "examples" / record["content_package"]["uri"]).read_text(encoding="utf-8"))
            selected = resolve_json_pointer(package, record["content_package"]["json_pointer"], name)
            self.assertEqual(selected["language_tag"], record["language_tag"] )
            self.assertEqual(sum(len(ch["verses"]) for ch in selected["chapters"]), record["coverage"]["unit_count"])

    def test_pointer_escapes_follow_rfc6901(self):
        self.assertEqual(resolve_json_pointer({"a/b": {"x~y": 7}}, "/a~1b/x~0y"), 7)

    def test_missing_and_invalid_pointers_are_rejected(self):
        for pointer in ("not/a/pointer", "/missing", "/a~2b"):
            with self.subTest(pointer=pointer):
                with self.assertRaises(ValueError):
                    resolve_json_pointer({"a": 1}, pointer)


if __name__ == "__main__":
    unittest.main()
