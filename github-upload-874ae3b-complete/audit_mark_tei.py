"""Audit Mark TEI identity and source numbering without exporting verse text."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "readers" / "source" / "mark" / "LIT2711Mark-original.xml"
OUTPUT = ROOT / "readers" / "source" / "mark" / "structure-audit.json"
NS = {"tei": "http://www.tei-c.org/ns/1.0"}
XML = "{http://www.w3.org/XML/1998/namespace}"


def build_audit() -> dict:
    raw = SOURCE.read_bytes()
    root = ET.fromstring(raw)
    if root.tag != f"{{{NS['tei']}}}TEI" or root.attrib.get(XML + "id") != "LIT2711Mark":
        raise ValueError("Mark TEI root/work identity does not match LIT2711Mark.")
    license_nodes = root.findall(".//tei:licence", NS)
    licenses = [
        {
            "target": node.get("target", ""),
            "statement": " ".join(" ".join(node.itertext()).split()),
        }
        for node in license_nodes
    ]
    if not any(
        item["target"] == "http://creativecommons.org/licenses/by-sa/4.0/"
        and "Creative Commons Attribution-ShareAlike 4.0" in item["statement"]
        for item in licenses
    ):
        raise ValueError("The captured Mark TEI no longer contains the recorded file-level CC BY-SA 4.0 notice.")
    body = root.find(".//tei:body", NS)
    if body is None:
        raise ValueError("Captured Mark TEI has no text body.")
    root_language = root.get(XML + "lang")
    edition_divisions = [
        div for div in body.findall(".//tei:div", NS)
        if div.get("type") == "edition" and div.get(XML + "lang")
    ]
    if len(edition_divisions) != 1 or edition_divisions[0].get(XML + "lang") != "gez":
        raise ValueError("Mark TEI must have one explicit Geʽez-language edition scope.")
    edition_scope = edition_divisions[0]
    scoped_chapters = edition_scope.findall(".//tei:div[@subtype='chapter']", NS)
    scoped_lines = edition_scope.findall(".//tei:l", NS)
    body_chapters = body.findall(".//tei:div[@subtype='chapter']", NS)
    body_lines = body.findall(".//tei:l", NS)
    if len(scoped_chapters) != len(body_chapters) or len(scoped_lines) != len(body_lines):
        raise ValueError("Not all Mark chapter and line elements inherit the explicit Geʽez edition language.")
    if any(node.get(XML + "lang") for line in scoped_lines for node in line.iter()):
        raise ValueError("A Mark line contains an xml:lang override; review its language before assigning one reader language.")
    chapters = []
    for div in body.findall(".//tei:div[@subtype='chapter']", NS):
        label = div.get("n")
        lines = div.findall(".//tei:l", NS)
        numbered = [line.get("n") for line in lines if line.get("n") is not None]
        unnumbered = len(lines) - len(numbered)
        numeric = [int(value) for value in numbered if value.isdecimal()]
        observed = set(numeric)
        missing_inside_observed_range = (
            [value for value in range(min(numeric), max(numeric) + 1) if value not in observed]
            if numeric else []
        )
        chapters.append({
            "source_label": label,
            "line_elements": len(lines),
            "numbered_line_elements": len(numbered),
            "unnumbered_line_elements": unnumbered,
            "numbered_labels": numbered,
            "nondecimal_numbered_labels": [value for value in numbered if not value.isdecimal()],
            "duplicate_numeric_labels": sorted({value for value in numeric if numeric.count(value) > 1}),
            "missing_numeric_labels_inside_observed_range": missing_inside_observed_range,
            "numeric_labels_in_observed_order_are_contiguous": (
                all(right == left + 1 for left, right in zip(numeric, numeric[1:]))
                if numeric else None
            ),
        })
    labels = [chapter["source_label"] for chapter in chapters]
    return {
        "audit_version": 1,
        "audit_kind": "Mark TEI structural audit; this report exports no text; a separate research-reader extraction is stored locally",
        "source_path": SOURCE.relative_to(ROOT).as_posix(),
        "source_bytes": len(raw),
        "source_sha256": hashlib.sha256(raw).hexdigest(),
        "tei_work_id": "LIT2711Mark",
        "file_license_notice": next(
            item for item in licenses
            if item["target"] == "http://creativecommons.org/licenses/by-sa/4.0/"
            and "Creative Commons Attribution-ShareAlike 4.0" in item["statement"]
        ),
        "language_context": {
            "root_default_xml_lang": root_language,
            "edition_scope_element": "div[@type='edition']",
            "edition_scope_xml_lang": edition_scope.get(XML + "lang"),
            "chapter_divisions_in_scope": len(scoped_chapters),
            "line_elements_in_scope": len(scoped_lines),
            "all_body_chapters_and_lines_inherit_edition_language": True,
            "line_content_language_overrides": 0,
            "interpretation": (
                "The TEI root declares xml:lang='en', but the enclosing text edition explicitly declares xml:lang='gez'. "
                "The TEI Guidelines specify that xml:lang is inherited from enclosing elements; the edition-level value "
                "therefore applies to its chapter and line descendants. The root default is retained as a metadata conflict, "
                "not used to override the explicitly tagged text edition."
            ),
        },
        "chapter_count": len(chapters),
        "chapter_labels_in_observed_order": labels,
        "chapter_labels_match_1_to_16_in_order": labels == [str(index) for index in range(1, 17)],
        "line_element_count": sum(chapter["line_elements"] for chapter in chapters),
        "numbered_line_element_count": sum(chapter["numbered_line_elements"] for chapter in chapters),
        "unnumbered_line_element_count": sum(chapter["unnumbered_line_elements"] for chapter in chapters),
        "chapters": chapters,
        "interpretation_boundary": (
            "This checks the captured TEI work ID, explicit item-level license notice, inherited edition-level language, ordered chapter division labels, and each chapter's numbered line-label sequence. "
            "Unnumbered line elements are counted and retained in the original TEI; this report does not interpret or discard them. "
            "It does not establish text accuracy, completeness against a print exemplar or manuscript, verse equivalence, current EOTC edition identity, or canon crosswalk. "
            "A separate reader preserves the extracted source lines as a research view; it is not canon-linked and does not count toward Church-list coverage."
        ),
    }


def main() -> None:
    report = build_audit()
    OUTPUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        f"Audited {report['chapter_count']} ordered Mark chapters and "
        f"{report['numbered_line_element_count']} numbered plus "
        f"{report['unnumbered_line_element_count']} unnumbered line elements. "
        "No verse text exported; not reader coverage."
    )


if __name__ == "__main__":
    main()
