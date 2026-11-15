"""Ruth source registration must preserve downstream rights evidence."""

from copy import deepcopy
import unittest

from build_brenton_ruth import ensure_source


class RuthSourceRegistrationTests(unittest.TestCase):
    def setUp(self):
        self.source = {
            "source_id": "SRC-095", "source_name": "Ruth chapter pages",
            "url": "https://ebible.org/eng-Brenton/RUT.htm",
        }

    def test_rebuilding_preserves_enrichment_and_is_idempotent(self):
        enriched = dict(self.source, rights_classification="unknown",
                        rights_status="Review pending", rights_basis="No license inspected")
        archive = {"sources": [enriched]}
        baseline = deepcopy(archive)
        ensure_source(archive, self.source)
        ensure_source(archive, self.source)
        self.assertEqual(archive, baseline)

    def test_genuine_identity_conflict_is_rejected_without_mutation(self):
        archive = {"sources": [dict(self.source, url="https://example.org/other")]}
        baseline = deepcopy(archive)
        with self.assertRaisesRegex(ValueError, "SRC-095: url"):
            ensure_source(archive, self.source)
        self.assertEqual(archive, baseline)

    def test_first_registration_then_repeat_does_not_duplicate(self):
        archive = {}
        ensure_source(archive, self.source)
        ensure_source(archive, self.source)
        self.assertEqual(archive["sources"], [self.source])


if __name__ == "__main__":
    unittest.main()
