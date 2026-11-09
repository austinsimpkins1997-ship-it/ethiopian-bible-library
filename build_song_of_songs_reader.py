"""Build the EOTCed Song of Songs reader from a pinned Beta maṣāḥǝft TEI."""

from __future__ import annotations

import hashlib
import json
from archive_manifest import write_text_atomically
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent
COMMIT = "ec53d3f4c5de47e463fa56a8465cf1090316a999"
WORK_ID = "LIT2362Songof"
SOURCE_DIR = ROOT / "readers" / "source" / "song-of-songs"
SOURCE_PATH = SOURCE_DIR / f"{WORK_ID}.xml"
SOURCE_PAGE_ID = "SRC-292"
SOURCE_FILE_ID = "SRC-293"
READER_ID = "song-of-songs-geez-betamasaheft-eotced"
CANON_ID = "eotc-ot-28"
CATALOGUE_ID = "eotc-028"
LICENSE = "https://creativecommons.org/licenses/by-sa/4.0/"
TEI = "http://www.tei-c.org/ns/1.0"
XML = "http://www.w3.org/XML/1998/namespace"
EXPECTED_SHA256 = "9f8be720efd8f336ef46835433576427bdf6485a0187561dd3a1b1eba57acf01"


def norm(node: ET.Element) -> str:
    return " ".join("".join(node.itertext()).split())


def build() -> dict:
    raw = SOURCE_PATH.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != EXPECTED_SHA256:
        raise ValueError(f"Pinned Song of Songs TEI checksum changed: {digest}")
    root = ET.fromstring(raw)
    if root.get(f"{{{XML}}}id") != WORK_ID or root.get(f"{{{XML}}}lang") != "en":
        raise ValueError("Unexpected Song of Songs TEI identity or document-default language")
    licence = next((x for x in root.iter(f"{{{TEI}}}licence") if "creativecommons.org/licenses/by-sa/4.0" in x.get("target", "")), None)
    if licence is None:
        raise ValueError("No file-level CC BY-SA 4.0 statement in pinned Song of Songs TEI")
    editions = [x for x in root.iter(f"{{{TEI}}}div") if x.get("type") == "edition"]
    edition = next((x for x in editions if x.get(f"{{{XML}}}id") == "EOTCed"), None)
    if edition is None or edition.get(f"{{{XML}}}lang") != "gez":
        raise ValueError("No explicit Geʽez EOTCed text division")
    notes = [norm(x) for x in edition.iter(f"{{{TEI}}}note")]
    if "Text of the EOTC printed Bible" not in notes:
        raise ValueError("EOTCed division does not identify the text as an EOTC printed Bible text")
    changes = [norm(x) for x in root.iter(f"{{{TEI}}}change")]
    if not any("added text from EOTC Bible edition" in item for item in changes):
        raise ValueError("TEI revision history does not record the EOTC Bible text addition")

    divisions = [x for x in edition if x.tag == f"{{{TEI}}}div" and x.get("subtype") == "chapter"]
    if [x.get("n") for x in divisions] != [str(i) for i in range(1, 9)]:
        raise ValueError("EOTCed Song of Songs does not have the expected ordered chapter divisions 1–8")
    chapters = []
    line_count = 0
    label_duplicates = []
    for order, division in enumerate(divisions, start=1):
        lines = list(division.iter(f"{{{TEI}}}l"))
        labels = [line.get("n") for line in lines]
        expected = [str(i) for i in range(1, len(lines) + 1)]
        if labels != expected:
            duplicates = sorted({x for x in labels if labels.count(x) > 1}, key=int)
            if not (order == 8 and labels == [str(i) for i in range(1, 15)] + ["14", "15", "16"] and duplicates == ["14"]):
                raise ValueError(f"Unexpected Song of Songs source labels in chapter {order}: {labels}")
            label_duplicates.append({"chapter": order, "source_marker": "14", "occurrences": 2})
        units = []
        for unit_order, line in enumerate(lines, start=1):
            text = norm(line)
            unit = {
                "number": unit_order,
                "unit_order": unit_order,
                "source_marker": line.get("n"),
                "source_element_id": line.get(f"{{{XML}}}id"),
                "source_refs": [ref.get("target") for ref in line.iter(f"{{{TEI}}}ref") if ref.get("target")],
                "text": text,
            }
            if not text:
                unit["source_text_state"] = "empty_source_element"
            units.append(unit)
        heading = next((norm(x) for x in division if x.tag == f"{{{TEI}}}label"), str(order))
        chapters.append({"chapter": order, "source_chapter_label": division.get("n"), "heading": [heading], "units": units, "notes": []})
        line_count += len(lines)
    if line_count != 131 or label_duplicates != [{"chapter": 8, "source_marker": "14", "occurrences": 2}]:
        raise ValueError(f"Unexpected line count or source-label anomaly: {line_count}, {label_duplicates}")

    source_url = f"https://github.com/BetaMasaheft/Works/blob/{COMMIT}/2001-3000/{WORK_ID}.xml"
    reader = {
        "reader_id": READER_ID,
        "canon_id": CANON_ID,
        "text_origin": "source_transcription",
        "title": "Song of Songs — Geʽez EOTCed text transcription",
        "display_name": "Song of Songs · Geʽez · EOTCed text",
        "language": "Geʽez (Classical Ethiopic)",
        "language_tag": "gez",
        "language_assignment_status": "explicit_xml_lang_on_EOTCed_edition; document root separately declares English",
        "script_code": "Ethi",
        "edition": f"Beta maṣāḥǝft {WORK_ID} TEI, EOTCed division, pinned at Works commit {COMMIT}",
        "edition_scope": (
            "The selected EOTCed division explicitly declares Geʽez, is labeled ‘Text of the EOTC printed Bible,’ and the TEI revision history says EOTC Bible text was added on 2025-06-05. The work record also says the text in the record was digitized from modern Vulgata printed editions and converted to XML; the exact print exemplar and relationship among these statements are not identified. This supports a source-asserted EOTC title link, not exact edition identity or textual correctness."
        ),
        "section_label": "Song of Songs",
        "unit_label": "TEI line element (source n marker preserved; not independently verified as a verse number)",
        "source_ids": ["SRC-029", "SRC-034", "SRC-176", SOURCE_PAGE_ID, SOURCE_FILE_ID],
        "source_snapshot_sha256": digest,
        "rights_classification": "open_license",
        "copyright_notice": (
            "The pinned TEI file states CC BY-SA 4.0. Attribute Beta maṣāḥǝft, link the pinned file and license, disclose extraction/whitespace normalization, and share adaptations alike. The provider site footer separately states CC BY-NC-SA 4.0; the relation between these notices remains unresolved. The file-level notice does not establish rights in the unidentified printed exemplar."
        ),
        "commercial_use": "The file states CC BY-SA 4.0, subject to its terms; the site separately displays CC BY-NC-SA 4.0, and the relationship is unresolved. Underlying print rights are not established.",
        "license_id": "CC-BY-SA-4.0",
        "license_url": LICENSE,
        "chapter_count": len(chapters),
        "unit_count": line_count,
        "source_numbered_unit_count": line_count,
        "source_unnumbered_unit_count": 0,
        "source_empty_unit_count": sum(not unit["text"] for chapter in chapters for unit in chapter["units"]),
        "chapter_structure_note": (
            "The selected EOTCed text has eight ordered chapter divisions. It contains 131 nonempty TEI line elements; source n markers are sequential in chapters 1–7. Chapter 8 contains 17 lines but repeats source marker 14 and then continues with 15 and 16. That duplicate is preserved and is not corrected or reinterpreted. Structural checks do not prove the printed edition is complete or accurate."
        ),
        "transcription_note": "Every TEI line element within the EOTCed division is retained in source order with its source n marker. Display whitespace is normalized and inline markup flattened; the pinned original TEI is bundled unchanged. No wording or labels are supplied or corrected.",
        "chapters": chapters,
        "verification_status": (
            "Pinned source hash, TEI identity, file-level license notice, EOTCed Geʽez language declaration, EOTC text note, revision history, eight chapter divisions, all 131 line elements, and source labels checked. Chapter 8 source marker 14 is duplicated and preserved. The source’s generic modern-Vulgata statement and EOTC-specific notes are both recorded; exact print exemplar and their relationship remain unresolved. No independent proofreading or collation was performed; accuracy and completeness are unverified."
        ),
    }
    (ROOT / "readers" / f"{READER_ID}.json").write_text(json.dumps(reader, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    archive_path = ROOT / "archive.json"
    archive = json.loads(archive_path.read_text(encoding="utf-8"))
    source_map = {x["source_id"]: x for x in archive["sources"]}
    source_map[SOURCE_PAGE_ID] = {
        "source_id": SOURCE_PAGE_ID,
        "source_name": "Beta maṣāḥǝft — Song of Songs (LIT2362Songof) work record",
        "url": "https://betamasaheft.awhamburg.de/works/LIT2362Songof/main",
        "inspection_and_limitations": (
            "The Beta maṣāḥǝft work record identifies Song of Songs (CAe 2362), records witnesses and the Gleave 1951 Ethiopic edition in its bibliography, and states that the text in the record was digitized from modern Vulgata printed editions and converted to XML. Its 2025-06-05 revision history says text from an EOTC Bible edition was added. The separate EOTCed division in the pinned TEI is Geʽez and explicitly notes ‘Text of the EOTC printed Bible.’ The exact printed exemplar, history/scope of each edition division, and relation of the EOTC note to the generic modern-Vulgata statement are not specified. The work page says the TEI file license is CC BY-SA 4.0; its footer separately displays CC BY-NC-SA 4.0. The relationship between notices remains unresolved. Inspected 2026-10-25."
        ),
        "archive_status": "Primary work record and its source-scope notes inspected; exact EOTC print exemplar, edition-division history, completeness, accuracy, and conflicting site-level license notice remain unresolved",
    }
    source_map[SOURCE_FILE_ID] = {
        "source_id": SOURCE_FILE_ID,
        "source_name": f"Beta maṣāḥǝft Works — pinned {WORK_ID} TEI source file",
        "url": source_url,
        "inspection_and_limitations": (
            f"Retrieved at BetaMasaheft/Works commit {COMMIT}, retained unchanged at readers/source/song-of-songs/{WORK_ID}.xml ({len(raw):,} bytes; SHA-256 {digest}). The root declares xml:lang=en; the selected EOTCed division declares xml:lang=gez. That division is explicitly noted ‘Text of the EOTC printed Bible,’ and the revision history records ‘added text from EOTC Bible edition’ on 2025-06-05. It has eight chapter divisions and 131 nonempty line elements. Chapter 8 has a duplicate line marker 14; it is preserved. The file's TEI licence states CC BY-SA 4.0. The work page separately displays a CC BY-NC-SA 4.0 site footer. Exact printed exemplar, rights in that exemplar, and relationship between license notices remain unresolved; no independent textual collation performed."
        ),
        "archive_status": "Pinned TEI source retained unchanged; extraction structure and explicit EOTC note checked; exact exemplar, underlying rights, accuracy, and completeness unresolved",
    }
    archive["sources"] = sorted(source_map.values(), key=lambda x: int(x["source_id"].split("-")[1]))

    registry_path = ROOT / "translation-registry.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    leads = {item["edition_id"]: item for item in registry.get("edition_leads", [])}
    leads["betamasaheft-song-of-songs-eotced-2025"] = {
        "edition_id": "betamasaheft-song-of-songs-eotced-2025",
        "candidate_canon_id": CANON_ID,
        "mapping_state": "asserted_by_source",
        "title": "Song of Songs — Beta maṣāḥǝft EOTCed Geʽez text",
        "witness_type": "digital_edition",
        "language_tag": "gez",
        "language_name": "Geʽez (Classical Ethiopic)",
        "script_code": "Ethi",
        "edition_statement": "The EOTCed division declares Geʽez and says ‘Text of the EOTC printed Bible’; the 2025 revision history says EOTC Bible text was added. Exact print exemplar and relation to the work record’s generic modern-Vulgata statement remain unresolved.",
        "scope_description": "Eight ordered chapters and 131 TEI line elements are bundled. Chapter 8 source marker 14 repeats and is preserved. This is evidence for a source-asserted title link, not proof of the physical exemplar, completeness, or accuracy.",
        "source_ids": reader["source_ids"],
        "text_bundled": False,
        "bundled_reader_id": READER_ID,
        "rights_status": "The pinned TEI file states CC BY-SA 4.0; the provider site footer separately displays CC BY-NC-SA 4.0 and their relationship remains unresolved. The file notice does not establish rights in the unidentified print exemplar.",
        "rights_classification": "open_license",
        "license_id": "CC-BY-SA-4.0",
        "license_url": LICENSE,
        "review_status": reader["verification_status"],
    }
    gez = next(item for item in registry["languages"] if item.get("language_tag") == "gez")
    language_records = {item["reader_id"]: item for item in gez.get("records", [])}
    language_records[READER_ID] = {
        "canon_id": CANON_ID,
        "reader_id": READER_ID,
        "layer_role": "source_text_transcription",
        "status": "bundled",
        "basis_language_tag": "gez",
        "basis_description": "The EOTCed division is Geʽez and explicitly notes ‘Text of the EOTC printed Bible’; the revision history says EOTC Bible text was added in 2025. The work page also gives a generic modern-Vulgata digitization statement. Exact print exemplar and relationship among these statements remain unresolved; accuracy and completeness have not been independently reviewed.",
        "rights_status": "CC BY-SA 4.0 on pinned file; separate site footer says CC BY-NC-SA 4.0, relationship unresolved; underlying print rights not established.",
        "rights_classification": "open_license",
        "source_ids": reader["source_ids"],
    }
    gez["records"] = sorted(language_records.values(), key=lambda x: x.get("reader_id", ""))
    registry["edition_leads"] = sorted(leads.values(), key=lambda x: x["edition_id"])
    archive["catalogue"] = archive.get("catalogue", [])
    for row in archive["catalogue"]:
        if row.get("catalogue_id") == CATALOGUE_ID:
            row["text_availability_status"] = "A Geʽez EOTCed TEI text is bundled; source note identifies it as EOTC printed Bible text. Exact printed exemplar, accuracy, and completeness remain unverified."
            row["chapter_count"] = "8 ordered EOTCed TEI chapter divisions; print-edition completeness unverified"
            row["chapter_order_status"] = "All 8 EOTCed divisions are ordered 1–8."
            row["completeness_status"] = "131 nonempty TEI line elements; source marker 14 repeats in chapter 8 and is preserved. Textual accuracy and completeness against the unidentified print exemplar remain unverified."
            row["rights_status"] = "Pinned TEI file states CC BY-SA 4.0; site footer separately states CC BY-NC-SA 4.0, relationship unresolved; rights in unidentified print exemplar not established."
            row["reviewer_notes"] = reader["verification_status"]
            row["evidence_source_ids"] = list(dict.fromkeys(row.get("evidence_source_ids", []) + reader["source_ids"]))
    write_text_atomically(archive_path, json.dumps(archive, ensure_ascii=False, indent=2) + "\n")
    registry_path.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return reader


if __name__ == "__main__":
    result = build()
    print(f"Built {result['reader_id']}: {result['chapter_count']} chapters, {result['unit_count']} source lines; chapter 8 marker duplication preserved.")
