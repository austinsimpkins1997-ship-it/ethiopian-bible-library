"""Build a research-only Isaiah reader from a pinned Beta maṣāḥǝft TEI file."""

from __future__ import annotations

import hashlib
import json
from archive_manifest import write_text_atomically
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCE_PATH = ROOT / "readers/source/isaiah/LIT1672Isaiah.xml"
COMMIT = "9029473659ab6efc4035ee52b9922192c99ba75e"
WORK_ID = "LIT1672Isaiah"
SOURCE_ID = "SRC-278"
READER_ID = "isaiah-betamasaheft-tei-research"
CORPUS_ID = "betamasaheft-isaiah-tei-research"
LICENSE = "https://creativecommons.org/licenses/by-sa/4.0/"
TEI = "http://www.tei-c.org/ns/1.0"
XML = "http://www.w3.org/XML/1998/namespace"


def norm(node: ET.Element) -> str:
    return " ".join("".join(node.itertext()).split())


def build() -> dict:
    raw = SOURCE_PATH.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    expected_digest = "5310b41b3f3f7ead567321b44b6333fafea99102f54f37b0ad43e7436da95a53"
    if digest != expected_digest:
        raise ValueError(f"Pinned Isaiah TEI checksum changed: {digest}")
    root = ET.fromstring(raw)
    if root.get(f"{{{XML}}}id") != WORK_ID or root.get(f"{{{XML}}}lang") != "en":
        raise ValueError("Unexpected Isaiah TEI identity or document-default language")
    license_node = next((x for x in root.iter(f"{{{TEI}}}licence") if x.get("target", "").rstrip("/").endswith("by-sa/4.0")), None)
    if license_node is None:
        raise ValueError("No file-level CC BY-SA 4.0 statement in pinned Isaiah TEI")
    edition = next((x for x in root.iter(f"{{{TEI}}}div") if x.get("type") == "edition"), None)
    if edition is None or edition.get(f"{{{XML}}}lang") != "gez":
        raise ValueError("No explicit Geʽez Isaiah edition division")
    chapters = [x for x in edition if x.get("type") == "textpart" and x.get("subtype") == "chapter"]
    if [x.get("n") for x in chapters] != [str(i) for i in range(1, 67)]:
        raise ValueError("Isaiah chapter divisions are not the expected ordered 1–66")
    chapter_data = []
    total_lines = 0
    for chapter_order, chapter in enumerate(chapters, 1):
        lines = list(chapter.iter(f"{{{TEI}}}l"))
        labels = [line.get("n") for line in lines]
        if labels != [str(i) for i in range(1, len(lines) + 1)]:
            raise ValueError(f"Unexpected Isaiah source labels in chapter {chapter_order}")
        units = []
        for order, line in enumerate(lines, 1):
            text = norm(line)
            unit = {
                "number": order,
                "unit_order": order,
                "source_marker": line.get("n"),
                "source_element_id": line.get(f"{{{XML}}}id"),
                "source_refs": [x.get("target") for x in line.iter(f"{{{TEI}}}ref") if x.get("target")],
                "text": text,
            }
            if not text:
                unit["source_text_state"] = "empty_source_element"
            units.append(unit)
        label = next((norm(x) for x in chapter if x.tag == f"{{{TEI}}}label"), f"Chapter {chapter_order}")
        chapter_data.append({
            "chapter": chapter_order,
            "source_chapter_label": chapter.get("n"),
            "heading": [label],
            "units": units,
            "notes": [],
        })
        total_lines += len(lines)
    if total_lines != 1289:
        raise ValueError(f"Unexpected Isaiah TEI line count: {total_lines}")

    source_url = f"https://github.com/BetaMasaheft/Works/blob/{COMMIT}/1001-2000/LIT1672Isaiah.xml"
    reader = {
        "reader_id": READER_ID,
        "research_corpus_id": CORPUS_ID,
        "text_origin": "source_transcription",
        "title": "Isaiah — Geʽez TEI research transcription (EOTC link unverified)",
        "display_name": "Isaiah · Geʽez · research text; EOTC link unverified",
        "language": "Geʽez (Classical Ethiopic)",
        "language_tag": "gez",
        "language_assignment_status": "explicit_xml_lang_on_edition_division",
        "script_code": "Ethi",
        "edition": f"Beta maṣāḥǝft {WORK_ID} TEI, pinned at Works commit {COMMIT}",
        "edition_scope": "The TEI title identifies the Book of Isaiah, and the edition division explicitly declares Geʽez. Its TEI bibliography points to Bachmann1893Jesaia, while Beta maṣāḥǝft’s work record gives the full Bachmann 1893 edition citation. The TEI does not state that this text is transcribed from that edition or from a current EOTC printed Bible. The document root declares English; that metadata conflict is preserved. This is a research witness, not an EOTC-verified text or established canon crosswalk.",
        "section_label": "Book of Isaiah",
        "unit_label": "TEI line element (source verse label retained)",
        "source_ids": ["SRC-029", "SRC-034", "SRC-036", SOURCE_ID],
        "source_snapshot_sha256": digest,
        "rights_classification": "open_license",
        "copyright_notice": "The retained Beta maṣāḥǝft TEI file states CC BY-SA 4.0. Attribute Beta maṣāḥǝft, link the pinned source and license, disclose extraction and whitespace normalization, and share adaptations alike. Beta maṣāḥǝft’s displayed site footer separately states CC BY-NC-SA 4.0; this archive records the file-level notice without independently resolving the relationship between those notices. Neither notice is treated here as proof of rights in the historical printed edition or manuscripts.",
        "commercial_use": "The TEI file states CC BY-SA 4.0, subject to attribution, change notice, and ShareAlike. The site also displays a separate CC BY-NC-SA 4.0 footer; the relationship between the two notices and rights in the underlying printed text have not been independently adjudicated.",
        "license_id": "CC-BY-SA-4.0",
        "license_url": LICENSE,
        "chapter_count": len(chapter_data),
        "unit_count": total_lines,
        "source_numbered_unit_count": total_lines,
        "source_unnumbered_unit_count": 0,
        "source_empty_unit_count": sum(not unit["text"] for ch in chapter_data for unit in ch["units"]),
        "chapter_structure_note": "The pinned TEI has 66 ordered chapter divisions, labeled 1–66, and 1,289 line elements. Within each chapter, source n labels are sequential from 1 with no gaps or duplicates in this file. These are structural checks against this TEI only; they do not prove the source edition is complete or textually accurate.",
        "transcription_note": "Every TEI line element in the Geʽez edition’s 66 chapter divisions is retained in source order. Source labels and associated reference targets are preserved. Display whitespace is normalized and inline markup is flattened; the original pinned TEI is bundled unchanged. No wording or labels are supplied or corrected.",
        "chapters": chapter_data,
        "verification_status": "Pinned source hash, TEI work identity, file-level license notice, Geʽez language declaration, ordered chapter divisions, all line elements, labels, and exact normalized line extraction checked. Textual accuracy, completeness, exact source edition, EOTC edition identity, and canon affiliation remain unverified.",
    }
    (ROOT / "readers" / f"{READER_ID}.json").write_text(json.dumps(reader, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    archive_path = ROOT / "archive.json"
    archive = json.loads(archive_path.read_text(encoding="utf-8"))
    sources = {x["source_id"]: x for x in archive["sources"]}
    sources[SOURCE_ID] = {
        "source_id": SOURCE_ID,
        "source_name": f"Beta maṣāḥǝft Works — pinned {WORK_ID} Geʽez Isaiah TEI",
        "url": source_url,
        "inspection_and_limitations": f"Retrieved from BetaMasaheft/Works commit {COMMIT} and retained unchanged at readers/source/isaiah/LIT1672Isaiah.xml ({len(raw):,} bytes; SHA-256 {digest}). The TEI root declares xml:lang=en, while the edition division declares xml:lang=gez; the reader follows the edition division and preserves the conflict. The file-level availability element states CC BY-SA 4.0; the provider page separately displays a CC BY-NC-SA 4.0 site footer, and the relationship is not independently resolved here. Its bibliography pointer is bm:Bachmann1893Jesaia; the Beta maṣāḥǝft work record cites Bachmann 1893, but the TEI does not explicitly say this text is transcribed from that edition. The 66 chapter divisions are ordered 1–66; their 1,289 line labels are sequential within each chapter and are all retained. Structural consistency does not establish completeness or accuracy. No EOTC printed-Bible note is present. Exact edition basis, print rights, accuracy, completeness, and canon mapping remain unverified. Inspected 2026-10-25; no wording was translated, generated, or corrected.",
        "archive_status": "Pinned, file-level CC BY-SA TEI retained locally; language, chapter/label structure and extraction checked; site-wide license relationship, exact edition basis, underlying rights, accuracy, completeness, and EOTC relationship remain unresolved",
    }
    archive["sources"] = sorted(sources.values(), key=lambda x: int(x["source_id"].split("-")[1]))
    write_text_atomically(archive_path, json.dumps(archive, ensure_ascii=False, indent=2) + "\n")

    registry_path = ROOT / "translation-registry.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    corpora = {x["corpus_id"]: x for x in registry.get("research_corpora", [])}
    corpora[CORPUS_ID] = {
        "corpus_id": CORPUS_ID,
        "title": "Isaiah (Geʽez) — Beta maṣāḥǝft TEI research transcription",
        "reader_id": READER_ID,
        "unit_count": total_lines,
        "reader_status": "bundled_research_reader",
        "canon_mapping_state": "uncertain",
        "candidate_canon_id": "eotc-ot-29",
        "canon_mapping_note": "The TEI work title matches Church-list Isaiah, but the TEI does not say it is the EOTC printed Bible and does not establish textual completeness, accuracy, or exact edition identity. This is a title candidate only and is excluded from canon-linked coverage.",
        "language_description": "The edition division explicitly declares Geʽez (gez); the TEI root declares English, retained as a document-default conflict.",
        "script_description": "The retained text uses Ethiopic script (Ethi).",
        "unit_summary": "66 source chapter divisions and 1,289 TEI line elements; every line has a sequential within-chapter source label.",
        "rights_classification": "open_license",
        "rights_status": "The retained TEI file states CC BY-SA 4.0. Beta maṣāḥǝft’s site footer separately states CC BY-NC-SA 4.0; their relationship is unresolved. Neither statement independently proves rights in the underlying printed edition or manuscript witnesses.",
        "license_id": "CC-BY-SA-4.0",
        "license_url": LICENSE,
        "review_status": "Automated source hash, declared language, file-level license notice, chapter sequence, label sequence, line count, and extraction checked. No independent proofreading, completeness review, source-edition identification, underlying rights adjudication, or EOTC affiliation review has been performed.",
        "source_ids": ["SRC-029", "SRC-034", "SRC-036", SOURCE_ID],
        "text_origin": "source_transcription",
        "language_tag": "gez",
        "script_code": "Ethi",
        "translation_id": None,
        "translator": None,
        "translation_basis_status": "not_applicable_source_transcription",
        "translation_basis_note": "This is a Geʽez source transcription, not an English translation.",
        "edition_statement": f"Beta maṣāḥǝft {WORK_ID}, pinned at {COMMIT}; bibliography pointer bm:Bachmann1893Jesaia, without an explicit statement that this exact text is transcribed from Bachmann 1893.",
    }
    registry["research_corpora"] = sorted(corpora.values(), key=lambda x: x["corpus_id"])
    registry_path.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    audit_path = ROOT / "readers/source/isaiah/SOURCE-AUDIT.md"
    audit_path.write_text(
        f"# Isaiah TEI source audit\n\n"
        f"Pinned `LIT1672Isaiah.xml` at BetaMasaheft/Works commit `{COMMIT}`. The retained file is {len(raw):,} bytes with SHA-256 `{digest}`. The TEI title identifies the Book of Isaiah; its edition division explicitly declares Geʽez (`gez`), while the document root declares English. The TEI file states CC BY-SA 4.0, while the provider’s displayed site footer separately states CC BY-NC-SA 4.0; this archive records both notices without resolving their relationship.\n\n"
        "The source contains 66 ordered chapter divisions labeled 1–66 and 1,289 line elements. Every line is numbered; within each chapter, labels are sequential with no gap or duplicate in the pinned file. All line elements and linked reference targets are retained. This verifies extraction against the pinned TEI only, not accuracy or completeness against a print edition or manuscript.\n\n"
        "The TEI bibliographic pointer is `bm:Bachmann1893Jesaia`; Beta maṣāḥǝft’s work page cites Bachmann’s 1893 Ethiopic edition. The TEI does not explicitly identify that edition as the source of this exact transcription. It contains no EOTC printed-Bible note. Accordingly, the Isaiah title match is a research candidate only; this reader is excluded from canon-linked coverage. Exact source basis, underlying print rights, transcription accuracy, and completeness remain unverified.\n\n"
        f"Source: [{WORK_ID} at pinned commit]({source_url}) · [Beta maṣāḥǝft work record](https://betamasaheft.awhamburg.de/works/LIT1672Isaiah/main).\n",
        encoding="utf-8",
    )
    return reader


if __name__ == "__main__":
    result = build()
    print(f"Built {result['reader_id']}: {result['chapter_count']} chapters, {result['unit_count']} lines; EOTC affiliation remains unverified.")
