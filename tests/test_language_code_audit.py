"""The archive's language identifiers must resolve offline against its retained IANA snapshot."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from language_code_audit import (
    SNAPSHOT_RELATIVE_PATH,
    parse_iana_language_subtags,
    validate_iana_special_script_audit,
    validate_language_subtag_audit,
)


ROOT = Path(__file__).resolve().parents[1]


class LanguageCodeAuditTests(unittest.TestCase):
    def test_archive_language_tags_resolve_in_bundled_iana_snapshot(self):
        audit = json.loads((ROOT / "language-script-code-audit.json").read_text(encoding="utf-8"))
        archive = json.loads((ROOT / "archive.json").read_text(encoding="utf-8"))
        language_registry = json.loads((ROOT / "translation-registry.json").read_text(encoding="utf-8"))
        source = next(item for item in archive["sources"] if item["source_id"] == "SRC-077")

        file_date, entries = parse_iana_language_subtags(ROOT / SNAPSHOT_RELATIVE_PATH)
        self.assertEqual(file_date, audit["language_subtags"]["registry_file_date"])
        registered = validate_language_subtag_audit(audit, language_registry, ROOT, source)
        validate_iana_special_script_audit(audit, ROOT, source)
        self.assertEqual(registered, {code.lower() for code in audit["language_subtags"]["codes"]})
        self.assertIn("gez", registered)
        self.assertIn("gmv", registered)
        self.assertEqual(
            {record["Type"] for record in entries["arb"]},
            {"language", "extlang"},
        )
        self.assertEqual(
            {record["Type"] for record in entries["zzzz"]},
            {"script"},
        )
        self.assertEqual(source["local_metadata_url"], SNAPSHOT_RELATIVE_PATH.as_posix())

    def test_authority_snapshot_hash_is_verified(self):
        audit = json.loads((ROOT / "language-script-code-audit.json").read_text(encoding="utf-8"))
        archive = json.loads((ROOT / "archive.json").read_text(encoding="utf-8"))
        language_registry = json.loads((ROOT / "translation-registry.json").read_text(encoding="utf-8"))
        source = next(item for item in archive["sources"] if item["source_id"] == "SRC-077")
        audit["language_subtags"]["snapshot_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "snapshot SHA-256 mismatch"):
            validate_language_subtag_audit(audit, language_registry, ROOT, source)


if __name__ == "__main__":
    unittest.main()
