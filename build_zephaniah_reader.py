"""Build the locally captured TAU Geʽez Zephaniah source-transcription reader."""

from __future__ import annotations

import copy
import hashlib
import json
import re
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CAPTURE = ROOT / "readers" / "source" / "zephaniah-tau-2022"
READER_PATH = ROOT / "readers" / "zephaniah-geez-lofgren-hacohen-tau.json"
LAYER_PATH = ROOT / "examples" / "zephaniah-geez-lofgren-hacohen-layer.json"
SOURCE_ID = "SRC-190"
CANON_ID = "eotc-ot-41"
READER_ID = "zephaniah-geez-lofgren-hacohen-tau"
BASE = "https://austinsimpkins1997-ship-it.github.io/ethiopian-bible-library/id"
CHAPTER_LABELS = {1: 18, 2: 14, 3: 20}


class ZephaniahPageParser(HTMLParser):
    """Extract only bodies following TAU's source-linked chapter/verse labels."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.current: tuple[str, int, str] | None = None
        self.parts: list[str] = []
        self.units: list[tuple[int, str, str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag != "a":
            return
        href = dict(attrs).get("href") or ""
        match = re.search(r"search=(Zeph)\+(\d+)%3A(\d+)", href)
        if match:
            self._finish()
            self.current = (match.group(1), int(match.group(2)), match.group(3))
            self.parts = []

    def handle_data(self, data: str) -> None:
        if self.current is not None:
            self.parts.append(data)

    def close(self) -> None:
        self._finish()
        super().close()

    def _finish(self) -> None:
        if self.current is None:
            return
        link_book, chapter, marker = self.current
        body = re.sub(r"\s+", " ", "".join(self.parts)).strip()
        # The source displays the linked number in the verse body; retain it
        # once in source_marker, separately from the Ethiopic wording.
        body = re.sub(rf"^{re.escape(marker)}\s+", "", body, count=1)
        self.units.append((chapter, marker, body, link_book))
        self.current = None
        self.parts = []


def _load_and_check_capture() -> tuple[dict, dict[int, list[tuple[str, str, str]]]]:
    manifest = json.loads((CAPTURE / "SOURCE-CAPTURE.json").read_text(encoding="utf-8"))
    for item in manifest["files"]:
        data = (CAPTURE / item["path"]).read_bytes()
        if (item.get("http_status") != 200
                or len(data) != item["size_bytes"]
                or hashlib.sha256(data).hexdigest() != item["sha256"]):
            raise ValueError(f"Zephaniah source capture failed its retained size/SHA/HTTP check: {item['path']}")

    by_chapter: dict[int, list[tuple[str, str, str]]] = {}
    for chapter, count in CHAPTER_LABELS.items():
        path = CAPTURE / f"zephaniah-chapter-{chapter}.html"
        parser = ZephaniahPageParser()
        parser.feed(path.read_bytes().decode("utf-8"))
        parser.close()
        labels = [(number, body, link_book) for ch, number, body, link_book in parser.units if ch == chapter]
        expected = [str(i) for i in range(1, count + 1)]
        if [number for number, _, _ in labels] != expected or any(not body for _, body, _ in labels):
            raise ValueError(f"Zephaniah chapter {chapter}: expected nonempty labels {expected}, observed {labels!r}")
        expected_link_book = "Zeph"
        if any(link_book != expected_link_book for _, _, link_book in labels):
            raise ValueError(f"Zephaniah chapter {chapter}: expected captured hyperlink target {expected_link_book}; observed {[item[2] for item in labels]!r}")
        if any(ch != chapter for ch, _, _, _ in parser.units):
            raise ValueError(f"Zephaniah chapter page {chapter} contains an unexpected chapter label.")
        by_chapter[chapter] = labels
    return manifest, by_chapter


def build() -> tuple[dict, dict]:
    manifest, by_chapter = _load_and_check_capture()
    file_map = {item["path"]: item for item in manifest["files"]}
    notice = (
        "© Ran HaCohen. For the digitized Ethiopic texts, permission to use, copy, and distribute for any "
        "NONCOMMERCIAL purpose is granted without fee, provided that the copyright notice Ran HaCohen and "
        "this permission notice appear in all copies of the text. For other uses, please contact the copyright owner."
    )
    total = sum(len(units) for units in by_chapter.values())
    source_ids = ["SRC-029", "SRC-034", "SRC-036", "SRC-157", "SRC-158", SOURCE_ID]
    chapters = [
        {
            "chapter": chapter,
            "source_marker": str(chapter),
            "source_sha256": hashlib.sha256((CAPTURE / f"zephaniah-chapter-{chapter}.html").read_bytes()).hexdigest(),
            "verses": [
                {"number": int(marker), "source_marker": marker, "source_link_target_book": link_book, "text": body}
                for marker, body, link_book in units
            ],
        }
        for chapter, units in by_chapter.items()
    ]
    pages = ", ".join(
        f"readers/source/zephaniah-tau-2022/zephaniah-chapter-{chapter}.html"
        for chapter in CHAPTER_LABELS
    )
    reader = {
        "reader_id": READER_ID,
        "text_origin": "source_transcription",
        "canon_id": CANON_ID,
        "title": "Zephaniah — Geʽez Löfgren / HaCohen transcription",
        "language": "Geʽez (Classical Ethiopic)",
        "language_tag": "gez",
        "script_code": "Ethi",
        "section_label": "Chapter",
        "source_ids": source_ids,
        "edition": "Oscar Löfgren (ed.), Jona, Nahum, Habakuk, Zephanja, Haggai, Sacharja und Maleachi äthiopisch, unter Zugrundelegung des Oxforder Ms. Huntington 625, nach mehreren Handschriften. Uppsala, 1930, Zephaniah section pp. 36–43; TAU text prepared by Ran HaCohen (March 2022).",
        "edition_scope": "The local reader transcribes the three TAU HTML text pages identified by its index as Zephaniah chapters 1–3. TAU identifies the underlying historical critical edition and states its bibliographic pages 36–43; the archive has not compared the captured digital chapter pages with that print span or manuscripts. The title-level link to the cited EOTC English list is provisional and does not establish identity with a current official EOTC edition.",
        "transcription_note": "Verse bodies are parsed from three captured TAU HTML pages. HTML whitespace is normalized to single spaces; each source-linked BibleGateway label is retained as a separate source_marker. The original pages are stored alongside this reader and checked by SHA-256. No wording was translated, silently emended, renumbered, or aligned to another witness.",
        "editorial_signs_note": "Visible Geʽez letters, punctuation, and editorial signs are retained in the extracted text. Image pages and Löfgren's critical apparatus are not bundled. The retained source HTML is the extraction authority for this reader.",
        "chapter_structure_note": "The TAU index offers text pages numbered 1–3. The captured pages contain displayed linked numbers 1–18, 1–14, and 1–20 respectively (52 total). All page links target the matching Zephaniah chapter. These are observed page labels, not a verified alignment to another numbering system or evidence of print-edition completeness.",
        "rights_classification": "permission_limited",
        "copyright_notice": notice,
        "commercial_use": "TAU's general notice grants noncommercial use only when its copyright and permission notice accompany every copy; other uses require contacting the rights holder. TAU credits Ran HaCohen with preparing the text. No separate commercial grant or open license is asserted here.",
        "license_id": None,
        "license_url": None,
        "chapter_count": len(chapters),
        "unit_count": total,
        "unit_label": "displayed linked number; target book retained per unit",
        "source_numbered_unit_count": total,
        "source_unnumbered_unit_count": 0,
        "verification_status": "Automated local validation confirms all six retained source HTML assets match the response status, byte length, and SHA-256 manifest. Parser output retains 52 nonempty sequential displayed labels across the three captured pages (chapter extents 18, 14, 20). All page links target the matching Zephaniah chapter. This verifies local capture-to-reader extraction and page structure only. No collation against Löfgren's 1930 print, critical apparatus, facsimile, or manuscripts was performed.",
        "source_pages": f"Three local HTML pages: {pages}. The TAU index lists text pages 1–3 and separate image pages; images are not bundled.",
        "chapters": chapters,
    }
    reader_bytes = (json.dumps(reader, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    reader_sha = hashlib.sha256(reader_bytes).hexdigest()

    # Start from the project's validated record shape, then replace every
    # Obadiah-specific identity, claim, and review statement.
    base_layer = json.loads((ROOT / "examples" / "obadiah-geez-bachmann-theot-layer.json").read_text(encoding="utf-8"))
    layer = copy.deepcopy(base_layer)
    layer.update({
        "record_id": f"{BASE}/layer/{READER_ID}",
        "work_id": f"{BASE}/work/zephaniah-eotc-candidate",
        "labels": [
            {"value": "Zephaniah — Geʽez source transcription", "language_tag": "en", "label_type": "preferred"},
            {"value": "ዘሰፎንያስ ፡ ነቢይ ።", "language_tag": "gez", "label_type": "original_form"},
        ],
        "tradition_assertions": [{
            "tradition_id": f"{BASE}/tradition/eotc",
            "canon_id": f"{BASE}/canon/{CANON_ID}",
            "mapping_state": "uncertain",
            "evidence_source_ids": ["SRC-029", "SRC-157", "SRC-158", SOURCE_ID],
            "notes": "The cited Church English list and TAU use the title Zephaniah. This is only a provisional title-level crosswalk to the corresponding listed entry; the project has not established the relation between this 1930 critical-edition-based transcription and the current EOTC printed text or its exact canon witness.",
        }],
        "witness": {
            "witness_id": f"{BASE}/witness/zephaniah-lofgren-1930-hacohen-tau-2022",
            "witness_type": "digital_edition",
            "title": "Löfgren 1930 Ethiopic Zephaniah; TAU text prepared by Ran HaCohen (March 2022)",
            "date_statement": "Printed edition 1930, pp. 36–43; TAU information page records text version March 2022",
            "repository_or_publisher": "Tel Aviv University website; text attributed to Ran HaCohen",
            "shelfmark_or_edition_id": "Zephaniah section of Löfgren's seven-prophet edition",
            "editorial_policy": "TAU says Löfgren's edition was based on Oxford MS Huntington 625 and other manuscripts, and that Ran HaCohen prepared the text; the captured source page does not identify a separate proofreader. The local capture retains three chapter pages and their linked source labels. Print collation, source manuscript inventory, and apparatus are not bundled.",
            "source_ids": ["SRC-034", "SRC-036", "SRC-157", "SRC-158", SOURCE_ID],
        },
        "text_origin": "source_transcription",
        "language_tag": "gez",
        "language_name_as_recorded": "Geʽez (Classical Ethiopic)",
        "script_code": "Ethi",
        "basis_path": ["gez"],
        "agents": [
            {"role": "editor", "name": "Oscar Löfgren", "authority_or_affiliation": None, "source_ids": ["SRC-157"]},
            {"role": "transcriber", "name": "Ran HaCohen", "authority_or_affiliation": "Tel Aviv University website; credited preparer", "source_ids": [SOURCE_ID]},
        ],
        "content_package": {"uri": f"../readers/{READER_ID}.json", "media_type": "application/json", "sha256": reader_sha, "format_version": "1"},
        "coverage": {
            "extent_state": "complete_for_declared_edition",
            "extent_basis": "source_inventory",
            "unit_count": total,
            "structure_description": "Three captured TAU text pages, corresponding to chapters 1–3 in its index, have sequential displayed linked numbers with extents 18, 14, and 20 (52 total). This is complete only for the three locally retained text pages; no printed-edition or manuscript completeness is claimed.",
            "missing_or_lacunose_ranges": [],
            "supplements_and_editorial_signs": "HTML whitespace and the separately displayed link labels are normalized; source markers and each link's actual book target remain separate, and visible Ethiopic text and signs are retained. Raw HTML is retained. Facsimiles and critical apparatus are excluded.",
            "numbering_policy": "Preserve source page and displayed linked-number sequence exactly: chapter pages 1–3, labels 1–18, 1–14, and 1–20. Preserve the actual link target book per unit (Zephaniah). Do not infer alignment to another witness's numbering.",
        },
        "rights": {
            "status": "permission_limited",
            "statement": notice,
            "license_id": None,
            "rights_holder": "Ran HaCohen (TAU site notice)",
            "attribution_required": True,
            "territory_or_term_limits": "TAU notice grants noncommercial use only with the copyright and permission notice attached; other uses require contacting the rights holder. No open license or commercial permission is claimed.",
            "evidence_source_ids": ["SRC-036", "SRC-157", "SRC-158", SOURCE_ID],
        },
        "review_dimensions": [
            {"dimension": "chapter_or_section_sequence", "state": "checked_with_limits", "scope": "Three retained source pages match their manifest checksums and yield sequential displayed labels 1–18, 1–14, and 1–20. All 52 source links target the chapter corresponding to the page title and TAU menu.", "reviewer": None, "review_method": "automated_validation", "review_process": "Zephaniah capture parser and archive build", "reviewed_at": file_map["zephaniah-chapter-1.html"]["captured_at"][:10], "evidence_source_ids": [SOURCE_ID], "notes": "Capture-to-reader structure only. Does not establish print or manuscript completeness or cross-witness numbering."},
            {"dimension": "transcription_accuracy", "state": "unknown", "scope": "No collation against Löfgren's 1930 print, cited manuscripts, image pages, or a current EOTC edition.", "reviewer": None, "review_method": "unknown", "review_process": None, "reviewed_at": None, "evidence_source_ids": ["SRC-157", "SRC-158", SOURCE_ID], "notes": "TAU credits text preparation to Ran HaCohen; this archive has not repeated or independently assessed that review."},
            {"dimension": "rights", "state": "checked_with_limits", "scope": "TAU general reuse notice and Zephaniah information page were captured locally.", "reviewer": None, "review_method": "source_inspection", "review_process": "Retained the noncommercial notice and the source page's author attribution.", "reviewed_at": file_map["zephaniah-information.html"]["captured_at"][:10], "evidence_source_ids": ["SRC-036", "SRC-157", "SRC-158", SOURCE_ID], "notes": "Noncommercial use with notices only; no open or commercial grant is asserted."},
        ],
        "publication_state": "bundled",
        "community_access_note": None,
        "additional_notes": "This record bundles no English translation. The English title and metadata are not translated text; the reader contains the captured Geʽez source transcription.",
    })
    return reader, layer


def write() -> tuple[dict, dict]:
    reader, layer = build()
    READER_PATH.write_bytes((json.dumps(reader, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    LAYER_PATH.write_bytes((json.dumps(layer, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    return reader, layer


if __name__ == "__main__":
    reader, layer = write()
    print(f"Built Zephaniah reader: {reader['chapter_count']} chapters, {reader['unit_count']} source labels; layer {layer['record_id']}.")
