"""Regression checks for the retained Lingala USFM-to-reader conversion."""

from __future__ import annotations

import hashlib
import json
import re
import unittest
import zipfile
from pathlib import Path

from build_lin_research_readers import SOURCE, audit_verse_and_table_text
from build_maale_research_readers import BOOK_NAMES


ROOT = Path(__file__).resolve().parents[1]
AUDIT_PATH = ROOT / "research" / "lin-verse-fidelity-audit.json"


class LingalaResearchReaderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.audit = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
        cls.readers = {
            path.stem.removeprefix("lin-2020-").removesuffix("-research").upper():
            json.loads(path.read_text(encoding="utf-8"))
            for path in ROOT.glob("readers/lin-2020-*-research.json")
        }

    def test_retained_source_and_persisted_readers_reproduce_fidelity_audit(self):
        self.assertEqual(self.audit["source_archive_sha256"], hashlib.sha256(SOURCE.read_bytes()).hexdigest())
        self.assertEqual(set(self.readers), set(BOOK_NAMES))
        verse_total = table_row_total = 0

        with zipfile.ZipFile(SOURCE) as package:
            self.assertIsNone(package.testzip())
            members = {
                match.group(1): (name, package.read(name))
                for name in package.namelist()
                if name.lower().endswith(".usfm")
                for match in [re.search(r"^\\id[ \t]+([A-Z0-9]{3})\b", package.read(name).decode("utf-8-sig"), re.M)]
                if match
            }

        self.assertEqual(set(members), set(BOOK_NAMES))
        for code in BOOK_NAMES:
            member_name, raw = members[code]
            result = audit_verse_and_table_text(raw, self.readers[code], member_name)
            verse_total += result["source_verse_lines"]
            table_row_total += result["source_table_rows"]
            self.assertEqual(result["verse_mismatches"], 0, code)
            self.assertEqual(result["table_row_mismatches"], 0, code)

            reader = self.readers[code]
            self.assertIsNone(reader["canon_id"], code)
            self.assertEqual(reader["language_tag"], "ln", code)
            self.assertEqual(reader["license_id"], "CC-BY-SA-4.0", code)
            self.assertEqual(reader["rights_classification"], "open_license", code)
            self.assertEqual(reader["translation_basis_status"], "unknown", code)

        self.assertEqual(verse_total, self.audit["source_verse_line_count"])
        self.assertEqual(verse_total, self.audit["matched_reader_verse_count"])
        self.assertEqual(table_row_total, self.audit["source_table_row_count"])
        self.assertEqual(table_row_total, self.audit["matched_reader_table_row_count"])

    def test_fidelity_report_keeps_its_scope_limits(self):
        limits = self.audit["scope_limitations"].lower()
        for limitation in (
            "does not establish notes/headings/front-matter/continuation fidelity",
            "translation accuracy",
            "community review",
            "canon equivalence",
        ):
            self.assertIn(limitation, limits)


if __name__ == "__main__":
    unittest.main()
