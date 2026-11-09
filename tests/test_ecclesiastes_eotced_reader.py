import hashlib
import json
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEI = "http://www.tei-c.org/ns/1.0"
XML = "http://www.w3.org/XML/1998/namespace"


@unittest.skip('Mixed-rights scripture and source XML are withheld from the public package.')
class EcclesiastesEotcedReaderTests(unittest.TestCase):
    def test_scoped_extract_matches_reader_and_preserves_source_boundaries(self):
        reader = json.loads((ROOT / "readers/ecclesiastes-geez-betamasaheft-eotced.json").read_text(encoding="utf-8"))
        archive = json.loads((ROOT / "archive.json").read_text(encoding="utf-8"))
        canon = json.loads((ROOT / "canon-registry.json").read_text(encoding="utf-8"))
        registry = json.loads((ROOT / "translation-registry.json").read_text(encoding="utf-8"))
        raw = (ROOT / "readers/source/ecclesiastes/LIT1320Eccles-EOTCed.xml").read_bytes()
        root = ET.fromstring(raw)
        self.assertEqual(hashlib.sha256(raw).hexdigest(), reader["source_snapshot_sha256"])
        self.assertEqual(reader["canon_id"], "eotc-ot-27")
        self.assertEqual((reader["chapter_count"], reader["unit_count"]), (12, 226))
        self.assertEqual(reader["source_ids"], ["SRC-029", "SRC-176", "SRC-279", "SRC-294"])
        self.assertEqual(root.get(f"{{{XML}}}lang"), "en")
        editions = [x for x in root.iter(f"{{{TEI}}}div") if x.get(f"{{{XML}}}id") == "EOTCed"]
        self.assertEqual(len(editions), 1)
        edition = editions[0]
        self.assertEqual(edition.get(f"{{{XML}}}lang"), "gez")
        self.assertFalse(any(x.get(f"{{{XML}}}id") == "Mercer" for x in root.iter(f"{{{TEI}}}div")))
        source_chapters = [x for x in edition if x.tag == f"{{{TEI}}}div"]
        self.assertEqual([x.get("n") for x in source_chapters], [str(i) for i in range(1, 13)])
        for chapter, source_chapter in zip(reader["chapters"], source_chapters):
            source_lines = list(source_chapter.iter(f"{{{TEI}}}l"))
            self.assertEqual(len(chapter["units"]), len(source_lines))
            for unit, source_line in zip(chapter["units"], source_lines):
                self.assertEqual(unit["source_marker"], source_line.get("n"))
                self.assertEqual(unit["text"], " ".join("".join(source_line.itertext()).split()))
                self.assertEqual(unit["source_refs"], [x.get("target") for x in source_line.iter(f"{{{TEI}}}ref") if x.get("target")])
        self.assertEqual(sum(len(u["source_refs"]) for ch in reader["chapters"] for u in ch["units"]), 222)
        chapter12 = reader["chapters"][11]["units"]
        self.assertEqual([(u["source_marker"], u["source_refs"][0].rsplit("=", 1)[-1]) for u in chapter12[12:]], [(str(i), str(i - 3)) for i in range(13, 18)])
        self.assertIn("underlying print rights", reader["copyright_notice"])
        self.assertIn("accuracy", reader["verification_status"])
        self.assertEqual(sum(x.get("canon_id") == "eotc-ot-27" for x in archive["readers"]), 1)
        self.assertEqual(canon["reader_count"], 19)
        book = next(x for x in canon["books"] if x["canon_id"] == "eotc-ot-27")
        self.assertEqual(book["reader_id"], reader["reader_id"])
        lead = next(x for x in registry["edition_leads"] if x["edition_id"] == "betamasaheft-ecclesiastes-eotced")
        self.assertEqual(lead["mapping_state"], "asserted_by_source")


if __name__ == "__main__":
    unittest.main()
