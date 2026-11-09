import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class SourceRightsDisplayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.archive = json.loads((ROOT / "archive.json").read_text(encoding="utf-8"))
        cls.app = (ROOT / "app.js").read_text(encoding="utf-8")

    def test_source_cards_state_when_structured_reuse_rights_are_missing(self):
        inventory = json.loads((ROOT / "package-inventory.json").read_text(encoding="utf-8"))
        self.assertEqual(len(self.archive["sources"]), inventory["source_record_count"])
        self.assertIn("SRC-397", {source["source_id"] for source in self.archive["sources"]})
        self.assertIn("SRC-398", {source["source_id"] for source in self.archive["sources"]})
        self.assertIn("SRC-399", {source["source_id"] for source in self.archive["sources"]})
        self.assertIn("SRC-400", {source["source_id"] for source in self.archive["sources"]})
        self.assertIn("SRC-401", {source["source_id"] for source in self.archive["sources"]})
        self.assertIn("SRC-402", {source["source_id"] for source in self.archive["sources"]})
        self.assertIn("SRC-403", {source["source_id"] for source in self.archive["sources"]})
        self.assertIn("SRC-404", {source["source_id"] for source in self.archive["sources"]})
        self.assertIn("SRC-405", {source["source_id"] for source in self.archive["sources"]})
        self.assertIn("SRC-406", {source["source_id"] for source in self.archive["sources"]})
        self.assertIn("function sourceRightsNote(source)", self.app)
        self.assertIn("Structured rights category: not recorded.", self.app)
        self.assertIn("No item-specific reuse terms are recorded in the structured rights fields.", self.app)
        self.assertIn("A citation is not a reuse license.", self.app)
        self.assertIn("Rights for any bundled reader text or media are documented separately.", self.app)
        self.assertIn('<details class="source-rights-note"><summary>Rights and reuse</summary>', self.app)
        self.assertIn("${sourceRightsNote(source)}", self.app)

    def test_explicit_source_rights_and_evidence_are_shown_and_escaped(self):
        self.assertIn("source.rights_classification", self.app)
        self.assertIn("source.rights_status", self.app)
        self.assertIn("source.rights_basis", self.app)
        self.assertIn("const basis = source.rights_basis", self.app)
        self.assertIn("Rights evidence basis:", self.app)
        self.assertIn("reader.rights_status", self.app)
        self.assertIn("Item copyright and reuse notice", self.app)
        self.assertIn("${escapeHTML(`${category}${notice}", self.app)

    def test_archived_publisher_rights_notice_is_linked_from_its_source_card(self):
        source = next(source for source in self.archive["sources"] if source["source_id"] == "SRC-414")
        local_notice = ROOT / source["local_rights_copy_url"]
        self.assertTrue(local_notice.is_file())
        self.assertIn("source.local_rights_copy_url", self.app)
        self.assertIn("View archived rights notice", self.app)


if __name__ == "__main__":
    unittest.main()
