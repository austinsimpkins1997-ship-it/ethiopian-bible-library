"""Build bounded Brenton English companions from the archived eBible USFM package."""

from __future__ import annotations

import hashlib
import json
import re
import zipfile
from pathlib import Path

from coverage_summary import build_coverage_statement
from layer_metadata import sync_layer_checksum

ROOT = Path(__file__).resolve().parent
PACKAGE = ROOT / "readers" / "source" / "brenton-septuagint" / "eng-Brenton_usfm.zip"
MANIFEST = ROOT / "readers" / "source" / "brenton-septuagint" / "capture-manifest.json"
SOURCE_URL = "https://ebible.org/Scriptures/eng-Brenton_usfm.zip"
SOURCE_PAGE_URL = "https://ebible.org/details.php?id=eng-Brenton"
NOTICE_SOURCE = "https://ebible.org/eng-Brenton/copyright.htm"
BOOKS = {
    "PSA": ("psalms", 23, "Psalms", 151),
    "LEV": ("leviticus", 3, "Leviticus", 27),
    "NUM": ("numbers", 4, "Numbers", 36),
    "DEU": ("deuteronomy", 5, "Deuteronomy", 34),
    "JOS": ("joshua", 6, "Joshua", 24),
    "JDG": ("judges", 7, "Judges", 21),
}
CANON_ID = {"PSA": "eotc-ot-23", "LEV": "eotc-ot-03", "NUM": "eotc-ot-04", "DEU": "eotc-ot-05", "JOS": "eotc-ot-06", "JDG": "eotc-ot-07"}
USFM_MEMBER = {"PSA": "20-PSAeng-Brenton.usfm", "LEV": "04-LEVeng-Brenton.usfm", "NUM": "05-NUMeng-Brenton.usfm", "DEU": "06-DEUeng-Brenton.usfm", "JOS": "07-JOSeng-Brenton.usfm", "JDG": "08-JDGeng-Brenton.usfm"}
READER_FILE = {"PSA": "psalms-geez-ludolf.json"}
GEEZ_LAYER_FILE = {"PSA": "psalms-geez-layer.json"}
NONVERSE_MARKERS = {"id", "h", "toc1", "toc2", "toc3", "mt1", "mt2", "p", "nb", "d", "b"}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def clean_usfm(text: str) -> str:
    """Remove USFM formatting controls while visibly retaining translator additions."""
    text = re.sub(r"\\add\s*(.*?)\\add\*", r"⟦\1⟧", text)
    text = re.sub(r"\\sc\s*(.*?)\\sc\*", r"\1", text)
    # USFM \fl marks a footnote label; retain its following source words while
    # removing the structural token itself.
    text = re.sub(r"\\fl\s*", " ", text)
    if re.search(r"\\[A-Za-z][A-Za-z0-9]*\*?", text):
        raise ValueError(f"Unexpected inline USFM marker in verse or note: {text[:100]!r}")
    return re.sub(r"\s+", " ", text).strip()


def note_from_markup(marker: str, body: str, verse: str, chapter: int) -> dict:
    reference_match = re.search(r"\\fr\s+([^\\]+)", body)
    reference = reference_match.group(1).strip() if reference_match else ""
    alt = "\\fqa" in body
    # Keep the content fields and suppress format/reference markers; their meaning is
    # represented in the note marker and verse field.
    text = re.sub(r"\\(?:fr|xo)\s+[^\\]+", "", body)
    text = re.sub(r"\\(?:ft|fqa|fq|xt)\s*", "", text)
    text = re.sub(r"^\s*\+\s*", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    text = clean_usfm(text)
    if not text:
        return {
            "verse": verse,
            "marker": "Source note marker without text",
            "text": None,
            "note_type": "source_note_marker_without_text",
            "source_reference": reference or None,
        }
    if reference and reference != f"{chapter}:{verse}":
        text = f"Source note reference {reference}. {text}"
    return {
        "verse": verse,
        "marker": "Alternative reading" if alt else ("Cross-reference" if marker == "x" else "Translator/editor note"),
        "text": text,
        "note_type": "cross_reference" if marker == "x" else ("alternate_reading" if alt else "translator_note"),
    }


def parse_usfm(raw: bytes, code: str, member_name: str, package_hash: str) -> dict:
    slug, canon_number, title, expected_chapters = BOOKS[code]
    source = raw.decode("utf-8-sig")
    if not re.search(rf"^\\id\s+{code}\s+-\s+Brenton English Septuagint\s*$", source, re.M):
        raise ValueError(f"{member_name} does not identify as the expected Brenton {title} source.")
    chapters: list[dict] = []
    current: dict | None = None
    observed_label_counts: list[int] = []
    structural_marker_counts: dict[str, int] = {}
    pending_markers: list[str] = []

    for line_number, line in enumerate(source.splitlines(), start=1):
        chapter_match = re.match(r"^\\c\s+(\d+)\s*$", line)
        if chapter_match:
            chapter_number = int(chapter_match.group(1))
            if current is not None:
                if pending_markers:
                    raise ValueError(f"Unattached USFM markers {pending_markers} at end of {title} chapter {current['chapter']}.")
                if not current["verses"]:
                    raise ValueError(f"{title} chapter {current['chapter']} has no verses.")
                observed_label_counts.append(len(current["verses"]))
                chapters.append(current)
            current = {"chapter": chapter_number, "verses": [], "notes": []}
            continue

        verse_match = re.match(r"^\\v\s+(\d+[a-z]?)\s*(.*)$", line)
        if not verse_match:
            marker_match = re.match(r"^\\([A-Za-z0-9]+)", line)
            if marker_match and marker_match.group(1) not in NONVERSE_MARKERS:
                raise ValueError(f"Unhandled USFM marker {marker_match.group(1)} at {member_name}:{line_number}.")
            if marker_match and marker_match.group(1) in {"p", "nb", "d", "b"}:
                if current is None:
                    raise ValueError(f"Structural marker appears before a chapter at {member_name}:{line_number}.")
                marker = marker_match.group(1)
                suffix = line[marker_match.end():].strip()
                structural_marker_counts[marker] = structural_marker_counts.get(marker, 0) + 1
                if suffix:
                    if marker == "d":
                        heading = clean_usfm(suffix)
                        if not heading:
                            raise ValueError(f"Empty USFM descriptive heading at {member_name}:{line_number}.")
                        current.setdefault("heading", []).append(heading)
                    elif marker == "p" and not current["verses"]:
                        heading = clean_usfm(suffix)
                        if not heading:
                            raise ValueError(f"Empty USFM introductory paragraph at {member_name}:{line_number}.")
                        current.setdefault("heading", []).append(heading)
                        current.setdefault("heading_markers", []).append("p")
                    elif marker != "p" or not current["verses"]:
                        raise ValueError(f"USFM \\{marker} contains inline text without a preceding verse at {member_name}:{line_number}.")
                    elif marker == "p":
                        prior_verse = current["verses"][-1]
                        continuation_notes = []
                        note_pattern = re.compile(r"\\([fx])\b(.*?)\\\1\*", re.S)
                        def pull_continuation_note(match: re.Match) -> str:
                            continuation_notes.append(note_from_markup(match.group(1), match.group(2), prior_verse["number"], current["chapter"]))
                            return " "
                        suffix = note_pattern.sub(pull_continuation_note, suffix)
                        continuation_text = clean_usfm(suffix)
                        if not continuation_text:
                            raise ValueError(f"Empty inline USFM \\p segment at {member_name}:{line_number}.")
                        prior_verse.setdefault("continuations", []).append({"source_marker": "p", "text": continuation_text})
                        prior_verse.setdefault("continuation_notes", []).extend(continuation_notes)
                        current["notes"].extend(continuation_notes)
                        structural_marker_counts["p_inline_text_segments"] = structural_marker_counts.get("p_inline_text_segments", 0) + 1
                    else:
                        raise ValueError(f"USFM \\{marker} has unexpected inline text at {member_name}:{line_number}.")
                else:
                    pending_markers.append(marker)
            if line.strip() and not marker_match:
                raise ValueError(f"Unmarked source content would be lost at {member_name}:{line_number}.")
            continue
        if current is None:
            raise ValueError(f"Verse appears before a chapter marker at {member_name}:{line_number}.")
        label, body = verse_match.groups()
        if any(item["number"] == label for item in current["verses"]):
            raise ValueError(f"Duplicate {title} {current['chapter']}:{label}.")

        # Extract footnotes/cross-references before cleaning the verse text. The
        # source USFM uses distinct \f and \x blocks; preserve their complete text.
        notes = []
        note_pattern = re.compile(r"\\([fx])\b(.*?)\\\1\*", re.S)
        def pull_note(match: re.Match) -> str:
            notes.append(note_from_markup(match.group(1), match.group(2), label, current["chapter"]))
            return " "
        body = note_pattern.sub(pull_note, body)
        verse_text = clean_usfm(body)
        if not verse_text:
            if not notes:
                raise ValueError(f"Empty {title} {current['chapter']}:{label} without an explanatory source note.")
            current["verses"].append({"number": label, "text": "", "source_text_state": "marker_only"})
        else:
            current["verses"].append({"number": label, "text": verse_text})
        if pending_markers:
            current["verses"][-1]["source_markers_before"] = list(pending_markers)
            pending_markers.clear()
        current["notes"].extend(notes)

    if current is not None:
        if pending_markers:
            raise ValueError(f"Unattached USFM markers {pending_markers} at end of {title} chapter {current['chapter']}.")
        if not current["verses"]:
            raise ValueError(f"{title} chapter {current['chapter']} has no verses.")
        observed_label_counts.append(len(current["verses"]))
        chapters.append(current)

    if [chapter["chapter"] for chapter in chapters] != list(range(1, expected_chapters + 1)):
        raise ValueError(f"{title} chapter sequence differs from 1–{expected_chapters}.")
    unit_count = sum(observed_label_counts)
    result = {
        "translation_id": f"{slug}-english-brenton-lxx-1851",
        "text_origin": "published_translation",
        "title": f"English companion — Brenton Septuagint (1851), {title}",
        "language": "English",
        "language_tag": "en",
        "script_code": "Latn",
        "translator": "Sir Lancelot Charles Lee Brenton",
        "basis_language_tag": "grc",
        "translation_method": "Historical English translation from the Greek Septuagint; not directly translated from or aligned to the bundled Geʽez transcription.",
        "edition": "The Septuagint Version of the Old Testament: According to the Vatican Text, Translated into English (1851).",
        "translation_basis": "eBible.org identifies Brenton's 1851 English Septuagint as translated from Greek. This independent English witness is paired for study, not a direct translation from Geʽez, a replacement for the Geʽez witness, or proof of verse-level equivalence.",
        "rights_classification": "public_domain_claimed",
        "text_notice": "eBible.org identifies Brenton's 1851 English translation as public domain. This is a provider-reported rights status, not a worldwide legal determination or a license for other layers. The original USFM \\add markers for translator-supplied words are retained as ⟦bracketed text⟧; the brackets are archival notation, not Brenton's original punctuation.",
        "source_ids": ["SRC-038", "SRC-142"],
        "chapter_count": len(chapters),
        "unit_count": unit_count,
        "unit_label": "English verse labels",
        "verse_label_count": unit_count,
        "note_count": sum(len(chapter["notes"]) for chapter in chapters),
        "continuation_segment_count": sum(len(verse.get("continuations", [])) for chapter in chapters for verse in chapter["verses"]),
        "structural_marker_counts": structural_marker_counts,
        "source_member": member_name,
        "source_package_sha256": package_hash,
        "source_member_sha256": sha256(raw),
        "verification_status": f"Parsed from archived eBible.org USFM member {member_name}; the source reports Brenton's 1851 Greek-to-English translation and public-domain status. Automated checks preserve the package member checksum, {len(chapters)} ordered chapters, all {unit_count} nonempty verse labels, footnotes, cross-references, \\add translator-supplied-word markings (rendered with archival brackets), and structural markers {structural_marker_counts}. This confirms local package-to-reader structure only; no independent collation against Brenton's printed edition or the Greek Septuagint was performed. Translation accuracy, print-edition completeness, and alignment with Geʽez remain unverified.",
        "chapters": chapters,
    }
    marker_only_count = sum(
        1 for chapter in chapters for verse in chapter["verses"]
        if verse.get("source_text_state") == "marker_only"
    )
    if marker_only_count:
        result["marker_only_unit_count"] = marker_only_count
    return result


def make_layer(slug: str, title: str, canon_id: str, companion: dict, reader_file: str) -> dict:
    layer_id = companion["translation_id"]
    base = json.loads((ROOT / "examples" / "ruth-brenton-translation-layer.json").read_text(encoding="utf-8"))
    base["record_id"] = f"https://austinsimpkins1997-ship-it.github.io/ethiopian-bible-library/id/layer/{layer_id}"
    base["work_id"] = f"https://austinsimpkins1997-ship-it.github.io/ethiopian-bible-library/id/work/{slug}-lxx"
    base["labels"] = [{"value": companion["title"], "language_tag": "en", "label_type": "preferred"}]
    base["tradition_assertions"] = [{
        "tradition_id": "https://austinsimpkins1997-ship-it.github.io/ethiopian-bible-library/id/tradition/eotc",
        "canon_id": f"https://austinsimpkins1997-ship-it.github.io/ethiopian-bible-library/id/canon/{canon_id}",
        "mapping_state": "related_work",
        "evidence_source_ids": ["SRC-038", "SRC-142"],
        "notes": "The EOTC catalogue lists a book with this title. Brenton's text is an English translation of the Greek Septuagint; this record does not claim it is the same textual witness, an EOTC edition, or a translation from the bundled Geʽez text.",
    }]
    base["witness"] = {
        "witness_id": f"https://austinsimpkins1997-ship-it.github.io/ethiopian-bible-library/id/witness/brenton-lxx-{slug}-1851",
        "witness_type": "digital_edition",
        "title": companion["title"],
        "date_statement": "Translation published 1851; USFM source package provided by eBible.org",
        "repository_or_publisher": "Sir Lancelot Charles Lee Brenton; digital text distributed by eBible.org",
        "shelfmark_or_edition_id": companion["source_member"],
        "editorial_policy": "USFM verse labels, footnotes, cross-references, paragraph starts (\\p), descriptive-title markers (\\d), and translator-supplied-word markers are retained. USFM formatting markers for small capitals are flattened to plain text; \\add words are wrapped in visible archival brackets.",
        "source_ids": ["SRC-038", "SRC-142"],
    }
    base["text_origin"] = "published_translation"
    base["language_tag"] = "en"
    base["language_name_as_recorded"] = "English"
    base["script_code"] = "Latn"
    base["basis_path"] = ["grc", "en"]
    base["agents"] = [{"role": "translator", "name": "Sir Lancelot Charles Lee Brenton", "authority_or_affiliation": None, "source_ids": ["SRC-038"]}]
    base["content_package"] = {
        "uri": f"../readers/{reader_file}",
        "media_type": "application/json",
        "sha256": "0" * 64,
        "format_version": "1",
        "json_pointer": "/parallel_translation",
    }
    base["coverage"] = {
        "extent_state": "complete_for_declared_edition",
        "extent_basis": "source_inventory",
        "unit_count": companion["unit_count"],
        "structure_description": f"The archived eBible.org USFM member contains {companion['chapter_count']} ordered chapters, {companion['unit_count']} numbered labels, and {companion['continuation_segment_count']} preserved unnumbered continuation segments; this is a count of the selected digital source package, not proof of printed-edition completeness.",
        "missing_or_lacunose_ranges": [],
        "supplements_and_editorial_signs": f"{companion['note_count']} footnotes and cross-references retained. The USFM \\add marker for translator-supplied words is rendered as visible ⟦brackets⟧; source \\p paragraph starts and \\d descriptive-title markers are retained before source-labeled units, and inline unnumbered \\p text is stored separately as continuation segments on the preceding verse; small-cap formatting is flattened to plain text.",
        "numbering_policy": "Source chapter and verse labels are retained as strings. Shared labels pair witnesses for navigation only; verse-level alignment with the Geʽez text has not been established.",
    }
    base["rights"] = {
        "status": "public_domain_claimed",
        "statement": "eBible.org's source notice identifies Brenton's 1851 English translation as public domain. The archive records this provider claim; it is not a worldwide legal determination and does not apply to other text layers or eBible.org page design.",
        "license_id": None,
        "rights_holder": None,
        "attribution_required": True,
        "territory_or_term_limits": "Provider-reported public-domain status; no jurisdiction-by-jurisdiction determination is claimed.",
        "evidence_source_ids": ["SRC-038", "SRC-142"],
    }
    date = "2026-10-25"
    base["review_dimensions"] = [
        {"dimension": "identity", "state": "checked_with_limits", "scope": f"eBible.org USFM member identifies this as Brenton English Septuagint {title}; no printed witness was collated.", "reviewer": None, "review_method": "combined_source_and_automated_validation", "review_process": "Archived package metadata and local member/header audit", "reviewed_at": date, "evidence_source_ids": ["SRC-038", "SRC-142"], "notes": "The provider's title and attribution are recorded; exact identity to every detail of the 1851 print edition remains unchecked."},
        {"dimension": "chapter_or_section_sequence", "state": "checked_with_limits", "scope": f"All {companion['chapter_count']} chapter markers in the identified USFM member are ordered 1–{companion['chapter_count']}.", "reviewer": None, "review_method": "automated_validation", "review_process": "Brenton USFM archive parser and integrity tests", "reviewed_at": date, "evidence_source_ids": ["SRC-142"], "notes": "Checks the archived digital source member, not completeness against the printed edition."},
        {"dimension": "unit_boundaries", "state": "checked_with_limits", "scope": f"All {companion['unit_count']} verse markers and {companion['continuation_segment_count']} unnumbered continuation segments are parsed with nonempty text; {companion['note_count']} footnotes/cross-references and structural markers {companion['structural_marker_counts']} are retained.", "reviewer": None, "review_method": "automated_validation", "review_process": "Brenton USFM parser and integrity tests", "reviewed_at": date, "evidence_source_ids": ["SRC-142"], "notes": "Structural source-package check only; not an independent textual or translation review."},
        {"dimension": "translation_accuracy", "state": "unknown", "scope": "No independent review against the Greek Septuagint or Brenton's printed 1851 edition.", "reviewer": None, "review_method": "unknown", "review_process": None, "reviewed_at": None, "evidence_source_ids": ["SRC-038", "SRC-142"], "notes": "This is not a direct translation from the bundled Geʽez text."},
        {"dimension": "rights", "state": "checked_with_limits", "scope": "eBible.org's public-domain notice for Brenton's 1851 English translation.", "reviewer": None, "review_method": "source_inspection", "review_process": "Provider copyright notice and source package metadata", "reviewed_at": date, "evidence_source_ids": ["SRC-038", "SRC-142"], "notes": "Provider-reported status; no international rights survey is claimed."},
    ]
    base["publication_state"] = "bundled"
    base["additional_notes"] = "A historical Greek-to-English Septuagint translation is paired with the distinct Geʽez source transcription for comparison. It is not an EOTC edition claim, a direct Geʽez translation, or a verified alignment. Local parser checks do not establish wording accuracy or printed-edition completeness."
    return base


def build() -> None:
    if not PACKAGE.is_file():
        raise FileNotFoundError(f"Missing archived Brenton source package: {PACKAGE}")
    package_bytes = PACKAGE.read_bytes()
    package_hash = sha256(package_bytes)
    records = []
    with zipfile.ZipFile(PACKAGE) as archive_zip:
        members = {}
        companions = {}
        for code, member_name in USFM_MEMBER.items():
            raw = archive_zip.read(member_name)
            members[member_name] = {"sha256": sha256(raw), "byte_length": len(raw)}
            companions[code] = parse_usfm(raw, code, member_name, package_hash)
        for code, (slug, _canon_number, title, expected_chapters) in BOOKS.items():
            companion = companions[code]
            reader_file = READER_FILE.get(code, f"{slug}-geez.json")
            reader_path = ROOT / "readers" / reader_file
            reader = json.loads(reader_path.read_text(encoding="utf-8"))
            if reader.get("canon_id") != CANON_ID[code]:
                raise ValueError(f"{slug} reader canon ID does not match the expected EOTC entry.")
            if companion["chapter_count"] != expected_chapters:
                raise ValueError(f"{title} USFM chapter count does not match the declared source scope.")
            reader_id = reader["reader_id"]
            reader["parallel_translation"] = companion
            reader["source_ids"] = sorted(set(reader.get("source_ids", [])) | {"SRC-038", "SRC-142"})
            reader_path.write_text(json.dumps(reader, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            geez_layer_file = GEEZ_LAYER_FILE.get(code, f"{slug}-geez-layer.json")
            sync_layer_checksum(ROOT / "examples" / geez_layer_file, reader_path)

            example_path = ROOT / "examples" / f"{slug}-brenton-translation-layer.json"
            example = make_layer(slug, title, CANON_ID[code], companion, reader_file)
            example_path.write_text(json.dumps(example, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            sync_layer_checksum(example_path, reader_path)
            records.append(example)

        capture_manifest = {
            "capture_date": "2026-10-25",
            "source_url": SOURCE_URL,
            "source_page_url": SOURCE_PAGE_URL,
            "source_notice_url": NOTICE_SOURCE,
            "archive_file": PACKAGE.name,
            "archive_sha256": package_hash,
            "archive_byte_length": len(package_bytes),
            "selected_members": members,
            "scope": "Six source package members used for Psalms, Leviticus, Numbers, Deuteronomy, Joshua, and Judges English companions. The original zip is retained; unrelated books in it are not imported by this build script.",
            "limitations": "The source provider identifies Brenton's translation as 1851 and public domain. Checks establish local package identity, parser structure, and extraction fidelity only; they do not establish print-edition completeness, Greek translation accuracy, or alignment with Geʽez.",
        }
        MANIFEST.write_text(json.dumps(capture_manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    source_record = {
        "source_id": "SRC-142",
        "source_name": "eBible.org — Brenton English Septuagint USFM package",
        "url": SOURCE_PAGE_URL,
        "inspection_and_limitations": f"The provider's Brenton page identifies Sir Lancelot Charles Lee Brenton's work as an English translation of the Greek Septuagint, published in 1851, and states that it is public domain. The archived USFM zip (SHA-256 {package_hash}; downloaded 2026-10-25) contains the six selected book members listed in readers/source/brenton-septuagint/capture-manifest.json. The local parser retains verse labels, footnotes, cross-references, paragraph starts, descriptive-title markers, and translator-supplied-word markers. These checks do not collate wording against Brenton's print edition or the Greek, prove printed-edition completeness, or establish alignment with the Geʽez witnesses. The rights statement is a provider claim, not a worldwide legal determination.",
        "archive_status": "Full source package stored locally; selected USFM members bundled as explicitly caveated English companions",
    }
    archive_path = ROOT / "archive.json"
    archive_data = json.loads(archive_path.read_text(encoding="utf-8"))
    sources = archive_data.setdefault("sources", [])
    existing_index = next((index for index, item in enumerate(sources) if item.get("source_id") == "SRC-142"), None)
    if existing_index is None:
        sources.append(source_record)
    elif sources[existing_index].get("source_name") != source_record["source_name"]:
        raise ValueError("SRC-142 is already assigned to a different source.")
    else:
        sources[existing_index] = source_record
    archive_data["sources"].sort(key=lambda item: int(item["source_id"].split("-")[1]))
    psalms = next((item for item in archive_data["catalogue"] if item.get("catalogue_id") == "eotc-027"), None)
    if psalms is None:
        raise ValueError("Expected Psalms catalogue entry eotc-027 is absent.")
    psalms.update({
        "chapter_count": "151 ordered chapters in the archived Brenton USFM witness; the accompanying Geʽez source is a 151-page TAU sequence",
        "chapter_order_status": "The archived Brenton source has 151 ordered chapter markers and the Geʽez reader preserves 151 ordered TAU page titles. Their numbering systems and contents are separate witnesses; exact textual alignment is unverified.",
        "text_availability_status": "Geʽez TAU transcription of Ludolf's Ethiopic Psalter plus Brenton's historical English translation of the Greek Septuagint; English is not translated from the bundled Geʽez witness.",
        "completeness_status": "The locally archived digital witnesses contain 151 source sections each. Brenton has 2,535 English verse labels and 88 preserved unnumbered continuation segments; the Geʽez capture has 2,537 numbered or marked units. This is a source-inventory count, not proof of completeness against print editions, manuscripts, or a Church edition.",
        "reviewer_notes": "The English companion preserves USFM paragraph starts, descriptive-title markers, footnotes, cross-references, and visible brackets for translator-supplied words. English and Geʽez are independent witnesses; the unique-label display is navigational only. Chapter numbering, wording accuracy, edition completeness, and exact Church-list crosswalk remain unverified.",
    })
    psalms["evidence_source_ids"] = list(dict.fromkeys(psalms.get("evidence_source_ids", []) + ["SRC-142"]))
    archive_path.write_text(json.dumps(archive_data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    registry_path = ROOT / "translation-registry.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    english = next(language for language in registry["languages"] if language["language_tag"] == "en")
    record_by_code = {}
    for code, (slug, _number, _title, _chapters) in BOOKS.items():
        companion = companions[code]
        canon_id = CANON_ID[code]
        reader_file = READER_FILE.get(code, f"{slug}-geez.json")
        reader = json.loads((ROOT / "readers" / reader_file).read_text(encoding="utf-8"))
        registry_record = {
            "canon_id": canon_id,
            "reader_id": reader["reader_id"],
            "translation_id": companion["translation_id"],
            "layer_role": "historical_companion_translation",
            "status": "bundled",
            "translator": "Sir Lancelot Charles Lee Brenton",
            "basis_language_tag": "grc",
            "basis_description": "Brenton's 1851 English Septuagint is based on Greek, not the accompanying Geʽez transcription. This is a historical companion witness; exact verse alignment is unverified.",
            "rights_status": "public_domain_per_cited_source",
            "rights_classification": "public_domain_claimed",
            "source_ids": ["SRC-038", "SRC-142"],
            "translation_path": ["grc", "en"],
        }
        english["records"] = [item for item in english["records"] if item.get("translation_id") != companion["translation_id"]]
        english["records"].append(registry_record)
        record_by_code[code] = companion
    english["records"].sort(key=lambda item: (item["canon_id"], item.get("translation_id", "")))
    english["source_ids"] = sorted(set(english.get("source_ids", [])) | {"SRC-142"})

    canon_path = ROOT / "canon-registry.json"
    canon = json.loads(canon_path.read_text(encoding="utf-8"))
    for code, (_slug, _num, _title, _chapters) in BOOKS.items():
        entry = next(item for item in canon["books"] if item["canon_id"] == CANON_ID[code])
        entry["reader_status"] = "Bundled: Geʽez source transcription + Brenton English Septuagint companion (Greek basis; independent witness, alignment unverified)"
    registry["coverage_statement"] = build_coverage_statement(registry, canon)
    canon_path.write_text(json.dumps(canon, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    registry_path.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Built Brenton companions:")
    for code, (_slug, _num, title, _chapters) in BOOKS.items():
        companion = record_by_code[code]
        marker_report = ", ".join(f"\\{marker}={count}" for marker, count in sorted(companion.get("structural_marker_counts", {}).items())) or "no paragraph/title markers"
        print(f"  {title}: {companion['chapter_count']} chapters, {companion['unit_count']} verse labels, {companion['note_count']} notes/references, {marker_report}")


def validate() -> None:
    """Fail if source bytes, parsed layers, or portable metadata have drifted."""
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    package_hash = sha256(PACKAGE.read_bytes())
    if package_hash != manifest.get("archive_sha256"):
        raise ValueError("Archived Brenton USFM package checksum differs from its capture manifest.")
    with zipfile.ZipFile(PACKAGE) as archive_zip:
        if not set(USFM_MEMBER.values()).issubset(manifest["selected_members"]):
            raise ValueError("Brenton USFM capture manifest is missing one or more selected companion members.")
        for code, (slug, _num, title, _chapters) in BOOKS.items():
            member = USFM_MEMBER[code]
            raw = archive_zip.read(member)
            member_metadata = manifest["selected_members"][member]
            if len(raw) != member_metadata["byte_length"] or sha256(raw) != member_metadata["sha256"]:
                raise ValueError(f"Brenton source member checksum/length mismatch: {member}.")
            expected = parse_usfm(raw, code, member, package_hash)
            reader_file = READER_FILE.get(code, f"{slug}-geez.json")
            reader_path = ROOT / "readers" / reader_file
            reader = json.loads(reader_path.read_text(encoding="utf-8"))
            if reader.get("parallel_translation") != expected:
                raise ValueError(f"Bundled {title} companion does not exactly match the archived USFM parser output.")
            layer_path = ROOT / "examples" / f"{slug}-brenton-translation-layer.json"
            layer = json.loads(layer_path.read_text(encoding="utf-8"))
            if layer.get("content_package", {}).get("sha256") != sha256(reader_path.read_bytes()):
                raise ValueError(f"Portable layer checksum is stale: {layer_path.name}.")
            translation_accuracy = next((item for item in layer.get("review_dimensions", [])
                                          if item.get("dimension") == "translation_accuracy"), {})
            if (layer.get("coverage", {}).get("unit_count") != expected["unit_count"]
                    or layer.get("publication_state") != "bundled"
                    or translation_accuracy.get("state") != "unknown"):
                raise ValueError(f"Portable layer scope or review state is invalid: {layer_path.name}.")

    archive_data = json.loads((ROOT / "archive.json").read_text(encoding="utf-8"))
    psalms = next((item for item in archive_data["catalogue"] if item.get("catalogue_id") == "eotc-027"), None)
    psalms_reader = json.loads((ROOT / "readers" / READER_FILE["PSA"]).read_text(encoding="utf-8"))
    if psalms is None or psalms.get("completeness_status", "").find("88 preserved unnumbered continuation segments") < 0:
        raise ValueError("Psalms catalogue metadata does not report the measured Brenton continuation segments.")
    if "not translated from the bundled Geʽez witness" not in psalms.get("text_availability_status", ""):
        raise ValueError("Psalms catalogue metadata must distinguish the English Septuagint from Geʽez.")
    if psalms_reader.get("parallel_translation", {}).get("continuation_segment_count") != 88:
        raise ValueError("Bundled Psalms English continuation segment count is missing or stale.")
    registry = json.loads((ROOT / "translation-registry.json").read_text(encoding="utf-8"))
    english = next(language for language in registry["languages"] if language["language_tag"] == "en")
    if not any(record.get("translation_id") == "psalms-english-brenton-lxx-1851" and record.get("status") == "bundled" for record in english["records"]):
        raise ValueError("Psalms Brenton translation is missing from the English language registry.")
    canon = json.loads((ROOT / "canon-registry.json").read_text(encoding="utf-8"))
    psalms_entry = next((item for item in canon["books"] if item.get("canon_id") == CANON_ID["PSA"]), None)
    if psalms_entry is None or "Brenton English Septuagint companion" not in psalms_entry.get("reader_status", ""):
        raise ValueError("Psalms canon registry omits the separate Brenton English companion.")


if __name__ == "__main__":
    build()
