"""Build research readers from retained TAU Geʽez Reigns I–II pages."""

from __future__ import annotations

import hashlib
import json
import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

ROOT = Path(__file__).resolve().parent
CAPTURE = ROOT / "readers" / "source" / "reigns-tau-dillmann"
SOURCE_ID = "SRC-336"
REVIEW_PATH = "research/reigns-title-crosswalk-review.md"
CANON_ID = "eotc-ot-09"
BASE = "https://austinsimpkins1997-ship-it.github.io/ethiopian-bible-library/id"
BOOKS = (
    {
        "roman": "I", "prefix": "regum-i", "tau_prefix": "RegI", "count": 31,
        "book_id": "1sa", "title": "I Samuel", "reader_id": "samuel-i-geez-research",
        "corpus_id": "tau-regum-i-research", "filename": "samuel-i-geez.json",
    },
    {
        "roman": "II", "prefix": "regum-ii", "tau_prefix": "RegII", "count": 24,
        "book_id": "2sa", "title": "II Samuel", "reader_id": "samuel-ii-geez-research",
        "corpus_id": "tau-regum-ii-research", "filename": "samuel-ii-geez.json",
    },
)
SOURCE_IDS = ["SRC-029", "SRC-036", "SRC-164", SOURCE_ID]
COPYRIGHT_NOTICE = (
    "© Ran HaCohen. For the digitized Ethiopic texts, permission to use, copy, and distribute for any "
    "NONCOMMERCIAL purpose is granted without fee, provided that the copyright notice Ran HaCohen and this "
    "permission notice appear in all copies of the text. For other uses, please contact the copyright owner."
)
RIGHTS_STATUS = (
    "TAU's site-wide notice permits copying and distribution for noncommercial use only, with the copyright and "
    "permission notice accompanying every copy; other uses require contacting the rights holder. This is a "
    "permission-limited grant, not an open-content or commercial license."
)


class ReignsPageParser(HTMLParser):
    """Extract each Geʽez segment anchored to TAU's displayed verse link."""

    def __init__(self, expected_book: str, expected_chapter: int) -> None:
        super().__init__(convert_charrefs=True)
        self.expected_book = expected_book
        self.expected_chapter = expected_chapter
        self.current: tuple[str, int, str] | None = None
        self.in_marker_link = False
        self.parts: list[str] = []
        self.units: list[tuple[str, int, int, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag != "a":
            return
        href = dict(attrs).get("href") or ""
        query = parse_qs(urlparse(href).query)
        search = query.get("search", [""])[0]
        match = re.fullmatch(r"(1sa|2sa|1ki|2ki)\s+(\d+):(\d+)", search)
        if not match and search in {"1ki", "2ki"} and query.get("chapter") and query.get("verse"):
            match = re.fullmatch(
                r"(1ki|2ki)\s+(\d+):(\d+)",
                f"{search} {query['chapter'][0]}:{query['verse'][0]}",
            )
        if not match:
            return
        self._finish()
        book, chapter, number = match.groups()
        self.current = (book, int(chapter), number)
        self.in_marker_link = True
        self.parts = []

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self.in_marker_link:
            self.in_marker_link = False

    def handle_data(self, data: str) -> None:
        if self.current is not None and not self.in_marker_link:
            self.parts.append(data)

    def close(self) -> None:
        self._finish()
        super().close()

    def _finish(self) -> None:
        if self.current is None:
            return
        book, chapter, marker = self.current
        body = re.sub(r"\s+", " ", "".join(self.parts)).strip()
        if not body:
            raise ValueError(f"Empty text at {book} {chapter}:{marker}.")
        self.units.append((book, chapter, int(marker), body))
        self.current = None
        self.in_marker_link = False
        self.parts = []


def _capture_manifest() -> tuple[dict, dict[str, dict]]:
    manifest = json.loads((CAPTURE / "SOURCE-CAPTURE.json").read_text(encoding="utf-8"))
    by_path: dict[str, dict] = {}
    for item in manifest["files"]:
        path = CAPTURE / item["path"]
        data = path.read_bytes()
        if (item.get("http_status") != 200 or len(data) != item["size_bytes"]
                or hashlib.sha256(data).hexdigest() != item["sha256"]):
            raise ValueError(f"Retained Reigns source failed HTTP/size/SHA check: {item['path']}")
        by_path[item["path"]] = item
    return manifest, by_path


def _menu_chapters(index_html: str, book: dict) -> list[int]:
    pattern = rf'new Option\("(\d+)","Regum/{book["tau_prefix"]} (\d+)\.html"\)'
    return [int(match.group(1)) for match in re.finditer(pattern, index_html)]


def _parse_chapters(book: dict, files: dict[str, dict]) -> tuple[list[dict], int, list[str]]:
    index_html = (CAPTURE / "tau-ethiopic-index.html").read_bytes().decode("ascii")
    observed_menu = _menu_chapters(index_html, book)
    expected_menu = list(range(1, book["count"] + 1))
    if observed_menu != expected_menu:
        raise ValueError(f"TAU {book['roman']} Regum menu mismatch: expected {expected_menu}; observed {observed_menu}.")

    chapters = []
    total_units = 0
    anomalies = []
    for chapter_number in expected_menu:
        name = f"{book['prefix']}-{chapter_number:02d}.html"
        raw = (CAPTURE / name).read_bytes()
        parser = ReignsPageParser(book["book_id"], chapter_number)
        parser.feed(raw.decode("ascii"))
        parser.close()
        if not parser.units:
            raise ValueError(f"TAU Reigns {book['roman']} chapter {chapter_number} has no linked units.")
        for target, target_chapter, number, _ in parser.units:
            if target != book["book_id"] or target_chapter != chapter_number:
                anomalies.append(
                    f"TAU Reigns {book['roman']} page {chapter_number} includes a span linked to "
                    f"{target} {target_chapter}:{number}; retained as a source-page boundary, not reassigned."
                )
        numbers = [number for _, _, number, _ in parser.units]
        if len(numbers) != len(set(numbers)):
            anomalies.append(f"{book['roman']} Reigns {chapter_number}: duplicate displayed labels retained")
        if numbers != sorted(numbers):
            anomalies.append(f"{book['roman']} Reigns {chapter_number}: nonsequential source order retained")
        if any(b - a > 1 for a, b in zip(numbers, numbers[1:])):
            anomalies.append(f"{book['roman']} Reigns {chapter_number}: label gaps retained")
        chapters.append({
            "chapter": chapter_number,
            "source_marker": f"Regum {book['roman']} {chapter_number}",
            "source_url": files[name]["url"],
            "source_sha256": files[name]["sha256"],
            "verses": [
                {
                    "number": number,
                    "source_marker": str(number),
                    "source_link_target_book": target,
                    "source_link_target_chapter": target_chapter,
                    "text": text,
                }
                for target, target_chapter, number, text in parser.units
            ],
        })
        total_units += len(parser.units)
    return chapters, total_units, anomalies


def build() -> tuple[list[dict], list[dict], list[dict]]:
    manifest, files = _capture_manifest()
    readers = []
    corpora = []
    all_anomalies = []
    all_chapter_entries: list[tuple[dict, dict]] = []
    context_paths = {"regum-information.html", "tau-general-information.html", "tau-ethiopic-index.html"}
    for book in BOOKS:
        chapters, unit_count, anomalies = _parse_chapters(book, files)
        all_anomalies.extend(anomalies)
        all_chapter_entries.extend((book, chapter) for chapter in chapters)
        chapter_paths = [f"{book['prefix']}-{number:02d}.html" for number in range(1, book["count"] + 1)]
        source_pages = [files[path]["url"] for path in chapter_paths]
        snapshot_hash = hashlib.sha256("".join(files[path]["sha256"] for path in chapter_paths).encode("ascii")).hexdigest()
        observed_label_summary = "; ".join(
            f"{chapter['chapter']}: {chapter['verses'][0]['number']}–{chapter['verses'][-1]['number']} "
            f"({len(chapter['verses'])} linked labels)"
            for chapter in chapters
        )
        mapping_note = (
            "Archive-reviewed work/title crosswalk: the Church's listed entry is ‘I and II Samuel’; TAU's source "
            "information identifies its digitized Ethiopic Reigns I–IV as ‘Samuel I–II and Kings I–II,’ and the "
            "two retained components are Regum I and II. This supports the named-work crosswalk only. The TAU "
            "equivalence remains attributed to TAU; it does not establish identity with a current EOTC edition, "
            "manuscript completeness, or wording accuracy. These component readers remain research records, not "
            "canon-linked coverage."
        )
        edition = (
            "August Dillmann (ed.), Veteris Testamenti Aethiopici Tomus Secundus, fasc. 1: Regum I et II, "
            "Leipzig, 1861; text digitized by Ran HaCohen at Tel Aviv University."
        )
        edition_scope = (
            f"This reader contains the {book['count']} TAU menu-listed Ethiopic pages for Regum {book['roman']}, "
            f"which TAU identifies as {book['title']}. It is one component of the grouped Church-list entry "
            "‘I and II Samuel’. The 1861 Dillmann critical-edition text was digitized with OCR and proofread "
            "according to TAU; TAU warns new errors may remain. This archive has not collated the wording "
            "against the print edition, manuscripts, or a current EOTC edition."
        )
        chapter_structure_note = (
            f"TAU's retained index lists Regum {book['roman']} chapters 1–{book['count']}. Each chapter page's "
            f"displayed verse labels link to BibleGateway book identifier {book['book_id']}; all observed labels "
            f"and their source-order text spans are retained. Observed chapter ranges/counts: {observed_label_summary}. "
            "These are page-structure counts, not proof of completeness or equivalence to another numbering system."
        )
        reader = {
            "reader_id": book["reader_id"],
            "research_corpus_id": book["corpus_id"],
            "text_origin": "source_transcription",
            "title": f"{book['title']} — Geʽez transcription of TAU's Dillmann Regum {book['roman']}",
            "display_name": f"{book['title']} (Geʽez; Dillmann 1861 / TAU)",
            "normalized_title_en": book["title"],
            "language": "Geʽez (Classical Ethiopic)",
            "language_tag": "gez",
            "script_code": "Ethi",
            "section_label": "Chapter",
            "source_ids": SOURCE_IDS,
            "edition": edition,
            "edition_scope": edition_scope,
            "transcription_note": (
                f"The Ethiopic text spans were extracted from {book['count']} retained TAU chapter HTML pages. "
                "HTML entities were decoded and whitespace normalized to single spaces. Each displayed source "
                "number and external book identifier is retained; no verse numbering is repaired, translated, "
                "or aligned to another witness."
            ),
            "editorial_signs_note": (
                "Visible Ethiopic characters, punctuation, and editorial marks are retained as decoded from the "
                "captured HTML; whitespace is normalized. Page headings and navigation are recorded separately "
                "from the verse text."
            ),
            "chapter_structure_note": chapter_structure_note,
            "rights_classification": "permission_limited",
            "copyright_notice": COPYRIGHT_NOTICE,
            "commercial_use": RIGHTS_STATUS,
            "license_id": None,
            "license_url": "https://www.tau.ac.il/~hacohen/Information.html",
            "chapter_count": len(chapters),
            "unit_count": unit_count,
            "unit_label": "linked source labels",
            "source_numbered_unit_count": unit_count,
            "source_unnumbered_unit_count": 0,
            "verification_status": (
                "The local capture hashes, menu-listed chapter order, linked book identifiers, nonempty spans, "
                "and observed source labels were structurally checked. The source reports OCR conversion and "
                "proofreading but warns of possible errors. This archive has not independently verified wording, "
                "manuscript/print completeness, or current EOTC edition identity."
            ),
            "source_pages": source_pages,
            "source_snapshot_sha256": snapshot_hash,
            "additional_notes": (
                f"Partial component reader for grouped entry ‘I and II Samuel’: this file covers only {book['title']}. "
                "The matching component is a separate reader. No English translation or verse alignment is bundled. "
                "See the cited source and the exact noncommercial permission notice."
            ),
            "chapters": chapters,
        }
        reader["chapter_count"] = len(chapters)
        readers.append(reader)
        corpora.append({
            "corpus_id": book["corpus_id"],
            "title": f"{book['title']} (TAU / Dillmann 1861) — Geʽez research transcription",
            "reader_id": book["reader_id"],
            "unit_count": unit_count,
            "reader_status": "bundled_research_reader",
            "canon_mapping_state": "reviewed_match",
            "candidate_canon_id": CANON_ID,
            "canon_mapping_note": mapping_note,
            "language_description": "TAU identifies these as Ethiopic Bible text pages; the archive records Geʽez (gez) as the reader language. This does not identify the historical translation's source language or relay path.",
            "script_description": "Ethiopic script (Ethi), observed in the retained TAU text pages.",
            "unit_summary": f"{len(chapters)} menu-listed chapter pages and {unit_count} nonempty linked text spans; observed chapter labels: {observed_label_summary}. Structure counts do not establish full-edition completeness or wording accuracy.",
            "rights_classification": "permission_limited",
            "rights_status": RIGHTS_STATUS,
            "review_status": reader["verification_status"],
            "source_ids": SOURCE_IDS,
            "text_origin": "source_transcription",
            "language_tag": "gez",
            "script_code": "Ethi",
        })

    target_occurrences: dict[tuple[str, int, int], list[tuple[dict, dict, dict]]] = {}
    for book, chapter in all_chapter_entries:
        for unit in chapter["verses"]:
            target_key = (
                unit["source_link_target_book"],
                unit["source_link_target_chapter"],
                unit["number"],
            )
            target_occurrences.setdefault(target_key, []).append((book, chapter, unit))
    for target_key, occurrences in target_occurrences.items():
        distinct_texts = {occurrence[2]["text"] for occurrence in occurrences}
        if len(occurrences) < 2 or len(distinct_texts) < 2:
            continue
        locations = "; ".join(
            f"Regum {book['roman']} chapter {chapter['chapter']}"
            for book, chapter, _ in occurrences
        )
        note_text = (
            f"TAU links more than one distinct source span to {target_key[0]} {target_key[1]}:{target_key[2]} "
            f"({locations}). Both source spans are preserved in their page locations; the external link target "
            "does not establish verse equivalence or authorize merging the spans."
        )
        for _, chapter, _ in occurrences:
            chapter.setdefault("notes", []).append({
                "verse": str(target_key[2]),
                "marker": "source-link boundary review",
                "text": note_text,
                "note_origin": "archive",
            })
        all_anomalies.append(note_text)

    capture_details = "; ".join(
        f"{item['path']} {item['size_bytes']} bytes SHA-256 {item['sha256']}"
        for item in manifest["files"] if item["path"] in context_paths
    )
    text_records = [item for item in manifest["files"] if item["path"] not in context_paths]
    text_bytes = sum(item["size_bytes"] for item in text_records)
    source = {
        "source_id": SOURCE_ID,
        "source_name": "Tel Aviv University — Ethiopic Books of Reigns I–II (Samuel I–II), locally retained text pages",
        "url": "https://www.tau.ac.il/~hacohen/Regum/Information.html",
        "local_review_url": REVIEW_PATH,
        "inspection_and_limitations": (
            f"Captured {len(text_records)} TAU chapter pages ({text_bytes:,} bytes) plus the Reigns information page, "
            "site-wide rights page, and index. Each retained file has an HTTP status, capture time, byte count, "
            "URL, and SHA-256 in the local capture manifest. Menu and linked label structure are checked by the "
            "reader builder. TAU identifies the Dillmann 1861 Reigns I–II text with Samuel I–II and reports OCR "
            "conversion and proofreading, while warning that errors may remain. This archive does not independently "
            "collate wording, establish complete print coverage, or assert a current EOTC edition match. TAU's "
            "noncommercial permission and required copyright notice are retained; no open or commercial license is claimed. "
            f"Context captures: {capture_details}. Structural anomalies retained: {all_anomalies or 'none detected in the linked labels.'}"
        ),
        "archive_status": "Bundled permission-limited Geʽez research transcriptions; chapter structure checked; wording not independently collated",
    }
    return readers, corpora, [source]


if __name__ == "__main__":
    readers, corpora, _ = build()
    for reader, corpus in zip(readers, corpora):
        print(f"Built {reader['reader_id']}: {reader['chapter_count']} chapters, {reader['unit_count']} linked source labels; reviewed title match only, research reader.")
