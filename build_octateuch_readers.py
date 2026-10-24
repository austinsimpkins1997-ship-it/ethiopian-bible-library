"""Build offline Geʽez readers for six archived HaCohen Octateuch books."""

from __future__ import annotations

from html.parser import HTMLParser
import hashlib
import json
from pathlib import Path
import re

from layer_metadata import sync_layer_checksum

ROOT = Path(__file__).resolve().parent
SOURCE_ROOT = ROOT / "readers" / "source" / "octateuch-additional"
CAPTURE = SOURCE_ROOT / "capture.json"
INDEX = ROOT / "readers" / "source" / "Octateuch-Index.html"
BASE_URL = "https://www.tau.ac.il/~hacohen/Octateuch/{source}%20{chapter}.html"
RIGHTS_NOTICE = (
    "© Ran HaCohen. The digitized Ethiopic text is permitted to be used, copied, and distributed "
    "for noncommercial purposes without fee, provided the copyright notice and this permission "
    "notice accompany all copies. For other uses, contact the copyright owner."
)

BOOKS = [
    {"name": "Leviticus", "source": "Leviticus", "slug": "leviticus", "count": 27, "ref": "Lev", "canon": "eotc-ot-03", "catalogue": "eotc-003"},
    {"name": "Numbers", "source": "Numeri", "slug": "numbers", "count": 36, "ref": "Num", "canon": "eotc-ot-04", "catalogue": "eotc-004"},
    {"name": "Deuteronomy", "source": "Deuteronomium", "slug": "deuteronomy", "count": 34, "ref": "Deu", "canon": "eotc-ot-05", "catalogue": "eotc-005"},
    {"name": "Joshua", "source": "Josua", "slug": "joshua", "count": 24, "ref": "Jos", "canon": "eotc-ot-06", "catalogue": "eotc-006"},
    {"name": "Judges", "source": "Judices", "slug": "judges", "count": 21, "ref": "Jdg", "canon": "eotc-ot-07", "catalogue": "eotc-007"},
    {"name": "Ruth", "source": "Ruth", "slug": "ruth", "count": 4, "ref": "Rut", "canon": "eotc-ot-08", "catalogue": "eotc-008"},
]


class SourcePage(HTMLParser):
    def __init__(self, chapter: int, ref: str) -> None:
        super().__init__(convert_charrefs=True)
        self.expected_chapter = chapter
        # HaCohen pages alternate between BibleGateway-style references and
        # classic.net.bible.org query parameters in the later books.
        self.reference = re.compile(
            rf"(?:search={re.escape(ref)}\+(\d+)%3A(\d+)|"
            rf"(?:search|book)={re.escape(ref)}&chapter=(\d+)&verse=(\d+))"
        )
        self.paragraphs: list[list[tuple[str, str | int]]] = []
        self.paragraph: list[tuple[str, str | int]] | None = None
        self.active_link = ""
        self.title = ""
        self.in_title = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        if tag.lower() == "title":
            self.in_title = True
        elif tag.lower() == "p":
            self.paragraph = []
        elif tag.lower() == "a":
            self.active_link = attributes.get("href") or ""
            match = self.reference.search(self.active_link)
            if match and self.paragraph is not None:
                groups = match.groups()
                link_chapter, link_verse = (
                    (groups[0], groups[1]) if groups[0] is not None else (groups[2], groups[3])
                )
                if int(link_chapter) != self.expected_chapter:
                    raise ValueError(f"Wrong source link in chapter {self.expected_chapter}: {self.active_link}")
                self.paragraph.append(("verse", int(link_verse)))

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


def load_capture() -> dict[tuple[str, int], dict]:
    captured = json.loads(CAPTURE.read_text(encoding="utf-8"))
    expected_pairs = [(book["source"], chapter) for book in BOOKS for chapter in range(1, book["count"] + 1)]
    pages = captured.get("chapters", [])
    pairs = [(page.get("book"), page.get("chapter")) for page in pages]
    if pairs != expected_pairs:
        raise ValueError("The locally captured source pages do not match the complete six-book menu sequence.")
    for page in pages:
        name, chapter = page["book"], page["chapter"]
        if page.get("status") != 200 or page.get("title") != f"{name} {chapter}":
            raise ValueError(f"Source page identity/status mismatch: {name} {chapter}.")
        if page.get("url") != BASE_URL.format(source=name, chapter=chapter):
            raise ValueError(f"Source page URL mismatch: {name} {chapter}.")
    return {(page["book"], page["chapter"]): page for page in pages}


def parse_chapter(book: dict, row: dict) -> dict:
    chapter = row["chapter"]
    raw = row["html"].encode("utf-8")
    book_dir = SOURCE_ROOT / book["slug"]
    book_dir.mkdir(parents=True, exist_ok=True)
    (book_dir / f"{book['source']}_{chapter:02d}.html").write_bytes(raw)
    page = SourcePage(chapter, book["ref"])
    page.feed(raw.decode("utf-8-sig"))
    if page.title.strip() != f"{book['source']} {chapter}":
        raise ValueError(f"Unexpected page title in {book['name']} chapter {chapter}: {page.title!r}")
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
                raise ValueError(f"Non-increasing source labels in {book['name']} {chapter}.")
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
        raise ValueError(f"Missing verse text in {book['name']} chapter {chapter}.")
    source_labels = [
        int(value)
        for paragraph in page.paragraphs
        for kind, value in paragraph
        if kind == "verse"
    ]
    reader_labels = [verse["number"] for verse in verses]
    if reader_labels != source_labels:
        raise ValueError(f"Parsed verse labels differ from source links in {book['name']} {chapter}.")
    return {
        "chapter": chapter,
        "verses": verses,
        "source_url": BASE_URL.format(source=book["source"], chapter=chapter),
        "source_sha256": hashlib.sha256(raw).hexdigest(),
    }


def make_layer(book: dict, reader: dict) -> dict:
    layer_id = f"{book['slug']}-geez-dillmann-hacohen"
    layer = {
        "schema_version": 1,
        "record_id": f"https://austinsimpkins1997-ship-it.github.io/ethiopian-bible-library/id/layer/{layer_id}",
        "work_id": f"https://austinsimpkins1997-ship-it.github.io/ethiopian-bible-library/id/work/{book['slug']}-eotc",
        "labels": [
            {"value": f"{book['name']} — Geʽez reader", "language_tag": "en", "label_type": "preferred"},
        ],
        "tradition_assertions": [{
            "tradition_id": "https://austinsimpkins1997-ship-it.github.io/ethiopian-bible-library/id/tradition/eotc",
            "canon_id": f"https://austinsimpkins1997-ship-it.github.io/ethiopian-bible-library/id/canon/{book['canon']}",
            "mapping_state": "asserted_by_source",
            "evidence_source_ids": ["SRC-029"],
            "notes": f"The Church's English canon list names {book['name']}. This historical edition is not claimed to be the current official printed edition.",
        }],
        "witness": {
            "witness_id": f"https://austinsimpkins1997-ship-it.github.io/ethiopian-bible-library/id/witness/{book['slug']}-dillmann-1853-1855",
            "witness_type": "printed_edition",
            "title": "August Dillmann (ed.), Veteris Testamenti Aethiopici Tomus Primus, sive Octateuchus Aethiopicus",
            "date_statement": "1853–1855",
            "repository_or_publisher": "Leipzig edition; digital transcription by Ran HaCohen",
            "shelfmark_or_edition_id": None,
            "editorial_policy": "Historical critical edition transcription; Dillmann's critical apparatus is not included in the digitized text.",
            "source_ids": ["SRC-034", "SRC-035", "SRC-036", "SRC-064"],
        },
        "layer_type": "source_text_transcription",
        "language_tag": "gez",
        "language_name_as_recorded": "Geʽez (Classical Ethiopic)",
        "script_code": "Ethi",
        "basis_path": ["gez"],
        "agents": [
            {"role": "editor", "name": "August Dillmann", "authority_or_affiliation": None, "source_ids": ["SRC-034", "SRC-035"]},
            {"role": "digitizer", "name": "Ran HaCohen", "authority_or_affiliation": "University of Tel Aviv", "source_ids": ["SRC-036"]},
        ],
        "content_package": {
            "uri": f"../readers/{book['slug']}-geez.json",
            "media_type": "application/json",
            "sha256": "0" * 64,
            "format_version": "1",
        },
        "coverage": {
            "extent_state": "complete_for_declared_edition",
            "extent_basis": "source_inventory",
            "unit_count": reader["verse_marker_count"],
            "structure_description": f"{book['count']} source chapters; {reader['verse_marker_count']} source-linked verse markers in the digitized transcription.",
            "missing_or_lacunose_ranges": [],
            "supplements_and_editorial_signs": "The transcription's visible editorial signs are retained where represented. Dillmann's full critical apparatus is not included.",
            "numbering_policy": "Preserve source-linked labels; no renumbering or cross-witness equivalence is implied.",
        },
        "rights": {
            "status": "permission_limited",
            "statement": "Noncommercial copy and distribution only with the copyright notice and permission notice accompanying every copy; other uses require contacting the rights holder.",
            "license_id": None,
            "rights_holder": "Ran HaCohen",
            "attribution_required": True,
            "territory_or_term_limits": "Commercial rights are not granted by the cited notice.",
            "evidence_source_ids": ["SRC-036"],
        },
        "review_dimensions": [
            {
                "dimension": "chapter_or_section_sequence",
                "state": "checked_with_limits",
                "scope": f"The locally archived menu and {book['count']} captured pages were checked in order; each page identity and source-linked verse-marker list was checked against its parsed chapter.",
                "reviewer": "Archive build validation",
                "reviewed_at": "2026-10-24",
                "evidence_source_ids": ["SRC-034", "SRC-035", "SRC-064"],
                "notes": "Confirms captured page sequence and linked labels, not manuscript completeness or transcription accuracy.",
            },
            {
                "dimension": "transcription_accuracy",
                "state": "unknown",
                "scope": "No fresh collation against Dillmann's print edition or manuscript witnesses.",
                "reviewer": None,
                "reviewed_at": None,
                "evidence_source_ids": ["SRC-036"],
                "notes": "The digitizer reports OCR and proofreading and warns that transcription errors may remain.",
            },
            {
                "dimension": "rights",
                "state": "checked_with_limits",
                "scope": "Permission notice for noncommercial reuse of the digitized transcription.",
                "reviewer": None,
                "reviewed_at": "2026-10-24",
                "evidence_source_ids": ["SRC-036"],
                "notes": "This is not a grant of commercial rights.",
            },
        ],
        "publication_state": "bundled",
        "community_access_note": None,
        "additional_notes": "This bundle contains the Geʽez digitizer's transcription only. No English translation or independent manuscript collation is included.",
    }
    return layer


def main() -> None:
    if not CAPTURE.is_file():
        raise ValueError(f"Missing source capture: {CAPTURE}")
    page_map = load_capture()
    menu = INDEX.read_text(encoding="utf-8-sig")
    all_readers: list[dict] = []
    source_hash = hashlib.sha256(CAPTURE.read_bytes()).hexdigest()
    for book in BOOKS:
        menu_chapters = [
            int(n) for n in re.findall(rf"Octateuch/{re.escape(book['source'])} (\d+)\.html", menu)
        ]
        if menu_chapters != list(range(1, book["count"] + 1)):
            raise ValueError(f"The archived menu does not list {book['source']} chapters in order.")
        chapters = [parse_chapter(book, page_map[(book["source"], number)]) for number in range(1, book["count"] + 1)]
        verse_count = sum(len(chapter["verses"]) for chapter in chapters)
        reader = {
            "reader_id": f"{book['slug']}-geez-dillmann-hacohen",
            "canon_id": book["canon"],
            "title": f"{book['name']} — Geʽez reader",
            "language": "Geʽez (Classical Ethiopic)",
            "language_tag": "gez",
            "script_code": "Ethi",
            "source_ids": ["SRC-064", "SRC-034", "SRC-035", "SRC-036", "SRC-058", "SRC-059", "SRC-060"],
            "edition": "August Dillmann (ed.), Veteris Testamenti Aethiopici Tomus Primus, sive Octateuchus Aethiopicus, Leipzig, 1853–1855; digitized and transcribed by Ran HaCohen.",
            "edition_scope": "Historical scholarly edition. It is not identified as the current official EOTC printed edition. Dillmann's critical apparatus is not included in this digital transcription.",
            "transcription_note": "HaCohen reports OCR followed by proofreading and correction of Dillmann's corrigenda, while warning that new transcription errors may remain. This archive bundles that transcription without fresh collation against Dillmann's print or manuscript witnesses.",
            "editorial_signs_note": "The digitizer's Octateuch notes say round parentheses mark additions to the Septuagint, square brackets mark omissions supplied from later Ethiopic manuscripts, and paired asterisks mark rare additions by Dillmann. These signs are retained where represented; Dillmann's full critical apparatus is not included.",
            "chapter_structure_note": f"The locally archived menu and source pages contain {book['name']} chapters 1–{book['count']} in order. Verse labels follow the source links and are retained as published; numbering has not been regularized.",
            "copyright_notice": RIGHTS_NOTICE,
            "commercial_use": "Not granted by the cited permission notice.",
            "source_pages": f"The {book['count']} source HTML pages are stored in readers/source/octateuch-additional/{book['slug']}/; chapter SHA-256 digests are included below.",
            "chapter_count": len(chapters),
            "verse_marker_count": verse_count,
            "verification_status": "The archived index lists the chapters; captured pages were checked by HTTP status and page title; source-linked verse markers match the parsed labels and are nonempty. No independent Geʽez manuscript collation or English translation is claimed.",
            "chapters": chapters,
        }
        all_readers.append(reader)
        output = ROOT / "readers" / f"{book['slug']}-geez.json"
        output.write_text(json.dumps(reader, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        layer_path = ROOT / "examples" / f"{book['slug']}-geez-layer.json"
        layer_path.write_text(json.dumps(make_layer(book, reader), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        sync_layer_checksum(layer_path, output)

    local_links = []
    for book in BOOKS:
        chapter_links = ", ".join(
            f'<a href="{book["slug"]}/{book["source"]}_{chapter:02d}.html">{chapter}</a>'
            for chapter in range(1, book["count"] + 1)
        )
        local_links.append(f'<section><h2>{book["name"]}</h2><p>Chapters: {chapter_links}</p></section>')
    index_html = (
        "<!doctype html><html lang=\"en\"><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">"
        "<title>Archived Geʽez Octateuch source pages</title><main><h1>Geʽez Octateuch source pages</h1>"
        "<p>Local copies of HaCohen's Leviticus, Numeri (Numbers), Deuteronomium (Deuteronomy), Josua (Joshua), "
        "Judices (Judges), and Ruth chapter pages from Dillmann's historical edition. These are digitizer transcriptions, "
        "not independently collated texts or English translations.</p><p>" + RIGHTS_NOTICE + "</p>" + "".join(local_links) + "</main></html>\n"
    )
    (SOURCE_ROOT / "index.html").write_text(index_html, encoding="utf-8")
    (SOURCE_ROOT / "SOURCE-NOTICE.txt").write_text(
        RIGHTS_NOTICE + "\n\nSource pages are retained in their original Geʽez transcription. Their page markup and source-linked verse labels are preserved; the reader parse also retains visible editorial marks. No English translations or independent manuscript collations are included.\n",
        encoding="utf-8",
    )

    archive_path = ROOT / "archive.json"
    archive = json.loads(archive_path.read_text(encoding="utf-8"))
    source = {
        "source_id": "SRC-064",
        "source_name": "University of Tel Aviv — HaCohen Octateuch chapters (Leviticus–Ruth, locally archived)",
        "url": "readers/source/octateuch-additional/index.html",
        "inspection_and_limitations": f"Local capture of {sum(book['count'] for book in BOOKS)} chapter pages listed by the archived HaCohen Octateuch index; capture SHA-256 {source_hash}. Page titles and source-linked verse markers are validated during build. The text remains HaCohen's transcription, not an independent correction, English translation, or manuscript collation. Reuse is subject to the noncommercial permission and notice in SRC-036.",
        "archive_status": "146 source pages preserved offline; parsed reader labels checked against each page's verse links; no independent collation",
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
    gez = next(language for language in registry["languages"] if language["language_tag"] == "gez")
    additional_ids = {reader["reader_id"] for reader in all_readers}
    gez["records"] = [record for record in gez["records"] if record.get("reader_id") not in additional_ids]
    for reader in all_readers:
        gez["records"].append({
            "canon_id": reader["canon_id"],
            "reader_id": reader["reader_id"],
            "layer_role": "source_text_transcription",
            "status": "bundled",
            "basis_language_tag": "gez",
            "basis_description": "Historical Dillmann Geʽez edition transcription; no fresh collation or English translation is claimed.",
            "rights_status": "noncommercial_with_required_notice",
            "source_ids": ["SRC-034", "SRC-035", "SRC-036", "SRC-064"],
        })
    gez["records"].sort(key=lambda record: (record["canon_id"], record.get("reader_id", "")))
    gez["source_ids"] = sorted(set(gez["source_ids"] + ["SRC-064"]))
    registry["coverage_statement"] = (
        "This prototype records bundled Geʽez source transcriptions for Genesis, Exodus, Leviticus, Numbers, "
        "Deuteronomy, Joshua, Judges, Ruth, and Jubilees, plus a historical Greek-to-English Genesis companion. "
        "It also records scoped Eritrean language/script profiles and unbundled Bible corpus leads. Tigrinya, Tigre, "
        "Kunama, Blin, and Saho leads are not bundled and do not establish Eritrean Orthodox canon coverage. "
        "Script profiles reflect dated cited sources and may vary by region and witness. This is not global language or canon coverage."
    )
    registry_path.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Built {len(all_readers)} additional Geez readers from {sum(book['count'] for book in BOOKS)} chapters; capture SHA-256 {source_hash}.")


if __name__ == "__main__":
    main()
