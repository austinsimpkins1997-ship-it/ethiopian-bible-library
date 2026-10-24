"""Build the offline Ge'ez Genesis reader from its archived source pages."""

from __future__ import annotations

from html.parser import HTMLParser
import hashlib
import json
from pathlib import Path
from layer_metadata import sync_layer_checksum
import re


ROOT = Path(__file__).resolve().parent
SOURCE_DIR = ROOT / "readers" / "source" / "genesis"
OUTPUT = ROOT / "readers" / "genesis-geez.json"
INDEX = ROOT / "readers" / "source" / "Octateuch-Index.html"
BASE_URL = "https://www.tau.ac.il/~hacohen/Octateuch/Genesis%20{chapter}.html"


class GenesisPage(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.paragraphs: list[list[tuple[str, str | int]]] = []
        self.paragraph: list[tuple[str, str | int]] | None = None
        self.active_link = ""
        self.title = ""
        self.in_title = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_map = dict(attrs)
        if tag.lower() == "title":
            self.in_title = True
        elif tag.lower() == "p":
            self.paragraph = []
        elif tag.lower() == "a":
            self.active_link = attrs_map.get("href") or ""
            match = re.search(r"Gen\+(\d+)%3A(\d+)", self.active_link)
            if match and self.paragraph is not None:
                if int(match.group(1)) != self.expected_chapter:
                    raise ValueError(f"Wrong chapter reference in {self.path.name}: {self.active_link}")
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


def parse_chapter(chapter: int) -> dict:
    path = SOURCE_DIR / f"Genesis_{chapter:02d}.html"
    if not path.is_file():
        raise ValueError(f"Missing archived source page: {path.name}")
    raw = path.read_bytes()
    page = GenesisPage()
    page.expected_chapter = chapter
    page.path = path
    page.feed(raw.decode("utf-8-sig"))
    if page.title.strip() != f"Genesis {chapter}":
        raise ValueError(f"Unexpected page title in {path.name}: {page.title!r}")

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
                raise ValueError(f"Non-increasing verse numbering in {path.name}")
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
        raise ValueError(f"Missing verse text in {path.name}")

    return {
        "chapter": chapter,
        "verses": verses,
        "source_url": BASE_URL.format(chapter=chapter),
        "source_sha256": hashlib.sha256(raw).hexdigest(),
    }


def main() -> None:
    index = INDEX.read_text(encoding="utf-8-sig")
    menu_chapters = [int(n) for n in re.findall(r"Octateuch/Genesis (\d+)\.html", index)]
    if menu_chapters != list(range(1, 51)):
        raise ValueError("The archived source menu does not list Genesis chapters 1–50 in order.")
    chapters = [parse_chapter(chapter) for chapter in range(1, 51)]
    total_verses = sum(len(chapter["verses"]) for chapter in chapters)
    companion_path = ROOT / "readers" / "genesis-brenton.json"
    companion = json.loads(companion_path.read_text(encoding="utf-8")) if companion_path.exists() else None
    reader = {
        "reader_id": "genesis-geez-dillmann-hacohen",
        "canon_id": "eotc-ot-01",
        "title": "Genesis — Geʽez reader",
        "language": "Geʽez (Classical Ethiopic)",
        "language_tag": "gez",
        "script_code": "Ethi",
        "ethiopic_title": "ኦሪት ፡ ዘልደት ።",
        "source_ids": ["SRC-034", "SRC-035", "SRC-036", "SRC-037", "SRC-038", "SRC-029"],
        "edition": "August Dillmann (ed.), Veteris Testamenti Aethiopici Tomus Primus, sive Octateuchus Aethiopicus, Leipzig, 1853–1855; digitized and transcribed by Ran HaCohen.",
        "edition_scope": "Historical scholarly edition. It is not represented as the current official EOTC printed edition. A later edition by Boyd appeared in 1909, but the digitizer says it stopped after Leviticus. Dillmann's critical apparatus is not included in this digital transcription.",
        "transcription_note": "The digitizer reports OCR followed by proofreading and correction of Dillmann's corrigenda, while warning that new transcription errors may remain. This archive bundles that transcription; it has not been freshly collated against Dillmann's printed pages or manuscript witnesses.",
        "editorial_signs_note": "The digitizer's Octateuch notes say round parentheses mark additions to the Septuagint, square brackets mark omissions supplied from later Ethiopic manuscripts, and paired asterisks mark rare additions by Dillmann. These signs are retained as printed in the transcription. The notes explain selected signs but do not include Dillmann's full critical apparatus; bracketed material must not be silently removed or treated as an archive emendation.",
        "chapter_structure_note": "The archived source menu and chapter files contain chapters 1–50 in order. Verse numbers follow the Septuagint; source notes warn that discontinuities may occur where the Ethiopic translation omits a Septuagint verse. Source numbering is preserved as published and has not been regularized.",
        "copyright_notice": "© Ran HaCohen. The digitized Ethiopic text is permitted to be used, copied, and distributed for noncommercial purposes without fee, provided the copyright notice and this permission notice accompany all copies. For other uses, contact the copyright owner.",
        "commercial_use": "Not granted by the cited permission notice.",
        "source_pages": "The 50 source HTML pages are archived in readers/source/genesis/; chapter SHA-256 digests are included below.",
        "chapter_count": len(chapters),
        "verse_marker_count": total_verses,
        "verification_status": "Source transcription bundled and checked for 50 ordered chapter pages and nonempty, increasing source-linked verse markers; no independent Geʽez manuscript collation.",
        "parallel_translation": companion,
        "chapters": chapters,
    }
    OUTPUT.write_text(json.dumps(reader, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    sync_layer_checksum(ROOT / "examples" / "genesis-geez-layer.json", OUTPUT)
    print(f"Built {OUTPUT.name}: {len(chapters)} chapters, {total_verses} source-linked verse markers.")


if __name__ == "__main__":
    main()
