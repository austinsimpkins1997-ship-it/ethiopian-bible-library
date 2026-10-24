"""Build a source-preserving reader from the locally archived TAU Psalter pages."""

from __future__ import annotations

import hashlib
import json
import re
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCE_DIR = ROOT / "readers" / "source" / "psalms-tau-2015"
OUTPUT = ROOT / "readers" / "psalms-geez-ludolf.json"


class PsalmPage(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.paragraphs: list[dict] = []
        self.paragraph: dict | None = None
        self.marker_depth = 0
        self.title = ""
        self.in_title = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = dict(attrs)
        if tag == "title":
            self.in_title = True
        elif tag == "p":
            self.paragraph = {"text": "", "markers": []}
            self.paragraphs.append(self.paragraph)
        elif tag == "span" and "font-size:70%" in (attrs_dict.get("style") or ""):
            self.marker_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self.in_title = False
        elif tag == "span" and self.marker_depth:
            self.marker_depth -= 1
        elif tag == "p":
            self.paragraph = None

    def handle_data(self, data: str) -> None:
        if self.in_title:
            self.title += data
        if self.paragraph is not None:
            self.paragraph["text"] += data
            if self.marker_depth and data.strip():
                self.paragraph["markers"].append(data.strip())


def clean(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def main() -> None:
    files = sorted(SOURCE_DIR.glob("PsalmNrR-*.html"))
    if [f.name for f in files] != [f"PsalmNrR-{i:03}.html" for i in range(1, 152)]:
        raise ValueError("Expected the complete local sequence PsalmNrR-001 through -151.")
    chapters = []
    all_labels: dict[str, list[str]] = {}
    for expected, path in enumerate(files, 1):
        raw = path.read_bytes()
        parser = PsalmPage()
        parser.feed(raw.decode("utf-8"))
        if clean(parser.title) != f"Psalmus {expected}":
            raise ValueError(f"Unexpected page title in {path.name}: {parser.title!r}")
        verses: list[dict[str, str]] = []
        headings: list[str] = []
        last = None
        for paragraph in parser.paragraphs:
            text = clean(paragraph["text"])
            markers = paragraph["markers"]
            if len(markers) > 1:
                raise ValueError(f"Multiple verse markers in one paragraph: {path.name}")
            if not text:
                continue
            if markers:
                label = clean(markers[0])
                # Remove marker from the paragraph text, preserving the source verse wording.
                body = clean(re.sub(rf"(?<!\w){re.escape(label)}(?!\w)", "", text, count=1))
                # The first numeric chapter link is not in a marker span; the first marker is.
                body = re.sub(rf"^\s*{expected}\s+", "", body, count=1)
                if not body:
                    raise ValueError(f"Empty numbered text {expected}:{label}")
                verses.append({"number": label, "text": body})
                last = verses[-1]
                all_labels.setdefault(str(expected), []).append(label)
            elif last is not None:
                last["text"] = clean(last["text"] + " " + text)
            elif not text.startswith("Nr. Vers."):
                # Retain page-specific superscriptions/section headings; discard only the
                # repeated edition's numbering-control paragraph.
                headings.append(text)
        if not verses:
            raise ValueError(f"No source-numbered text found in Psalm {expected}")
        # The page's Sacred Texts hyperlink supplies a chapter number, not verse text.
        # Retain only non-global headings; common book title is edition chrome.
        headings = [h for h in headings if h != "መዝሙራት ፡ ዘዳዊት ።"]
        headings = [re.sub(rf"^\s*{expected}\s+", "", h, count=1) for h in headings]
        chapters.append({
            "chapter": expected,
            "title": f"Psalm {expected}",
            "heading": headings,
            "verses": verses,
            "source_url": f"https://www.tau.ac.il/~hacohen/Psalm/PsalmNrR%20{expected}.html",
            "source_sha256": hashlib.sha256(raw).hexdigest(),
        })
    irregular = []
    for chapter in chapters:
        labels = [v["number"] for v in chapter["verses"]]
        numeric = [int(label) for label in labels if label.isdigit()]
        if len(numeric) != len(labels) or numeric != list(range(numeric[0], numeric[0] + len(numeric))):
            irregular.append({"chapter": chapter["chapter"], "labels": labels})
    reader = {
        "reader_id": "psalms-geez-ludolf-hacohen",
        "canon_id": "eotc-ot-23",
        "title": "Psalms — Geʽez Ludolf reader",
        "language": "Geʽez (Classical Ethiopic)",
        "language_tag": "gez",
        "script_code": "Ethi",
        "section_label": "Psalm",
        "section_unit_plural": "psalms",
        "source_ids": ["SRC-029", "SRC-036", "SRC-058", "SRC-059", "SRC-067", "SRC-068", "SRC-069"],
        "edition": "Hiob Ludolf (ed.), Psalterium Davidis aethiopice et latine (Frankfurt am Main, 1701), digitized and retyped by Ran HaCohen.",
        "edition_scope": "Geʽez Psalter transcription presented by the Tel Aviv University source. This reader follows the site's Rahlfs Septuagint numbering page sequence (151 pages); it is not a critical edition or an independent manuscript collation.",
        "transcription_note": "TAU describes the text as retyped from Ludolf's edition, proofread, and corrected, while warning that new typographical errors may remain. This archive preserves the captured source text and has not independently collated it against the 1701 print or manuscripts.",
        "chapter_structure_note": "151 source pages are preserved as reader chapters. Verse labels are kept as printed in the Rahlfs-numbered pages; gaps and duplicate labels are not normalized. Chapter headings/superscriptions are retained where separable from the verse paragraphs.",
        "copyright_notice": "© Ran HaCohen. The digitized Ethiopic text may be copied and distributed for noncommercial purposes only when the copyright and permission notice accompany every copy. Other uses require contacting the copyright owner.",
        "commercial_use": "Not granted by the cited permission notice.",
        "source_pages": "Local capture of all 151 TAU Rahlfs-numbered page URLs; per-page SHA-256 digests are stored below and in the capture manifest.",
        "chapter_count": len(chapters),
        "verse_marker_count": sum(len(ch["verses"]) for ch in chapters),
        "verification_status": f"Local structural audit: {len(chapters)} ordered pages, {sum(len(ch['verses']) for ch in chapters)} nonempty source-numbered units. Source label irregularities are retained in place. No independent transcription collation; see source limits and capture notice.",
        "numbering_irregularities": irregular,
        "chapters": chapters,
    }
    OUTPUT.write_text(json.dumps(reader, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Built {OUTPUT.name}: {len(chapters)} pages, {reader['verse_marker_count']} units, {len(irregular)} numbering-irregular chapters.")


if __name__ == "__main__":
    main()
