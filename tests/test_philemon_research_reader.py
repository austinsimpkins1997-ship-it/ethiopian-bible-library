import hashlib
import json
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEI = "http://www.tei-c.org/ns/1.0"
XML = "http://www.w3.org/XML/1998/namespace"


@unittest.skip('Mixed-rights scripture and source XML are withheld from the public package.')
class PhilemonResearchReaderTests(unittest.TestCase):
    def test_pinned_geez_text_is_retained_without_claiming_eotc_identity(self):
        source_path = ROOT / "readers/source/philemon/LIT3528Epistle.xml"
        raw = source_path.read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        self.assertEqual(digest, "1a2597840fe862777544855e9f9924de13d45102776dff8d5c03c201f024f130")
        root = ET.fromstring(raw)
        self.assertEqual(root.get(f"{{{XML}}}id"), "LIT3528Epistle")
        self.assertEqual(root.get(f"{{{XML}}}lang"), "en")
        license_node = next(x for x in root.iter(f"{{{TEI}}}licence") if "by-sa/4.0" in x.get("target", ""))
        self.assertIn("by-sa/4.0", license_node.get("target"))
        epistle = next(x for x in root.iter(f"{{{TEI}}}div") if x.get(f"{{{XML}}}id") == "Epistle")
        self.assertEqual(epistle.get(f"{{{XML}}}lang"), "gez")
        chapter_divs = [x for x in epistle.iter(f"{{{TEI}}}div") if x.get("subtype") == "chapter"]
        source_lines = [line for chapter in chapter_divs for line in chapter.iter(f"{{{TEI}}}l")]
        reader = json.loads((ROOT / "readers/philemon-betamasaheft-tei-research.json").read_text(encoding="utf-8"))
        units = reader["chapters"][0]["units"]
        self.assertEqual([x.get("n") for x in chapter_divs], ["1"])
        self.assertEqual((len(source_lines), sum(x.get("n") is not None for x in source_lines)), (28, 25))
        self.assertEqual(reader["source_snapshot_sha256"], digest)
        self.assertEqual((reader["language_tag"], reader["script_code"], reader["rights_classification"]), ("gez", "Ethi", "open_license"))
        self.assertEqual(len(units), len(source_lines))
        for original, extracted in zip(source_lines, units):
            self.assertEqual(extracted["source_marker"], original.get("n"))
            self.assertEqual(extracted["text"], " ".join("".join(original.itertext()).split()))
        self.assertEqual(reader.get("canon_id"), None)
        self.assertIn("root declares English", reader["edition_scope"])
        self.assertIn("not an EOTC-verified text", reader["edition_scope"])
        self.assertIn("unverified", reader["verification_status"])

    def test_candidate_is_research_only_and_coverage_is_not_inflated(self):
        archive = json.loads((ROOT / "archive.json").read_text(encoding="utf-8"))
        registry = json.loads((ROOT / "translation-registry.json").read_text(encoding="utf-8"))
        canon = json.loads((ROOT / "canon-registry.json").read_text(encoding="utf-8"))
        corpus = next(x for x in registry["research_corpora"] if x["corpus_id"] == "betamasaheft-philemon-tei-research")
        record = next(x for x in archive["sources"] if x["source_id"] == "SRC-277")
        book = next(x for x in canon["books"] if x["canon_id"] == "eotc-nt-18")
        self.assertEqual((corpus["candidate_canon_id"], corpus["canon_mapping_state"]), ("eotc-nt-18", "uncertain"))
        self.assertIn("excluded from canon-linked reader coverage", corpus["canon_mapping_note"])
        self.assertIn("current bundled records", corpus["canon_mapping_note"])
        self.assertEqual(book["reader_status"], "No reader bundled here; external availability not assessed")
        self.assertIn("exact textual basis is unresolved", record["inspection_and_limitations"])
        self.assertIn("no eotc printed-bible note", record["inspection_and_limitations"].lower())
        self.assertEqual(len(archive["readers"]), 194)
        self.assertEqual(canon["reader_count"], 19)


if __name__ == "__main__":
    unittest.main()
