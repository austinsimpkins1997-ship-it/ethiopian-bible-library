"""Generated Clement source-review sections must replace, not multiply."""

from __future__ import annotations

import unittest
from pathlib import Path

from build_clement_english_lead import replace_generated_review_section


ROOT = Path(__file__).resolve().parents[1]
GENERATED_START = "## Beta maṣāḥǝft work record (metadata and short incipits, not a reader)"
LEGACY_START = "## English print-edition lead (not yet text-reviewed)"


class ClementBuildIdempotencyTests(unittest.TestCase):
    def test_replacing_generated_review_section_is_idempotent(self):
        addition = f"{GENERATED_START}\n\nEvidence.\n\n{LEGACY_START}\n\nMore evidence."
        original = "# Clement review\n\nStable editorial introduction.\n\n" + addition

        once = replace_generated_review_section(original, addition)
        twice = replace_generated_review_section(once, addition)

        self.assertEqual(twice, once)
        self.assertEqual(once.count(GENERATED_START), 1)
        self.assertEqual(once.count(LEGACY_START), 1)
        self.assertIn("Stable editorial introduction.", once)

    def test_current_clement_review_has_one_generated_block(self):
        review = (ROOT / "research" / "clement-source-review.md").read_text(encoding="utf-8")
        self.assertEqual(review.count(GENERATED_START), 1)
        self.assertEqual(review.count(LEGACY_START), 1)


if __name__ == "__main__":
    unittest.main()
