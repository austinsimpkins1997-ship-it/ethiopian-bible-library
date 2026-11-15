from pathlib import Path
from html.parser import HTMLParser
import unittest

ROOT = Path(__file__).resolve().parents[1]

class LayoutParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.sections = []
        self.disclosures = []
        self.ids = []
    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if attributes.get("id"):
            self.ids.append(attributes["id"])
        if tag == "section" and attributes.get("id"):
            self.sections.append(attributes["id"])
        if tag == "details" and "section-disclosure" in attributes.get("class", "").split():
            self.disclosures.append(attributes)

class ReaderFirstLayoutTests(unittest.TestCase):
    def test_reader_precedes_catalogue_and_research(self):
        parser = LayoutParser()
        parser.feed((ROOT / "index.html").read_text(encoding="utf-8"))
        self.assertLess(parser.sections.index("reader"), parser.sections.index("library"))
        self.assertEqual(len(parser.ids), len(set(parser.ids)), "anchors must remain unique")
        self.assertEqual(len(parser.disclosures), 7)
        self.assertTrue(all("open" not in item for item in parser.disclosures))
        for name in ("sources", "canon-coverage", "language-coverage", "studies", "related", "about"):
            self.assertIn(name, parser.sections)
    def test_read_aloud_assets_are_available_offline(self):
        worker = (ROOT / "sw.js").read_text(encoding="utf-8")
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        for name in ("reader-audio.js", "reader-first.css"):
            self.assertIn(name, worker)
            self.assertIn(name, html)
            self.assertTrue((ROOT / name).is_file())
        self.assertIn('id="reader-audio-play"', html)
        self.assertIn("localService === true", (ROOT / "reader-audio.js").read_text(encoding="utf-8"))

if __name__ == "__main__":
    unittest.main()
