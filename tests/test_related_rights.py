"""Related-work rights must stay explicit and source-scoped."""
from __future__ import annotations

import json
import unittest
from pathlib import Path

from build_standalone import validate_closed_schema_objects, validate_schema_constraints

ROOT = Path(__file__).resolve().parents[1]


class RelatedRightsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.archive = json.loads((ROOT / "archive.json").read_text(encoding="utf-8"))
        cls.schema = json.loads((ROOT / "schemas/related-text.schema.json").read_text(encoding="utf-8"))
        cls.sources = {row["source_id"] for row in cls.archive["sources"]}

    def test_related_work_rights_preserve_edition_specific_claims_and_limits(self):
        records = self.archive["related_texts"]
        self.assertEqual({record["related_id"] for record in records},
                         {f"REL-{number:03d}" for number in range(1, 10)})
        self.assertEqual({record["related_id"]: record["rights_classification"] for record in records},
                         {f"REL-{number:03d}": "public_domain_claimed" if number == 8 else "unknown"
                          for number in range(1, 10)})
        second_enoch = next(record for record in records if record["related_id"] == "REL-008")
        self.assertIn("U.S.", second_enoch["rights_status"])
        self.assertIn("not completed territory-specific rights review", second_enoch["rights_status"])
        for record in records:
            with self.subTest(related_id=record["related_id"]):
                validate_closed_schema_objects(record, self.schema, self.schema, record["related_id"])
                validate_schema_constraints(record, self.schema, self.schema, record["related_id"])
                self.assertTrue(record["rights_status"].strip())
                self.assertTrue(set(record["source_ids"]) <= self.sources)
                self.assertNotIn("text", record)

    def test_rights_limits_remain_visible_as_recorded_detail(self):
        records = {row["related_id"]: row for row in self.archive["related_texts"]}
        self.assertIn("copyrighted", records["REL-001"]["rights_status"].lower())
        self.assertIn("unresolved", records["REL-002"]["rights_status"].lower())
        self.assertIn("noncommercial", records["REL-006"]["rights_status"].lower())
        self.assertIn("work-specific", records["REL-007"]["rights_status"].lower())


if __name__ == "__main__":
    unittest.main()
