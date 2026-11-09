"""Build an edition-specific chapter-indexed view of unproofread Didascalia OCR."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET

from archive_manifest import write_text_atomically


ROOT = Path(__file__).resolve().parent
CAPTURE_DIR = ROOT / "readers" / "source" / "didascalia-harden1920"
CAPTURE_PATH = CAPTURE_DIR / "capture-manifest.json"
AUDIT_PATH = ROOT / "research" / "didascalia-harden1920-chapter-heading-audit.json"
OUTPUT_PATH = ROOT / "research" / "didascalia-harden1920-ocr-chapters.json"
CHAPTER_LINE = re.compile(r"^\s*CHAPTER\s+([IVXLCDM]+)\.", re.IGNORECASE)


def build() -> dict:
    capture = json.loads(CAPTURE_PATH.read_text(encoding="utf-8"))
    audit = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
    xml_path = CAPTURE_DIR / "djvu.xml"
    xml_bytes = xml_path.read_bytes()
    xml_hash = hashlib.sha256(xml_bytes).hexdigest()
    if xml_hash != audit.get("ocr_xml_sha256"):
        raise ValueError("Harden OCR XML no longer matches the visually checked heading audit.")
    xml_record = next((item for item in capture.get("files", []) if item.get("path") == "djvu.xml"), None)
    if (xml_record is None or len(xml_bytes) != xml_record.get("byte_length")
            or xml_hash != xml_record.get("sha256")):
        raise ValueError("Harden OCR XML failed the stored capture-manifest integrity check.")
    if (audit.get("chapter_heading_count") != 43
            or audit.get("visually_collated_heading_count") != 43
            or audit.get("body_text_proofread") is not False
            or audit.get("scan_completeness_reviewed") is not False
            or audit.get("church_list_identity_verified") is not False):
        raise ValueError("Harden heading audit scope changed; review before building the OCR view.")

    pages = [node for node in ET.fromstring(xml_bytes).iter() if node.tag.upper() == "OBJECT"]
    audit_entries = audit["entries"]
    if len(audit_entries) != 43 or len(pages) != capture.get("observed_limits", {}).get("xml_page_object_count"):
        raise ValueError("Harden OCR page or chapter-heading inventory changed.")

    chapters: list[dict] = []
    active: dict | None = None
    heading_index = 0
    for page_number, page in enumerate(pages, start=1):
        if page_number > 215:
            break  # The audited source review identifies the later OCR pages as index matter.
        for line in page.iter("LINE"):
            line_text = " ".join((word.text or "") for word in line.iter("WORD")).strip()
            if not line_text:
                continue
            match = CHAPTER_LINE.match(line_text)
            if match:
                if heading_index >= len(audit_entries):
                    raise ValueError("The OCR contains more main-text chapter headings than the visual audit.")
                audited = audit_entries[heading_index]
                if (page_number != audited["scan_pdf_page"]
                        or match.group(1).upper() != audited["ocr_label"].upper()):
                    raise ValueError(
                        f"OCR heading {heading_index + 1} no longer matches its audited page and label."
                    )
                active = {
                    "chapter_number": audited["chapter_number"],
                    "heading": audited["visually_confirmed_label"],
                    "ocr_heading_label": audited["ocr_label"],
                    "heading_corrected_from_ocr": not audited["ocr_matches_scan"],
                    "correction_note": audited["correction_note"],
                    "heading_scan_pdf_page": page_number,
                    "pages": [],
                }
                chapters.append(active)
                heading_index += 1
                # The printed chapter title follows the audited chapter heading.
                continue
            if active is None:
                continue
            if not active["pages"] or active["pages"][-1]["scan_pdf_page"] != page_number:
                active["pages"].append({"scan_pdf_page": page_number, "lines": []})
            active["pages"][-1]["lines"].append(line_text)

    if heading_index != len(audit_entries) or [item["chapter_number"] for item in chapters] != list(range(1, 44)):
        raise ValueError(f"Expected the visually audited I–XLIII sequence; found {heading_index} headings.")
    if any(not chapter["pages"] or not any(page["lines"] for page in chapter["pages"]) for chapter in chapters):
        raise ValueError("A chapter heading has no OCR body lines in the indexed source pages.")

    result = {
        "schema_version": 1,
        "record_id": "didascalia-harden1920-raw-ocr-view",
        "title": "The Ethiopic Didascalia — Harden 1920 English raw OCR research view",
        "source_id": "SRC-376",
        "language_tag": "en",
        "script_code": "Latn",
        "text_origin": "published_translation",
        "translation_basis_status": "unknown",
        "rights_classification": "public_domain_claimed",
        "rights_status": "The scanned edition's front matter states that no known copyright restrictions apply in the United States. This is a US-scoped claim, not a worldwide legal determination or an open license.",
        "candidate_canon_id": "eotc-nt-35",
        "canon_mapping_state": "uncertain",
        "chapter_count": len(chapters),
        "source_ocr_path": "readers/source/didascalia-harden1920/djvu.xml",
        "source_ocr_sha256": xml_hash,
        "heading_audit_path": "research/didascalia-harden1920-chapter-heading-audit.json",
        "scope_note": "This is an edition-specific navigation aid for raw Tesseract OCR, not a proofread transcription or a canon-verified reader. All 43 chapter headings in this edition were visually collated against the scan; chapter boundaries in other witnesses, scan completeness, body-text accuracy, and exact identity with the Church-list Didascalia remain unverified. Two OCR heading numerals are shown using their visually confirmed labels; their OCR readings and correction notes are retained here.",
        "chapters": chapters,
    }
    write_text_atomically(OUTPUT_PATH, json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    return result


if __name__ == "__main__":
    view = build()
    lines = sum(len(page["lines"]) for chapter in view["chapters"] for page in chapter["pages"])
    print(f"Built an edition-specific raw OCR view: {len(view['chapters'])} audited headings, {lines} OCR lines.")
