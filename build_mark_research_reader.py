"""Extract the pinned Mark TEI; the public build adds a provisional title-level canon link.

The body-level edition declares Geʽez, overriding the root's inherited English
default. Exact print exemplar, completeness, transcription accuracy, and current
EOTC edition identity remain unverified.
"""

from __future__ import annotations

import hashlib
import json
from archive_manifest import write_text_atomically
import re
from pathlib import Path
import xml.etree.ElementTree as ET

from audit_mark_tei import build_audit
from coverage_summary import build_coverage_statement
from layer_metadata import sync_layer_checksum


ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "readers" / "source" / "mark" / "LIT2711Mark-original.xml"
OUTPUT = ROOT / "readers" / "mark-research-tei.json"
REGISTRY = ROOT / "translation-registry.json"
NS = {"tei": "http://www.tei-c.org/ns/1.0"}
XML = "{http://www.w3.org/XML/1998/namespace}"
SOURCE_IDS = ["SRC-083", "SRC-084", "SRC-091", "SRC-092", "SRC-176"]
CORPUS_ID = "betamasaheft-mark-tei-research"
READER_ID = "mark-betamasaheft-tei-research"


def build() -> dict:
    raise RuntimeError("Publication blocked: Mark scripture text is withheld pending Beta maṣāḥǝft rights clarification.")
    raw = SOURCE.read_bytes()
    root = ET.fromstring(raw)
    if root.get(XML + "id") != "LIT2711Mark":
        raise ValueError("Mark research reader source must be the pinned LIT2711Mark TEI.")
    audit = build_audit()
    language_context = audit["language_context"]
    language_tag = language_context["edition_scope_xml_lang"]
    if language_tag != "gez" or not language_context["all_body_chapters_and_lines_inherit_edition_language"]:
        raise ValueError("The pinned Mark TEI no longer establishes Geʽez for every extracted text line.")
    body = root.find(".//tei:body", NS)
    if body is None:
        raise ValueError("Mark TEI has no body to render.")
    divisions = body.findall(".//tei:div[@subtype='chapter']", NS)
    chapters = []
    for chapter_order, division in enumerate(divisions, start=1):
        label = division.get("n")
        if label != str(chapter_order):
            raise ValueError("Mark chapter divisions must preserve the observed 1–16 source order.")
        units = []
        for unit_order, line in enumerate(division.findall(".//tei:l", NS), start=1):
            # Keep the source sequence index distinct from the original TEI n.
            # The original XML remains bundled for all inline markup and refs.
            text = re.sub(r"\s+", " ", "".join(line.itertext())).strip()
            if not text:
                raise ValueError(f"Empty TEI line element in chapter {label}, position {unit_order}.")
            units.append({
                "unit_order": unit_order,
                "source_marker": line.get("n"),
                "source_element_id": line.get(XML + "id"),
                "source_refs": [node.get("target") for node in line.findall(".//tei:ref", NS) if node.get("target")],
                "text": text,
            })
        heading = division.find("tei:label", NS)
        chapter_heading = re.sub(r"\s+", " ", "".join(heading.itertext())).strip() if heading is not None else ""
        chapters.append({
            "chapter": chapter_order,
            "source_chapter_label": label,
            "heading": [chapter_heading] if chapter_heading else [],
            "units": units,
        })

    declared_lines = sum(len(chapter["units"]) for chapter in chapters)
    numbered_lines = sum(unit["source_marker"] is not None for chapter in chapters for unit in chapter["units"])
    if (declared_lines != audit["line_element_count"]
            or numbered_lines != audit["numbered_line_element_count"]
            or declared_lines - numbered_lines != audit["unnumbered_line_element_count"]):
        raise ValueError("The readable line extraction does not match the retained TEI structural audit.")

    reader = {
        "reader_id": READER_ID,
        "research_corpus_id": CORPUS_ID,
        "reader_scope": "research_witness_unmapped",
        "title": "Gospel of Mark (LIT2711Mark) — Beta maṣāḥǝft TEI research transcription",
        "display_name": "Research witness — Mark (LIT2711Mark; Geʽez text; canon link unresolved)",
        "language": "Geʽez (Classical Ethiopic)",
        "language_tag": language_tag,
        "language_assignment_status": "source_declared_inherited_edition_xml_lang",
        "script_code": "Ethi",
        "text_origin": "source_transcription",
        "edition": "Beta maṣāḥǝft LIT2711Mark TEI snapshot, captured 2026-10-25",
        "edition_scope": "The Beta maṣāḥǝft work record describes this Gospel as Geʽez, and its TEI body contains one enclosing div type=\"edition\" with xml:lang=\"gez\". That scope contains all 16 chapter divisions and all 765 extracted line elements, with no line-content language overrides. The TEI root's xml:lang=\"en\" is a document default; the edition-level declaration supplies the text language under TEI inheritance rules. The root value is retained as a metadata conflict, not used to override the explicitly tagged text edition. The source says the text was digitized from modern Vulgata printed editions; the exact exemplar is not identified.",
        "rights_classification": "open_license",
        "copyright_notice": "The item-level TEI file states CC BY-SA 4.0. Attribution: Beta maṣāḥǝft; general editor Alessandro Bausi; contributors Pietro Maria Liuzzo, Massimo Villa, and Eugenia Sokolinski (the revision history credits Sokolinski with adding the text on 2025-06-05). This reader view is an adapted extraction: inline TEI markup is flattened and whitespace is normalized; the original XML is retained beside it. Link the source and license, indicate these changes, and distribute this adapted text under CC BY-SA 4.0. The site's separate footer notice is not this file's license. License: https://creativecommons.org/licenses/by-sa/4.0/",
        "commercial_use": "The file-level CC BY-SA 4.0 permits commercial sharing and adaptations under its terms; preserve attribution, indicate changes, and share adaptations alike. This does not relicense the surrounding website or other source materials.",
        "license_id": "CC-BY-SA-4.0",
        "license_url": "https://creativecommons.org/licenses/by-sa/4.0/",
        "chapter_count": len(chapters),
        "unit_count": declared_lines,
        "unit_label": "TEI line element (all numbered and unnumbered elements)",
        "source_numbered_unit_count": numbered_lines,
        "source_unnumbered_unit_count": declared_lines - numbered_lines,
        "section_label": "Chapter",
        "chapter_structure_note": "The source contains 16 ordered chapter divisions and 765 line elements: 678 carry a source n label and 87 do not. Original labels are retained exactly when present; unnumbered elements are not given invented source labels. The displayed order number is an archive navigation index, not a verse number. The original TEI preserves inline markup and reference targets.",
        "transcription_note": "Reader text is extracted from every TEI line element in source order. Inline XML markup is flattened and whitespace is normalized for display; inspect the paired original TEI for exact markup. This structural extraction has not been collated against a printed exemplar or manuscript.",
        "editorial_signs_note": "The function of unnumbered line elements and the meaning of TEI references have not been interpreted. No omitted or missing wording has been reconstructed.",
        "verification_status": "Research-only reader view of the locally retained LIT2711Mark TEI snapshot. Structural checks match all 16 chapters and all 765 source line elements (678 numbered, 87 unnumbered). The work record and enclosing TEI edition scope identify the text as Geʽez (gez); the root's xml:lang=\"en\" default is preserved as a metadata conflict. Language identification does not establish text accuracy, exact print exemplar, completeness, or relationship to a current EOTC edition. Not verified scripture and not counted as an EOTC canon reader.",
        "source_ids": SOURCE_IDS,
        "source_pages": "readers/source/mark/LIT2711Mark-original.xml (original TEI, preserved unchanged)",
        "source_snapshot_sha256": hashlib.sha256(raw).hexdigest(),
        "chapters": chapters,
    }

    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    registry["corpus_leads"] = [item for item in registry.get("corpus_leads", []) if item.get("corpus_id") != "betamasaheft-geez-mark-tei"]
    registry["research_corpora"] = [item for item in registry.get("research_corpora", []) if item.get("corpus_id") != CORPUS_ID]
    registry["research_corpora"].append({
        "corpus_id": CORPUS_ID,
        "title": "Gospel of Mark (LIT2711Mark) — related Beta maṣāḥǝft research transcription",
        "reader_id": READER_ID,
        "unit_count": declared_lines,
        "reader_status": "bundled_research_reader",
        "canon_mapping_state": "uncertain",
        "candidate_canon_id": "eotc-nt-02",
        "canon_mapping_note": "Title-level candidate only: the TEI identifies a Gospel of Mark work, but the exact Church-list work/edition crosswalk, current EOTC edition identity, text accuracy, and completeness are not established. The text language is identified from the enclosing TEI edition's xml:lang=\"gez\" declaration; the root's xml:lang=\"en\" default is retained as a metadata conflict. This research witness has no canon_id and is excluded from the 81-entry reader count.",
        "language_description": "Geʽez (gez), explicitly declared on the enclosing TEI text edition and inherited by all 16 chapters and 765 extracted line elements. The root xml:lang=\"en\" default is preserved as a metadata conflict.",
        "script_description": "Ethiopic script (Ethi), observed in the retained text; script and language are recorded as distinct metadata.",
        "unit_summary": "765 TEI line elements observed: 678 numbered and 87 unnumbered; source labels retained; not a verse count.",
        "rights_classification": "open_license",
        "license_id": "CC-BY-SA-4.0",
        "license_url": "https://creativecommons.org/licenses/by-sa/4.0/",
        "rights_status": "The retained TEI file explicitly states CC BY-SA 4.0. The extracted reader view indicates flattening of inline TEI and whitespace normalization; retain attribution, link the license, indicate changes, and license the adaptation alike. The website footer's separate terms do not replace the TEI file license.",
        "review_status": reader["verification_status"],
        "source_ids": SOURCE_IDS,
    })
    registry["research_corpora"].sort(key=lambda item: item["corpus_id"])
    canon_registry = json.loads((ROOT / "canon-registry.json").read_text(encoding="utf-8"))
    registry["coverage_statement"] = build_coverage_statement(registry, canon_registry)
    REGISTRY.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    OUTPUT.write_text(json.dumps(reader, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    layer = {
        "schema_version": 2,
        "record_id": "https://austinsimpkins1997-ship-it.github.io/ethiopian-bible-library/id/layer/mark-betamasaheft-tei-research",
        "work_id": "https://austinsimpkins1997-ship-it.github.io/ethiopian-bible-library/id/work/mark-betamasaheft-lit2711",
        "labels": [{
            "value": "Gospel of Mark (LIT2711Mark) — Geʽez research transcription; canon link unresolved",
            "language_tag": "en",
            "label_type": "preferred",
        }],
        "tradition_assertions": [{
            "tradition_id": "https://austinsimpkins1997-ship-it.github.io/ethiopian-bible-library/id/tradition/eotc",
            "canon_id": "https://austinsimpkins1997-ship-it.github.io/ethiopian-bible-library/id/canon/eotc-nt-02",
            "mapping_state": "uncertain",
            "evidence_source_ids": ["SRC-029", *SOURCE_IDS],
            "notes": "The TEI identifies a Mark work and declares Geʽez for its text edition, but the exact Church-list work/edition crosswalk, completeness, and relation to a current EOTC edition are unresolved. This is a related research transcription, not a canon-linked reader.",
        }],
        "witness": {
            "witness_id": "https://austinsimpkins1997-ship-it.github.io/ethiopian-bible-library/id/witness/betamasaheft-lith2711-mark-tei",
            "witness_type": "transcription",
            "title": "Beta maṣāḥǝft TEI record LIT2711Mark, captured 2026-10-25",
            "date_statement": "Local snapshot captured 2026-10-25; exact printed exemplar not identified",
            "repository_or_publisher": "Beta maṣāḥǝft project",
            "shelfmark_or_edition_id": "LIT2711Mark",
            "editorial_policy": "The source TEI is retained unchanged. The reader flattens inline markup and normalizes whitespace; chapter labels, line order, source n labels when present, and source references are preserved in the extracted data. Unnumbered line elements are not assigned verse labels.",
            "source_ids": SOURCE_IDS,
        },
        "layer_type": "source_text_transcription",
        "text_origin": "source_transcription",
        "language_tag": language_tag,
        "language_name_as_recorded": "gez",
        "script_code": "Ethi",
        "basis_path": [language_tag],
        "agents": [],
        "content_package": {
            "uri": "../readers/mark-research-tei.json",
            "media_type": "application/json",
            "sha256": "0" * 64,
            "format_version": "1",
            "json_pointer": "",
        },
        "coverage": {
            "extent_state": "unknown",
            "extent_basis": "source_inventory",
            "unit_count": declared_lines,
            "structure_description": "The retained TEI snapshot contains 16 ordered chapter divisions and 765 line elements: 678 have source n labels and 87 do not. This counts elements in the snapshot; the completeness of the intended printed work is unknown.",
            "missing_or_lacunose_ranges": [],
            "supplements_and_editorial_signs": "The flattened reader preserves source line markers, inline reference targets, and an archive display order separately. It does not interpret unnumbered lines or reconstruct omitted wording; consult the unchanged source TEI for inline markup.",
            "numbering_policy": "Retain each source n label exactly when present. Do not assign source verse numbers to the 87 unnumbered line elements; display sequence numbers are navigation indexes only.",
        },
        "rights": {
            "status": "open_license",
            "statement": "The item-level TEI file explicitly states CC BY-SA 4.0. This reader is an adaptation that flattens inline TEI markup and normalizes whitespace; attribute Beta maṣāḥǝft and the file credits, indicate changes, link https://creativecommons.org/licenses/by-sa/4.0/, and distribute adaptations under the same terms. The separate website footer license does not replace the source-file license.",
            "license_id": "CC-BY-SA-4.0",
            "rights_holder": None,
            "attribution_required": True,
            "territory_or_term_limits": "The file-level license applies to the cited TEI file and its adaptations, not every Mark edition or the whole website.",
            "evidence_source_ids": ["SRC-092"],
        },
        "review_dimensions": [
            {"dimension": "identity", "state": "checked_with_limits", "scope": "Pinned TEI xml:id is LIT2711Mark; exact print exemplar and current EOTC edition are unidentified.", "reviewer": None, "review_method": "combined_source_and_automated_validation", "review_process": "Pinned TEI identity check and source metadata audit", "reviewed_at": "2026-10-25", "evidence_source_ids": ["SRC-083", "SRC-091"], "notes": "A related Mark work is identified; it is not a verified edition-level match."},
            {"dimension": "language_identification", "state": "checked_with_limits", "scope": "The work record identifies Geʽez; the enclosing TEI edition declares xml:lang=gez for all 16 chapters and 765 extracted line elements. The document root declares xml:lang=en as its default.", "reviewer": None, "review_method": "source_inspection", "review_process": "Comparison of the official work record, retained TEI edition scope, and TEI P5 xml:lang inheritance guidance", "reviewed_at": "2026-10-25", "evidence_source_ids": ["SRC-083", "SRC-091", "SRC-092", "SRC-176"], "notes": "The reader uses gez for the explicitly tagged edition while preserving the conflicting root default. This resolves the text-language label only; it does not establish textual accuracy, exact exemplar, completeness, or canon mapping."},
            {"dimension": "chapter_or_section_sequence", "state": "checked_with_limits", "scope": "All 16 chapter divisions are ordered 1–16 in the retained TEI snapshot.", "reviewer": None, "review_method": "automated_validation", "review_process": "audit_mark_tei.py and build_mark_research_reader.py", "reviewed_at": "2026-10-25", "evidence_source_ids": ["SRC-091"], "notes": "Structural sequence only; not evidence of the completeness of a printed edition."},
            {"dimension": "unit_boundaries", "state": "checked_with_limits", "scope": "All 765 TEI line elements are retained in order; 678 carry source labels and 87 do not.", "reviewer": None, "review_method": "automated_validation", "review_process": "TEI line-element audit and reader extraction comparison", "reviewed_at": "2026-10-25", "evidence_source_ids": ["SRC-091", "SRC-092"], "notes": "The 765 units are TEI line elements, not a verse count."},
            {"dimension": "completeness", "state": "unknown", "scope": "No comparison against the exact printed exemplar was possible because it is unidentified.", "reviewer": None, "review_method": "unknown", "review_process": None, "reviewed_at": None, "evidence_source_ids": ["SRC-083", "SRC-091"], "notes": "The count describes the retained TEI only."},
            {"dimension": "transcription_accuracy", "state": "unknown", "scope": "No independent collation against print or manuscript witnesses was performed.", "reviewer": None, "review_method": "unknown", "review_process": None, "reviewed_at": None, "evidence_source_ids": ["SRC-091", "SRC-092"], "notes": "Automated structural checks do not establish textual accuracy."},
            {"dimension": "rights", "state": "checked_with_limits", "scope": "The original TEI file's explicit CC BY-SA 4.0 notice and conditions for adaptations.", "reviewer": None, "review_method": "source_inspection", "review_process": "Inspection of the retained TEI license statement", "reviewed_at": "2026-10-25", "evidence_source_ids": ["SRC-092"], "notes": "This does not apply the TEI license to the entire website or unrelated editions."},
        ],
        "publication_state": "bundled",
        "community_access_note": None,
        "additional_notes": "The language tag gez follows the inherited xml:lang on the text edition; the root xml:lang=en remains noted as a conflicting document default. Ethi records the text script separately. This is not verified scripture or an EOTC edition match. No missing wording or viewpoints are generated.",
    }
    layer_path = ROOT / "examples" / "mark-research-tei-layer.json"
    layer_path.write_text(json.dumps(layer, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    sync_layer_checksum(layer_path, OUTPUT)

    archive_path = ROOT / "archive.json"
    archive = json.loads(archive_path.read_text(encoding="utf-8"))
    mark_rows = [book for book in archive.get("catalogue", []) if book.get("display_name", "").casefold() == "mark"]
    if len(mark_rows) != 1:
        raise ValueError("Expected exactly one Mark catalogue discovery row for the related research-witness note.")
    mark_row = mark_rows[0]
    mark_row["chapter_count"] = "16 source chapter divisions in a related research witness; not verified for this catalogue entry"
    mark_row["chapter_order_status"] = "The Beta maṣāḥǝft research snapshot contains 16 ordered divisions; these do not establish the boundaries of this catalogue's intended edition."
    mark_row["text_availability_status"] = "No canon-linked reader is bundled for this entry. A separate Geʽez Mark TEI research witness is available; its exact Church-list work/edition crosswalk remains unresolved."
    mark_row["completeness_status"] = "The related TEI contains 765 line elements (678 numbered, 87 unnumbered). Structural counts do not establish completeness of the printed edition or applicability to this catalogue record."
    mark_row["rights_status"] = "CC BY-SA 4.0 is explicitly stated in the related LIT2711Mark TEI file and applies to that file and its marked/share-alike adaptations; it is not a rights determination for every Mark edition or catalogue crosswalk."
    mark_row["reviewer_notes"] = "Related research reader only. Geʽez is identified from the work description and the enclosing TEI edition's inherited xml:lang=gez; the TEI root's xml:lang=en document default remains recorded as a metadata conflict. Accuracy, exact print exemplar, completeness, current EOTC edition relation, and canon crosswalk remain unknown. It is not counted as canon-linked coverage."
    mark_row["evidence_source_ids"] = list(dict.fromkeys(mark_row.get("evidence_source_ids", []) + SOURCE_IDS))
    source_updates = {
        "SRC-083": "Official LIT2711Mark work record identifies the Gospel of Mark as Geʽez and says it was digitized from modern Vulgata printed editions. The retained TEI root declares xml:lang=\"en\", but the enclosing text edition declares xml:lang=\"gez\" for all chapters and lines, as verified against the TEI inheritance rule and the local snapshot. The text-language label is therefore Geʽez; the exact print exemplar, current EOTC edition relation, and canon crosswalk remain unknown.",
        "SRC-092": "Locally retained LIT2711Mark TEI snapshot and checksum-matched structural audit. A separate reader extracts every one of the 765 <l> elements (678 numbered, 87 unnumbered) and preserves original chapter labels and order. The enclosing edition declares xml:lang=\"gez\" for all extracted lines; the root's xml:lang=\"en\" default is preserved as a conflict. Inline markup is flattened and whitespace normalized in the display view; the unchanged TEI remains bundled. Accuracy, print completeness, and canon mapping remain unknown; the reader is outside canon-linked coverage.",
    }
    for source in archive.get("sources", []):
        if source.get("source_id") in source_updates:
            source["inspection_and_limitations"] = source_updates[source["source_id"]]
            source["archive_status"] = "Locally retained and readable as a separately scoped Geʽez research witness; exact EOTC work/edition crosswalk unresolved; not counted as canon coverage"
    if not any(source.get("source_id") == "SRC-176" for source in archive.get("sources", [])):
        archive.setdefault("sources", []).append({
            "source_id": "SRC-176",
            "source_name": "TEI Consortium — P5 Guidelines: global xml:lang attribute",
            "url": "https://tei-c.org/Vault/P5/current/doc/tei-p5-doc/en/html/ref-att.global.html",
            "inspection_and_limitations": "The TEI P5 Guidelines state that xml:lang indicates the language of an element's content and is inherited from enclosing elements. This supports interpreting the explicit xml:lang=\"gez\" on the Mark edition div as applying to its chapter and line descendants, despite the root's xml:lang=\"en\" default. The standard defines markup semantics; it does not establish whether the source's language assignment is textually correct or the transcription accurate.",
            "archive_status": "Official TEI language-inheritance guidance used to interpret the pinned Mark TEI's edition-level language declaration",
        })
    for source in archive.get("sources", []):
        if source.get("source_id") == "SRC-176":
            source["inspection_and_limitations"] = "The TEI P5 Guidelines state that xml:lang indicates the language of an element's content and is inherited from enclosing elements. This supports interpreting the explicit xml:lang=\"gez\" on the Mark edition div as applying to its chapter and line descendants, despite the root's xml:lang=\"en\" default. The standard defines markup semantics; it does not establish whether the source's language assignment is textually correct or the transcription accurate."
            source["archive_status"] = "Official TEI language-inheritance guidance used to interpret the pinned Mark TEI's edition-level language declaration"
    write_text_atomically(archive_path, json.dumps(archive, ensure_ascii=False, indent=2) + "\n")
    print(f"Extracted Mark TEI: {len(chapters)} chapters; {declared_lines} line elements ({numbered_lines} numbered, {declared_lines-numbered_lines} unnumbered).")
    return reader


if __name__ == "__main__":
    from build_mark_canon_reader import main
    main()
