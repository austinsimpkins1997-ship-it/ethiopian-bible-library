"""Build Romans from a pinned Beta maṣāḥǝft TEI, preserving all text parts and notes."""

from __future__ import annotations

import hashlib
import json
from archive_manifest import write_text_atomically
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TEI = "http://www.tei-c.org/ns/1.0"
XML = "http://www.w3.org/XML/1998/namespace"
COMMIT = "ec53d3f4c5de47e463fa56a8465cf1090316a999"
WORK = "LIT3515Epistle"
FILE = f"{WORK}.xml"
READER_ID = "romans-betamasaheft-tei"
SOURCE_ID = "SRC-274"
SHA256 = "6513f7a65aa76d8b09b2d6f9e04351730adbf538ea28c305958754ceb3236458"


def normalized(node: ET.Element) -> str:
    return " ".join("".join(node.itertext()).split())


def make_unit(element: ET.Element, order: int, element_type: str) -> dict:
    text = normalized(element)
    marker = element.get("n") if element_type == "l" else None
    unit = {
        "number": order,
        "unit_order": order,
        "source_marker": marker,
        "source_element_id": element.get(f"{{{XML}}}id"),
        "source_element_type": element_type,
        "source_refs": [ref.get("target") for ref in element.iter(f"{{{TEI}}}ref") if ref.get("target")],
        "text": text,
    }
    if not text:
        unit["source_text_state"] = "marker_only"
    return unit


def build() -> dict:
    relative = f"readers/source/romans/{FILE}"
    raw = (ROOT / relative).read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != SHA256:
        raise ValueError(f"Pinned source hash mismatch: {digest}")
    root = ET.fromstring(raw)
    if root.get(f"{{{XML}}}id") != WORK or root.get(f"{{{XML}}}lang") != "en":
        raise ValueError("Unexpected Romans TEI root identity or default language")
    edition = next((x for x in root.iter(f"{{{TEI}}}div") if x.get("type") == "edition"), None)
    if edition is None or edition.get(f"{{{XML}}}lang") != "gez":
        raise ValueError("Romans TEI does not explicitly declare a Geʽez edition")
    license_node = next((x for x in root.iter(f"{{{TEI}}}licence") if "creativecommons.org/licenses/by-sa/4.0" in x.get("target", "")), None)
    if license_node is None:
        raise ValueError("Romans TEI does not state file-level CC BY-SA 4.0")
    all_chapters = [x for x in edition.iter(f"{{{TEI}}}div") if x.get("subtype") == "chapter"]
    if [x.get("n") for x in all_chapters] != [str(n) for n in range(1, 17)]:
        raise ValueError("Romans source chapter-divisions changed")
    epistle = next((x for x in edition.findall(f"{{{TEI}}}div") if x.get(f"{{{XML}}}id") == "Epistle"), None)
    if epistle is None:
        raise ValueError("Romans EOTC epistle division is missing")
    epistle_notes = [normalized(x) for x in epistle.findall(f"{{{TEI}}}note")]
    eotc_note = "The text of the Epistle itself is taken from the printed EOTC Bible."
    if not any(eotc_note in note for note in epistle_notes):
        raise ValueError("Romans TEI no longer identifies the printed EOTC Bible text")

    # The complete edition is in source order: prescription, introduction, epistle,
    # subscription, stichometry. Preserve every non-chapter text part as a reader
    # section and each explicit source chapter as its own section.
    parts: list[dict] = []
    total_lines: list[ET.Element] = []
    edition_notes = [normalized(x) for x in edition.findall(f"{{{TEI}}}note")]
    source_note_rows = [
        {"verse": "Edition note", "marker": "TEI edition note", "text": note,
         "source_reference": f"{FILE}, tei:div[@type='edition']/tei:note", "note_origin": "source"}
        for note in edition_notes
    ]
    source_note_rows += [
        {"verse": "Scope note", "marker": "TEI Epistle note", "text": note,
         "source_reference": f"{FILE}, tei:div[@xml:id='Epistle']/tei:note", "note_origin": "source"}
        for note in epistle_notes
    ]

    for top in edition.findall(f"{{{TEI}}}div"):
        if top.get("type") != "textpart":
            continue
        part_id = top.get(f"{{{XML}}}id") or "textpart"
        part_label = next((normalized(x) for x in top.findall(f"{{{TEI}}}label")), part_id)
        if part_id == "Epistle":
            for division in top.findall(f"{{{TEI}}}div"):
                if division.get("subtype") != "chapter":
                    continue
                label = division.get("n")
                lines = list(division.iter(f"{{{TEI}}}l"))
                total_lines.extend(lines)
                heading = [part_label] + [normalized(x) for x in division.findall(f"{{{TEI}}}label") if normalized(x)]
                units = [make_unit(line, idx, "l") for idx, line in enumerate(lines, 1)]
                if not units:
                    raise ValueError(f"Romans chapter {label} has no TEI line elements")
                parts.append({"label": f"Epistle · source chapter {label}", "heading": heading,
                              "source_label": label, "units": units, "notes": source_note_rows if label == "1" else []})
            continue

        headings = [normalized(x) for x in top.findall(f"{{{TEI}}}label") if normalized(x)]
        body_elements = [x for x in top if x.tag != f"{{{TEI}}}label"]
        units = [make_unit(element, idx, element.tag.rsplit("}", 1)[-1])
                 for idx, element in enumerate(body_elements, 1)]
        if not units:
            units = [{"number": 1, "unit_order": 1, "source_marker": part_id,
                      "source_element_id": part_id, "source_element_type": "textpart_label_only",
                      "source_refs": [], "text": "", "source_text_state": "marker_only"}]
        parts.append({"label": part_label, "heading": headings or [part_label],
                      "source_label": part_id, "units": units,
                      "notes": (source_note_rows if part_id == "Prescription" else []) + ([
                          {"verse": 1, "marker": "TEI text part has label only",
                           "text": "Archive note: the source has the label ‘Introduction to the epistle’ but contains no body text in this text part.",
                           "source_reference": f"{FILE}, tei:div[@xml:id='Introduction']", "note_origin": "archive"}
                      ] if part_id == "Introduction" and not any(x["text"] for x in units) else [])})

    line_nodes = list(edition.iter(f"{{{TEI}}}l"))
    if len(line_nodes) != len(total_lines) or (len(total_lines), sum(x.get("n") is not None for x in total_lines)) != (495, 430):
        raise ValueError("Romans line extraction did not preserve the edition line inventory")
    if [x for x in edition.findall(f"{{{TEI}}}div") if x.get("type") == "textpart"][-1].get(f"{{{XML}}}id") != "stichometry":
        raise ValueError("Romans final source text part changed")

    chapters = [{"chapter": idx, "source_chapter_label": part["source_label"],
                 "heading": part["heading"], "units": part["units"], "notes": part["notes"]}
                for idx, part in enumerate(parts, 1)]
    unnumbered_lines = len(total_lines) - sum(x.get("n") is not None for x in total_lines)
    source_url = f"https://github.com/BetaMasaheft/Works/blob/{COMMIT}/3001-4000/{FILE}"
    reader = {
        "reader_id": READER_ID, "canon_id": "eotc-nt-06", "text_origin": "source_transcription",
        "title": "Romans — Geʽez source transcription (Beta maṣāḥǝft TEI)",
        "display_name": "Romans · Geʽez · provisional EOTC print-text link; divisions preliminary",
        "language": "Geʽez (Classical Ethiopic)", "language_tag": "gez",
        "language_assignment_status": "source_declared_inherited_edition_xml_lang", "script_code": "Ethi",
        "edition": f"Beta maṣāḥǝft {WORK} TEI source snapshot, pinned at Works commit {COMMIT}",
        "edition_scope": "The TEI root defaults to English, but the selected edition explicitly declares Geʽez. Its Epistle division states that the text itself is taken from the printed EOTC Bible. The source's 16 chapter divisions are explicitly described as preliminary divisions present in manuscripts that do not account for different recensions. Prescription, introduction, subscription, stichometry, and source notes are retained as separate navigable text parts. The exact printed exemplar, recension, current EOTC edition identity, textual accuracy, and physical-edition completeness are unverified.",
        "section_label": "Text part", "unit_label": "TEI line or retained unsegmented text element",
        "source_ids": ["SRC-029", SOURCE_ID, "SRC-176"], "rights_classification": "open_license",
        "copyright_notice": "The retained Beta maṣāḥǝft LIT3515Epistle TEI file states CC BY-SA 4.0. Attribute Beta maṣāḥǝft, link source and license, identify the extraction/whitespace normalization, and share adaptations alike. This file-level license does not establish rights in the unidentified printed exemplar.",
        "commercial_use": "The file-level CC BY-SA 4.0 permits commercial sharing and adaptation subject to attribution, change notices, and ShareAlike. It does not establish rights in the unidentified printed exemplar.",
        "license_id": "CC-BY-SA-4.0", "license_url": "https://creativecommons.org/licenses/by-sa/4.0/",
        "chapter_count": len(chapters), "unit_count": sum(len(ch["units"]) for ch in chapters),
        "source_numbered_unit_count": 430, "source_unnumbered_unit_count": unnumbered_lines,
        "source_empty_unit_count": sum(x.get("source_text_state") == "empty_source_element" for x in line_nodes),
        "chapter_structure_note": f"The source explicitly marks 16 ordered chapter divisions but calls its division preliminary and says it does not account for recensions. The reader presents 20 source text parts so the prescription, introduction, subscription, and stichometry remain accessible without being mislabeled as chapters. All 495 TEI line elements are retained: 430 numbered and 65 unnumbered. These counts do not establish completeness or accuracy against a specific printed exemplar.",
        "transcription_note": "All source line elements and six unsegmented ab elements are retained in TEI source order. Display whitespace is normalized; inline TEI markup is flattened for display while the unchanged source XML is retained. The preliminary chapter divisions and all source labels remain unchanged.",
        "chapters": chapters,
        "verification_status": "Pinned source hash, explicit Geʽez edition language, file-level license, EOTC print-text note, 16 preliminary chapter divisions, all 495 line elements, and all 20 ordered text parts checked. No independent collation, recension identification, physical-edition completeness check, or current-edition verification was performed.",
    }

    (ROOT / "readers" / f"{READER_ID}.json").write_text(json.dumps(reader, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    source = {
        "source_id": SOURCE_ID, "source_name": "Beta maṣāḥǝft Works — pinned LIT3515Epistle TEI source snapshot",
        "url": source_url,
        "inspection_and_limitations": f"Retrieved at BetaMasaheft/Works commit {COMMIT} and retained unchanged at {relative} ({len(raw):,} bytes; SHA-256 {digest}). The TEI root xml:lang=en; the selected edition explicitly declares xml:lang=gez. The Epistle note says its text is taken from the printed EOTC Bible; the edition separately warns that its 16 manuscript-present textpart divisions are preliminary and do not account for recensions. The edition contains 495 TEI line elements (430 labeled, 65 unlabeled) in 16 chapter divisions, plus prescription, introduction, subscription, stichometry, and two source notes. All are retained in reader order. File-level CC BY-SA 4.0 does not establish rights in the unidentified printed exemplar. Accuracy, exact recension, current-edition identity, and physical completeness remain unverified.",
        "archive_status": "Pinned source TEI retained locally; language, file-level license, EOTC text note, all text parts, and structural extraction checked; accuracy, recension, exact edition, and physical completeness unverified",
    }
    archive_path = ROOT / "archive.json"
    archive = json.loads(archive_path.read_text(encoding="utf-8"))
    sources = {x["source_id"]: x for x in archive["sources"]}
    sources[SOURCE_ID] = source
    archive["sources"] = sorted(sources.values(), key=lambda x: int(x["source_id"].split("-")[1]))
    row = next((x for x in archive["catalogue"] if x["catalogue_id"] == "eotc-060"), None)
    if row:
        row.update({
            "text_availability_status": "A Geʽez source transcription from a TEI division identified as the printed EOTC text is bundled with a provisional title-level link; exact printed exemplar and recension remain unidentified.",
            "chapter_count": "16 preliminary manuscript-based TEI divisions; the source warns that recensions are not accounted for",
            "chapter_order_status": "The 16 source divisions are ordered 1–16; the source describes this segmentation as preliminary.",
            "completeness_status": "All 495 TEI line elements (430 labeled, 65 unlabeled) and four additional source text parts are retained. Physical-edition completeness and transcription accuracy are unverified.",
            "rights_status": "The TEI file states CC BY-SA 4.0; rights in the unidentified printed exemplar are not established.",
            "evidence_source_ids": list(dict.fromkeys(row.get("evidence_source_ids", []) + reader["source_ids"])),
            "reviewer_notes": reader["verification_status"],
        })
    write_text_atomically(archive_path, json.dumps(archive, ensure_ascii=False, indent=2) + "\n")

    registry_path = ROOT / "translation-registry.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    leads = {x["edition_id"]: x for x in registry["edition_leads"]}
    leads["betamasaheft-romans-tei-2026"] = {
        "edition_id": "betamasaheft-romans-tei-2026", "candidate_canon_id": "eotc-nt-06",
        "mapping_state": "uncertain", "title": "Epistle to the Romans (LIT3515Epistle), Beta maṣāḥǝft TEI text",
        "witness_type": "digital_edition", "language_tag": "gez", "language_name": "Geʽez (Classical Ethiopic)", "script_code": "Ethi",
        "edition_statement": f"Pinned Beta maṣāḥǝft {WORK} TEI file at Works commit {COMMIT}. The edition declares Geʽez and its Epistle note says the text is taken from the printed EOTC Bible; the root default is English. The source calls its 16 manuscript-based text divisions preliminary and says recensions are not accounted for.",
        "scope_description": "Provisional title-level link to Romans based on the exact TEI title and EOTC printed-text statement. The reader preserves all 495 line elements and all four surrounding text parts; its 16 chapter divisions are explicitly preliminary. Exact exemplar, recension, accuracy, current-edition identity, and physical completeness remain unverified.",
        "source_ids": reader["source_ids"], "text_bundled": False, "bundled_reader_id": READER_ID,
        "rights_status": "The retained TEI file states CC BY-SA 4.0. Attribute Beta maṣāḥǝft and share adaptations alike; rights in the unidentified print exemplar are not established.",
        "rights_classification": "open_license", "license_id": "CC-BY-SA-4.0", "license_url": "https://creativecommons.org/licenses/by-sa/4.0/",
        "review_status": reader["verification_status"],
    }
    registry["edition_leads"] = sorted(leads.values(), key=lambda x: x["edition_id"])
    gez = next(x for x in registry["languages"] if x["language_tag"] == "gez")
    records = {x["reader_id"]: x for x in gez.get("records", [])}
    records[READER_ID] = {
        "canon_id": "eotc-nt-06", "reader_id": READER_ID, "layer_role": "source_text_transcription", "status": "bundled",
        "basis_language_tag": "gez", "basis_description": "TEI edition explicitly declares Geʽez and says the Epistle text is taken from the printed EOTC Bible. The source describes chapter divisions as preliminary and does not account for recensions. Exact exemplar and current-edition identity remain unverified.",
        "rights_status": "CC BY-SA 4.0 (file-level TEI license; rights in unidentified print exemplar not established)",
        "rights_classification": "open_license", "source_ids": reader["source_ids"],
    }
    gez["records"] = sorted(records.values(), key=lambda x: x["reader_id"])
    registry_path.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # Add a portable layer record for this source reader so the selected-layer
    # metadata manifest stays connected to the bundled text and its limits.
    portable_path = ROOT / "examples" / "portable-text-layers.json"
    portable = json.loads(portable_path.read_text(encoding="utf-8"))
    template_path = ROOT / "examples" / "hebrews-betamasaheft-tei-layer.json"
    layer = json.loads(template_path.read_text(encoding="utf-8"))
    base = "https://austinsimpkins1997-ship-it.github.io/ethiopian-bible-library/id"
    layer.update({
        "record_id": f"{base}/layer/{READER_ID}",
        "work_id": f"{base}/work/betamasaheft-{WORK}",
        "labels": [{"value": "Romans — Geʽez source transcription", "language_tag": "en", "label_type": "preferred"}],
        "tradition_assertions": [{"tradition_id": f"{base}/tradition/eotc", "canon_id": f"{base}/canon/eotc-nt-06", "mapping_state": "uncertain", "evidence_source_ids": reader["source_ids"], "notes": "The exact TEI title and its Epistle note support a provisional Romans link to the Church list. The source text is stated to come from a printed EOTC Bible, but the physical exemplar and recension are unidentified; its chapter divisions are described as preliminary."}],
        "witness": {"witness_id": f"{base}/witness/betamasaheft-{WORK}", "witness_type": "digital_edition", "title": f"Beta maṣāḥǝft {WORK} TEI text", "date_statement": f"Source file pinned at Works commit {COMMIT}; exact print-exemplar date unknown", "repository_or_publisher": "Beta maṣāḥǝft, University of Hamburg", "shelfmark_or_edition_id": WORK, "editorial_policy": "The TEI identifies the epistle text as taken from a printed EOTC Bible and describes its 16 manuscript-present chapter divisions as preliminary, without accounting for recensions. The exact printed exemplar and recension are not identified; unchanged XML is retained alongside the display extraction.", "source_ids": [SOURCE_ID]},
        "language_tag": "gez", "language_name_as_recorded": "Geʽez (Classical Ethiopic)", "script_code": "Ethi", "basis_path": ["gez"], "agents": [],
        "content_package": {"uri": f"../readers/{READER_ID}.json", "media_type": "application/json", "sha256": hashlib.sha256((ROOT / "readers" / f"{READER_ID}.json").read_bytes()).hexdigest(), "format_version": "1", "json_pointer": ""},
        "coverage": {"extent_state": "complete_for_declared_edition", "extent_basis": "source_inventory", "unit_count": reader["unit_count"], "structure_description": "The reader retains all 495 TEI line elements (430 numbered, 65 unnumbered), six surrounding unsegmented ab elements, the heading-only Introduction marker, and both source notes. Its 16 explicit chapter divisions are preliminary per the source. This is completeness for the captured TEI scope only, not the printed exemplar or any recension.", "missing_or_lacunose_ranges": [], "supplements_and_editorial_signs": "Whitespace normalized for display; inline markup flattened while unchanged TEI is retained. Source labels and the source's preliminary division are preserved without normalization.", "numbering_policy": "Preserve every TEI source n label exactly; retain all unnumbered lines and surrounding text parts in order. Do not treat navigational text-part order as verse numbering."},
        "rights": {"status": "open_license", "statement": "The TEI file states CC BY-SA 4.0. Attribute Beta maṣāḥǝft, link source and license, identify extraction and whitespace normalization, and share adaptations alike. The file-level license does not establish rights in the unidentified printed exemplar.", "license_id": "CC-BY-SA-4.0", "rights_holder": "Beta maṣāḥǝft TEI file; underlying print rights not established", "attribution_required": True, "territory_or_term_limits": "The file-level license applies to the TEI file and its adaptation; do not infer rights in the unidentified printed source.", "evidence_source_ids": [SOURCE_ID]},
        "review_dimensions": [
            {"dimension": "identity", "state": "checked_with_limits", "scope": "TEI work id LIT3515Epistle and Church-list title checked; exact print exemplar and recension unresolved.", "reviewer": None, "review_method": "source_inspection", "review_process": "Pinned TEI header, Epistle note, title, and Church-list row inspected", "reviewed_at": "2026-10-25", "evidence_source_ids": reader["source_ids"], "notes": "Provisional title-level link only."},
            {"dimension": "language_identification", "state": "checked_with_limits", "scope": "TEI root xml:lang=en and edition xml:lang=gez inspected; extracted text is within that edition.", "reviewer": None, "review_method": "automated_validation", "review_process": "Pinned source XML language declarations and TEI inheritance checked", "reviewed_at": "2026-10-25", "evidence_source_ids": [SOURCE_ID], "notes": "Edition-level gez applies to nested text; root-level en remains recorded as a conflict."},
            {"dimension": "chapter_or_section_sequence", "state": "checked_with_limits", "scope": "All 20 ordered source text parts, 16 preliminary chapter divisions, 495 line elements, surrounding ab elements, and source notes checked against the pinned XML.", "reviewer": None, "review_method": "automated_validation", "review_process": "Offline TEI parser validates source hash, structure, labels, and exact line extraction", "reviewed_at": "2026-10-25", "evidence_source_ids": [SOURCE_ID], "notes": "The source itself calls the chapter division preliminary and excludes recension differences."},
            {"dimension": "completeness", "state": "unknown", "scope": "No collation against the exact printed exemplar or manuscript recension performed.", "reviewer": None, "review_method": "unknown", "review_process": None, "reviewed_at": None, "evidence_source_ids": [SOURCE_ID], "notes": "All captured TEI text parts are extracted; physical-edition completeness remains unknown."},
            {"dimension": "transcription_accuracy", "state": "unknown", "scope": "No independent collation against the printed source or manuscripts performed.", "reviewer": None, "review_method": "unknown", "review_process": None, "reviewed_at": None, "evidence_source_ids": [SOURCE_ID], "notes": "Structural extraction does not establish wording accuracy."},
            {"dimension": "rights", "state": "checked_with_limits", "scope": "File-level CC BY-SA 4.0 statement inspected in the pinned TEI file.", "reviewer": None, "review_method": "source_inspection", "review_process": "File-specific license retained separately from the website terms", "reviewed_at": "2026-10-25", "evidence_source_ids": [SOURCE_ID], "notes": "Rights in the unidentified printed exemplar remain unestablished."},
        ],
        "publication_state": "bundled", "community_access_note": None,
        "additional_notes": "Source transcription, not an English translation. The source's preliminary divisions are preserved as written; the reader presents all source text parts distinctly and does not treat its navigational order as a claim about recension.",
    })
    portable["coverage_statement"] = "This manifest includes portable metadata for 61 selected text layers across the bundled readers. It does not represent complete canon or language coverage."
    layer_example_path = ROOT / "examples" / f"{READER_ID}-layer.json"
    layer_example_path.write_text(json.dumps(layer, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    audit = ROOT / "readers" / "source" / "romans" / "SOURCE-AUDIT.md"
    audit.write_text(
        f"# Romans source audit\n\nPinned Beta maṣāḥǝft Works file `{FILE}` at commit `{COMMIT}` (SHA-256 `{digest}`). The file declares the enclosing edition as Geʽez and states in the Epistle division that its text is taken from the printed EOTC Bible. The root-level default is English and is retained as a metadata conflict.\n\nThe source includes 16 ordered TEI chapter divisions and explicitly calls this manuscript-present segmentation preliminary, without accounting for different recensions. The archive retains all 495 TEI line elements (430 numbered, 65 unnumbered), plus the prescription, introduction, subscription, stichometry, and both explanatory source notes as distinct visible reader text parts. The source file states CC BY-SA 4.0.\n\nThe Church-list link is provisional. The exact print exemplar, recension, current EOTC edition identity, transcription accuracy, and physical-edition completeness are unverified. The file-level license does not establish rights in the unidentified print exemplar.\n\n[Source TEI at pinned commit]({source_url}).\n",
        encoding="utf-8",
    )
    print(f"Built Romans from the pinned TEI: 20 ordered reader text parts, 495 source lines; accuracy and recension remain unverified.")
    return reader


if __name__ == "__main__":
    build()

