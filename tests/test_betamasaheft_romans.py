import hashlib
import json
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEI = "http://www.tei-c.org/ns/1.0"
XML = "http://www.w3.org/XML/1998/namespace"
SOURCE_SHA256 = "6513f7a65aa76d8b09b2d6f9e04351730adbf538ea28c305958754ceb3236458"


@unittest.skip('Mixed-rights scripture and source XML are withheld from the public package.')
class BetaMasaheftRomansTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.archive = json.loads((ROOT / "archive.json").read_text(encoding="utf-8"))
        cls.reader = next(r for r in cls.archive["readers"] if r["reader_id"] == "romans-betamasaheft-tei")
        cls.registry = cls.archive["translation_registry"]

    def test_all_lines_and_surrounding_text_parts_are_retained_in_order(self):
        raw = (ROOT / "readers/source/romans/LIT3515Epistle.xml").read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(), SOURCE_SHA256)
        root = ET.fromstring(raw)
        edition = next(x for x in root.iter(f"{{{TEI}}}div") if x.get("type") == "edition")
        self.assertEqual(edition.get(f"{{{XML}}}lang"), "gez")
        top_parts = [x.get(f"{{{XML}}}id") for x in edition.findall(f"{{{TEI}}}div") if x.get("type") == "textpart"]
        self.assertEqual(top_parts, ["Prescription", "Introduction", "Epistle", "subscription", "stichometry"])
        source_chapters = [x for x in edition.iter(f"{{{TEI}}}div") if x.get("subtype") == "chapter"]
        self.assertEqual([x.get("n") for x in source_chapters], [str(i) for i in range(1, 17)])
        source_lines = list(edition.iter(f"{{{TEI}}}l"))
        reader_lines = [u for ch in self.reader["chapters"] for u in ch["units"] if u.get("source_element_type") == "l"]
        self.assertEqual((len(source_lines), sum(x.get("n") is not None for x in source_lines)), (495, 430))
        self.assertEqual(len(reader_lines), len(source_lines))
        for source, unit in zip(source_lines, reader_lines):
            self.assertEqual(unit["source_marker"], source.get("n"))
            self.assertEqual(unit["text"], " ".join("".join(source.itertext()).split()))
        self.assertEqual((self.reader["chapter_count"], self.reader["source_numbered_unit_count"], self.reader["source_unnumbered_unit_count"]), (20, 430, 65))
        self.assertIn("source text parts", self.reader["chapter_structure_note"])
        all_notes = [note["text"] for chapter in self.reader["chapters"] for note in chapter["notes"]]
        self.assertTrue(any("preliminary division" in note for note in all_notes))
        self.assertTrue(any("printed EOTC Bible" in note for note in all_notes))
        self.assertTrue(any("no body text" in note for note in all_notes))

    def test_provisional_mapping_rights_and_catalogue_are_connected(self):
        self.assertEqual(self.reader["canon_id"], "eotc-nt-06")
        self.assertEqual(self.reader["rights_classification"], "mixed")
        self.assertIn("recension", self.reader["verification_status"].lower())
        book = next(b for b in self.archive["canon_registry"]["books"] if b["canon_id"] == "eotc-nt-06")
        self.assertEqual(book["reader_id"], self.reader["reader_id"])
        self.assertIn("preliminary", book["mapping_note"])
        lead = next(x for x in self.registry["edition_leads"] if x["edition_id"] == "betamasaheft-romans-tei-2026")
        self.assertEqual((lead["mapping_state"], lead["candidate_canon_id"], lead["text_bundled"]), ("uncertain", "eotc-nt-06", False))
        catalogue = next(x for x in self.archive["catalogue"] if x["catalogue_id"] == "eotc-060")
        self.assertIn("preliminary", catalogue["chapter_count"])


if __name__ == "__main__":
    unittest.main()
