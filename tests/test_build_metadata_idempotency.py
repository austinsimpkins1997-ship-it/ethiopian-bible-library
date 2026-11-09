import json
import unittest
from pathlib import Path

from build_standalone import IANA_LINGALA_NOTE, ensure_appended_note_once
from build_teezaz_discovery import (
    ARCHIVE_STATUS_NOTE,
    COWLEY_TEEZAZ_NOTE,
    HORNER_EDITION_NOTE,
    ensure_appended_note_once as ensure_teezaz_note_once,
)
from build_daniel_reader import DANIEL_SOURCE_NOTE


ROOT = Path(__file__).resolve().parents[1]


class BuildMetadataIdempotencyTests(unittest.TestCase):
    def test_generated_source_note_is_added_once_even_after_repeated_builds(self):
        initial = "Base source evidence. " + IANA_LINGALA_NOTE + " " + IANA_LINGALA_NOTE
        normalized = ensure_appended_note_once(initial, IANA_LINGALA_NOTE)
        self.assertEqual(normalized.count(IANA_LINGALA_NOTE), 1)
        self.assertEqual(ensure_appended_note_once(normalized, IANA_LINGALA_NOTE), normalized)

    def test_teezaz_source_notes_are_normalized_idempotently(self):
        for note, separator in (
            (COWLEY_TEEZAZ_NOTE, " "),
            (ARCHIVE_STATUS_NOTE, "; "),
            (HORNER_EDITION_NOTE, " "),
            (DANIEL_SOURCE_NOTE.format(byte_count=1234, sha="a" * 64), " "),
        ):
            with self.subTest(note=note[:35]):
                initial = f"Base evidence.{separator}{note}{separator}{note}"
                normalized = ensure_teezaz_note_once(initial, note, separator)
                self.assertEqual(normalized.count(note), 1)
                self.assertEqual(
                    ensure_teezaz_note_once(normalized, note, separator), normalized
                )

    def test_teezaz_archive_notes_are_present_exactly_once(self):
        archive = json.loads((ROOT / "archive.json").read_text(encoding="utf-8"))
        source = next(item for item in archive["sources"] if item["source_id"] == "SRC-210")
        translation = json.loads((ROOT / "translation-registry.json").read_text(encoding="utf-8"))
        lead = next(
            item for item in translation["edition_leads"]
            if item["edition_id"] == "tau-horner-teezaz-image-edition-1904"
        )
        self.assertEqual(source["inspection_and_limitations"].count(COWLEY_TEEZAZ_NOTE), 1)
        self.assertEqual(source["archive_status"].count(ARCHIVE_STATUS_NOTE), 1)
        self.assertEqual(lead["edition_statement"].count(HORNER_EDITION_NOTE), 1)

    def test_daniel_source_note_is_present_exactly_once(self):
        archive = json.loads((ROOT / "archive.json").read_text(encoding="utf-8"))
        source = next(item for item in archive["sources"] if item["source_id"] == "SRC-282")
        self.assertIn("Scripture content from this cited file is withheld from the public bundle", source["inspection_and_limitations"])
        self.assertEqual(source["archive_status"], "Metadata citation retained; source scripture file withheld from this public bundle pending rights clarification.")

    def test_current_archive_and_graph_do_not_duplicate_generated_note(self):
        archive = json.loads((ROOT / "archive.json").read_text(encoding="utf-8"))
        source = next(item for item in archive["sources"] if item["source_id"] == "SRC-077")
        graph = json.loads((ROOT / "examples" / "archive-graph-registered-layers.json").read_text(encoding="utf-8"))
        claims = [
            claim
            for claim in graph.get("citations", [])
            if claim.get("source_id") == "SRC-077"
        ]
        self.assertEqual(source["inspection_and_limitations"].count(IANA_LINGALA_NOTE), 1)
        self.assertTrue(claims)
        self.assertTrue(all(claim["supports_claim"].count(IANA_LINGALA_NOTE) == 1 for claim in claims))


if __name__ == "__main__":
    unittest.main()
