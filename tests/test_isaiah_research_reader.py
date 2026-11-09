import hashlib
import json
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEI = "http://www.tei-c.org/ns/1.0"
XML = "http://www.w3.org/XML/1998/namespace"


@unittest.skip('Mixed-rights scripture and source XML are withheld from the public package.')
class IsaiahResearchReaderTests(unittest.TestCase):
    def test_pinned_source_structure_and_exact_line_extraction(self):
        source_path = ROOT / "readers/source/isaiah/LIT1672Isaiah.xml"
        raw = source_path.read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        self.assertEqual(digest, "5310b41b3f3f7ead567321b44b6333fafea99102f54f37b0ad43e7436da95a53")
        root = ET.fromstring(raw)
        self.assertEqual(root.get(f"{{{XML}}}id"), "LIT1672Isaiah")
        self.assertEqual(root.get(f"{{{XML}}}lang"), "en")
        edition = next(x for x in root.iter(f"{{{TEI}}}div") if x.get("type") == "edition")
        self.assertEqual(edition.get(f"{{{XML}}}lang"), "gez")
        license_node = next(x for x in root.iter(f"{{{TEI}}}licence") if "by-sa/4.0" in x.get("target", ""))
        self.assertIn("by-sa/4.0", license_node.get("target"))
        chapters = [x for x in edition if x.get("type") == "textpart" and x.get("subtype") == "chapter"]
        self.assertEqual([x.get("n") for x in chapters], [str(i) for i in range(1, 67)])
        source_lines = [line for chapter in chapters for line in chapter.iter(f"{{{TEI}}}l")]
        self.assertEqual(len(source_lines), 1289)
        reader = json.loads((ROOT / "readers/isaiah-betamasaheft-tei-research.json").read_text(encoding="utf-8"))
        self.assertEqual(reader["source_snapshot_sha256"], digest)
        self.assertEqual((reader["language_tag"], reader["script_code"], reader["chapter_count"], reader["unit_count"]), ("gez", "Ethi", 66, 1289))
        all_units = [unit for chapter in reader["chapters"] for unit in chapter["units"]]
        self.assertEqual(len(all_units), len(source_lines))
        for original, extracted in zip(source_lines, all_units):
            self.assertEqual(extracted["source_marker"], original.get("n"))
            self.assertEqual(extracted["text"], " ".join("".join(original.itertext()).split()))
            self.assertEqual(extracted["source_refs"], [ref.get("target") for ref in original.iter(f"{{{TEI}}}ref") if ref.get("target")])
        self.assertTrue(all(unit["source_marker"] for unit in all_units))
        self.assertFalse(reader.get("canon_id"))
        self.assertIn("root declares English", reader["edition_scope"])
        self.assertIn("not an EOTC-verified text", reader["edition_scope"])
        self.assertIn("accuracy, completeness", reader["verification_status"])

    def test_candidate_is_separate_from_canon_linked_coverage(self):
        archive = json.loads((ROOT / "archive.json").read_text(encoding="utf-8"))
        registry = json.loads((ROOT / "translation-registry.json").read_text(encoding="utf-8"))
        canon = json.loads((ROOT / "canon-registry.json").read_text(encoding="utf-8"))
        corpus = next(x for x in registry["research_corpora"] if x["corpus_id"] == "betamasaheft-isaiah-tei-research")
        record = next(x for x in archive["sources"] if x["source_id"] == "SRC-278")
        book = next(x for x in canon["books"] if x["canon_id"] == "eotc-ot-29")
        self.assertEqual((corpus["candidate_canon_id"], corpus["canon_mapping_state"]), ("eotc-ot-29", "uncertain"))
        self.assertIn("excluded from canon-linked coverage", corpus["canon_mapping_note"])
        self.assertEqual(book["reader_status"], "No reader bundled here; external availability not assessed")
        self.assertIn("relationship is not independently resolved", record["inspection_and_limitations"])
        self.assertIn("does not explicitly say", record["inspection_and_limitations"])
        self.assertEqual(len(archive["readers"]), 194)
        self.assertEqual(canon["reader_count"], 19)


if __name__ == "__main__":
    unittest.main()
