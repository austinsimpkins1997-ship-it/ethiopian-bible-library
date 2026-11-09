import hashlib
import json
import re
import unittest
from collections import Counter
from pathlib import Path

from build_standalone import validate_closed_schema_objects, validate_schema_constraints


ROOT = Path(__file__).resolve().parents[1]
LENS_PATH = ROOT / "research" / "genesis-1-divine-person-lens.json"
SCHEMA_PATH = ROOT / "schemas" / "textual-lens.schema.json"
NOTE_PATH = ROOT / "research" / "genesis-1-divine-person-lens.md"
GEʽEZ_STRING = "እግዚአብሔር"


def chapter_hash(chapter):
    text = "".join(f"{verse['number']}: {verse['text']}\n" for verse in chapter["verses"])
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class GenesisDivinePersonLensTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.archive = json.loads((ROOT / "archive.json").read_text(encoding="utf-8"))
        cls.lens = json.loads(LENS_PATH.read_text(encoding="utf-8"))
        cls.schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        cls.note = NOTE_PATH.read_text(encoding="utf-8")
        cls.app = (ROOT / "app.js").read_text(encoding="utf-8")
        cls.html = (ROOT / "index.html").read_text(encoding="utf-8")
        cls.service_worker = (ROOT / "sw.js").read_text(encoding="utf-8")
        readers = {item["reader_id"]: item for item in cls.archive["readers"]}
        cls.reader = readers["genesis-geez-dillmann-hacohen"]
        cls.english = cls.reader["parallel_translation"]
        cls.geez_chapter = next(chapter for chapter in cls.reader["chapters"] if chapter["chapter"] == 1)
        cls.english_chapter = next(chapter for chapter in cls.english["chapters"] if chapter["chapter"] == 1)

    def test_machine_lens_is_bound_to_named_local_witnesses(self):
        self.assertEqual(self.lens["record_id"], "genesis-1-divine-person-lens")
        self.assertEqual(self.lens["schema_version"], self.schema["properties"]["schema_version"]["const"])
        validate_closed_schema_objects(self.lens, self.schema, self.schema, "Genesis 1 lens record")
        validate_schema_constraints(self.lens, self.schema, self.schema, "Genesis 1 lens record")
        self.assertEqual(self.lens["scope"]["unit"], {"unit_type": "chapter", "chapter": 1})
        witnesses = {item["witness_id"]: item for item in self.lens["scope"]["witnesses"]}
        self.assertEqual(witnesses[self.reader["reader_id"]]["source_ids"], self.reader["source_ids"])
        self.assertEqual(witnesses[self.reader["reader_id"]]["language_tag"], self.reader["language_tag"])
        self.assertEqual(witnesses[self.english["translation_id"]]["source_ids"], self.english["source_ids"])
        self.assertEqual(witnesses[self.english["translation_id"]]["language_tag"], self.english["language_tag"])
        source_ids = {source["source_id"] for source in self.archive["sources"]}
        self.assertTrue(set(self.reader["source_ids"] + self.english["source_ids"]) <= source_ids)
        self.assertIn("not independently reviewed", self.lens["status"])

    def test_manual_speech_excerpts_are_exact_stored_english_and_reproduce_pronoun_counts(self):
        english_verses = {str(verse["number"]): verse["text"] for verse in self.english_chapter["verses"]}
        measurements = {item["measurement_id"]: item for item in self.lens["measurements"]}
        first_person = measurements["english-first-person-forms-in-attributed-divine-speech"]
        observed = Counter()
        for span in first_person["excerpts"]:
            self.assertIn(span["text"], english_verses[span["unit_label"]])
            observed.update(token.casefold() for token in re.findall(
                r"(?<![\w])(?:I|me|my|mine|we|us|our|ours)(?![\w])", span["text"], re.IGNORECASE
            ))
        token_breakdown = next(item for item in first_person["breakdowns"] if item["dimension"] == "token")
        self.assertEqual(dict(sorted(observed.items())), {item["value"]: item["count"] for item in token_breakdown["values"]})
        self.assertEqual(sum(observed.values()), first_person["count"])
        self.assertEqual(dict(sorted(observed.items())), {"i": 1, "our": 1, "us": 1})
        self.assertEqual(measurements["english-second-person-audience-reference-in-attributed-speech"]["count"], 2)

    def test_english_noun_and_geez_string_counts_match_chapter_and_fingerprints(self):
        measurements = {item["measurement_id"]: item for item in self.lens["measurements"]}
        english_verses = {str(verse["number"]): verse["text"] for verse in self.english_chapter["verses"]}
        english_counts = {
            label: len(re.findall(r"\bGod\b", text, re.IGNORECASE))
            for label, text in english_verses.items()
        }
        english_counts = {label: count for label, count in english_counts.items() if count}
        noun = measurements["english-explicit-noun-god"]
        noun_breakdown = next(item for item in noun["breakdowns"] if item["dimension"] == "verse")
        self.assertEqual(english_counts, {item["value"]: item["count"] for item in noun_breakdown["values"]})
        self.assertEqual(sum(english_counts.values()), 33)
        narrator = measurements["english-third-person-narrator-noun-god"]
        attributed_counts = Counter()
        first_person = measurements["english-first-person-forms-in-attributed-divine-speech"]
        for span in first_person["excerpts"]:
            attributed_counts[span["unit_label"]] += len(re.findall(r"\bGod\b", span["text"], re.IGNORECASE))
        expected_narrator = {
            label: count - attributed_counts.get(label, 0)
            for label, count in english_counts.items()
            if count - attributed_counts.get(label, 0)
        }
        narrator_breakdown = next(item for item in narrator["breakdowns"] if item["dimension"] == "verse")
        self.assertEqual(expected_narrator, {item["value"]: item["count"] for item in narrator_breakdown["values"]})
        self.assertEqual(narrator["count"], 33)
        self.assertEqual(sum(attributed_counts.values()), 0)
        self.assertIn("lexical proxy", narrator["operational_definition"])
        third_person = measurements["english-third-person-pronoun-god-reference"]
        pronoun_spans = third_person["excerpts"]
        self.assertEqual([(item["unit_label"], item["text"]) for item in pronoun_spans], [
            ("5", "he called Night"),
            ("10", "he called Seas"),
            ("27", "he made him"),
            ("27", "he made them"),
            ("31", "he had made"),
        ])
        for span in pronoun_spans:
            self.assertIn(span["text"], english_verses[span["unit_label"]])
        self.assertEqual(third_person["count"], 5)
        self.assertEqual(third_person["count_unit"], "token")
        self.assertIn("not a chapter-wide count", third_person["operational_definition"])
        geez_counts = {
            str(verse["number"]): verse["text"].count(GEʽEZ_STRING)
            for verse in self.geez_chapter["verses"]
        }
        geez_counts = {label: count for label, count in geez_counts.items() if count}
        geez_string = measurements["geez-exact-string-lexical-occurrences"]
        self.assertEqual(geez_string["observed_value"], GEʽEZ_STRING)
        self.assertEqual(geez_string["language_tag"], "gez")
        geez_breakdown = next(item for item in geez_string["breakdowns"] if item["dimension"] == "verse")
        self.assertEqual(geez_counts, {item["value"]: item["count"] for item in geez_breakdown["values"]})
        self.assertEqual(sum(geez_counts.values()), 33)
        geez_grammar = measurements["geez-first-person-grammatical-forms"]
        self.assertIsNone(geez_grammar["count"])
        self.assertEqual(geez_grammar["state"], "unassessed")
        self.assertIn("not zero", geez_grammar["reason_for_state"])
        witnesses = {item["witness_id"]: item for item in self.lens["scope"]["witnesses"]}
        self.assertEqual(witnesses[self.english["translation_id"]]["text_sha256"], chapter_hash(self.english_chapter))
        self.assertEqual(witnesses[self.reader["reader_id"]]["text_sha256"], chapter_hash(self.geez_chapter))

    def test_human_note_matches_machine_counts_and_preserves_limits(self):
        self.assertIn("(genesis-1-divine-person-lens.json)", self.note)
        self.assertIn("| First-person self-reference inside words attributed to God | 3 |", self.note)
        self.assertIn("| Third-person narrator reference: noun “God” outside the selected speech excerpts | 33 |", self.note)
        self.assertIn("| Third-person narrator reference: subject pronoun “he” manually attributed to God | 5 |", self.note)
        self.assertIn("| Exact Geʽez divine-name string `እግዚአብሔር` in the source reader | 33 |", self.note)
        self.assertIn("not a count of Geʽez grammatical person", self.note)
        self.assertIn("not decide what their plural means theologically", self.note)
        self.assertIn("textual-lens.schema.json", self.note)

    def test_bounded_lens_is_available_in_reader_and_cached_offline(self):
        self.assertIn('<option value="lexical">Textual lexical lens</option>', self.html)
        self.assertIn("function renderGenesisLexicalLens(record)", self.app)
        self.assertIn("record.measurements", self.app)
        self.assertIn("fetch('research/genesis-1-divine-person-lens.json'", self.app)
        self.assertIn("reader.reader_id === 'genesis-geez-dillmann-hacohen' && chapter.chapter === 1", self.app)
        self.assertIn("Geʽez first-person grammatical forms", self.app)
        self.assertIn("Third-person narrator reference · noun “God”", self.app)
        self.assertIn("Third-person narrator reference · pronoun “he” attributed to God", self.app)
        self.assertIn("schemas/textual-lens.schema.json", self.app)
        self.assertIn('lang="${escapeHTML(geezString.language_tag)}"', self.app)
        self.assertIn("research/genesis-1-divine-person-lens.json", self.service_worker)
        self.assertIn("schemas/textual-lens.schema.json", self.service_worker)
        self.assertRegex(self.service_worker, r"const CACHE_NAME = `\$\{CACHE_PREFIX\}shell-v\d+`;")
        self.assertIn("schemas/eotc-canon-registry.schema.json", self.service_worker)
        self.assertIn("const formatChapterLabel = (reader, item)", self.app)
        self.assertIn("formatChapterLabel(reader, chapter)", self.app)
        self.assertNotIn("chapterDisplayLabel", self.app)


if __name__ == "__main__":
    unittest.main()
