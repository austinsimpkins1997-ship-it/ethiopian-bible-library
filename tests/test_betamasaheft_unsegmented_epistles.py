import hashlib
import json
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEI = "http://www.tei-c.org/ns/1.0"
XML = "http://www.w3.org/XML/1998/namespace"
BOOKS = {
    "II John": ("LIT3510Epistle", "ii-john-betamasaheft-tei-research", "eotc-nt-23", 15, 13, "13bdbd8aab7f924d1ea5c4b75adeb9ec674844078481fdd3d896b1f7d1c3307b"),
    "III John": ("LIT3511Epistle", "iii-john-betamasaheft-tei-research", "eotc-nt-24", 17, 15, "614268415cb8006b21f914b7ec4d406aa1020488a53446437a2ae03f5dcea952"),
    "Jude": ("LIT3513Epistle", "jude-betamasaheft-tei-research", "eotc-nt-26", 28, 25, "9d4ce8878c332696fb8d4246b83089108d0770f84948f76c984383be696350a6"),
}


@unittest.skip('Mixed-rights scripture and source XML are withheld from the public package.')
class BetaMasaheftUnsegmentedEpistleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.archive = json.loads((ROOT / "archive.json").read_text(encoding="utf-8"))
        cls.registry = json.loads((ROOT / "translation-registry.json").read_text(encoding="utf-8"))
        cls.readers = {r["reader_id"]: r for r in cls.archive["readers"]}
        cls.corpora = {r["reader_id"]: r for r in cls.registry["research_corpora"]}

    def test_exact_source_extraction_and_noncanon_status(self):
        for name, (work, reader_id, candidate, line_count, numbered_count, digest) in BOOKS.items():
            with self.subTest(book=name):
                raw = (ROOT / "readers" / "source" / "unsegmented-epistles" / f"{work}.xml").read_bytes()
                self.assertEqual(hashlib.sha256(raw).hexdigest(), digest)
                root = ET.fromstring(raw)
                self.assertEqual(root.get(f"{{{XML}}}id"), work)
                edition = next(x for x in root.iter(f"{{{TEI}}}div") if x.get("type") == "edition")
                self.assertEqual(edition.get(f"{{{XML}}}lang"), "gez")
                self.assertFalse(any(x.get("subtype") == "chapter" for x in edition.iter(f"{{{TEI}}}div")))
                self.assertFalse(any("Text of the EOTC printed Bible" in " ".join("".join(n.itertext()).split()) for n in edition.iter(f"{{{TEI}}}note")))
                source_lines = list(edition.iter(f"{{{TEI}}}l"))
                reader = self.readers[reader_id]
                units = reader["chapters"][0]["units"]
                self.assertIsNone(reader.get("canon_id"))
                self.assertEqual(reader["chapter_count"], 1)  # navigation container only; source has no chapter divisions
                self.assertIn("not a claim that the TEI labels it chapter 1", reader["chapter_structure_note"])
                self.assertEqual((len(source_lines), sum(line.get("n") is not None for line in source_lines)), (line_count, numbered_count))
                self.assertEqual(len(units), len(source_lines))
                for source_line, unit in zip(source_lines, units):
                    self.assertEqual(unit["source_marker"], source_line.get("n"))
                    self.assertEqual(unit["text"], " ".join("".join(source_line.itertext()).split()))
                corpus = self.corpora[reader_id]
                self.assertEqual((corpus["candidate_canon_id"], corpus["canon_mapping_state"]), (candidate, "uncertain"))
                self.assertIn("excluded from canon-linked coverage", corpus["canon_mapping_note"])
                self.assertEqual(reader["rights_classification"], "mixed")
                source = next(x for x in self.archive["sources"] if x["source_id"] == reader["source_ids"][0])
                self.assertIn(digest, source["inspection_and_limitations"])


if __name__ == "__main__":
    unittest.main()
