"""Build a source-faithful offline Exodus reader from archived HaCohen pages."""

from __future__ import annotations

from html.parser import HTMLParser
import hashlib
import json
from pathlib import Path
import re
from layer_metadata import sync_layer_checksum

ROOT = Path(__file__).resolve().parent
SOURCE_DIR = ROOT / "readers" / "source" / "exodus"
CAPTURE = SOURCE_DIR / "capture.json"
OUTPUT = ROOT / "readers" / "exodus-geez.json"
INDEX = ROOT / "readers" / "source" / "Octateuch-Index.html"
BASE_URL = "https://www.tau.ac.il/~hacohen/Octateuch/Exodus%20{chapter}.html"


class ExodusPage(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.paragraphs: list[list[tuple[str, str | int]]] = []
        self.paragraph: list[tuple[str, str | int]] | None = None
        self.active_link = ""
        self.title = ""
        self.in_title = False
        self.expected_chapter = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_map = dict(attrs)
        if tag.lower() == "title":
            self.in_title = True
        elif tag.lower() == "p":
            self.paragraph = []
        elif tag.lower() == "a":
            self.active_link = attrs_map.get("href") or ""
            match = re.search(r"Ex\+(\d+)%3A(\d+)", self.active_link)
            if match and self.paragraph is not None:
                if int(match.group(1)) != self.expected_chapter:
                    raise ValueError(f"Wrong chapter reference: {self.active_link}")
                self.paragraph.append(("verse", int(match.group(2))))

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "title":
            self.in_title = False
        elif tag.lower() == "a":
            self.active_link = ""
        elif tag.lower() == "p" and self.paragraph is not None:
            self.paragraphs.append(self.paragraph)
            self.paragraph = None

    def handle_data(self, data: str) -> None:
        if self.in_title:
            self.title += data
        if self.paragraph is not None and not self.active_link:
            self.paragraph.append(("text", data))


def load_capture() -> list[dict]:
    capture = json.loads(CAPTURE.read_text(encoding="utf-8"))
    rows = capture.get("chapters", [])
    if len(rows) != 40 or [row.get("chapter") for row in rows] != list(range(1, 41)):
        raise ValueError("Captured pages must contain Exodus chapters 1–40 in order.")
    for row in rows:
        if row.get("status") != 200 or row.get("title") != f"Exodus {row['chapter']}":
            raise ValueError(f"Captured page identity/status mismatch: chapter {row.get('chapter')}.")
        if row.get("url") != BASE_URL.format(chapter=row["chapter"]):
            raise ValueError(f"Captured page URL mismatch: chapter {row.get('chapter')}.")
    return rows


def parse_chapter(row: dict) -> dict:
    chapter = row["chapter"]
    raw = row["html"].encode("utf-8")
    path = SOURCE_DIR / f"Exodus_{chapter:02d}.html"
    path.write_bytes(raw)
    page = ExodusPage()
    page.expected_chapter = chapter
    page.feed(raw.decode("utf-8-sig"))
    if page.title.strip() != f"Exodus {chapter}":
        raise ValueError(f"Unexpected page title in chapter {chapter}: {page.title!r}")
    scripture = max(page.paragraphs, key=lambda p: sum(kind == "verse" for kind, _ in p))
    verses: list[dict] = []
    current: dict | None = None
    for kind, value in scripture:
        if kind == "verse":
            number = int(value)
            if current:
                current["text"] = current["text"].strip()
                verses.append(current)
            if verses and number <= verses[-1]["number"]:
                raise ValueError(f"Non-increasing verse numbering in Exodus {chapter}.")
            current = {"number": number, "text": "", "paragraph_start": False}
        elif current:
            fragment = str(value)
            if "¶" in fragment:
                current["paragraph_start"] = True
                fragment = fragment.replace("¶", "")
            current["text"] += fragment
    if current:
        current["text"] = current["text"].strip()
        verses.append(current)
    if not verses or any(not verse["text"] for verse in verses):
        raise ValueError(f"Missing verse text in Exodus {chapter}.")
    source_labels = [int(number) for number in re.findall(r"Ex\+\d+%3A(\d+)", row["html"])]
    reader_labels = [verse["number"] for verse in verses]
    if reader_labels != source_labels:
        raise ValueError(
            f"Parsed verse labels differ from source links in Exodus {chapter}: "
            f"reader={reader_labels}, source={source_labels}."
        )
    return {
        "chapter": chapter,
        "verses": verses,
        "source_url": BASE_URL.format(chapter=chapter),
        "source_sha256": hashlib.sha256(raw).hexdigest(),
    }


def main() -> None:
    menu = INDEX.read_text(encoding="utf-8-sig")
    menu_chapters = [int(n) for n in re.findall(r"Octateuch/Exodus (\d+)\.html", menu)]
    if menu_chapters != list(range(1, 41)):
        raise ValueError("The archived source menu does not list Exodus chapters 1–40 in order.")
    chapters = [parse_chapter(row) for row in load_capture()]
    page_links = "\n".join(
        f'<li><a href="Exodus_{chapter:02d}.html">Exodus {chapter}</a></li>'
        for chapter in range(1, 41)
    )
    (SOURCE_DIR / "index.html").write_text(
        "<!doctype html><html lang=\"en\"><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">"
        "<title>Archived Geʽez Exodus source pages</title><main><h1>Geʽez Exodus source pages</h1>"
        "<p>Local copies of Ran HaCohen's 40 chapter pages from Dillmann's historical Octateuch edition. "
        "The text is a digitizer's transcription, not an independently collated edition. No English translation is included.</p>"
        "<p>© Ran HaCohen. The digitized Ethiopic text is permitted to be used, copied, and distributed for noncommercial "
        "purposes without fee, provided the copyright notice and this permission notice accompany all copies. For other uses, "
        "contact the copyright owner.</p><ul>" + page_links + "</ul></main></html>\n",
        encoding="utf-8",
    )
    verse_count = sum(len(chapter["verses"]) for chapter in chapters)
    reader = {
        "reader_id": "exodus-geez-dillmann-hacohen",
        "canon_id": "eotc-ot-02",
        "title": "Exodus — Geʽez reader",
        "language": "Geʽez (Classical Ethiopic)",
        "language_tag": "gez",
        "script_code": "Ethi",
        "ethiopic_title": "ኦሪት ፡ ዘጽአት ።",
        "source_ids": ["SRC-061", "SRC-034", "SRC-035", "SRC-036", "SRC-058", "SRC-059"],
        "edition": "August Dillmann (ed.), Veteris Testamenti Aethiopici Tomus Primus, sive Octateuchus Aethiopicus, Leipzig, 1853–1855; digitized and transcribed by Ran HaCohen.",
        "edition_scope": "Historical scholarly edition. It is not identified as the current official EOTC printed edition. Dillmann's critical apparatus is not included in this digital transcription.",
        "transcription_note": "HaCohen reports OCR followed by proofreading and correction of Dillmann's corrigenda, while warning that new transcription errors may remain. This archive bundles that transcription without fresh collation against Dillmann's print or manuscript witnesses.",
        "editorial_signs_note": "The digitizer's Octateuch notes say round parentheses mark additions to the Septuagint, square brackets mark omissions supplied from later Ethiopic manuscripts, and paired asterisks mark rare additions by Dillmann. These signs are retained where represented in the transcription; no editorial signs have been silently removed. Dillmann's full critical apparatus is not included.",
        "chapter_structure_note": "The locally archived menu and captured source pages contain Exodus chapters 1–40 in order. Verse labels follow the source links and are retained as published; numbering has not been regularized.",
        "copyright_notice": "© Ran HaCohen. The digitized Ethiopic text is permitted to be used, copied, and distributed for noncommercial purposes without fee, provided the copyright notice and this permission notice accompany all copies. For other uses, contact the copyright owner.",
        "commercial_use": "Not granted by the cited permission notice.",
        "source_pages": "The 40 source HTML pages are archived in readers/source/exodus/; chapter SHA-256 digests are included below.",
        "chapter_count": len(chapters),
        "verse_marker_count": verse_count,
        "verification_status": "The archived index lists 40 chapters; captured pages are verified by HTTP status and page title; source-linked verse markers are increasing and nonempty. No independent Geʽez manuscript collation or English translation is claimed.",
        "chapters": chapters,
    }
    OUTPUT.write_text(json.dumps(reader, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    archive_path = ROOT / "archive.json"
    archive = json.loads(archive_path.read_text(encoding="utf-8"))
    capture_hash = hashlib.sha256(CAPTURE.read_bytes()).hexdigest()
    source = {
        "source_id": "SRC-061",
        "source_name": "University of Tel Aviv — HaCohen Octateuch Exodus chapter pages (locally archived)",
        "url": "readers/source/exodus/index.html",
        "inspection_and_limitations": f"Local capture of the 40 chapter pages linked by the archived HaCohen Octateuch index; capture SHA-256 {capture_hash}. Pages retain the digitizer's Geʽez transcription and visible editorial marks. The capture is not a new translation, manuscript collation, or independent correction of the digitizer's text. Reuse is subject to the noncommercial permission and notice in SRC-036.",
        "archive_status": "All 40 source pages preserved offline; source transcription, not independently collated",
    }
    sources = archive.setdefault("sources", [])
    existing = next((item for item in sources if item.get("source_id") == source["source_id"]), None)
    if existing:
        sources[sources.index(existing)] = source
    else:
        sources.append(source)
    archive_path.write_text(json.dumps(archive, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    registry_path = ROOT / "translation-registry.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    geez = next(language for language in registry["languages"] if language["language_tag"] == "gez")
    reader_id = reader["reader_id"]
    geez["records"] = [item for item in geez["records"] if item.get("reader_id") != reader_id]
    geez["records"].append({
        "canon_id": reader["canon_id"],
        "reader_id": reader_id,
        "layer_role": "source_text_transcription",
        "status": "bundled",
        "basis_language_tag": "gez",
        "basis_description": "Historical Dillmann Geʽez edition transcription; no fresh collation or English translation is claimed.",
        "rights_status": "noncommercial_with_required_notice",
        "source_ids": ["SRC-034", "SRC-035", "SRC-036", "SRC-058", "SRC-059", "SRC-061"],
    })
    geez["records"].sort(key=lambda item: (item["canon_id"], item.get("reader_id", "")))
    geez["source_ids"] = sorted(set(geez["source_ids"] + ["SRC-061"]))
    registry_path.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    sync_layer_checksum(ROOT / "examples" / "exodus-geez-layer.json", OUTPUT)
    print(f"Built {OUTPUT.name}: {len(chapters)} chapters, {verse_count} source-linked verse markers.")


if __name__ == "__main__":
    main()
