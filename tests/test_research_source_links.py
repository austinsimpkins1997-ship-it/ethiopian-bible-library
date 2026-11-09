import json
from html.parser import HTMLParser
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]


class SourceLinkParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.active_link = None

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            self.active_link = [dict(attrs).get("href", ""), []]

    def handle_data(self, data):
        if self.active_link is not None:
            self.active_link[1].append(data)

    def handle_endtag(self, tag):
        if tag == "a" and self.active_link is not None:
            self.links.append((self.active_link[0], "".join(self.active_link[1]).strip()))
            self.active_link = None


class ResearchSourceLinksTests(unittest.TestCase):
    def test_source_citation_labels_match_linked_records(self):
        archive = json.loads((ROOT / "archive.json").read_text(encoding="utf-8"))
        source_ids = {source["source_id"] for source in archive["sources"]}
        mismatches = []

        for page in sorted((ROOT / "research").glob("*.html")):
            parser = SourceLinkParser()
            parser.feed(page.read_text(encoding="utf-8"))
            for href, label in parser.links:
                match = re.search(r"#source-(SRC-\d+)$", href, re.IGNORECASE)
                if not match:
                    continue
                linked_id = match.group(1).upper()
                if linked_id not in source_ids:
                    mismatches.append(f"{page.relative_to(ROOT)} links to absent source {linked_id}")
                if linked_id not in label.upper():
                    mismatches.append(
                        f"{page.relative_to(ROOT)} labels {label!r} but links to {linked_id}"
                    )

        self.assertEqual(mismatches, [])


if __name__ == "__main__":
    unittest.main()
