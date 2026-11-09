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
            parsed_modules.append(module)
        self.assertEqual(len(parsed_modules), 81)
        self.assertEqual(sum(item["chapter_count"] for item in parsed_modules), 1402)
        self.assertEqual(sum(item["unit_count"] for item in parsed_modules), 38058)

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
