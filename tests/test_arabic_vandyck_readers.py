import unittest

from build_arabic_vandyck_readers import BOOKS, build
from book_code_crosswalks import PUBLISHER_BOOK_CODE_CANDIDATES, candidate_note


class ArabicVanDyckReaderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.readers, cls.corpora = build()

    def test_package_inventory_and_structure_counts(self):
        self.assertEqual(len(self.readers), 66)
        self.assertEqual(len(self.corpora), 66)
        self.assertEqual(sum(reader["chapter_count"] for reader in self.readers), 1189)
        self.assertEqual(sum(reader["unit_count"] for reader in self.readers), 31104)
        self.assertEqual({reader["reader_id"].split("-")[2].upper() for reader in self.readers}, set(BOOKS))

    def test_reader_scope_and_source_provenance_are_not_overstated(self):
        for reader, corpus in zip(self.readers, self.corpora):
            self.assertTrue(reader["rights_status"])
            self.assertEqual(reader["language_tag"], "arb")
            self.assertEqual(reader["language"], "Standard Arabic")
            self.assertEqual(reader["script_code"], "Arab")
            self.assertEqual(reader["translation_basis_status"], "unknown")
            self.assertNotIn("canon_id", reader)
            code = reader["reader_id"].split("-")[2].upper()
            candidate = PUBLISHER_BOOK_CODE_CANDIDATES.get(code)
            self.assertEqual(corpus["candidate_canon_id"], candidate)
            self.assertEqual(corpus["canon_mapping_state"], "uncertain" if candidate else "not_mapped")
            if candidate:
                self.assertIn("not asserted by eBible.org", corpus["canon_mapping_note"])
                self.assertIn("SRC-029", corpus["source_ids"])
                self.assertIn("SRC-196", corpus["source_ids"])
                self.assertIn("SRC-396", corpus["source_ids"])
            self.assertEqual(corpus["language_tag"], "arb")
            self.assertEqual(len(reader["source_member_sha256"]), 64)

    def test_standard_codes_preserve_documented_scope_distinctions(self):
        expected = {
            "EST": "Hebrew Esther",
            "PSA": "151 Psalms in Orthodox Bibles",
            "PRO": "24 in the Ethiopian Bible",
            "DAN": "Greek Septuagint Daniel separately as DAG",
            "EZR": "Ezra-Nehemiah when treated as one book",
        }
        for code, phrase in expected.items():
            with self.subTest(code=code):
                note = candidate_note(code, PUBLISHER_BOOK_CODE_CANDIDATES[code])
                self.assertIn(phrase, note)
                self.assertIn("SRC-396", note)
                self.assertIn("research reader", note)
                self.assertIn("does not establish", note)
        self.assertNotIn("code-specific distinction", candidate_note("GEN", PUBLISHER_BOOK_CODE_CANDIDATES["GEN"]))

    def test_genesis_opening_and_source_heading_are_retained(self):
        genesis = next(reader for reader in self.readers if reader["reader_id"] == "arb-vd-gen-research")
        first_chapter = genesis["chapters"][0]
        self.assertEqual(first_chapter["chapter"], 1)
        self.assertEqual(first_chapter["verses"][0]["number"], "1")
        self.assertIn("فِي ٱلْبَدْءِ", first_chapter["verses"][0]["text"])
        self.assertTrue(any(verse.get("source_headings_before") for verse in first_chapter["verses"]))


if __name__ == "__main__":
    unittest.main()
