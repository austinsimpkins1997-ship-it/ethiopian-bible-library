"""A later catalogue note must not make repeated rights builds grow the text."""
import json
from pathlib import Path
import unittest

from build_betamasaheft_license_audit import WITHHELD_MAPPING_NOTE, stable_withheld_mapping_note
from metadata_helpers import ensure_appended_note_once


class WithheldNoteRebuildTests(unittest.TestCase):
    def test_interleaved_notes_do_not_accumulate_whitespace(self):
        first, second = "First generated notice.", "Second generated notice."
        value = f"Evidence. {first} {second}"
        for _ in range(20):
            value = ensure_appended_note_once(value, first)
            value = ensure_appended_note_once(value, second)
            self.assertEqual(value, f"Evidence. {first} {second}")

    def test_plain_metadata_line_breaks_are_retained(self):
        self.assertEqual(ensure_appended_note_once("Evidence.\nMore evidence.  Notice.", "Notice."),
                         "Evidence.\nMore evidence. Notice.")

    def test_following_catalogue_note_survives_repeated_rebuilds(self):
        original = f"Evidence. {WITHHELD_MAPPING_NOTE} Standard research candidate."
        once = stable_withheld_mapping_note(original)
        for _ in range(20):
            self.assertEqual(stable_withheld_mapping_note(once), once)
        self.assertEqual(once.count(WITHHELD_MAPPING_NOTE), 1)
        self.assertIn("Standard research candidate.", once)

    def test_existing_duplicate_growth_is_repaired_without_losing_evidence(self):
        legacy = "Evidence. " + (WITHHELD_MAPPING_NOTE + "  ") * 100 + "Catalogue note."
        result = stable_withheld_mapping_note(legacy)
        self.assertEqual(result, f"Evidence. Catalogue note. {WITHHELD_MAPPING_NOTE}")

    def test_generated_canon_notes_have_at_most_one_rights_notice(self):
        root = Path(__file__).resolve().parents[1]
        canon = json.loads((root / "canon-registry.json").read_text(encoding="utf-8"))
        for book in canon["books"]:
            self.assertLessEqual(book.get("mapping_note", "").count(WITHHELD_MAPPING_NOTE), 1,
                                 book["canon_id"])


if __name__ == "__main__":
    unittest.main()
