"""Build an offline Geʽez Daniel reader from its pinned, licensed Beta maṣāḥǝft TEI."""

from __future__ import annotations

import hashlib
import json
from archive_manifest import write_text_atomically
from metadata_helpers import ensure_appended_note_once
import re
import xml.etree.ElementTree as ET
from pathlib import Path

from build_daniel_discovery import build as build_discovery

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "readers/source/daniel/LIT3529Daniel-original.xml"
OUTPUT = ROOT / "readers/daniel-betamasaheft-tei.json"
NS = {"tei": "http://www.tei-c.org/ns/1.0"}
XML = "{http://www.w3.org/XML/1998/namespace}"
SOURCE_ID = "SRC-282"
READER_ID = "daniel-betamasaheft-tei"
CANON_ID = "eotc-ot-32"
EDITION_ID = "betamasaheft-daniel-tei-2026"
EXPECTED_SHA256 = "bb8688848c941c67a1b104f76a13542e3ac30c1bb81d9b899c8601d6f206953b"
LICENSE_URL = "https://creativecommons.org/licenses/by-sa/4.0/"
DANIEL_SOURCE_NOTE = (
    "The exact pinned TEI snapshot is retained at readers/source/daniel/LIT3529Daniel-original.xml "
    "({byte_count:,} bytes; SHA-256 {sha}); an offline reader structurally preserves all 14 ordered "
    "divisions and 437 nonempty labeled line elements. The reader is provisionally linked by title "
    "to the Church-list Daniel entry. No print collation, exact-edition crosswalk, accuracy, or "
    "physical completeness check is claimed. The TEI abstract also names several Daniel-associated "
    "stories/prayers whose boundaries are not separately verified."
)


def _flat_text(element: ET.Element) -> str:
    return re.sub(r"\s+", " ", "".join(element.itertext())).strip()


def build() -> dict:
    raise RuntimeError("Publication blocked: Daniel scripture text is withheld pending Beta maṣāḥǝft rights clarification.")
    build_discovery()
    raw = SOURCE.read_bytes()
    root = ET.fromstring(raw)
    if root.get(XML + "id") != "LIT3529Daniel":
        raise ValueError("Daniel source snapshot has an unexpected TEI identity.")
    editions = root.findall(".//tei:div[@type='edition']", NS)
    if len(editions) != 1 or editions[0].get(XML + "lang") != "gez":
        raise ValueError("Daniel text must come from the sole explicitly Geʽez TEI edition.")
    license_nodes = root.findall(".//tei:licence", NS)
    if not any("creativecommons.org/licenses/by-sa/4.0" in node.get("target", "") for node in license_nodes):
        raise ValueError("Pinned Daniel TEI no longer carries its CC BY-SA 4.0 file-level notice.")
    divisions = editions[0].findall("tei:div[@type='textpart'][@subtype='chapter']", NS)
    if len(divisions) != 14:
        raise ValueError(f"Expected 14 TEI chapter divisions, found {len(divisions)}.")

    chapters = []
    for chapter_order, division in enumerate(divisions, start=1):
        source_chapter = division.get("n")
        if source_chapter != str(chapter_order):
            raise ValueError(f"Unexpected Daniel source chapter order at {chapter_order}: {source_chapter!r}")
        units = []
        for unit_order, line in enumerate(division.findall(".//tei:l", NS), start=1):
            text = _flat_text(line)
            if not text:
                raise ValueError(f"Empty TEI line in Daniel chapter {source_chapter}, position {unit_order}.")
            units.append({
                "unit_order": unit_order,
                "source_marker": line.get("n"),
                "source_element_id": line.get(XML + "id"),
                "source_refs": [ref.get("target") for ref in line.findall(".//tei:ref", NS) if ref.get("target")],
                "text": text,
            })
        label = division.find("tei:label", NS)
        heading = _flat_text(label) if label is not None else ""
        chapters.append({
            "chapter": chapter_order,
            "source_chapter_label": source_chapter,
            "heading": [heading] if heading else [],
            "units": units,
        })

    line_count = sum(len(chapter["units"]) for chapter in chapters)
    if line_count != 437:
        raise ValueError(f"Pinned Daniel structure changed: expected 437 lines, found {line_count}.")
    if [u["source_marker"] for u in chapters[13]["units"]] != ["0", "1", "2"]:
        raise ValueError("Preserve and review the observed chapter 14 line markers 0, 1, 2.")

    sha = hashlib.sha256(raw).hexdigest()
    if sha != EXPECTED_SHA256:
        raise ValueError("The local Daniel TEI snapshot differs from the pinned source hash.")
    reader = {
        "reader_id": READER_ID,
        "canon_id": CANON_ID,
        "title": "Daniel — Geʽez source transcription (Beta maṣāḥǝft TEI)",
        "display_name": "Daniel · Geʽez · provisional title-level link; edition and completeness unverified",
        "language": "Geʽez (Classical Ethiopic)",
        "language_tag": "gez",
        "language_assignment_status": "source_declared_inherited_edition_xml_lang",
        "script_code": "Ethi",
        "text_origin": "source_transcription",
        "edition": f"Beta maṣāḥǝft LIT3529Daniel TEI snapshot, pinned at Works commit ddee2d46c14eff7d738099a8503af1f0e084763e",
        "edition_scope": (
            "The TEI root defaults to English (xml:lang=en); the sole text edition explicitly declares Geʽez "
            "(xml:lang=gez), which governs the extracted text. Its note says ‘Text of the EOTC printed Bible.’ "
            "The TEI abstract describes Daniel as including Susanna, Bel and the Dragon, the Prayer of Azariah "
            "and the Three Holy Children, the Prayer of the Three Children, and the Third Song of the Three "
            "Youths in the Furnace. The reader preserves all 14 TEI chapter divisions as supplied; it does not "
            "assert the exact boundaries of these components against the Church-list entry or any print exemplar."
        ),
        "rights_classification": "open_license",
        "copyright_notice": (
            "The pinned item-level TEI file states CC BY-SA 4.0. Attribution: Beta maṣāḥǝft, published by the "
            "Hiob-Ludolf-Zentrum für Äthiopistik. The TEI credits a general editor by key AB and revision actors "
            "PL, MV, and ES; their full names are not identified in this file. This reader flattens inline XML "
            "markup and normalizes whitespace; the original TEI is retained unchanged. Indicate these changes, "
            "link the source and license, and distribute this adaptation under CC BY-SA 4.0. The file-level "
            "license is not a rights determination for other editions or the surrounding website."
        ),
        "commercial_use": "CC BY-SA 4.0 permits commercial sharing and adaptation under its terms; preserve attribution, indicate changes, and share adaptations alike.",
        "license_id": "CC-BY-SA-4.0",
        "license_url": LICENSE_URL,
        "chapter_count": 14,
        "unit_count": line_count,
        "unit_label": "TEI line element (not independently verified verse count)",
        "source_numbered_unit_count": line_count,
        "source_unnumbered_unit_count": 0,
        "section_label": "Chapter",
        "chapter_structure_note": (
            "The pinned TEI has 14 ordered chapter divisions and 437 line elements; all have source n labels. "
            "Chapter 14 labels its three lines 0, 1, and 2. Labels are preserved exactly. Reader order is a "
            "navigation index, not a corrected or independently verified verse scheme."
        ),
        "transcription_note": "Every TEI line element is extracted in order. Inline XML markup is flattened and whitespace normalized for display; inspect the paired original TEI for markup and exact encoding. No print or manuscript collation was performed.",
        "editorial_signs_note": "Chapter 14 source markers 0–2 are retained as found. The TEI abstract's named Daniel-associated components are not separated into independently verified works here. No missing wording is reconstructed.",
        "verification_status": (
            "Structural extraction matches the pinned source: 14 ordered chapter divisions and all 437 nonempty "
            "line elements, including chapter 14 markers 0–2. The selected edition declares Geʽez and says it "
            "is text of the EOTC printed Bible; this supports a provisional title-level navigation link to the "
            "Church-list Daniel entry only. Exact print exemplar, current-edition identity, textual accuracy, "
            "and completeness remain unverified."
        ),
        "source_ids": ["SRC-029", SOURCE_ID],
        "source_pages": "readers/source/daniel/LIT3529Daniel-original.xml (pinned original TEI, preserved unchanged)",
        "source_snapshot_sha256": sha,
        "chapters": chapters,
    }
    OUTPUT.write_text(json.dumps(reader, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    reader_sha = hashlib.sha256(OUTPUT.read_bytes()).hexdigest()

    registry_path = ROOT / "translation-registry.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    lead = next(item for item in registry["edition_leads"] if item["edition_id"] == EDITION_ID)
    lead.update({
        "mapping_state": "uncertain",
        "text_bundled": False,
        "bundled_reader_id": READER_ID,
        "rights_classification": "open_license",
        "license_id": "CC-BY-SA-4.0",
        "license_url": LICENSE_URL,
        "rights_status": "The pinned TEI file explicitly states CC BY-SA 4.0; the reader distributes an attributed extraction under the same license. This applies to this source file and adaptation, not other editions or the website.",
        "review_status": "Pinned TEI identity, file-level license, Geʽez edition scope, complete 14-division/437-line structural extraction, and observed chapter-14 numbering anomaly checked. Provisional title-level link only; source print exemplar, textual accuracy, physical completeness, and exact current EOTC edition identity are unverified.",
    })
    geez = next(item for item in registry["languages"] if item["language_tag"] == "gez")
    geez["source_ids"] = sorted(set(geez.get("source_ids", [])) | {SOURCE_ID}, key=lambda value: int(value.split("-")[1]))
    geez["records"] = [item for item in geez.get("records", []) if item.get("reader_id") != READER_ID]
    geez["records"].append({
        "canon_id": CANON_ID,
        "reader_id": READER_ID,
        "layer_role": "source_text_transcription",
        "status": "bundled",
        "basis_language_tag": "gez",
        "basis_description": "The TEI edition declares Geʽez. The Church-list Daniel link is provisional and title-level; exact edition identity, accuracy, and completeness are unverified.",
        "rights_status": "CC BY-SA 4.0 on the pinned TEI file and this marked adaptation",
        "rights_classification": "open_license",
        "license_id": "CC-BY-SA-4.0",
        "license_url": LICENSE_URL,
        "source_ids": ["SRC-029", SOURCE_ID],
    })
    registry_path.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    layer = {
        "schema_version": 2,
        "record_id": "https://austinsimpkins1997-ship-it.github.io/ethiopian-bible-library/id/layer/daniel-betamasaheft-tei",
        "work_id": "https://austinsimpkins1997-ship-it.github.io/ethiopian-bible-library/id/work/betamasaheft-LIT3529Daniel",
        "labels": [{"value": "Daniel — Geʽez source transcription", "language_tag": "en", "label_type": "preferred"}],
        "tradition_assertions": [{
            "tradition_id": "https://austinsimpkins1997-ship-it.github.io/ethiopian-bible-library/id/tradition/eotc",
            "canon_id": "https://austinsimpkins1997-ship-it.github.io/ethiopian-bible-library/id/canon/eotc-ot-32",
            "mapping_state": "uncertain",
            "evidence_source_ids": ["SRC-029", SOURCE_ID],
            "notes": "A provisional title-level link only. The TEI's EOTC-print note and Daniel title support navigation; exact printed-edition identity and component boundaries remain unverified.",
        }],
        "witness": {
            "witness_id": "https://austinsimpkins1997-ship-it.github.io/ethiopian-bible-library/id/witness/betamasaheft-LIT3529Daniel-pinned-tei",
            "witness_type": "digital_edition",
            "title": "Beta maṣāḥǝft LIT3529Daniel TEI, pinned Works snapshot",
            "date_statement": "Works commit ddee2d46c14eff7d738099a8503af1f0e084763e; snapshot hash recorded in the reader",
            "repository_or_publisher": "Beta maṣāḥǝft / Hiob-Ludolf-Zentrum für Äthiopistik",
            "shelfmark_or_edition_id": "LIT3529Daniel",
            "editorial_policy": "Original TEI retained unchanged. Reader flattens inline markup and normalizes whitespace; chapter labels, line order and source markers are retained.",
            "source_ids": [SOURCE_ID],
        },
        "layer_type": "source_text_transcription",
        "text_origin": "source_transcription",
        "language_tag": "gez",
        "language_name_as_recorded": "Geʽez (Classical Ethiopic)",
        "script_code": "Ethi",
        "basis_path": ["gez"],
        "agents": [],
        "content_package": {
            "uri": "../readers/daniel-betamasaheft-tei.json",
            "media_type": "application/json",
            "sha256": reader_sha,
            "format_version": "1",
        },
        "coverage": {
            "extent_state": "unknown",
            "extent_basis": "source_inventory",
            "unit_count": line_count,
            "structure_description": "The retained TEI contains 14 ordered chapter divisions and 437 labeled lines; complete extent of the printed exemplar is unknown.",
            "missing_or_lacunose_ranges": [],
            "supplements_and_editorial_signs": "All line markers, including chapter 14 labels 0–2, are retained. Inline TEI markup is available in the paired original XML. The abstract's Daniel-associated components are not independently divided or mapped.",
            "numbering_policy": "Preserve source chapter divisions and each line n attribute exactly; navigation order is separate and must not replace source labels.",
        },
        "rights": {
            "status": "open_license",
            "statement": "Pinned TEI file states CC BY-SA 4.0. This reader is an extraction that flattens inline markup and normalizes whitespace. Attribute Beta maṣāḥǝft, indicate changes, link the license, and share this adaptation under CC BY-SA 4.0. This does not establish rights for other editions or the website.",
            "license_id": "CC-BY-SA-4.0",
            "rights_holder": None,
            "attribution_required": True,
            "territory_or_term_limits": "File-specific license and adaptation; not a rights determination for other editions or website content.",
            "evidence_source_ids": [SOURCE_ID],
        },
        "review_dimensions": [
            {"dimension": "identity", "state": "checked_with_limits", "scope": "Pinned TEI xml:id is LIT3529Daniel; exact print exemplar and current EOTC edition remain unidentified.", "reviewer": None, "review_method": "source_inspection", "review_process": "Pinned TEI identity, edition note, and abstract inspected", "reviewed_at": "2026-10-25", "evidence_source_ids": [SOURCE_ID], "notes": "Title-level Church-list link is provisional."},
            {"dimension": "language_identification", "state": "checked_with_limits", "scope": "The enclosing text edition declares xml:lang=gez; TEI root default is xml:lang=en.", "reviewer": None, "review_method": "source_inspection", "review_process": "TEI language inheritance and selected edition scope checked", "reviewed_at": "2026-10-25", "evidence_source_ids": [SOURCE_ID], "notes": "The reader uses the explicit edition language and preserves the root-default conflict."},
            {"dimension": "chapter_or_section_sequence", "state": "checked_with_limits", "scope": "All 14 TEI chapter divisions are ordered 1–14.", "reviewer": None, "review_method": "automated_validation", "review_process": "Pinned source parser and hash validation", "reviewed_at": "2026-10-25", "evidence_source_ids": [SOURCE_ID], "notes": "Structural sequence only."},
            {"dimension": "unit_boundaries", "state": "checked_with_limits", "scope": "All 437 nonempty TEI line elements and their source markers are retained in order.", "reviewer": None, "review_method": "automated_validation", "review_process": "Reader-to-TEI structural comparison", "reviewed_at": "2026-10-25", "evidence_source_ids": [SOURCE_ID], "notes": "These are TEI lines, not an independently verified verse count."},
            {"dimension": "completeness", "state": "unknown", "scope": "No comparison against the unidentified printed exemplar or manuscript witnesses.", "reviewer": None, "review_method": "unknown", "review_process": None, "reviewed_at": None, "evidence_source_ids": [SOURCE_ID], "notes": "This count describes only the retained TEI snapshot."},
            {"dimension": "transcription_accuracy", "state": "unknown", "scope": "No independent collation against the print source or manuscripts.", "reviewer": None, "review_method": "unknown", "review_process": None, "reviewed_at": None, "evidence_source_ids": [SOURCE_ID], "notes": "Automated extraction checks do not establish wording accuracy."},
            {"dimension": "rights", "state": "checked_with_limits", "scope": "The source TEI file's explicit CC BY-SA 4.0 notice and terms for adaptations.", "reviewer": None, "review_method": "source_inspection", "review_process": "Pinned TEI license statement inspected", "reviewed_at": "2026-10-25", "evidence_source_ids": [SOURCE_ID], "notes": "This is file-specific and does not establish rights in other editions or site content."},
        ],
        "publication_state": "bundled",
        "community_access_note": None,
        "additional_notes": "No English translation or alignment is bundled. Source markers, including the chapter 14 anomaly, are retained rather than normalized.",
    }
    layer_path = ROOT / "examples/daniel-betamasaheft-tei-layer.json"
    layer_path.write_text(json.dumps(layer, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    audit_dir = ROOT / "readers/source/daniel"
    audit_dir.mkdir(parents=True, exist_ok=True)
    (audit_dir / "SOURCE-AUDIT.md").write_text(
        "# Daniel source and reader audit\n\n"
        f"- Source: [Beta maṣāḥǝft Works LIT3529Daniel at pinned commit](https://github.com/BetaMasaheft/Works/blob/ddee2d46c14eff7d738099a8503af1f0e084763e/3001-4000/LIT3529Daniel.xml).\n"
        f"- Local source snapshot: `LIT3529Daniel-original.xml` ({len(raw):,} bytes; SHA-256 `{sha}`), retained unchanged.\n"
        "- Language: root default is English; the sole text edition explicitly declares Geʽez (`gez`), used for the reader.\n"
        "- Source scope: the note calls it ‘Text of the EOTC printed Bible.’ The TEI abstract lists Susanna; Bel and the Dragon; the Prayer of Azariah and the Three Holy Children; the Prayer of the Three Children; and the Third Song of the Three Youths in the Furnace as Daniel-associated components. This archive preserves the source's 14 divisions; exact boundaries against the Church-list entry are not independently verified.\n"
        "- License: the source file states CC BY-SA 4.0. The reader is a whitespace-normalized, inline-markup-flattened adaptation and is distributed under the same terms with attribution.\n"
        "- Structure: 14 ordered chapter divisions, 437 nonempty labeled TEI lines. Chapter 14 labels are `0`, `1`, `2`; no renumbering was applied. These are source structure counts, not a verified verse count.\n"
        "- Crosswalk: provisionally linked by title and the TEI's own EOTC-print note to the Church-list Daniel row. Exact current print identity, transcription accuracy, and completeness are unknown. This link does not certify all 14 divisions against a particular physical edition.\n",
        encoding="utf-8",
    )

    archive_path = ROOT / "archive.json"
    archive = json.loads(archive_path.read_text(encoding="utf-8"))
    source = next(item for item in archive["sources"] if item["source_id"] == SOURCE_ID)
    source["inspection_and_limitations"] = ensure_appended_note_once(
        source["inspection_and_limitations"],
        DANIEL_SOURCE_NOTE.format(byte_count=len(raw), sha=sha),
    )
    source["archive_status"] = "Pinned Geʽez TEI and CC BY-SA 4.0 adaptation bundled for offline reading; provisional title-level canon link; textual accuracy and completeness unverified"
    row = next(item for item in archive["catalogue"] if item.get("catalogue_id") == "eotc-040")
    row.update({
        "text_availability_status": "Bundled Geʽez source transcription; provisional title-level link to the Church-list Daniel entry",
        "chapter_count": "14 ordered TEI divisions; physical-edition completeness unverified",
        "chapter_order_status": "TEI chapters labeled 1–14; chapter 14 line labels 0–2 preserved as supplied",
        "completeness_status": "All 437 lines in the pinned TEI are bundled; completeness against an unidentified printed exemplar is unknown",
        "rights_status": "Pinned TEI file states CC BY-SA 4.0; attribution, change notice, and share-alike terms applied to the reader adaptation",
        "reviewer_notes": "The source is a Geʽez edition labeled ‘Text of the EOTC printed Bible.’ Its title-level link to the Church-list Daniel entry is provisional. The TEI abstract lists Susanna, Bel and the Dragon, and associated prayers/song components; their exact division against this catalogue row is not independently collated. Chapter 14 labels 0–2 are preserved. Textual accuracy, exact print exemplar, current-edition identity, and physical completeness are unknown.",
        "source_id": SOURCE_ID,
        "evidence_source_ids": ["SRC-029", SOURCE_ID],
    })
    write_text_atomically(archive_path, json.dumps(archive, ensure_ascii=False, indent=2) + "\n")
    print(f"Built Daniel reader: 14 TEI chapters, {line_count} lines, source SHA-256 {sha}; title link remains provisional.")


if __name__ == "__main__":
    build()
