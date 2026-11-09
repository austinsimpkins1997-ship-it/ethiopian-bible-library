"""Build TAU/Dillmann Reigns III–IV as provenance-preserving Kings research readers."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

from build_reigns_readers import ReignsPageParser
from capture_kings_sources import EXPECTED_MENU

ROOT = Path(__file__).resolve().parent
CAPTURE = ROOT / "readers" / "source" / "reigns-kings-tau-dillmann"
SOURCE_ID = "SRC-337"
CANON_ID = "eotc-ot-10"
SOURCE_IDS = ["SRC-029", "SRC-034", "SRC-036", "SRC-164", SOURCE_ID]
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
BOOKS = (
    {
        "roman": "III", "tau_prefix": "RegIII", "book_id": "1ki", "title": "I Kings",
        "reader_id": "kings-i-geez-research", "corpus_id": "tau-regum-iii-research",
        "reader_file": "kings-i-geez-research.json",
    },
    {
        "roman": "IV", "tau_prefix": "RegIV", "book_id": "2ki", "title": "II Kings",
        "reader_id": "kings-ii-geez-research", "corpus_id": "tau-regum-iv-research",
        "reader_file": "kings-ii-geez-research.json",
    },
)


def _load_capture() -> tuple[dict, dict[str, dict]]:
    manifest = json.loads((CAPTURE / "SOURCE-CAPTURE.json").read_text(encoding="utf-8"))
    by_path: dict[str, dict] = {}
    for item in manifest["files"]:
        path = CAPTURE / item["path"]
        raw = path.read_bytes()
        if (item.get("http_status") != 200 or len(raw) != item["size_bytes"]
                or hashlib.sha256(raw).hexdigest() != item["sha256"]):
            raise ValueError(f"Retained TAU Kings source failed HTTP/size/SHA check: {item['path']}")
        by_path[item["path"]] = item
    return manifest, by_path


def _page_token(label: str) -> str:
    return label.lower() if label[-1:].isalpha() else f"{int(label):02d}"


def _parse_book(book: dict, files: dict[str, dict]) -> tuple[list[dict], int, list[str]]:
    index_html = (CAPTURE / "tau-ethiopic-index.html").read_bytes().decode("ascii")
    pattern = rf'new Option\("([^\"]+)","Regum/{book["tau_prefix"]} ([^\"]+\.html)"\)'
    menu = [(match.group(1), match.group(2)) for match in re.finditer(pattern, index_html)]
    labels = [label for label, _ in menu]
    if labels != EXPECTED_MENU[book["roman"]]:
        raise ValueError(f"TAU Regum {book['roman']} menu order changed: {labels!r}.")

    pages = []
    total_units = 0
    anomalies = []
    for position, label in enumerate(labels, start=1):
        token = _page_token(label)
        path = f"regum-{book['roman'].lower()}-{token}.html"
        if path not in files:
            raise ValueError(f"TAU Reigns capture manifest is missing indexed page {path}.")
        raw = (CAPTURE / path).read_bytes()
        expected_chapter = int(re.match(r"\d+", label).group())
        parser = ReignsPageParser(book["book_id"], expected_chapter)
        parser.feed(raw.decode("ascii"))
        parser.close()
        if not parser.units:
            raise ValueError(f"TAU Regum {book['roman']} page {label} has no linked text spans.")
        for target, chapter, number, _ in parser.units:
            if target != book["book_id"] or chapter != expected_chapter:
                anomalies.append(
                    f"Regum {book['roman']} page {label} contains a span linked to {target} {chapter}:{number}; "
                    "the link is retained without moving the span to another page."
                )
        numbers = [number for _, _, number, _ in parser.units]
        if len(numbers) != len(set(numbers)):
            anomalies.append(f"Regum {book['roman']} page {label}: repeated linked labels retained in source order.")
        if numbers != sorted(numbers):
            anomalies.append(f"Regum {book['roman']} page {label}: nonsequential linked labels retained in source order.")
        if any(b - a > 1 for a, b in zip(numbers, numbers[1:])):
            anomalies.append(f"Regum {book['roman']} page {label}: linked-label gaps retained without interpolation.")
        pages.append({
            "chapter": position,
            "source_marker": f"Regum {book['roman']} {label}",
            "source_page_label": label,
            "source_url": files[path]["url"],
            "source_sha256": files[path]["sha256"],
            "verses": [
                {
                    "number": number,
                    "source_marker": str(number),
                    "source_link_target_book": target,
                    "source_link_target_chapter": chapter,
                    "text": text,
                }
                for target, chapter, number, text in parser.units
            ],
        })
        total_units += len(parser.units)
    return pages, total_units, anomalies


def build() -> tuple[list[dict], list[dict], list[dict]]:
    manifest, files = _load_capture()
    contexts = {"regum-information.html", "tau-general-information.html", "tau-ethiopic-index.html"}
    readers = []
    corpora = []
    all_chapters: list[tuple[dict, dict]] = []
    anomalies = []

    for book in BOOKS:
        chapters, unit_count, book_anomalies = _parse_book(book, files)
        anomalies.extend(book_anomalies)
        all_chapters.extend((book, chapter) for chapter in chapters)
        page_labels = [chapter["source_page_label"] for chapter in chapters]
        source_pages = [chapter["source_url"] for chapter in chapters]
        snapshot_hash = hashlib.sha256("".join(chapter["source_sha256"] for chapter in chapters).encode("ascii")).hexdigest()
        label_summary = "; ".join(
            f"{chapter['source_page_label']}: {chapter['verses'][0]['number']}–{chapter['verses'][-1]['number']} "
            f"({len(chapter['verses'])} linked labels)"
            for chapter in chapters
        )
        mapping_note = (
            "Archive-reviewed work/title crosswalk: the Church's listed entry is ‘I and II Kings’; TAU's source "
            "information identifies its digitized Ethiopic Reigns I–IV as ‘Samuel I–II and Kings I–II,’ and the "
            "two retained components are Regum III and IV. This supports the named-work crosswalk only. The TAU "
            "equivalence remains attributed to TAU; it does not establish identity with a current EOTC edition, "
            "manuscript completeness, or wording accuracy. These component readers remain research records, not "
            "canon-linked coverage."
        )
        page_anomaly_note = (
            "The retained TAU menu labels Regum III pages 3a and 3b separately and lists page 21 before page 20. "
            "The reader preserves the source menu order and labels; its navigation positions are not claims that the "
            "menu labels equal standard chapter numbers."
        )
        edition = (
            "August Dillmann (ed.), Veteris Testamenti Aethiopici Tomus Secundus, fasc. 2: Regum III et IV, "
            "Leipzig, 1871; text digitized by Ran HaCohen at Tel Aviv University."
        )
        chapter_note = (
            f"TAU's captured index lists {len(chapters)} Regum {book['roman']} source pages in this order: "
            f"{', '.join(page_labels)}. Each page contains Ethiopic spans linked to an external BibleGateway book/chapter/label. "
            f"Observed ranges and counts: {label_summary}. For navigation, archive chapter numbers are page positions; "
            "source page labels remain separately recorded and visible. These are source-page counts, not proof of print completeness."
        )
        reader = {
            "reader_id": book["reader_id"],
            "research_corpus_id": book["corpus_id"],
            "text_origin": "source_transcription",
            "title": f"{book['title']} — Geʽez transcription of TAU's Dillmann Regum {book['roman']}",
            "display_name": f"{book['title']} (Geʽez; Dillmann 1871 / TAU)",
            "normalized_title_en": book["title"],
            "language": "Geʽez (Classical Ethiopic)",
            "language_tag": "gez",
            "script_code": "Ethi",
            "section_label": "TAU source page",
            "section_unit_plural": "source-page divisions",
            "source_ids": SOURCE_IDS,
            "edition": edition,
            "edition_scope": (
                f"This reader contains {len(chapters)} menu-listed source pages for TAU Regum {book['roman']}, which TAU "
                f"identifies as {book['title']}. It is a research candidate associated with the grouped Church-list title "
                "‘I and II Kings’. TAU says the Dillmann edition was scanned, converted by OCR, and proofread, but also warns "
                "that errors may remain. This archive has not collated the text against print, manuscripts, or a current EOTC edition."
            ),
            "transcription_note": (
                f"Text spans were extracted from {len(chapters)} retained TAU HTML pages. Ethiopic characters and punctuation "
                "were decoded from captured HTML and whitespace normalized. Source labels, page labels, linked target book/chapter, "
                "and source order are retained; no text was translated, renumbered, or moved between pages."
            ),
            "editorial_signs_note": (
                "Decoded Ethiopic characters and punctuation are retained; whitespace is normalized. The separate source menu "
                "labels, including 3a/3b and its observed 21-before-20 order, remain in the reader metadata and navigation."
            ),
            "chapter_structure_note": chapter_note + " " + page_anomaly_note,
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
                "Local capture HTTP status, byte lengths and SHA-256 hashes, TAU menu labels and order, nonempty linked text spans, "
                "and source-label order were checked. TAU reports OCR conversion and proofreading but warns errors may remain. "
                "Wording, manuscript/print completeness, and exact current EOTC edition identity are not independently verified."
            ),
            "source_pages": source_pages,
            "source_snapshot_sha256": snapshot_hash,
            "additional_notes": (
                f"TAU source pages for {book['title']}; the source divides Regum III into distinct menu pages 3a and 3b and orders "
                "pages 21 before 20. This reader retains those labels and page positions. It is not canon-linked, and no English "
                "translation or verse alignment is bundled. See the source record and notice."
            ),
            "chapters": chapters,
        }
        readers.append(reader)
        corpora.append({
            "corpus_id": book["corpus_id"],
            "title": f"{book['title']} (TAU / Dillmann 1871) — Geʽez research transcription",
            "reader_id": book["reader_id"],
            "unit_count": unit_count,
            "reader_status": "bundled_research_reader",
            "canon_mapping_state": "reviewed_match",
            "candidate_canon_id": CANON_ID,
            "canon_mapping_note": mapping_note,
            "language_description": "TAU identifies the page set as part of the Ethiopic Bible; the archive records Geʽez (gez). The historical translation path is not established.",
            "script_description": "Ethiopic script (Ethi), observed in the retained source pages.",
            "unit_summary": f"{len(chapters)} source-page divisions, menu labels {', '.join(page_labels)}, and {unit_count} linked text spans; source order and anomalies are retained. Counts do not establish print-edition completeness or wording accuracy.",
            "rights_classification": "permission_limited",
            "rights_status": RIGHTS_STATUS,
            "review_status": reader["verification_status"],
            "source_ids": SOURCE_IDS,
            "text_origin": "source_transcription",
            "language_tag": "gez",
            "script_code": "Ethi",
        })

    # Preserve duplicate link targets across split source pages as notes; never merge by a link alone.
    target_occurrences: dict[tuple[str, int, int], list[tuple[dict, dict, dict]]] = {}
    for book, chapter in all_chapters:
        for unit in chapter["verses"]:
            key = (unit["source_link_target_book"], unit["source_link_target_chapter"], unit["number"])
            target_occurrences.setdefault(key, []).append((book, chapter, unit))
    for key, occurrences in target_occurrences.items():
        if len(occurrences) < 2 or len({item[2]["text"] for item in occurrences}) < 2:
            continue
        locations = "; ".join(
            f"Regum {book['roman']} page {chapter['source_page_label']}"
            for book, chapter, _ in occurrences
        )
        note = (
            f"TAU links distinct source spans to {key[0]} {key[1]}:{key[2]} ({locations}). All spans remain in their "
            "source-page positions; a shared external target does not establish verse equivalence or permit merging."
        )
        for _, chapter, _ in occurrences:
            chapter.setdefault("notes", []).append({
                "verse": str(key[2]), "marker": "source-link boundary review", "text": note, "note_origin": "archive",
            })
        anomalies.append(note)

    context_details = "; ".join(
        f"{item['path']} {item['size_bytes']} bytes SHA-256 {item['sha256']}"
        for item in manifest["files"] if item["path"] in contexts
    )
    text_files = [item for item in manifest["files"] if item["path"] not in contexts]
    text_bytes = sum(item["size_bytes"] for item in text_files)
    source = {
        "source_id": SOURCE_ID,
        "source_name": "Tel Aviv University — Ethiopic Books of Reigns III–IV (Kings I–II), locally retained text pages",
        "url": "https://www.tau.ac.il/~hacohen/Regum/Information.html",
        "inspection_and_limitations": (
            f"Captured {len(text_files)} TAU menu-listed chapter pages ({text_bytes:,} bytes) plus the Reigns information page, "
            "site-wide rights page, and Ethiopic Bible index. Every captured file records HTTP status, capture time, byte count, "
            "URL and SHA-256. The builder checks menu labels/order, nonempty linked spans, and source numbering. TAU explicitly "
            "identifies Regum III–IV with Kings I–II and describes OCR conversion plus proofreading while warning errors may remain. "
            "No independent wording collation, print-completeness audit, or current EOTC edition identification is claimed. "
            "TAU's permission is noncommercial and notice-bound, not open or commercial. "
            f"Context captures: {context_details}. Structural anomalies retained: {anomalies or 'none detected.'}"
        ),
        "archive_status": "Bundled permission-limited Geʽez source transcriptions; page structure checked; wording and current-edition identity not independently verified",
    }
    return readers, corpora, [source]


if __name__ == "__main__":
    readers, _, _ = build()
    for reader in readers:
        print(f"Built {reader['reader_id']}: {reader['chapter_count']} source-page divisions, {reader['unit_count']} linked spans; reviewed title match only, research reader.")
