"""Build research-only Gamo reader layers from the licensed eBible HTML witness.

This keeps publisher order, printed verse labels, chapter headings, and linked
reference notes. It does not translate titles, map this 66-entry edition to the
EOTC catalogue, or assert textual accuracy/completeness beyond the captured files.
"""

from __future__ import annotations

from html.parser import HTMLParser
from html import escape
import hashlib
import json
from pathlib import Path
import re
import re
import zipfile

from coverage_summary import build_coverage_statement


ROOT = Path(__file__).resolve().parent
SOURCE_ZIP = ROOT / "readers" / "source" / "gamo" / "gmve-html-pages.zip"
OUTPUT_DIR = ROOT / "readers"
MENU_JSON_PATH = ROOT / "research" / "gamo-menu.json"
MENU_HTML_PATH = ROOT / "research" / "gamo-menu.html"
ARCHIVE_PATH = ROOT / "archive.json"
REGISTRY_PATH = ROOT / "translation-registry.json"
SOURCE_ID = "SRC-178"
EDITION_ID = "GMVETW / gmve"
SOURCE_ZIP_SHA256 = "a61457709d70b19016534807e381d9a13cc813cf890b8a128874888f4ca0bd58"
UPSTREAM_ZIP_SHA256 = "57d4266f4cfa9606b340d30a2bc06101f5bfb396f69d154e32555d711e33378d"
UPSTREAM_ZIP_URL = "https://ebible.org/Scriptures/gmve_html.zip"
LICENSE_URL = "https://creativecommons.org/licenses/by-sa/4.0/"
SOURCE_PAGE_URL = "https://ebible.org/Bible/details.php?id=gmve"
MENU_URL = "https://ebible.org/gmve/"
LICENSE_ID = "CC-BY-SA-4.0"
COPYRIGHT = "© 2024 The Word for the World International. Gamo translation contributed by The Word for the World Northern Africa. Source: eBible.org, GMVETW / gmve, Gamo Bible (ጌሻ ማጻፋ), Ethiopic script. Licensed CC BY-SA 4.0. This archive converted HTML structure to JSON and whitespace for display; those changes do not imply publisher endorsement."
BLOCK_TAGS = {"div", "p", "br", "li", "blockquote"}
HEADING_CLASSES = {"s", "ms", "mr", "r"}
VOID_TAGS = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}


class Node:
    def __init__(self, tag: str, attrs: list[tuple[str, str | None]] | None = None):
        self.tag = tag
        self.attrs = dict(attrs or [])
        self.children: list[Node | str] = []

    def text(self) -> str:
        return "".join(child if isinstance(child, str) else child.text() for child in self.children)

    def classes(self) -> set[str]:
        return set((self.attrs.get("class") or "").split())


class TreeParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = Node("document")
        self.stack = [self.root]

    def handle_starttag(self, tag, attrs):
        node = Node(tag.lower(), attrs)
        self.stack[-1].children.append(node)
        if tag.lower() not in VOID_TAGS:
            self.stack.append(node)

    def handle_startendtag(self, tag, attrs):
        self.stack[-1].children.append(Node(tag.lower(), attrs))

    def handle_endtag(self, tag):
        tag = tag.lower()
        for index in range(len(self.stack) - 1, 0, -1):
            if self.stack[index].tag == tag:
                del self.stack[index:]
                break

    def handle_data(self, data):
        if data:
            self.stack[-1].children.append(data)


def parse_html(raw: bytes) -> Node:
    parser = TreeParser()
    parser.feed(raw.decode("utf-8-sig"))
    parser.close()
    return parser.root


def walk(node: Node):
    yield node
    for child in node.children:
        if isinstance(child, Node):
            yield from walk(child)


def find(node: Node, predicate) -> list[Node]:
    return [item for item in walk(node) if predicate(item)]


def normalized(text: str) -> str:
    text = text.replace("\xa0", " ").replace("\u200b", "")
    text = re.sub(r"[ \t\r\f\v]+", " ", text)
    text = re.sub(r" *\n+ *", "\n", text)
    return text.strip()


def read_book_menu(root: Node) -> list[dict]:
    index = parse_html(root)
    menu_nodes = find(index, lambda n: n.tag == "div" and "bookList" in n.classes())
    if len(menu_nodes) != 1:
        raise ValueError("Expected exactly one publisher bookList in index.htm.")
    entries = []
    for anchor in find(menu_nodes[0], lambda n: n.tag == "a"):
        href = (anchor.attrs.get("href") or "").split("?")[0]
        # The publisher's front page links directly to each book's chapter 1,
        # with Psalm using a three-digit chapter number (PSA001.htm).
        match = re.fullmatch(r"([A-Z0-9]{3})(?:01|001)\.htm", href)
        title = normalized(anchor.text())
        if match and title:
            entries.append({"code": match.group(1), "source_title": title, "position": len(entries) + 1})
    if len(entries) != 66 or len({row["code"] for row in entries}) != 66:
        raise ValueError(f"Expected 66 unique source menu book links, found {len(entries)}.")
    return entries


def chapter_links(book_index: Node, code: str) -> list[tuple[int, str, str]]:
    result = []
    for anchor in find(book_index, lambda n: n.tag == "a"):
        href = (anchor.attrs.get("href") or "").split("?")[0]
        match = re.fullmatch(re.escape(code) + r"(\d{2,3})\.htm", href)
        if not match:
            continue
        number = int(match.group(1))
        if number == 0:
            continue
        result.append((number, href, normalized(anchor.text())))
    if not result:
        raise ValueError(f"No numbered chapter links in {code}.htm.")
    result.sort(key=lambda row: row[0])
    observed = [row[0] for row in result]
    if observed != list(range(1, observed[-1] + 1)):
        raise ValueError(f"Non-contiguous chapter links for {code}: {observed!r}.")
    if len({row[1] for row in result}) != len(result):
        raise ValueError(f"Duplicate chapter page links for {code}.")
    return result


def extract_notes(main: Node) -> list[dict]:
    notes = []
    for paragraph in find(main, lambda n: n.tag == "p" and "x" in n.classes()):
        backrefs = find(paragraph, lambda n: n.tag == "a" and "notebackref" in n.classes())
        crossrefs = find(paragraph, lambda n: n.tag == "span" and "xt" in n.classes())
        note_text = normalized(" ".join(item.text() for item in crossrefs))
        if not note_text:
            # Retain the recorded back-reference even when this HTML has no note body.
            note_text = normalized(paragraph.text())
        backref = normalized(backrefs[0].text()) if backrefs else ""
        notes.append({
            "verse": backref or "Unlinked source note",
            "marker": "cross-reference" if crossrefs else "source note",
            "text": note_text,
            "source_reference": (paragraph.attrs.get("id") or "").removeprefix("FN"),
        })
    return notes


def extract_chapter(raw: bytes, code: str, expected_number: int) -> tuple[str, list[str], list[dict], list[dict]]:
    document = parse_html(raw)
    main_nodes = find(document, lambda n: n.tag == "div" and "main" in n.classes())
    if len(main_nodes) != 1:
        raise ValueError(f"Expected one .main container in {code}{expected_number}.")
    main = main_nodes[0]
    title_nodes = find(document, lambda n: n.tag == "title")
    page_title = normalized(title_nodes[0].text()) if title_nodes else ""
    chapter_labels = find(main, lambda n: n.tag == "div" and "chapterlabel" in n.classes() and n.attrs.get("id") == "V0")
    if len(chapter_labels) != 1:
        raise ValueError(f"Missing or ambiguous V0 chapter label in {code}{expected_number}.")
    chapter_label = normalized(chapter_labels[0].text())
    if chapter_label != str(expected_number):
        raise ValueError(f"Chapter page {code}{expected_number} labels itself {chapter_label!r}.")

    headings = []
    for heading in find(main, lambda n: n.tag == "div" and bool(n.classes() & HEADING_CLASSES)):
        # Exclude the book-level overview, which precedes the explicit V0 chapter label.
        if heading is chapter_labels[0] or "chapterlabel" in heading.classes():
            continue
        text = normalized(heading.text())
        if text and text not in headings:
            headings.append(text)

    # Traverse only the main body after the chapter label. Verse labels come
    # from the literal inline span content (e.g. 6-7), not from generated IDs.
    events: list[tuple[str, str | Node]] = []

    def append_after_label(node: Node, found_label: bool = False) -> bool:
        for child in node.children:
            if isinstance(child, str):
                if found_label and child:
                    events.append(("text", child))
                continue
            if child is chapter_labels[0]:
                found_label = True
                continue
            if found_label:
                events.append(("start", child))
            found_label = append_after_label(child, found_label)
            if found_label:
                events.append(("end", child))
        return found_label

    append_after_label(main)
    units: list[dict] = []
    current: dict | None = None
    fragments: list[str] = []
    skip_notemark = 0
    skip_verse_label = 0

    def flush():
        nonlocal current, fragments
        if current is None:
            return
        current["text"] = normalized("".join(fragments))
        if not current["text"]:
            raise ValueError(f"Empty verse text at {code} {expected_number}:{current['source_marker']}.")
        units.append(current)
        current = None
        fragments = []

    for kind, value in events:
        if kind == "text":
            if current is not None and skip_notemark == 0 and skip_verse_label == 0:
                fragments.append(value)  # type: ignore[arg-type]
            continue
        element = value
        assert isinstance(element, Node)
        if kind == "start":
            if element.tag == "span" and "verse" in element.classes():
                flush()
                marker_text = normalized(element.text())
                if not marker_text:
                    raise ValueError(f"Verse marker has no displayed label in {code} {expected_number}.")
                element_id = element.attrs.get("id")
                current = {"source_marker": marker_text, "source_element_id": element_id}
                skip_notemark = 0
                skip_verse_label = 1
                continue
            if skip_verse_label:
                skip_verse_label += 1
                continue
            if current is not None and element.tag == "a" and "notemark" in element.classes():
                skip_notemark += 1
                continue
            if current is not None and element.tag == "div" and fragments:
                fragments.append("\n")
            if current is not None and element.tag == "br":
                fragments.append("\n")
        else:
            if skip_verse_label:
                skip_verse_label -= 1
                continue
            if current is not None and element.tag == "a" and "notemark" in element.classes() and skip_notemark:
                skip_notemark -= 1
    flush()
    if not units:
        raise ValueError(f"No source verse spans in {code} {expected_number}.")
    markers = [unit["source_marker"] for unit in units]
    ids = [unit["source_element_id"] for unit in units]
    if len(set(ids)) != len(ids):
        raise ValueError(f"Duplicate source verse element IDs in {code} {expected_number}.")
    for order, unit in enumerate(units, start=1):
        unit["unit_order"] = order
    return page_title, headings, units, extract_notes(main)


def build_readers() -> tuple[list[dict], list[dict], dict[str, dict]]:
    raw_zip = SOURCE_ZIP.read_bytes()
    digest = hashlib.sha256(raw_zip).hexdigest()
    if digest != SOURCE_ZIP_SHA256:
        raise ValueError(f"Captured HTML source zip checksum mismatch: {digest}.")
    with zipfile.ZipFile(SOURCE_ZIP) as source:
        pages = {Path(name).name: source.read(name) for name in source.namelist() if name.lower().endswith((".htm", ".html"))}
    if len(pages) != 1323 or "index.htm" not in pages:
        raise ValueError(f"Expected 1,323 HTML pages including the menu, found {len(pages)}.")
    menu = read_book_menu(pages["index.htm"])
    readers = []
    corpora = []
    coverage = {}
    all_page_names = set(pages)
    for book in menu:
        code, source_title = book["code"], book["source_title"]
        if code + ".htm" not in pages:
            raise ValueError(f"Publisher menu link lacks its book index: {code}.htm.")
        links = chapter_links(parse_html(pages[code + ".htm"]), code)
        chapters = []
        unit_count = 0
        page_hashes = []
        for chapter_number, filename, menu_label in links:
            if filename not in pages:
                raise ValueError(f"Publisher chapter menu points to missing page {filename}.")
            page_title, headings, units, notes = extract_chapter(pages[filename], code, chapter_number)
            page_hashes.append({"page": filename, "sha256": hashlib.sha256(pages[filename]).hexdigest()})
            unit_count += len(units)
            chapters.append({
                "chapter": chapter_number,
                "source_chapter_label": str(chapter_number),
                "source_page_title": page_title,
                "heading": headings,
                "units": units,
                "notes": notes,
            })
        reader_id = f"gamo-{code.lower()}-research"
        corpus_id = f"gmvetw-{code.lower()}-research"
        readers.append({
            "reader_id": reader_id,
            "research_corpus_id": corpus_id,
            "publisher_book_code": code,
            "source_menu_position": book["position"],
            "source_title_label": source_title,
            "reader_scope": "research_witness_unmapped",
            "title": f"{source_title} — eBible.org GMVETW / gmve Gamo text",
            "display_name": f"{source_title} · Gamo (GMVETW)",
            "text_origin": "published_translation",
            "language": "Gamo (Gamotso)",
            "language_tag": "gmv",
            "language_assignment_status": "publisher_identified_gmv_gamotso_gamo",
            "script_code": "Ethi",
            "translation_id": f"gmvetw-gamo-{code.lower()}",
            "translator": "Not identified in the cited publisher edition record",
            "translation_basis_status": "unknown",
            "translation_basis_note": "The cited eBible.org edition page does not identify the source language or relay-language path. No source language or translation path is inferred.",
            "edition": "The Word for the World International, Gamo Bible (ጌሻ ማጻፋ), GMVETW / gmve; source files dated 2025-05-03; mobile HTML generated 2026-10-20.",
            "edition_scope": f"This is the Gamo edition's publisher-menu entry {book['position'] if 'position' in book else 'in source order'}; the exact source book label is {source_title!r}, publisher code {code}. Its place in other Bible or Ethiopian Orthodox Tewahedo Church catalogues is not established.",
            "rights_classification": "open_license",
            "copyright_notice": COPYRIGHT,
            "commercial_use": "The provider page grants share and adaptation rights under CC BY-SA 4.0 subject to attribution, change indication, and share-alike. This notice covers only this source-derived Gamo reader layer, not other site content or separately licensed images.",
            "license_id": LICENSE_ID,
            "license_url": LICENSE_URL,
            "chapter_count": len(chapters),
            "unit_count": unit_count,
            "unit_label": "publisher verse marker",
            "section_label": "Chapter",
            "chapter_structure_note": "Chapter pages and order follow the publisher's own book index. Displayed verse labels are preserved verbatim, including combined labels such as 6-7; they are not renumbered. Counts describe extracted source spans only.",
            "transcription_note": "Text was extracted from the captured publisher HTML into JSON. The displayed text normalizes HTML whitespace and line breaks; source marker labels are retained. Publisher cross-reference notes are preserved in chapter notes. Images, fonts, and CSS are excluded because the publisher says pictures have separate terms. The captured HTML-only source archive is retained alongside this reader.",
            "editorial_signs_note": "The reader preserves publisher verse labels and captured cross-reference note text. It does not reconstruct missing apparatus or independently interpret editorial conventions.",
            "verification_status": f"Structural extraction from the captured eBible.org GMVETW / gmve HTML snapshot: this menu entry links to {len(chapters)} consecutive chapter pages; {unit_count} nonempty verse spans retain their displayed labels; each source chapter page hash is recorded in the reader. This verifies extraction against the captured HTML package only. It does not verify translation accuracy, completeness against any print edition, manuscript agreement, or canon mapping, and is not counted as an EOTC canon reader.",
            "source_ids": ["SRC-168", "SRC-169", SOURCE_ID],
            "source_pages": f"readers/source/gamo/gmve-html-pages.zip; publisher pages {code}.htm and {code} chapter pages",
            "source_snapshot_url": UPSTREAM_ZIP_URL,
            "source_snapshot_sha256": UPSTREAM_ZIP_SHA256,
            "source_extract_sha256": digest,
            "source_page_hashes": page_hashes,
            "chapters": chapters,
        })
        corpora.append({
            "corpus_id": corpus_id,
            "title": f"{source_title} (GMVETW / gmve) — Gamo research reader",
            "reader_id": reader_id,
            "unit_count": unit_count,
            "reader_status": "bundled_research_reader",
            "canon_mapping_state": "not_mapped",
            "candidate_canon_id": None,
            "canon_mapping_note": "This source-menu entry remains a distinct research reader. No crosswalk to the EOTC 81-entry list, an 88-book tradition, or another catalogue has been verified; it is excluded from canon-linked coverage.",
            "language_description": "The provider identifies this edition as Gamo/Gamotso and associates it with language code gmv; this reader preserves the publisher's Ethiopic-script text.",
            "script_description": "Ethiopic script (Ethi), as identified by the publisher for this Gamo edition.",
            "unit_summary": f"{len(chapters)} linked chapter pages and {unit_count} nonempty publisher verse spans in this one menu entry; these are source-structure counts, not an independent completeness audit.",
            "rights_classification": "open_license",
            "rights_status": "The publisher identifies the translation as CC BY-SA 4.0 and requires attribution, clear indication of changes, and share-alike for redistributed adaptations. This converted reader is distributed under the same license. Pictures have separate terms and were excluded.",
            "license_id": LICENSE_ID,
            "license_url": LICENSE_URL,
            "review_status": "Machine-checked structural extraction only; wording and completeness have not been independently reviewed against print or another witness. Not canon-linked or included in EOTC coverage.",
            "source_ids": ["SRC-168", "SRC-169", SOURCE_ID],
            "text_origin": "published_translation",
            "language_tag": "gmv",
            "script_code": "Ethi",
            "translation_id": f"gmvetw-gamo-{code.lower()}",
            "translator": "Not identified in the cited publisher edition record",
            "translation_basis_status": "unknown",
            "translation_basis_note": "The cited eBible.org edition page does not identify the source language or relay-language path. No source language or translation path is inferred.",
            "edition_statement": f"eBible.org mobile HTML package GMVETW / gmve, publisher menu label {source_title!r}, code {code}; files dated 2025-05-03.",
        })
        coverage[code] = {"chapter_count": len(chapters), "unit_count": unit_count}
    return readers, corpora, coverage


def build() -> None:
    readers, corpora, coverage = build_readers()
    for reader in readers:
        path = OUTPUT_DIR / f"{reader['reader_id']}.json"
        path.write_text(json.dumps(reader, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    menu = json.loads(MENU_JSON_PATH.read_text(encoding="utf-8"))
    menu.update({
        "raw_html_retained": False,
        "scripture_text_retained": False,
        "scope_note": (
            "The original online landing-page response is not retained. This index preserves its 66 visible title labels; "
            "the separate mobile HTML package is archived as a media-free source capture. Each source label is linked by "
            "publisher book code to its locally bundled Gamo research reader. The labels are not translated, and no EOTC "
            "81-entry or other canon crosswalk is assigned."
        ),
        "entries": [{
            "position": reader["source_menu_position"],
            "source_title_label": reader["source_title_label"],
            "publisher_book_code": reader["publisher_book_code"],
            "reader_id": reader["reader_id"],
            "chapter_count": reader["chapter_count"],
            "unit_count": reader["unit_count"],
        } for reader in readers],
    })
    MENU_JSON_PATH.write_text(json.dumps(menu, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    page = MENU_HTML_PATH.read_text(encoding="utf-8")
    page = page.replace(
        "This is a menu transcription, not the scripture text. Raw HTML was not retained, no chapter sequence was audited, the labels have not been translated here, and no title is crosswalked to the Ethiopian Orthodox Tewahedo Church’s 81-entry list. The provider page remains the authority for current menu content.",
        "The original online landing-page response is not retained. A separate, media-free capture of the publisher's mobile HTML package is archived. Each source label below opens its corresponding locally bundled Gamo research reader; labels remain untranslated and no title is crosswalked to the Ethiopian Orthodox Tewahedo Church's 81-entry list.",
    )
    page = page.replace(
        '<a href="https://ebible.org/gmve/">Open the publisher’s Gamo menu</a>',
        '<a href="../index.html?reader=gamo-gen-research#reader">Open a Gamo reader</a>\n    <a href="https://ebible.org/gmve/">Open the publisher’s Gamo menu</a>',
    )
    page = page.replace("<h2>66 visible title labels, in source order</h2>", "<h2>66 source labels with local research readers</h2>")
    list_markup = "\n".join(
        f'    <li class="source-label"><span>{escape(row["source_title_label"])}</span> '
        f'<a href="../index.html?reader={escape(row["reader_id"])}#reader">Open reader · {escape(row["chapter_count"] and str(row["chapter_count"]))} chapters</a></li>'
        for row in menu["entries"]
    )
    page, replacements = re.subn(
        r'(<ol lang="gmv" translate="no">).*?(</ol>)',
        lambda match: match.group(1) + "\n" + list_markup + "\n  " + match.group(2),
        page,
        count=1,
        flags=re.DOTALL,
    )
    if replacements != 1:
        raise ValueError("Could not update the Gamo menu page's source-label list.")
    MENU_HTML_PATH.write_text(page, encoding="utf-8", newline="\n")

    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    research = [row for row in registry.get("research_corpora", []) if not row.get("corpus_id", "").startswith("gmvetw-")]
    registry["research_corpora"] = sorted(research + corpora, key=lambda row: row["corpus_id"])
    for language in registry.get("languages", []):
        if language.get("language_tag") == "gmv":
            language["source_ids"] = sorted(set(language.get("source_ids", [])) | {SOURCE_ID})
            language["script_profile_note"] = "The eBible.org GMVETW / gmve edition identifies Gamo/Gamotso (gmv) and Ethiopic script. This identifies that witness only and does not establish all Gamo orthographic practice or a catalogue crosswalk."
            # Research corpora stay in the dedicated research_corpora list; the
            # layer schema requires a canon ID, so do not misstate these as canon-linked layers.
    registry["coverage_statement"] = build_coverage_statement(registry, json.loads((ROOT / "canon-registry.json").read_text(encoding="utf-8")))
    REGISTRY_PATH.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    archive = json.loads(ARCHIVE_PATH.read_text(encoding="utf-8"))
    source = next((row for row in archive.get("sources", []) if row.get("source_id") == SOURCE_ID), None)
    if source is None:
        source = {"source_id": SOURCE_ID}
        archive.setdefault("sources", []).append(source)
    source.update({
        "source_name": "eBible.org — Gamo Bible (GMVETW / gmve), mobile HTML source package capture",
        "url": SOURCE_PAGE_URL,
        "inspection_and_limitations": (
            "The official edition page identifies Gamo/Gamotso [gmv], title ጌሻ ማጻፋ / Gamo Bible, ID GMVETW or gmve, "
            "Ethiopic script, © 2024 The Word for the World International, contributor The Word for the World Northern Africa, "
            "and CC BY-SA 4.0 terms requiring attribution, change notice, and share-alike. It states that pictures have separate terms. "
            f"The upstream mobile HTML archive was captured at {UPSTREAM_ZIP_URL} (SHA-256 {UPSTREAM_ZIP_SHA256}); the site retains "
            f"only its 1,323 HTML pages (SHA-256 {hashlib.sha256(SOURCE_ZIP.read_bytes()).hexdigest()}) and excludes images, fonts, and CSS. "
            f"The captured publisher menu lists {len(coverage)} entries; their linked pages produce the per-book extraction counts. "
            "This is not an independent accuracy, print-completeness, or EOTC canon-crosswalk review."
        ),
        "archive_status": "Rights-scoped HTML-only source capture and structurally extracted Gamo research readers are stored locally; images, fonts, and CSS excluded; no EOTC canon mapping asserted",
    })
    source_by_id = {row.get("source_id"): row for row in archive.get("sources", [])}
    if "SRC-169" in source_by_id:
        source_by_id["SRC-169"].update({
            "inspection_and_limitations": (
                "The provider landing-page navigation displays 66 title links. Their visible labels and order are recorded in "
                "research/gamo-menu.html and .json. The response body of that landing page was not retained. A separate "
                "mobile HTML package and its index/chapter pages are preserved under source record SRC-178. This menu count "
                "does not itself prove textual accuracy, print completeness, translation basis, or an EOTC 81-book crosswalk."
            ),
            "archive_status": "66 online landing-page labels recorded; matching mobile package HTML is separately captured under SRC-178; no canon mapping inferred",
        })
    if "SRC-171" in source_by_id:
        source_by_id["SRC-171"].update({
            "inspection_and_limitations": (
                "This local page preserves the 66 visible labels transcribed from https://ebible.org/gmve/. Its JSON also "
                "records the matching publisher book codes and links to the corresponding locally bundled research readers. "
                "The original landing-page response is not retained; the separately downloaded mobile package pages are in "
                "readers/source/gamo/gmve-html-pages.zip. Labels are not translated and no EOTC or other canon crosswalk is assigned."
            ),
            "archive_status": "Local 66-title navigation and reader index; book-code links derived from captured publisher package; no canon crosswalk",
        })
    archive["sources"] = sorted(archive["sources"], key=lambda row: row.get("source_id", ""))
    ARCHIVE_PATH.write_text(json.dumps(archive, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Built {len(readers)} unmapped Gamo research readers; {sum(x['chapter_count'] for x in readers)} chapter pages; {sum(x['unit_count'] for x in readers)} nonempty source verse spans.")
    print("Per-book structural counts:", json.dumps(coverage, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    build()
