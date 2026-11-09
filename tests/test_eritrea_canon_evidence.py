import json
import unicodedata
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class EritreaCanonEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.archive = json.loads((ROOT / "archive.json").read_text(encoding="utf-8"))
        cls.transcription = json.loads(
            (ROOT / "research" / "eritrea-canon-source-transcription.json").read_text(encoding="utf-8")
        )
        cls.comparison = json.loads(
            (ROOT / "research" / "eritrea-eotc-label-comparison.json").read_text(encoding="utf-8")
        )

    def test_diaspora_diocese_source_is_attributed_and_scoped(self):
        source = next(item for item in self.archive["sources"] if item["source_id"] == "SRC-045")
        self.assertEqual(self.transcription["record_type"], "institutional_webpage_list_transcription")
        self.assertEqual(self.transcription["source_id"], source["source_id"])
        self.assertEqual(self.transcription["source_url"], source["url"])
        self.assertIn("Diocese of the U.S.A. and Canada", self.transcription["page_attribution"])
        self.assertEqual(self.transcription["source_page_checked_at"], "2026-10-27")
        self.assertIn("not checked against a synodical canon list", self.transcription["review_status"])
        self.assertIn("Metadata transcription only", self.transcription["reuse_note"])

    def test_transcribed_entry_counts_and_boundaries_are_exact(self):
        numbered = self.transcription["counts_as_numbered_by_page"]
        self.assertEqual(numbered["Old Testament"]["count"], 46)
        self.assertEqual(numbered["New Testament"]["count"], 35)
        self.assertEqual(numbered["total_numbered_entries"], 81)
        self.assertEqual(len(numbered["Old Testament"]["entries"]), 46)
        self.assertEqual(len(numbered["New Testament"]["entries"]), 35)
        self.assertEqual(numbered["Old Testament"]["entries"][-1], "The Book of Josephas the Son of Bengorion")
        self.assertEqual(numbered["New Testament"]["entries"][-1], "Didascalia | Didache")
        self.assertIn("not decide whether that denotes one combined entry", " ".join(self.transcription["interpretive_cautions"]))

    def test_comparison_reproduces_source_labels_without_claiming_canon_equivalence(self):
        registry_books = self.archive["canon_registry"]["books"]
        expected_rows = []
        for section, section_key in (("Old Testament", "Old Testament"), ("New Testament", "New Testament")):
            eotc_labels = [item["source_label"] for item in registry_books if item["section"] == section]
            diocese_labels = self.transcription["counts_as_numbered_by_page"][section_key]["entries"]
            self.assertEqual(len(eotc_labels), len(diocese_labels))
            expected_rows.extend(zip([section] * len(eotc_labels), eotc_labels, diocese_labels))

        actual_rows = [
            (item["section"], item["eotc_source_label"], item["eritrea_diocese_page_label"])
            for item in self.comparison["entries"]
        ]
        self.assertEqual(actual_rows, expected_rows)
        exact = sum(left == right for _, left, right in expected_rows)
        normalized = sum(
            " ".join(unicodedata.normalize("NFKC", left).split()).casefold()
            == " ".join(unicodedata.normalize("NFKC", right).split()).casefold()
            for _, left, right in expected_rows
        )
        self.assertEqual((self.comparison["entry_count"], exact, normalized), (81, 77, 78))
        self.assertEqual(self.comparison["source_ids"], ["SRC-029", "SRC-045"])
        self.assertIn("not a canon crosswalk", self.comparison["scope_note"])
        self.assertIn("does not establish synod-approved Eritrean canon status", self.comparison["scope_note"])
        self.assertEqual(len(registry_books), 81)


if __name__ == "__main__":
    unittest.main()
