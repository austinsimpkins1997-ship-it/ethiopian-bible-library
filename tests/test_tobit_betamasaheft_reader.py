import hashlib
import json
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
READER_ID = "tobit-geez-betamasaheft-eotced"
SHA256 = "d732fb21c75002ff4b8e03affc12c9dc10883d6db73154f8b0ca84334c03943e"

@unittest.skip('Mixed-rights scripture and source XML are withheld from the public package.')
class TobitBetaMasaheftReaderTests(unittest.TestCase):
    def test_pinned_source_and_extraction_structure(self):
        source = ROOT / "readers/source/tobit/LIT2473TobitB-original.xml"
        data = source.read_bytes()
        self.assertEqual(hashlib.sha256(data).hexdigest(), SHA256)
        root = ET.fromstring(data)
        ns = "http://www.tei-c.org/ns/1.0"
        xml = "http://www.w3.org/XML/1998/namespace"
        edition = next(e for e in root.iter(f"{{{ns}}}div") if e.get("type") == "edition")
        self.assertEqual(root.get(f"{{{xml}}}lang"), "en")
        self.assertEqual(edition.get(f"{{{xml}}}lang"), "gez")
        chapters = [e for e in edition if e.get("subtype") == "chapter"]
        self.assertEqual(len(chapters), 14)
        self.assertEqual(sum(len(list(ch.iter(f"{{{ns}}}l"))) for ch in chapters), 242)
        reader = json.loads((ROOT / f"readers/{READER_ID}.json").read_text(encoding="utf-8"))
        self.assertEqual(reader["source_snapshot_sha256"], SHA256)
        self.assertEqual((reader["chapter_count"], reader["unit_count"]), (14, 242))
        self.assertEqual(reader["language_assignment_status"], "source_declared_inherited_edition_xml_lang")
        self.assertFalse(reader.get("parallel_translation"))
        self.assertTrue(all(v["text"] for c in reader["chapters"] for v in c["verses"]))

    def test_canon_registry_and_rights_provenance(self):
        canon = json.loads((ROOT / "canon-registry.json").read_text(encoding="utf-8"))
        entry = next(x for x in canon["books"] if x["canon_id"] == "eotc-ot-17")
        self.assertEqual(entry["reader_id"], READER_ID)
        self.assertIn("unverified", entry["mapping_note"])
        archive = json.loads((ROOT / "archive.json").read_text(encoding="utf-8"))
        source = next(x for x in archive["sources"] if x["source_id"] == "SRC-218")
        self.assertIn(SHA256, source["inspection_and_limitations"])
        registry = json.loads((ROOT / "translation-registry.json").read_text(encoding="utf-8"))
        lead = next(x for x in registry["edition_leads"] if x["edition_id"] == "betamasaheft-tobit-tei-vulgata-2025")
        self.assertEqual(lead["rights_classification"], "mixed")
        self.assertEqual(lead["bundled_reader_id"], READER_ID)
        self.assertIn("accuracy", lead["review_status"])

if __name__ == "__main__":
    unittest.main()
