import hashlib
import json
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


@unittest.skip('Mixed-rights scripture and source XML are withheld from the public package.')
class SongOfSongsReaderTests(unittest.TestCase):
    def test_eotced_text_is_pinned_bundled_and_source_asserted(self):
        reader = json.loads((ROOT / "readers/song-of-songs-geez-betamasaheft-eotced.json").read_text(encoding="utf-8"))
        archive = json.loads((ROOT / "archive.json").read_text(encoding="utf-8"))
        canon = json.loads((ROOT / "canon-registry.json").read_text(encoding="utf-8"))
        registry = json.loads((ROOT / "translation-registry.json").read_text(encoding="utf-8"))
        raw = (ROOT / "readers/source/song-of-songs/LIT2362Songof.xml").read_bytes()
        tei = ET.fromstring(raw)
        ns = {"t": "http://www.tei-c.org/ns/1.0"}
        source_edition = next(x for x in tei.findall('.//t:div[@type="edition"]', ns) if x.get("{http://www.w3.org/XML/1998/namespace}id") == "EOTCed")
        self.assertEqual(reader["source_snapshot_sha256"], hashlib.sha256(raw).hexdigest())
        self.assertEqual(reader["canon_id"], "eotc-ot-28")
        self.assertEqual((reader["chapter_count"], reader["unit_count"]), (8, 131))
        self.assertEqual([chapter["source_chapter_label"] for chapter in reader["chapters"]], [str(i) for i in range(1, 9)])
        self.assertEqual(sum(len(chapter["units"]) for chapter in reader["chapters"]), 131)
        for chapter, source_chapter in zip(reader["chapters"], [x for x in source_edition if x.get("type") == "textpart" and x.get("subtype") == "chapter"]):
            source_lines = list(source_chapter.iter("{http://www.tei-c.org/ns/1.0}l"))
            self.assertEqual(len(chapter["units"]), len(source_lines))
            for unit, source_line in zip(chapter["units"], source_lines):
                self.assertEqual(unit["source_marker"], source_line.get("n"))
                self.assertEqual(unit["text"], " ".join("".join(source_line.itertext()).split()))
        self.assertIn("EOTC printed Bible", reader["edition_scope"])
        self.assertIn("modern Vulgata", reader["edition_scope"])
        self.assertIn("remains unresolved", reader["copyright_notice"])
        chap8 = [unit["source_marker"] for unit in reader["chapters"][7]["units"]]
        self.assertEqual(chap8, [str(i) for i in range(1, 15)] + ["14", "15", "16"])
        self.assertEqual(sum(item.get("canon_id") == "eotc-ot-28" for item in archive["readers"]), 1)
        layer = next(row for row in next(x for x in registry["languages"] if x["language_tag"] == "gez")["records"] if row["reader_id"] == reader["reader_id"])
        self.assertEqual(layer["status"], "bundled")
        self.assertIn("modern-Vulgata", layer["basis_description"])
        lead = next(row for row in registry["edition_leads"] if row["edition_id"] == "betamasaheft-song-of-songs-eotced-2025")
        self.assertEqual(lead["mapping_state"], "asserted_by_source")
        entry = next(row for row in canon["books"] if row["canon_id"] == "eotc-ot-28")
        self.assertEqual(entry["reader_id"], reader["reader_id"])
        catalogue = next(row for row in archive["catalogue"] if row["catalogue_id"] == "eotc-028")
        self.assertIn("Exact printed exemplar", catalogue["text_availability_status"])

    def test_coverage_counts_linked_reader_without_claiming_accuracy(self):
        archive = json.loads((ROOT / "archive.json").read_text(encoding="utf-8"))
        canon = json.loads((ROOT / "canon-registry.json").read_text(encoding="utf-8"))
        self.assertEqual(canon["reader_count"], 19)
        reader = next(x for x in archive["readers"] if x["reader_id"] == "song-of-songs-geez-betamasaheft-eotced")
        self.assertIn("accuracy", reader["verification_status"])


if __name__ == "__main__":
    unittest.main()
