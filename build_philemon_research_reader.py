"""Build a pinned, research-only Philemon reader from its licensed TEI file."""

from __future__ import annotations

import hashlib
import json
from archive_manifest import write_text_atomically
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCE_PATH = ROOT / "readers/source/philemon/LIT3528Epistle.xml"
COMMIT = "9029473659ab6efc4035ee52b9922192c99ba75e"
WORK_ID = "LIT3528Epistle"
SOURCE_ID = "SRC-277"
READER_ID = "philemon-betamasaheft-tei-research"
CORPUS_ID = "betamasaheft-philemon-tei-research"
LICENSE = "https://creativecommons.org/licenses/by-sa/4.0/"
TEI = "http://www.tei-c.org/ns/1.0"
XML = "http://www.w3.org/XML/1998/namespace"


def norm(node: ET.Element) -> str:
    return " ".join("".join(node.itertext()).split())


def build() -> dict:
    raw = SOURCE_PATH.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != "1a2597840fe862777544855e9f9924de13d45102776dff8d5c03c201f024f130":
        raise ValueError(f"Pinned Philemon TEI checksum changed: {digest}")
    root = ET.fromstring(raw)
    if root.get(f"{{{XML}}}id") != WORK_ID or root.get(f"{{{XML}}}lang") != "en":
        raise ValueError("Unexpected Philemon TEI identity or root language metadata")
    license_node = next((x for x in root.iter(f"{{{TEI}}}licence") if x.get("target", "").rstrip("/").endswith("by-sa/4.0")), None)
    if license_node is None:
        raise ValueError("No file-level CC BY-SA 4.0 notice in pinned TEI")
    edition = next((x for x in root.iter(f"{{{TEI}}}div") if x.get("type") == "edition"), None)
    if edition is None:
        raise ValueError("No TEI edition division")
    parts = {x.get(f"{{{XML}}}id"): x for x in edition.findall(f"{{{TEI}}}div") if x.get("type") == "textpart"}
    epistle = parts.get("Epistle")
    introduction = parts.get("Introduction")
    if epistle is None or epistle.get(f"{{{XML}}}lang") != "gez" or introduction is None:
        raise ValueError("Expected Geʽez Epistle and Introduction textparts")
    chapters = [x for x in epistle.iter(f"{{{TEI}}}div") if x.get("subtype") == "chapter"]
    if [x.get("n") for x in chapters] != ["1"]:
        raise ValueError("Unexpected Philemon chapter divisions")

    units = []
    source_lines = list(chapters[0].iter(f"{{{TEI}}}l"))
    for order, line in enumerate(source_lines, 1):
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
    numbered = sum(x.get("n") is not None for x in source_lines)
    if (len(source_lines), numbered) != (28, 25):
        raise ValueError(f"Unexpected Philemon line inventory: {len(source_lines)} total, {numbered} labeled")

    source_url = f"https://github.com/BetaMasaheft/Works/blob/{COMMIT}/3001-4000/LIT3528Epistle.xml"
    reader = {
        "reader_id": READER_ID,
        "research_corpus_id": CORPUS_ID,
        "text_origin": "source_transcription",
        "title": "Philemon — Geʽez TEI research transcription (EOTC link unverified)",
        "display_name": "Philemon · Geʽez · research text; EOTC link unverified",
        "language": "Geʽez (Classical Ethiopic)",
        "language_tag": "gez",
        "language_assignment_status": "explicit_xml_lang_on_Epistle_textpart",
        "script_code": "Ethi",
        "edition": f"Beta maṣāḥǝft {WORK_ID} TEI, pinned at Works commit {COMMIT}",
        "edition_scope": "The TEI title names the Epistle to Philemon and its Epistle textpart explicitly declares Geʽez. The document root declares English, and the edition includes an empty-source citation note. Its bibliography cites Uhlig and Maehlum’s 1993 Die Gefangenschaftsbriefe, but the TEI does not clearly identify that citation as the exact basis of this transcription. It does not say the text is from an EOTC printed Bible. This is a research witness, not an EOTC-verified text or an established canon crosswalk.",
        "section_label": "Epistle",
        "unit_label": "TEI line element (all labeled and unlabeled elements)",
        "source_ids": [SOURCE_ID],
        "source_snapshot_sha256": digest,
        "rights_classification": "open_license",
        "copyright_notice": "The retained Beta maṣāḥǝft TEI file states CC BY-SA 4.0. Attribute Beta maṣāḥǝft, link the pinned source and license, disclose extraction and whitespace normalization, and share adaptations alike. The file-level license notice does not independently establish rights in the cited or unidentified underlying printed exemplar.",
        "commercial_use": "The TEI file states CC BY-SA 4.0; reuse of that file is subject to attribution, change notice, and ShareAlike. Rights in the underlying edition or exemplar are not independently established.",
        "license_id": "CC-BY-SA-4.0",
        "license_url": LICENSE,
        "chapter_count": 1,
        "unit_count": len(units),
        "source_numbered_unit_count": numbered,
        "source_unnumbered_unit_count": len(units) - numbered,
        "source_empty_unit_count": sum(not x["text"] for x in units),
        "chapter_structure_note": "The TEI explicitly marks one chapter (n=1). All 28 source line elements are retained in order; 25 carry numeric n labels and three are unlabeled heading/section lines. Their wording is retained as source lines without assigning verse labels.",
        "transcription_note": "Every TEI line element inside the Epistle chapter division is retained in source order. Display whitespace is normalized and inline markup is flattened; the pinned original TEI remains bundled unchanged. The separate Introduction textpart contains only its label and is preserved in the raw TEI, not rendered as chapter text.",
        "chapters": [{
            "chapter": 1,
            "source_chapter_label": "1",
            "heading": ["Epistle"],
            "units": units,
            "notes": [],
        }],
        "verification_status": "Pinned source hash, TEI work identity, file-level license statement, Geʽez textpart declaration, one chapter division, all 28 line elements, and exact line extraction checked. Textual accuracy and completeness are unverified; no print-exemplar identification, EOTC edition confirmation, or canon crosswalk is claimed.",
    }
    (ROOT / "readers" / f"{READER_ID}.json").write_text(json.dumps(reader, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    archive_path = ROOT / "archive.json"
    archive = json.loads(archive_path.read_text(encoding="utf-8"))
    sources = {x["source_id"]: x for x in archive["sources"]}
    sources[SOURCE_ID] = {
        "source_id": SOURCE_ID,
        "source_name": f"Beta maṣāḥǝft Works — pinned {WORK_ID} Geʽez Philemon TEI",
        "url": source_url,
        "inspection_and_limitations": f"Retrieved from BetaMasaheft/Works commit {COMMIT} and retained unchanged at readers/source/philemon/LIT3528Epistle.xml ({len(raw):,} bytes; SHA-256 {digest}). The TEI root declares xml:lang=en, while its Epistle textpart declares xml:lang=gez; the archive follows the local textpart for the reader language and preserves this metadata conflict. Its Introduction textpart contains only its label. The Epistle has one chapter division with 28 line elements (25 labeled, 3 unlabeled), all retained in order. The file states CC BY-SA 4.0. Its bibliography cites Uhlig and Maehlum 1993 but the edition note says 'All excerpts are taken from .' with no source supplied; the exact textual basis is unresolved. No EOTC printed-Bible note is present. Underlying print rights, exact exemplar, accuracy, completeness, and canon mapping remain unverified. Inspected 2026-10-25; no generated or translated wording added.",
        "archive_status": "Pinned, file-level CC BY-SA TEI retained locally; source structure and extraction checked; exact edition basis, underlying print rights, accuracy, completeness, and EOTC relationship unverified",
    }
    archive["sources"] = sorted(sources.values(), key=lambda x: int(x["source_id"].split("-")[1]))
    write_text_atomically(archive_path, json.dumps(archive, ensure_ascii=False, indent=2) + "\n")

    registry_path = ROOT / "translation-registry.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    corpora = {x["corpus_id"]: x for x in registry.get("research_corpora", [])}
    corpora[CORPUS_ID] = {
        "corpus_id": CORPUS_ID,
        "title": "Philemon (Geʽez) — Beta maṣāḥǝft TEI research transcription",
        "reader_id": READER_ID,
        "unit_count": len(units),
        "reader_status": "bundled_research_reader",
        "canon_mapping_state": "uncertain",
        "candidate_canon_id": "eotc-nt-18",
        "canon_mapping_note": "The title matches Church-list Philemon, but this TEI has no EOTC printed-Bible note and its exact underlying edition basis is unclear. This title candidate is research-only and excluded from canon-linked reader coverage; coverage counts are derived from the current bundled records.",
        "language_description": "The Epistle textpart explicitly declares Geʽez (gez); the document root has an English default, retained as a metadata conflict.",
        "script_description": "Ethiopic script (Ethi) is present in the retained source text.",
        "unit_summary": "One source-marked chapter with all 28 TEI line elements retained in order (25 labeled and 3 unlabeled).",
        "rights_classification": "open_license",
        "rights_status": "The TEI file states CC BY-SA 4.0. This file-level license does not independently establish rights in the cited or unidentified printed exemplar.",
        "license_id": "CC-BY-SA-4.0",
        "license_url": LICENSE,
        "review_status": "Automated source hash, language declaration, license declaration, chapter division, source line count/labels, and exact extraction checked. Textual accuracy, print completeness, exact exemplar, underlying rights, and canon affiliation remain unverified.",
        "source_ids": [SOURCE_ID],
        "text_origin": "source_transcription",
        "language_tag": "gez",
        "script_code": "Ethi",
        "translation_id": None,
        "translator": None,
        "translation_basis_status": "not_applicable_source_transcription",
        "translation_basis_note": "This is a Geʽez source transcription, not an English translation.",
        "edition_statement": f"Beta maṣāḥǝft {WORK_ID}, pinned at {COMMIT}; TEI bibliography cites Uhlig and Maehlum 1993, but the supplied-from note is blank and exact textual basis is unresolved.",
    }
    registry["research_corpora"] = sorted(corpora.values(), key=lambda x: x["corpus_id"])
    registry_path.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    audit_path = ROOT / "readers/source/philemon/SOURCE-AUDIT.md"
    audit_path.write_text(
        f"# Philemon TEI source audit\n\n"
        f"Pinned `LIT3528Epistle.xml` at BetaMasaheft/Works commit `{COMMIT}`. The retained file is {len(raw):,} bytes with SHA-256 `{digest}`. Its title identifies the Epistle to Philemon; the Epistle textpart declares Geʽez (`gez`), although the TEI root default is English. The file declares CC BY-SA 4.0.\n\n"
        "The Epistle textpart has one explicit chapter division and 28 TEI line elements: 25 labeled elements and three unlabeled heading/section lines. All are preserved in order. The separate Introduction textpart contains only its heading label.\n\n"
        "The TEI bibliography cites Uhlig and Maehlum’s 1993 *Die Gefangenschaftsbriefe*, but the edition note reads ‘All excerpts are taken from .’ with no source supplied. The precise textual basis is therefore unresolved. No EOTC printed-Bible note is present. The title match to Church-list Philemon is only a candidate and is excluded from canon-linked coverage. The file-level license does not independently settle rights in the underlying printed exemplar. No independent collation or completeness review has been performed.\n\n"
        f"Source: [{WORK_ID} at pinned commit]({source_url}).\n",
        encoding="utf-8",
    )
    return reader


if __name__ == "__main__":
    result = build()
    print(f"Built {result['reader_id']}: {result['chapter_count']} chapter, {result['unit_count']} lines; EOTC affiliation remains unverified.")
