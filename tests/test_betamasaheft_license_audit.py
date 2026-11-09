import copy
import json
import unittest
from pathlib import Path
from urllib.parse import urlparse

from build_betamasaheft_license_audit import (
    DATASET_ID, DATASET_URL, GUIDELINES_ID, GUIDELINES_URL, RIGHTS_NOTE, build,
)

ROOT = Path(__file__).resolve().parents[1]


class BetaMasaheftLicenseAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original = json.loads((ROOT / "archive.json").read_text(encoding="utf-8"))

    def test_mixed_rights_text_is_metadata_only(self):
        archive = copy.deepcopy(self.original)
        count = build(archive)
        withheld = archive["rights_withheld_texts"]
        self.assertEqual(count, 42)
        self.assertEqual(len(withheld), 42)
        withheld_ids = {item["reader_id"] for item in withheld}
        self.assertFalse(withheld_ids & {item["reader_id"] for item in archive["readers"]})
        for item in withheld:
            self.assertEqual(item["rights_classification"], "mixed")
            self.assertFalse(item["public_text_included"])
            self.assertEqual(item["distribution_state"], "withheld_pending_rights_clarification")
            self.assertIn(GUIDELINES_ID, item["source_ids"])
            self.assertIn(DATASET_ID, item["source_ids"])
            self.assertFalse(any(key in item for key in ("chapters", "units", "text", "verses")))
            reader_path = ROOT / "readers" / f"{item['reader_id']}.json"
            self.assertFalse(reader_path.exists(), f"Withheld reader file is still public: {reader_path}")
            source_name = Path(urlparse(item["source_url"]).path).name
            matching_sources = list((ROOT / "readers" / "source").rglob(source_name))
            self.assertFalse(matching_sources, f"Withheld source TEI is still public: {source_name}")
        portable = json.loads((ROOT / "examples" / "portable-text-layers.json").read_text(encoding="utf-8"))
        self.assertFalse(any(
            reader_id in record.get("record_id", "")
            for reader_id in {item["reader_id"] for item in withheld}
            for record in portable.get("records", [])
        ))

    def test_source_and_catalogue_metadata_resolve(self):
        archive = copy.deepcopy(self.original)
        build(archive)
        sources = {item["source_id"]: item for item in archive["sources"]}
        self.assertEqual(sources[GUIDELINES_ID]["url"], GUIDELINES_URL)
        self.assertEqual(sources[DATASET_ID]["url"], DATASET_URL)
        source_ids = set(sources)
        for item in archive["rights_withheld_texts"]:
            self.assertTrue(set(item["source_ids"]) <= source_ids)
        for book in archive["canon_registry"]["books"]:
            if "withheld pending rights clarification" in book.get("reader_status", ""):
                self.assertIsNone(book["reader_id"])
        for lead in archive["translation_registry"]["corpus_leads"]:
            if lead.get("rights_classification") == "mixed":
                self.assertFalse(lead["text_bundled"])
                self.assertTrue(set(lead["source_ids"]) <= source_ids)

    def test_rebuilding_withheld_rights_leads_does_not_repeat_review_notices(self):
        archive = copy.deepcopy(self.original)
        build(archive)
        # The archive also contains a metadata-only Clement work lead whose
        # source IDs include the same Beta maṣāḥǝft policy records. It is not
        # one of the TEI scripture texts withheld by this audit, so scope this
        # assertion to leads that carry the audit's explicit withheld notice.
        build(archive)
        beta_leads = [
            lead for lead in archive["translation_registry"]["edition_leads"]
            if lead.get("rights_classification") == "mixed"
            and {GUIDELINES_ID, DATASET_ID}.issubset(set(lead.get("source_ids", [])))
        ]
        leads = [
            lead for lead in beta_leads
            if "Text withheld pending rights clarification; this is a metadata-only lead."
            in lead.get("review_status", "")
        ]
        self.assertEqual(len(beta_leads), 33)
        self.assertEqual(len(leads), 32)
        for lead in beta_leads:
            with self.subTest(lead=lead["edition_id"]):
                self.assertEqual(lead["review_status"].count(RIGHTS_NOTE), 1)
        for lead in leads:
            with self.subTest(withheld_lead=lead["edition_id"]):
                self.assertEqual(lead["review_status"].count("Text withheld pending rights clarification; this is a metadata-only lead."), 1)

    def test_clarification_request_is_unsent_and_covers_all_snapshots(self):
        archive = copy.deepcopy(self.original)
        build(archive)
        request = (ROOT / "research/betamasaheft-rights-clarification-request.md").read_text(encoding="utf-8")
        self.assertIn("draft only; not sent", request)
        self.assertIn("No response or silence will be treated as permission", request)
        self.assertIn("underlying printed translation/text", request)
        self.assertEqual(sum(line.startswith("| `") for line in request.splitlines()), 42)
        for item in archive["rights_withheld_texts"]:
            self.assertIn(item["reader_id"], request)
            if item.get("source_snapshot_sha256"):
                self.assertIn(item["source_snapshot_sha256"], request)


if __name__ == "__main__":
    unittest.main()
