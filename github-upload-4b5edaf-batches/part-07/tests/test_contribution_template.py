from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / ".github" / "ISSUE_TEMPLATE" / "source-or-translation-proposal.md"


class ContributionTemplateTests(unittest.TestCase):
    def test_issue_template_front_matter_and_integrity_prompts(self):
        text = TEMPLATE.read_text(encoding="utf-8-sig")
        self.assertTrue(text.startswith("---\n"))
        _, front_matter, body = text.split("---\n", 2)
        keys = re.findall(r"^(name|about|title|labels|assignees):", front_matter, re.MULTILINE)
        self.assertEqual(keys, ["name", "about", "title"])
        self.assertNotRegex(front_matter, r"^\s+\w+: ")
        for phrase in (
            "Unknown or uncertain is a valid answer",
            "Actual observed chapter/section labels and count",
            "Rights and redistribution",
            "Do not attach full text, scans, or copyrighted files",
            "Do not submit machine output or OCR as verified scripture",
        ):
            self.assertIn(phrase, body)


if __name__ == "__main__":
    unittest.main()
