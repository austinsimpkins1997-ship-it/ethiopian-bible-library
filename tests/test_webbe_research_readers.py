import unittest

import build_webbe_research_readers as builder


class WebbeResearchReaderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.package, cls.members, cls.inventory = builder._package_data()
        cls.package_hash = builder.sha256(cls.package)

    def test_inventory_distinguishes_scripture_from_preface_and_glossary(self):
        roles = [item["role"] for item in self.inventory]
        modules = [item for item in self.inventory if item["role"] == "scripture_module"]
        self.assertEqual(len(self.inventory), 87)
        self.assertEqual(len(modules), 81)
        self.assertEqual(roles.count("publisher_preface"), 1)
        self.assertEqual(roles.count("publisher_glossary"), 1)
        self.assertEqual(len({item["source_book_code"] for item in modules}), 81)
        self.assertEqual({item["source_book_code"] for item in modules if item["source_book_code"] in {"DAN", "DAG"}}, {"DAN", "DAG"})

    def test_all_eighty_one_modules_parse_with_local_source_codes_and_counts(self):
        parsed_modules = []
        for item in self.inventory:
            if item["role"] != "scripture_module":
                continue
            reader, corpus, module = builder._parse_module(
                item["source_book_code"], item["path"], self.members[item["path"]], self.package_hash
            )
            self.assertIsNone(reader["canon_id"])
            self.assertIsNone(corpus["candidate_canon_id"])
            self.assertEqual(reader["research_corpus_id"], corpus["corpus_id"])
            self.assertEqual(reader["unit_count"], sum(len(chapter["verses"]) for chapter in reader["chapters"]))
            self.assertEqual(reader["source_member_sha256"], item["sha256"])
            def assert_no_word_attributes(value):
                if isinstance(value, dict):
                    for child in value.values():
                        assert_no_word_attributes(child)
                elif isinstance(value, list):
                    for child in value:
                        assert_no_word_attributes(child)
                elif isinstance(value, str):
                    self.assertNotRegex(value, r'\|(?:strong|lemma|srcloc|x-[A-Za-z0-9-]+)\s*=')
            assert_no_word_attributes(reader["chapters"])
            assert_no_word_attributes(reader.get("front_matter", []))
            parsed_modules.append(module)
        self.assertEqual(len(parsed_modules), 81)
        self.assertEqual(sum(item["chapter_count"] for item in parsed_modules), 1402)
        self.assertEqual(sum(item["unit_count"] for item in parsed_modules), 38058)

    def test_revelation_1_11_preserves_words_punctuation_and_separate_notes(self):
        item = next(item for item in self.inventory if item.get("source_book_code") == "REV")
        raw = self.members[item["path"]]
        self.assertIn(b'\\+w What|strong="G3739"\\+w*', raw)
        reader, _, _ = builder._parse_module("REV", item["path"], raw, self.package_hash)
        verse = next(verse for verse in reader["chapters"][0]["verses"] if str(verse["number"]) == "11")
        self.assertEqual(verse["text"],
            'saying, “What you see, write in a book and send to the seven assemblies: '
            'to Ephesus, Smyrna, Pergamum, Thyatira, Sardis, Philadelphia, and to Laodicea.”')
        notes = [note["text"] for note in reader["chapters"][0]["notes"] if str(note["verse"]) == "11"]
        self.assertTrue(any("Alpha and the Omega" in text for text in notes))
        self.assertTrue(any("which are in Asia" in text for text in notes))

    def test_nested_word_attributes_are_removed_before_generic_wrappers(self):
        self.assertEqual(builder.usfm.clean_usfm(
            r'He said, \wj “\+w Keep|lemma="keep" strong="G5083" x-occurrence="1"\+w* going.”\wj*',
            strip_nested_plus=True), 'He said, “Keep going.”')
        self.assertEqual(builder.usfm.clean_usfm(
            r'\w gracious|strong="H1234,G5485"\w* and \w merciful\w*'),
            'gracious and merciful')
        self.assertEqual(builder.usfm.clean_usfm(
            r'\wj “\+w most holy|strong="H6944,H6944"\+w*!”\wj*',
            strip_nested_plus=True), '“most holy!”')
        for broken in (r'word|strong="G3739"', r'\+w word|strong="G3739"\w*'):
            with self.assertRaisesRegex(ValueError, 'USFM'):
                builder.usfm.clean_usfm(broken, strip_nested_plus=True)

    def test_greek_daniel_and_psalm_151_labels_are_not_collapsed(self):
        psalm_item = next(item for item in self.inventory if item.get("source_book_code") == "PS2")
        reader, _, _ = builder._parse_module("PS2", psalm_item["path"], self.members[psalm_item["path"]], self.package_hash)
        self.assertEqual(len(reader["chapters"]), 1)
        self.assertEqual(reader["chapters"][0]["source_page_label"], "151")
        self.assertEqual(reader["chapters"][0]["verses"][0]["text"], "I was small amongst my brothers,")
        self.assertEqual(reader["chapters"][0]["verses"][0]["continuations"][0]["text"], "and youngest in my father’s house.")

    def test_source_manifest_describes_provider_key_trust_boundary(self):
        manifest = builder._capture_manifest(self.package, self.inventory)
        integrity = manifest["package_integrity"]
        self.assertIn("good signature", integrity["signature_verification"])
        self.assertIn("not independently authenticated", integrity["signature_verification"])
        self.assertEqual(manifest["inventory_summary"]["canonical_scope"], "eBible.org module inventory only; not an Ethiopian Orthodox Tewahedo or Eritrean Orthodox canon list")


if __name__ == "__main__":
    unittest.main()
