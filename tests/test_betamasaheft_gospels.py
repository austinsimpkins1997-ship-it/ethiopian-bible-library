import hashlib
import json
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMMIT = "9029473659ab6efc4035ee52b9922192c99ba75e"
TEI = "http://www.tei-c.org/ns/1.0"
XML = "http://www.w3.org/XML/1998/namespace"
NS = {"tei": TEI}
BOOKS = {
    "Matthew": ("LIT2709Matthew", "matthew-betamasaheft-tei", "eotc-nt-01", "eotc-055", 28, 1187, 1072, 0, "017bf4aefa51768328c9b045abe203ad73096895daa9fb9c9534935a52304f1d"),
    "Luke": ("LIT2713Luke", "luke-betamasaheft-tei", "eotc-nt-03", "eotc-057", 24, 1277, 1151, 1, "2dacd571061a9b57dc8ad50f8857f7ea07eb1319ce4a345fc53268659cf0ecc8"),
    "John": ("LIT2715John", "john-betamasaheft-tei", "eotc-nt-04", "eotc-058", 21, 937, 879, 0, "576aa7e7b29c3d6864555924da0488757e4e9efe6980e2b46fceea3393f85f46"),
}
ADDED_BOOKS = {
    "Esther": ("LIT1362Esther", "esther-betamasaheft-tei", "eotc-ot-19", "eotc-022", "esther", 13, 252, 252, "05bd1bef15988fc2175dcc93c16a8dffcb3078dacc7f9ffdfc515505e43a0903"),
    "Judith": ("LIT1701Judith", "judith-betamasaheft-tei", "eotc-ot-18", "eotc-021", "judith", 16, 343, 343, "65d0ced34f1943d8a73e4904be675b64d86f4161f5a3460696f0e8be416e647e"),
    "Revelation": ("LIT3179Revela", "revelation-betamasaheft-tei", "eotc-nt-27", "eotc-081", "revelation", 22, 434, 402, "bc116db0d64cfa3c32b6ca5205bcd65001f0f2e1b2fd90194b09bab6538a4178"),
    "Hosea": ("LIT3144Hosea", "hosea-betamasaheft-tei", "eotc-ot-33", "eotc-041", "hosea", 14, 197, 197, "6e479dee151b6615aec674ed34590ccb65829f1b067ba867674a2e4f0e3bad0e"),
    "Micah": ("LIT3146Micah", "micah-betamasaheft-tei", "eotc-ot-35", "eotc-043", "micah", 7, 106, 106, "6340d57733c72037d0ac492aa8fa0ea2edb67c201d0a12f7dc93db8f6fffb9fd"),
    "Zechariah": ("LIT3150Zechar", "zechariah-betamasaheft-tei", "eotc-ot-43", "eotc-051", "zechariah", 14, 202, 202, "6d7f2f9123b4519606db400708261904b0e40d5c6b507336bfda7aea1135cbfa"),
    "James": ("LIT3512Epistle", "james-betamasaheft-tei", "eotc-nt-25", "eotc-074", "james", 5, 126, 108, "985018579310735be485b8b1c5944ea75ff2825d5cdc9b1ebcd4ba6756927164"),
    "Hebrews": ("LIT3524Epistle", "hebrews-betamasaheft-tei", "eotc-nt-19", "eotc-073", "hebrews", 13, 328, 302, "f51b0b47f9f7d3067161a2d1e6374ee829832155228754db57d32bb3e33165dc"),
    "I Peter": ("LIT3507Epistle", "first-peter-betamasaheft-tei", "eotc-nt-20", "eotc-075", "first-peter", 5, 121, 105, "ce5a3a9803745dbece47718dfb769878ec5bf75d2e0a61997159e8578aedd790"),
    "II Peter": ("LIT3508Epistle", "second-peter-betamasaheft-tei", "eotc-nt-21", "eotc-076", "second-peter", 3, 70, 61, "2f8940d9492df8ddb1381aaa5572b845bf7d1fd26062203d6cbc7eb3a614bc7b"),
    "I John": ("LIT3509Epistle", "first-john-betamasaheft-tei", "eotc-nt-22", "eotc-077", "first-john", 5, 121, 105, "8b4eca0e30099c8a48c3df5a6e190b6c809f491a2ffa9ab193658d716081d2c0"),
    "I Corinthians": ("LIT3516Epistle", "first-corinthians-betamasaheft-tei", "eotc-nt-07", "eotc-061", "first-corinthians", 16, 477, 438, "ad7c3687cf53b760b75f1b35f5930ac3247658a21d3d0f0a8b905841700db4a2"),
    "II Corinthians": ("LIT3517Epistle", "second-corinthians-betamasaheft-tei", "eotc-nt-08", "eotc-062", "second-corinthians", 13, 283, 260, "208bb290478e1c61f9a5e5c88e5480572cc3ea8f45a6cc60f0169a18e1a4c270"),
    "Galatians": ("LIT3518Epistle", "galatians-betamasaheft-tei", "eotc-nt-09", "eotc-063", "galatians", 6, 165, 149, "784fc8445297aef446000f7f739be9bd3c26dc4e94533e753d241adc9fe97e5e"),
    "Ephesians": ("LIT3519Epistle", "ephesians-betamasaheft-tei", "eotc-nt-10", "eotc-064", "ephesians", 6, 174, 154, "3b9f4d927a16c03744577f7402240cc8d1efc57e99d4d055ed4ef1d87b39365f"),
    "Philippians": ("LIT3520Epistle", "philippians-betamasaheft-tei", "eotc-nt-11", "eotc-065", "philippians", 4, 117, 104, "8d037f36a473481136184d38ad34d469e4122340f952fcb4d57170a229c5a13c"),
    "Colossians": ("LIT3521Epistle", "colossians-betamasaheft-tei", "eotc-nt-12", "eotc-066", "colossians", 4, 110, 94, "24077a6e7780f5a90bc56cfc1f9a9b7991348390bc23b66eecf1514c4fec389c"),
    "I Thessalonians": ("LIT3522Epistle", "first-thessalonians-betamasaheft-tei", "eotc-nt-13", "eotc-067", "first-thessalonians", 5, 101, 89, "ecb36c3b2ba14e82982632b14ecabd905550a854b567581183772e39eb28d683"),
    "II Thessalonians": ("LIT3523Epistle", "second-thessalonians-betamasaheft-tei", "eotc-nt-14", "eotc-068", "second-thessalonians", 3, 58, 47, "f537eb52a268006c91d05c083c1d8eff477d82b1e9da982072881e7265864b0e"),
    "I Timothy": ("LIT3525Epistle", "first-timothy-betamasaheft-tei", "eotc-nt-15", "eotc-069", "first-timothy", 6, 133, 113, "584627269c10ee239b869e659261f8d4151ead78485cac652f03dd5d284a66cb"),
    "II Timothy": ("LIT3526Epistle", "second-timothy-betamasaheft-tei", "eotc-nt-16", "eotc-070", "second-timothy", 4, 99, 84, "1d05badea8d0c426b96173feb2bd9e34de2a836279ae3ae376d794f50463dba1"),
    "Titus": ("LIT3527Epistle", "titus-betamasaheft-tei", "eotc-nt-17", "eotc-071", "titus", 3, 52, 46, "3273f833ac32ddbf2742dab82450e83be9330e22366f9586deed9645617fd031"),
}


@unittest.skip('Mixed-rights scripture and source XML are withheld from the public package.')
class BetaMasaheftGospelReaderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.archive = json.loads((ROOT / "archive.json").read_text(encoding="utf-8"))
        cls.canon = json.loads((ROOT / "canon-registry.json").read_text(encoding="utf-8"))
        cls.translation_registry = json.loads((ROOT / "translation-registry.json").read_text(encoding="utf-8"))
        cls.readers = {item["reader_id"]: item for item in cls.archive["readers"]}

    def test_pinned_sources_and_exact_line_extraction(self):
        for name, (work_id, reader_id, canon_id, catalogue_id, chapter_count, line_count, numbered_count, empty_count, digest) in BOOKS.items():
            with self.subTest(book=name):
                source_path = ROOT / "readers" / "source" / "gospels" / f"{work_id}.xml-original.xml"
                raw = source_path.read_bytes()
                self.assertEqual(hashlib.sha256(raw).hexdigest(), digest)
                root = ET.fromstring(raw)
                self.assertEqual(root.get(f"{{{XML}}}id"), work_id)
                self.assertEqual(root.get(f"{{{XML}}}lang"), "en")
                edition = next(node for node in root.iter(f"{{{TEI}}}div") if node.get("type") == "edition")
                self.assertEqual(edition.get(f"{{{XML}}}lang"), "gez")
                self.assertIn("Text of the EOTC printed Bible", [" ".join("".join(node.itertext()).split()) for node in edition.findall(f"{{{TEI}}}note")])
                license_node = next(node for node in root.iter(f"{{{TEI}}}licence") if "by-sa/4.0" in node.get("target", ""))
                self.assertTrue(license_node.get("target").startswith("http://creativecommons.org/licenses/by-sa/4.0"))
                divisions = [node for node in edition if node.tag == f"{{{TEI}}}div" and node.get("subtype") == "chapter"]
                self.assertEqual([node.get("n") for node in divisions], [str(i) for i in range(1, chapter_count + 1)])
                source_lines = [line for division in divisions for line in division.iter(f"{{{TEI}}}l")]
                reader = self.readers[reader_id]
                reader_units = [unit for chapter in reader["chapters"] for unit in chapter["units"]]
                self.assertEqual(reader["source_snapshot_sha256"], digest)
                self.assertEqual((reader["canon_id"], reader["language_tag"], reader["script_code"]), (canon_id, "gez", "Ethi"))
                self.assertEqual(len(reader["chapters"]), chapter_count)
                self.assertEqual(len(source_lines), line_count)
                self.assertEqual(sum(line.get("n") is not None for line in source_lines), numbered_count)
                self.assertEqual(sum(not " ".join("".join(line.itertext()).split()) for line in source_lines), empty_count)
                self.assertEqual(len(reader_units), len(source_lines))
                for source_line, unit in zip(source_lines, reader_units):
                    self.assertEqual(unit["source_marker"], source_line.get("n"))
                    self.assertEqual(unit["text"], " ".join("".join(source_line.itertext()).split()))
                self.assertIn("unverified", reader["verification_status"].lower())
                self.assertIn("current EOTC edition", reader["verification_status"])
                self.assertFalse(reader.get("parallel_translation"))
                self.assertEqual(reader["rights_classification"], "mixed")
                self.assertEqual(reader["license_id"], "CC-BY-SA-4.0")
                self.assertIn("does not establish rights in the unidentified printed exemplar", reader["copyright_notice"])

    def test_source_anomalies_are_kept_and_empty_line_is_not_filled(self):
        matthew = self.readers["matthew-betamasaheft-tei"]
        ch7 = matthew["chapters"][6]["units"]
        self.assertEqual([unit["source_marker"] for unit in ch7[-3:]], ["27", "28", "24"])
        self.assertIn("label 24", matthew["chapter_structure_note"])
        luke = self.readers["luke-betamasaheft-tei"]
        empty = luke["chapters"][20]["units"][0]
        self.assertEqual((empty["unit_order"], empty["source_marker"], empty["text"], empty["source_text_state"]), (1, "21", "", "empty_source_element"))
        self.assertEqual(luke["chapters"][20]["notes"][0]["note_origin"], "archive")
        self.assertIn("no wording has been supplied", luke["chapters"][20]["notes"][0]["text"])
        self.assertIn("empty TEI line", luke["chapter_structure_note"])
        app = (ROOT / "app.js").read_text(encoding="utf-8")
        self.assertIn("This source line element is empty in the retained TEI", app)
        self.assertIn("note.note_origin === 'archive'", app)

    def test_canon_catalogue_source_rights_and_portable_layers_are_connected(self):
        for name, (_, reader_id, canon_id, catalogue_id, chapter_count, line_count, _, _, digest) in BOOKS.items():
            with self.subTest(book=name):
                canon = next(row for row in self.canon["books"] if row["canon_id"] == canon_id)
                self.assertEqual(canon["reader_id"], reader_id)
                self.assertIn("provisional title-level link", canon["mapping_note"])
                row = next(row for row in self.archive["catalogue"] if row["catalogue_id"] == catalogue_id)
                self.assertIn("provisional title-level link", row["text_availability_status"])
                self.assertIn("completeness unverified", row["chapter_count"])
                reader = self.readers[reader_id]
                source_ids = set(reader["source_ids"])
                self.assertTrue(source_ids <= {source["source_id"] for source in self.archive["sources"]})
                snapshot = next(
                    source for source in self.archive["sources"]
                    if source["source_id"] in source_ids
                    and "github.com/BetaMasaheft/Works" in source.get("url", "")
                )
                self.assertIn(digest, snapshot["inspection_and_limitations"])
                lead = next(item for item in self.translation_registry["edition_leads"] if item.get("bundled_reader_id") == reader_id)
                self.assertEqual(lead["mapping_state"], "uncertain")
                self.assertFalse(lead["text_bundled"])
                self.assertEqual(lead["rights_classification"], "mixed")
                self.assertIn("completeness against the physical edition", lead["scope_description"])
                layer_path = ROOT / "examples" / f"{reader_id}-layer.json"
                layer = json.loads(layer_path.read_text(encoding="utf-8"))
                content_path = (ROOT / "examples" / layer["content_package"]["uri"]).resolve()
                self.assertEqual(hashlib.sha256(content_path.read_bytes()).hexdigest(), layer["content_package"]["sha256"])
                reader_hash = hashlib.sha256((ROOT / "readers" / f"{reader_id}.json").read_bytes()).hexdigest()
                self.assertEqual(layer["content_package"]["sha256"], reader_hash)
                self.assertEqual(layer["tradition_assertions"][0]["mapping_state"], "uncertain")
                self.assertEqual(layer["rights"]["license_id"], "CC-BY-SA-4.0")
        self.assertEqual((len(self.archive["readers"]), self.canon["reader_count"]), (153, 19))
        self.assertIn("19 currently link to bundled source-text readers", self.translation_registry["coverage_statement"])
        self.assertIn("62 have no canon-linked reader", self.translation_registry["coverage_statement"])

    def test_new_pinned_books_preserve_source_and_provisional_links(self):
        for name, (work_id, reader_id, canon_id, catalogue_id, folder, chapter_count, line_count, numbered_count, digest) in ADDED_BOOKS.items():
            with self.subTest(book=name):
                source_path = ROOT / "readers" / "source" / folder / f"{work_id}.xml"
                raw = source_path.read_bytes()
                self.assertEqual(hashlib.sha256(raw).hexdigest(), digest)
                root = ET.fromstring(raw)
                self.assertEqual(root.get(f"{{{XML}}}id"), work_id)
                edition = next(node for node in root.iter(f"{{{TEI}}}div") if node.get("type") == "edition")
                self.assertEqual(edition.get(f"{{{XML}}}lang"), "gez")
                scopes = [edition] + [node for node in edition.iter(f"{{{TEI}}}div") if node is not edition]
                scope = next(node for node in scopes if any("Text of the EOTC printed Bible" in " ".join("".join(note.itertext()).split()) for note in node.findall(f"{{{TEI}}}note")))
                divisions = [node for node in scope if node.tag == f"{{{TEI}}}div" and node.get("subtype") == "chapter"]
                self.assertEqual([node.get("n") for node in divisions], [str(i) for i in range(1, chapter_count + 1)])
                source_lines = [line for chapter in divisions for line in chapter.iter(f"{{{TEI}}}l")]
                reader = self.readers[reader_id]
                reader_units = [unit for chapter in reader["chapters"] for unit in chapter["units"]]
                self.assertEqual((len(source_lines), len(reader_units)), (line_count, line_count))
                self.assertEqual(sum(line.get("n") is not None for line in source_lines), numbered_count)
                self.assertEqual((reader["canon_id"], reader["source_snapshot_sha256"]), (canon_id, digest))
                for source_line, unit in zip(source_lines, reader_units):
                    self.assertEqual(unit["source_marker"], source_line.get("n"))
                    self.assertEqual(unit["text"], " ".join("".join(source_line.itertext()).split()))
                self.assertIn("accuracy", reader["verification_status"].lower())
                self.assertIn("unverified", reader["verification_status"].lower())
                self.assertEqual(reader["rights_classification"], "mixed")
                canon = next(book for book in self.canon["books"] if book["canon_id"] == canon_id)
                self.assertEqual(canon["reader_id"], reader_id)
                self.assertIn("provisional title-level link", canon["mapping_note"])
                row = next(entry for entry in self.archive["catalogue"] if entry["catalogue_id"] == catalogue_id)
                first_source = {"Esther": 227, "Judith": 229, "Revelation": 231, "Hosea": 233, "Micah": 235, "Zechariah": 237, "James": 239, "Hebrews": 241,
                                "I Peter": 243, "II Peter": 245, "I John": 247, "I Corinthians": 249, "II Corinthians": 251, "Galatians": 253, "Ephesians": 255,
                                "Philippians": 257, "Colossians": 259, "I Thessalonians": 261, "II Thessalonians": 263, "I Timothy": 265, "II Timothy": 267, "Titus": 269}[name]
                new_sources = [f"SRC-{first_source}", f"SRC-{first_source + 1}"]
                self.assertTrue(set(new_sources) <= set(row["evidence_source_ids"]))
        rev = self.readers["revelation-betamasaheft-tei"]
        self.assertEqual([u["source_marker"] for u in rev["chapters"][1]["units"][25:28]], ["26", "26", "28"])
        for name, count in (("James", 18), ("Hebrews", 26)):
            reader = self.readers[ADDED_BOOKS[name][1]]
            units = [unit for chapter in reader["chapters"] for unit in chapter["units"]]
            self.assertEqual(sum(unit["source_marker"] is None for unit in units), count)

    def test_acts_source_scope_boundaries_and_source_label_anomalies(self):
        source_path = ROOT / "readers" / "source" / "acts" / "LIT1019Actsof.xml"
        raw = source_path.read_bytes()
        digest = "97d28f9b6ef3de974526d54572aaa7c509cd895563aca02fe45427d9e941611d"
        self.assertEqual(hashlib.sha256(raw).hexdigest(), digest)
        root = ET.fromstring(raw)
        self.assertEqual(root.get(f"{{{XML}}}id"), "LIT1019Actsof")
        self.assertEqual(root.get(f"{{{XML}}}lang"), "en")
        edition = next(node for node in root.iter(f"{{{TEI}}}div") if node.get("type") == "edition")
        self.assertEqual(edition.get(f"{{{XML}}}lang"), "gez")
        acts_scope = next(node for node in edition.iter(f"{{{TEI}}}div") if node.get(f"{{{XML}}}id") == "Acts")
        self.assertIn("Text of the EOTC printed Bible", [" ".join("".join(node.itertext()).split()) for node in acts_scope.findall(f"{{{TEI}}}note")])
        divisions = [node for node in acts_scope if node.tag == f"{{{TEI}}}div" and node.get("subtype") == "chapter"]
        self.assertEqual([node.get("n") for node in divisions], [str(i) for i in range(1, 29)])
        source_lines = [line for division in divisions for line in division.iter(f"{{{TEI}}}l")]
        reader = self.readers["acts-betamasaheft-tei"]
        reader_units = [unit for chapter in reader["chapters"] for unit in chapter["units"]]
        self.assertEqual(reader["source_snapshot_sha256"], digest)
        self.assertEqual((len(source_lines), len(reader_units)), (1208, 1208))
        self.assertEqual(sum(line.get("n") is not None for line in source_lines), 1007)
        for source_line, unit in zip(source_lines, reader_units):
            self.assertEqual(unit["source_marker"], source_line.get("n"))
            self.assertEqual(unit["text"], " ".join("".join(source_line.itertext()).split()))
        self.assertEqual([u["source_marker"] for u in reader["chapters"][11]["units"] if u["source_marker"]], ["1", "2", "3", "3", "4", "5", "6", "8", "9", "10", "11", "12", "13", "14", "15", "16", "17", "18", "19", "20", "21", "22", "23", "24", "25"])
        self.assertEqual([u["source_marker"] for u in reader["chapters"][13]["units"] if u["source_marker"]][-4:], ["24", "25", "25", "26", "27"][-4:])
        self.assertEqual([u["source_marker"] for u in reader["chapters"][25]["units"] if u["source_marker"]], ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "13", "14", "15", "16", "16", "17", "18", "19", "20", "21", "22", "23", "24", "25", "26", "27", "28", "29", "30", "31", "32"])
        intro = next(node for node in edition.iter(f"{{{TEI}}}div") if node.get(f"{{{XML}}}id") == "IntroductionActs")
        self.assertGreater(len(intro.findall(".//tei:l", NS)), 0)
        self.assertIn("IntroductionActs section", reader["additional_notes"])
        self.assertNotIn("Gospel", reader["title"])
        canon_book = next(book for book in self.canon["books"] if book["canon_id"] == "eotc-nt-05")
        self.assertEqual(canon_book["reader_id"], "acts-betamasaheft-tei")
        catalogue_row = next(row for row in self.archive["catalogue"] if row["catalogue_id"] == "eotc-059")
        self.assertIn("provisional title-level link", catalogue_row["text_availability_status"])
        source = next(s for s in self.archive["sources"] if s["source_id"] == "SRC-226")
        self.assertIn(digest, source["inspection_and_limitations"])
        audit = (ROOT / "readers" / "source" / "acts" / "SOURCE-AUDIT.md").read_text(encoding="utf-8")
        self.assertIn("repeats label `3`", audit)


if __name__ == "__main__":
    unittest.main()
