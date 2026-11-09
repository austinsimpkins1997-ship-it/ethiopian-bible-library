"""Record TAU/Platt Didascalia discovery evidence without claiming a verified reader."""

from __future__ import annotations

import json
import hashlib
import re
from pathlib import Path

from archive_manifest import write_text_atomically

ROOT = Path(__file__).resolve().parent
TAU_MENU_SOURCE = "SRC-086"
TAU_RIGHTS_SOURCE = "SRC-100"
TAU_INFO_SOURCE = "SRC-345"
MDZ_SOURCE = "SRC-346"
IA_OCR_SOURCE = "SRC-358"
QNL_CATALOGUE_SOURCE = "SRC-359"
QNL_RIGHTS_SOURCE = "SRC-360"
HARDEN_IA_SOURCE = "SRC-376"
HARDEN_GOOGLE_SOURCE = "SRC-377"
GEBRU_THESIS_SOURCE = "SRC-423"
HARDEN_BIO_SOURCE = "SRC-429"
CHURCH_SOURCE = "SRC-029"
SCHOLARSHIP_SOURCE = "SRC-073"
CANON_ID = "eotc-nt-35"
CATALOGUE_ID = "eotc-089"
EDITION_ID = "tau-platt-ethiopic-didascalia-1834"
TAU_INFO_URL = "https://www.tau.ac.il/~hacohen/Didas/Information.html"
MDZ_URL = "https://www.digitale-sammlungen.de/en/details/bsb10218768"
IA_URL = "https://archive.org/details/ethiopicdidascal00platrich"
HARDEN_IA_URL = "https://archive.org/details/cu31924096083336"
HARDEN_GOOGLE_URL = "https://books.google.com/books/about/The_Ethiopic_Didascalia.html?id=944gAAAAMAAJ"
GEBRU_THESIS_URL = "https://www.collectionscanada.gc.ca/obj/thesescanada/vol2/OTU/TC-OTU-35210.pdf"
HARDEN_BIO_URL = "https://arquivo.igreja-lusitana.org/e1izg"
QNL_URL = "https://ediscovery.qnl.qa/islandora/object/QNL:00012804"
QNL_DISCLAIMER_URL = "https://ediscovery.qnl.qa/disclaimer"
HEADING_AUDIT_PATH = ROOT / "research" / "didascalia-harden1920-chapter-heading-audit.json"


def _sort_sources(values: set[str]) -> list[str]:
    return sorted(values, key=lambda value: int(value.rsplit("-", 1)[1]))


def _put_edition_lead(registry: dict, lead: dict) -> None:
    leads = {item["edition_id"]: item for item in registry.get("edition_leads", [])}
    leads[lead["edition_id"]] = lead
    registry["edition_leads"] = sorted(leads.values(), key=lambda item: item["edition_id"])


def _put_translation_lead(registry: dict, lead: dict) -> None:
    leads = [
        item for item in registry.get("translation_leads", [])
        if not (item.get("canon_id") == lead["canon_id"]
                and item.get("language_tag") == lead["language_tag"]
                and item.get("edition") == lead["edition"])
    ]
    leads.append(lead)
    registry["translation_leads"] = leads


def build() -> None:
    archive_path = ROOT / "archive.json"
    archive = json.loads(archive_path.read_text(encoding="utf-8"))
    sources = {item["source_id"]: item for item in archive["sources"]}
    capture_dir = ROOT / "readers" / "source" / "didascalia-platt1834"
    capture_path = capture_dir / "capture-manifest.json"
    manifest_path = capture_dir / "iiif-manifest.json"
    capture = json.loads(capture_path.read_text(encoding="utf-8"))
    manifest_bytes = manifest_path.read_bytes()
    manifest = json.loads(manifest_bytes)
    canvases = manifest.get("sequences", [{}])[0].get("canvases", [])
    if (hashlib.sha256(manifest_bytes).hexdigest() != capture.get("sha256")
            or len(manifest_bytes) != capture.get("byte_length")
            or manifest.get("@id") != capture.get("manifest_url")
            or len(canvases) != capture.get("declared_canvas_count")
            or not canvases
            or canvases[0].get("label") != capture.get("first_canvas_label")
            or canvases[-1].get("label") != capture.get("last_canvas_label")):
        raise ValueError("Didascalia IIIF manifest capture does not match its local capture metadata.")

    ia_capture_path = capture_dir / "internet-archive-capture-manifest.json"
    ia_capture = json.loads(ia_capture_path.read_text(encoding="utf-8"))
    ia_files = {row["path"]: row for row in ia_capture.get("files", [])}
    expected_ia_files = {"internet-archive-djvu.txt", "internet-archive-djvu.xml"}
    if set(ia_files) != expected_ia_files:
        raise ValueError("Didascalia IA capture must inventory its raw TXT and XML OCR files.")
    for filename, metadata in ia_files.items():
        data = (capture_dir / filename).read_bytes()
        if (len(data) != metadata.get("byte_length")
                or hashlib.sha256(data).hexdigest() != metadata.get("sha256")
                or hashlib.md5(data).hexdigest() != metadata.get("md5")
                or hashlib.sha1(data).hexdigest() != metadata.get("sha1")):
            raise ValueError(f"Didascalia IA OCR capture failed local checksum validation: {filename}")
    import xml.etree.ElementTree as ET
    ia_text = (capture_dir / "internet-archive-djvu.txt").read_text(encoding="utf-8")
    ia_xml = ET.parse(capture_dir / "internet-archive-djvu.xml").getroot()
    ia_page_objects = sum(1 for node in ia_xml.iter() if node.tag.upper() == "OBJECT")
    ia_geez_codepoints = sum(1 for char in ia_text if "\u1200" <= char <= "\u137f")
    observed_limits = ia_capture.get("observed_limits", {})
    if (ia_page_objects != observed_limits.get("xml_page_object_count")
            or ia_geez_codepoints != observed_limits.get("ethiopic_unicode_codepoint_count")
            or ia_geez_codepoints != 0
            or ia_page_objects != 186
            or observed_limits.get("internet_archive_page_count") != 190):
        raise ValueError("Didascalia IA OCR observations changed; review the source audit before rebuilding.")

    harden_dir = ROOT / "readers" / "source" / "didascalia-harden1920"
    harden_metadata = json.loads((harden_dir / "internet-archive-metadata.json").read_text(encoding="utf-8"))
    harden_capture = json.loads((harden_dir / "capture-manifest.json").read_text(encoding="utf-8"))
    harden_files = {row["path"]: row for row in harden_capture.get("files", [])}
    provider_files = {row["name"]: row for row in harden_metadata.get("files", [])}
    if (harden_metadata.get("metadata", {}).get("identifier") != "cu31924096083336"
            or harden_metadata.get("metadata", {}).get("date") != "1920"
            or "Harden" not in harden_metadata.get("metadata", {}).get("creator", "")
            or set(harden_files) != {"djvu.txt", "djvu.xml"}):
        raise ValueError("Harden 1920 Didascalia metadata or OCR inventory is incomplete.")
    for filename, row in harden_files.items():
        data = (harden_dir / filename).read_bytes()
        provider_row = provider_files.get(f"cu31924096083336_{filename}", {})
        if (len(data) != row.get("byte_length")
                or hashlib.sha256(data).hexdigest() != row.get("sha256")
                or hashlib.md5(data).hexdigest() != row.get("md5")
                or hashlib.sha1(data).hexdigest() != row.get("sha1")
                or row.get("provider_md5") != provider_row.get("md5")
                or row.get("provider_sha1") != provider_row.get("sha1")):
            raise ValueError(f"Harden 1920 OCR capture failed provider/local checksum validation: {filename}")
    harden_xml = ET.parse(harden_dir / "djvu.xml").getroot()
    harden_page_objects = sum(1 for node in harden_xml.iter() if node.tag.upper() == "OBJECT")
    harden_text = (harden_dir / "djvu.txt").read_text(encoding="utf-8")
    harden_geez_codepoints = sum(1 for char in harden_text if "\u1200" <= char <= "\u137f")
    if (harden_page_objects != harden_capture.get("observed_limits", {}).get("xml_page_object_count")
            or harden_geez_codepoints != harden_capture.get("observed_limits", {}).get("unicode_geez_codepoints")
            or harden_page_objects != 238
            or harden_geez_codepoints != 0):
        raise ValueError("Harden 1920 OCR observations changed; review the source audit before rebuilding.")

    def to_roman(number: int) -> str:
        values = ((40, "XL"), (10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I"))
        result = []
        for value, numeral in values:
            while number >= value:
                result.append(numeral)
                number -= value
        return "".join(result)

    heading_occurrences = []
    for scan_page, page_object in enumerate(
            (node for node in harden_xml.iter() if node.tag.upper() == "OBJECT"), start=1):
        if not 29 <= scan_page <= 215:
            continue  # Excludes front matter and the general index after chapter XLIII.
        for line in page_object.iter("LINE"):
            line_text = " ".join((word.text or "") for word in line.iter("WORD"))
            match = re.search(r"\bCHAPTER\s+([IVXLCDM]+)\.", line_text, re.IGNORECASE)
            if match:
                heading_occurrences.append({
                    "scan_pdf_page": scan_page,
                    "ocr_label": match.group(1),
                })
    if len(heading_occurrences) != 43:
        raise ValueError(
            f"Harden heading audit expected 43 main-text OCR headings; found {len(heading_occurrences)}."
        )
    heading_entries = []
    corrections = {10: {"scan_pdf_page": 87, "ocr_label": "xX"},
                   31: {"scan_pdf_page": 165, "ocr_label": "XXXII"}}
    for number, occurrence in enumerate(heading_occurrences, start=1):
        confirmed = to_roman(number)
        correction = corrections.get(number)
        raw_label = occurrence["ocr_label"]
        mismatch = raw_label.upper() != confirmed
        if correction:
            if (occurrence["scan_pdf_page"] != correction["scan_pdf_page"]
                    or raw_label != correction["ocr_label"] or not mismatch):
                raise ValueError(f"Harden chapter {number} OCR correction no longer matches its reviewed scan page.")
        elif mismatch:
            raise ValueError(
                f"Unreviewed Harden chapter-heading discrepancy at occurrence {number}, PDF page "
                f"{occurrence['scan_pdf_page']}: OCR {raw_label!r}, expected scan label {confirmed!r}."
            )
        heading_entries.append({
            "chapter_number": number,
            "visually_confirmed_label": confirmed,
            "scan_pdf_page": occurrence["scan_pdf_page"],
            "ocr_label": raw_label,
            "ocr_matches_scan": not mismatch,
            "correction_note": (
                "The scanned heading reads X; Tesseract reads xX." if number == 10 else
                "The scanned heading reads XXXI; Tesseract reads XXXII." if number == 31 else None
            ),
        })
    heading_audit = {
        "schema_version": 1,
        "record_id": "didascalia-harden1920-chapter-heading-audit",
        "title": "Harden 1920 Ethiopic Didascalia: chapter-heading audit",
        "source_ids": [HARDEN_IA_SOURCE, HARDEN_GOOGLE_SOURCE],
        "ocr_xml_path": "readers/source/didascalia-harden1920/djvu.xml",
        "ocr_xml_sha256": harden_files["djvu.xml"]["sha256"],
        "scan_item_url": HARDEN_IA_URL,
        "scan_pdf_page_count_reported": 238,
        "chapter_heading_count": len(heading_entries),
        "visually_collated_heading_count": len(heading_entries),
        "visually_collated_scan_pdf_pages": sorted({item["scan_pdf_page"] for item in heading_entries}),
        "ocr_correction_count": sum(not item["ocr_matches_scan"] for item in heading_entries),
        "entries": heading_entries,
        "scope_note": (
            "All 43 OCR-detected main-text chapter headings were visually checked against the corresponding scan pages and form a "
            "continuous I–XLIII sequence in this 1920 printed edition. The source introduction reports manuscript variation, including "
            "a witness that joins IV/V. This edition-specific heading audit does not establish completeness of the digital scan, accuracy of "
            "the OCR body text, boundaries in every manuscript, or identity with the Ethiopian Orthodox Church-list Didascalia. No reader text is created."
        ),
        "body_text_proofread": False,
        "scan_completeness_reviewed": False,
        "church_list_identity_verified": False,
    }
    write_text_atomically(HEADING_AUDIT_PATH, json.dumps(heading_audit, ensure_ascii=False, indent=2) + "\n")

    # The top-level menu form was inspected in its HTML source: its control
    # exposes labels and relative scan-page targets, not transcribed scripture.
    sources[TAU_MENU_SOURCE] = {
        "source_id": TAU_MENU_SOURCE,
        "source_name": "Tel Aviv University — Ethiopic New Testament menu (Platt 1830 digitization)",
        "url": "https://www.tau.ac.il/~hacohen/NTBiblia.html",
        "inspection_and_limitations": (
            "Inspected 2026-10-25. The live page labels Didascalia under ‘LIBRI APOCRYPHI’. Its HTML form provides "
            "the labels ‘Cont.’, ‘Intro.’, chapters I–XXII, and ‘Notae’, each with a separate relative Didascalia page "
            "target. Four targets (Intro., I, XXI, Notae) were sampled; each wrapper contains one scan image. This "
            "verifies navigation to selected image pages, not complete page coverage, the contents of all chapters, "
            "transcription accuracy, or an exact crosswalk to any Church-list entry. See SRC-345 for the edition note "
            "and SRC-100 for the site-wide conditional reuse terms."
        ),
        "archive_status": "Didascalia image-page navigation inspected; sampled targets only; no transcription bundled",
    }
    sources[TAU_INFO_SOURCE] = {
        "source_id": TAU_INFO_SOURCE,
        "source_name": "Tel Aviv University — Ethiopic Didascalia edition information (Platt 1834)",
        "url": TAU_INFO_URL,
        "inspection_and_limitations": (
            "Inspected 2026-10-25. TAU identifies Thomas Pell Platt’s 1834 Ethiopic Didascalia, titled as including "
            "an English translation, and describes the website copy as an internet image version following that "
            "edition. It says each section and Platt’s notes are accessible from the main menu and points to a scan "
            "at the Internet Archive. This page does not inventory every scan page or establish that the 22 menu "
            "chapter labels equal the complete extent of the Church-list work. No image or text was copied."
        ),
        "archive_status": "Edition-level bibliographic and digitization metadata; no page-completeness or text audit",
    }
    sources[MDZ_SOURCE] = {
        "source_id": MDZ_SOURCE,
        "source_name": "Munich Digitization Center — Platt, The Ethiopic Didascalia (1834)",
        "url": MDZ_URL,
        "local_metadata_url": "readers/source/didascalia-platt1834/capture-manifest.json",
        "inspection_and_limitations": (
            "The Bayerische Staatsbibliothek catalogue identifies Thomas Pell Platt as editor and translator, gives "
            "the 1834 London publication, lists English and Geʽez, and describes 178 scans. The displayed rights "
            "statement is ‘No Copyright - Non-Commercial Use Only’. These catalogue statements identify a digitized "
            f"printed edition and its access terms. Its official IIIF Presentation manifest is archived locally; {len(canvases)} "
            f"canvas labels run from {canvases[0]['label']} through {canvases[-1]['label']}, matching the catalogue scan count. "
            "Only manifest metadata was saved; no scan images, OCR, or transcription were copied. The inventory does not "
            "establish completeness against the printed volume, textual accuracy, Church-list work boundaries, or an exact "
            "canon crosswalk. Inspected 2026-10-26."
        ),
        "archive_status": "Official 178-canvas IIIF manifest captured as metadata only; NoC-NC; no text or images bundled; work boundaries unverified",
    }
    sources[QNL_CATALOGUE_SOURCE] = {
        "source_id": QNL_CATALOGUE_SOURCE,
        "source_name": "Qatar National Library Digital Repository — Platt, The Ethiopic Didascalia (1834)",
        "url": QNL_URL,
        "rights_classification": "unknown",
        "rights_status": (
            "Qatar National Library's item record says ‘No Known Copyright’, but its repository disclaimer warns that content may be protected by third-party rights "
            "and disclaims a guarantee that reuse is clear. No item-specific redistribution license or permission was verified. Keep rights unknown; the catalogue label is not a reuse grant."
        ),
        "inspection_and_limitations": (
            "Inspected 2026-10-26. The Qatar National Library catalog identifies Thomas Pell Platt as editor/translator, "
            "gives the title as including an English translation, dates the edition to 1834, and records its extent as "
            "2 unnumbered pages, xvi, 131 pages, and 21 unnumbered pages. Its Rights field says ‘No Known Copyright’; "
            "this is catalog metadata, not a reuse license. QNL's repository disclaimer says content may be subject to "
            "third-party rights, public domain, or Creative Commons terms, disclaims a guarantee against infringement, "
            "and places responsibility for determining conditions on users. No scan or text was copied. This record does "
            "not establish worldwide reuse rights, complete pagination, or identity with the Church-list work."
        ),
        "archive_status": "Institutional catalogue evidence only; QNL Rights field says No Known Copyright, but repository disclaimer leaves reuse status undetermined; no text or images bundled",
    }
    sources[QNL_RIGHTS_SOURCE] = {
        "source_id": QNL_RIGHTS_SOURCE,
        "source_name": "Qatar National Library Digital Repository — copyright disclaimer",
        "url": QNL_DISCLAIMER_URL,
        "rights_classification": "unknown",
        "rights_status": (
            "This is repository-wide guidance, not an item-specific license. QNL says site content may be third-party-protected, public domain, or Creative Commons, "
            "does not warrant that sharing is free of third-party claims, and assigns users responsibility for determining reuse conditions. It grants no reuse right in the Platt volume."
        ),
        "inspection_and_limitations": (
            "Inspected 2026-10-26. The repository disclaimer says its content may be third-party-protected or may be "
            "public domain or Creative Commons; QNL does not warrant that sharing will be free of third-party claims "
            "and places responsibility for determining and satisfying copyright/use conditions on the user. This is a "
            "repository-wide disclaimer, not an item-specific license for the Platt volume."
        ),
        "archive_status": "Repository-wide terms evidence; not an item-specific license or global rights clearance",
    }
    sources[IA_OCR_SOURCE] = {
        "source_id": IA_OCR_SOURCE,
        "source_name": "Internet Archive — Platt 1834 Didascalia, raw ABBYY OCR files",
        "url": IA_URL,
        "local_ocr_url": "readers/source/didascalia-platt1834/internet-archive-djvu.txt",
        "local_metadata_url": "readers/source/didascalia-platt1834/internet-archive-capture-manifest.json",
        "rights_classification": "public_domain_claimed",
        "rights_status": (
            "Internet Archive metadata labels the 1834 item ‘Possible copyright status: NOT_IN_COPYRIGHT’ for the United States; this is provider metadata, not a license. "
            "The claim is scoped to the underlying publication in the United States and does not establish worldwide status or separate rights in the OCR or scan."
        ),
        "inspection_and_limitations": (
            "Internet Archive metadata identifies an 1834 publication, records no visible copyright notice, and displays "
            "‘Possible copyright status: NOT_IN_COPYRIGHT’ for the United States; its metadata API supplies no explicit "
            "license URL. The underlying 1834 publication is recorded as public-domain claimed for the US only, not as "
            "an open license or worldwide legal determination. The raw ABBYY TXT and XML OCR downloads are retained "
            "byte-for-byte with provider MD5/SHA-1 and local SHA-256 checks in the capture manifest. The TXT has no "
            "Ethiopic Unicode codepoints or form-feed page boundaries; the XML contains 186 page objects while the item "
            "page reports 190 pages. OCR accuracy, page completeness, Geʽez transcription, translation quality, and "
            "Church-list crosswalk were not verified. See the local metadata notice before reuse."
        ),
        "archive_status": (
            "Raw OCR stored locally for offline research only; explicitly unreviewed and not reader text; no reader or "
            "canon-linked coverage added; rights claim is US-only for the underlying 1834 publication"
        ),
    }
    sources[HARDEN_IA_SOURCE] = {
        "source_id": HARDEN_IA_SOURCE,
        "source_name": "Internet Archive — Harden 1920 Ethiopic Didascalia scan and raw OCR",
        "url": HARDEN_IA_URL,
        "local_ocr_url": "readers/source/didascalia-harden1920/djvu.txt",
        "local_metadata_url": "readers/source/didascalia-harden1920/capture-manifest.json",
        "local_heading_audit_url": "research/didascalia-harden1920-chapter-heading-audit.json",
        "local_research_view_url": "research/didascalia-harden1920-ocr-reader.html",
        "local_research_view_label": "Open chapter-indexed unproofread OCR research view",
        "rights_classification": "public_domain_claimed",
        "rights_status": (
            "The scanned book's front matter states that there are no known copyright restrictions in the United States. This is a US-scoped source claim, not a worldwide legal determination "
            "or a reuse license for the scan/OCR files. The Arquivo Histórico da Igreja Lusitana's preliminary authority record (SRC-429) lists a John Mason Harden as 1871–1931; "
            "this is a biographical lead only and identity with the translator is not established. The raw OCR remains unreviewed research material, not reader text."
        ),
        "inspection_and_limitations": (
            "The Internet Archive item describes a Cornell University Library scan of J. M. Harden's The Ethiopic Didascalia, "
            "published in 1920, and its front matter states that there are no known copyright restrictions in the United States. "
            "Harden's Introduction (pp. xvii–xviii) says the known-complete Ethiopic work is divided into 43 chapters in four of five "
            "British Museum manuscripts; MS 798 and Platt's manuscript join chapters IV and V under one title. This is an edition-level "
            "report, not proof of the Church-list entry's chapter structure. The local OCR contains 43 main-text chapter-heading occurrences. "
            "The raw Tesseract TXT and XML OCR are retained byte-for-byte; their MD5/SHA-1 values match the provider metadata and "
            "their local SHA-256 values are recorded in the capture manifest. The TXT is not proofread, and the XML has 238 image "
            "objects. Visual checks of scan PDF pages 87, 165, and 169 show the printed headings CHAPTER X, CHAPTER XXXI, and "
            "CHAPTER XXXII; the OCR misreads the first two as XX and XXXII. All 43 detected headings were visually collated, and the "
            "structured audit is stored locally. This does not verify a complete text or every manuscript's chapter boundaries. OCR is not a verified reader, translation "
            "accuracy is not assessed, the catalogued scan does not establish global rights, and exact identity with the Church-list "
            "Didascalia is unresolved."
        ),
        "archive_status": (
            "Raw 1920 English OCR and source metadata stored offline for research; all 43 detected headings visually checked, with two OCR numeral errors corrected in the audit; "
            "no reader text or canon-linked coverage; "
            "public-domain claim scoped to the United States; translator identity and worldwide rights unresolved"
        ),
    }
    sources[HARDEN_GOOGLE_SOURCE] = {
        "source_id": HARDEN_GOOGLE_SOURCE,
        "source_name": "Google Books — Harden, The Ethiopic Didascalia (1920) bibliographic record",
        "url": HARDEN_GOOGLE_URL,
        "inspection_and_limitations": (
            "Google Books bibliographic metadata identifies John Mason Harden as editor and translator, gives the 1920 "
            "publication, Society for Promoting Christian Knowledge, and 204 pages. This is edition metadata, not a text "
            "transcription or a complete-work/canon identity determination."
        ),
        "archive_status": "Bibliographic corroboration for the distinct Harden 1920 edition; no text accuracy or Church-list crosswalk established",
    }
    sources[GEBRU_THESIS_SOURCE] = {
        "source_id": GEBRU_THESIS_SOURCE,
        "source_name": "Mebratu Kiros Gebru — Liturgical Cosmology: The Theological and Sacramental Dimensions of Creation in the Ethiopian Liturgy (2012 doctoral thesis)",
        "url": GEBRU_THESIS_URL,
        "inspection_and_limitations": (
            "Inspected the 2012 PhD thesis awarded by the University of St. Michael's College, Toronto School of Theology. "
            "On printed p. 29, Gebru describes the Ethiopic Didascalia as a 43-chapter work, says chapters 1–32 correspond "
            "with variations to the 27 chapters of the Syriac Didascalia Apostolorum, and describes chapters 33–43 as material "
            "from Books VI–VII of the Apostolic Constitutions, including an abridged Book VII sequence with a reported omission. "
            "Gebru reviews competing scholarly accounts of the Ethiopic work's textual ancestry and suggests an Arabic basis; "
            "this is attributed scholarly interpretation, not a settled or independently verified stemma. The thesis states that "
            "Harden's 1920 translation is complete and Platt's 1834 translation contains only the first 23 chapters. These are "
            "secondary scholarly claims about those editions, not a local collation of either scan or proof of the Church-list "
            "entry's exact boundaries. No thesis text or scripture text is copied into the archive. Inspected 2026-10-26."
        ),
        "rights_classification": "unknown",
        "rights_status": (
            "This source record stores bibliographic citation and a concise attributed research note only. No license or permission "
            "to reproduce the thesis or its full text is recorded; rights for reuse remain unknown."
        ),
        "archive_status": "Scholarly scope and textual-history lead; attributed claims only; no reader text or canon coverage added",
    }
    sources[HARDEN_BIO_SOURCE] = {
        "source_id": HARDEN_BIO_SOURCE,
        "source_name": "Arquivo Histórico da Igreja Lusitana — archival authority record for John Mason Harden",
        "url": HARDEN_BIO_URL,
        "inspection_and_limitations": (
            "The archive authority record labels John Mason Harden's dates as 1871–1931 and describes his education and church career. "
            "The record is marked preliminary and minimum detail, and it cites Eduardo Henriques Moreira (1949) as a source. "
            "The name and dates are a biographical lead for the J. M. Harden credited in the 1920 Didascalia edition; this record alone "
            "does not establish that identity or determine copyright status in any jurisdiction. The page's notice restricts reuse of its "
            "text and images; no image or extended text is copied here. Inspected 2026-10-26."
        ),
        "archive_status": "Attributed biographical dates lead only; identity and jurisdictional rights remain unverified",
        "rights_classification": "unknown",
        "rights_status": (
            "The archive page restricts reuse of its text and images without permission. This project stores only a brief factual research note, "
            "not the page's image or extended text; the record's own reuse terms remain applicable to the linked resource."
        ),
    }
    archive["sources"] = sorted(sources.values(), key=lambda item: int(item["source_id"].split("-")[1]))

    catalogue = next(item for item in archive["catalogue"] if item["catalogue_id"] == CATALOGUE_ID)
    catalogue.update({
        "display_name": "Ethiopic Didascalia (Didǝsqǝlya)",
        "alternate_names_or_notes": (
            "TAU labels its Platt 1834 image edition Didascalia; this is a title-level candidate only, not a verified "
            "identification with the Church-list work or another manuscript recension."
        ),
        "identity_status": (
            "A Geʽez/English Platt 1834 edition is identified; its exact identity and scope relative to this Church-list entry remain unverified"
        ),
        "edition_or_translation": (
            "Distinct candidate editions include Thomas Pell Platt's 1834 bilingual Geʽez/English volume and J. M. Harden's "
            "1920 English edition. Raw IA OCR for both is stored as unreviewed research data; neither is a verified reader or "
            "an established exact match to the Church-list entry."
        ),
        "chapter_count": (
            "Not established for the Church-list work. Harden's 1920 Introduction reports 43 chapters in four of five manuscripts and says "
            "Platt's witness joins IV/V; Gebru (2012, printed p. 29) also describes 43 chapters and reports that Platt's English translation "
            "contains only the first 23 chapters. TAU's Platt menu labels I–XXII. These edition-specific reports are not interchangeable or a verified Church-list count."
        ),
        "chapter_order_status": (
            "Harden's Introduction reports 43 chapters in four of five manuscripts and says one manuscript combines IV/V; Gebru (2012, printed p. 29) independently describes 43 chapters and reports Platt's English translation as only the first 23. The local Harden OCR contains 43 main-text heading occurrences. All 43 heading labels were visually checked against the scan, confirming the printed I–XLIII sequence; the OCR misreads X as xX at PDF page 87 and XXXI as XXXII at page 165. The structured audit records each heading and its scan page. TAU's Platt menu labels I–XXII. These edition-specific observations do not establish the Church-list work's boundaries or reconcile the distinct witnesses."
        ),
        "text_availability_status": (
            "Platt 1834 and Harden 1920 editions are catalogued externally. Raw OCR from both Internet Archive scans is stored locally "
            "for research and is linked in the evidence records; it is unproofread and not a reader transcription."
        ),
        "local_research_views": [
            {
                "title": "Harden 1920 · chapter-indexed OCR research view",
                "path": "research/didascalia-harden1920-ocr-reader.html",
                "link_label": "Open local OCR research view",
                "scope_note": (
                    "Stored locally for inspection. All 43 chapter headings were checked against the scan; the body OCR is unproofread, "
                    "scan completeness is unassessed, and this is not a canon-verified reader or translation."
                ),
            }
        ],
        "completeness_status": (
            "Not assessed for the Church-list work or either edition; catalog extent and OCR image counts do not establish completeness."
        ),
        "rights_status": (
            "Platt 1834 scan providers state conditional noncommercial reuse terms or leave third-party rights unresolved. The Harden 1920 "
            "scan front matter says no known copyright restrictions in the United States; this is not an explicit open license or a "
            "worldwide legal determination. No blanket rights conclusion is asserted."
        ),
        "verification_date": "2026-10-26",
        "reviewer_notes": (
            "The Church-list page and Asale's attributed canon discussion support the displayed title's catalogue placement. Gebru's 2012 thesis (SRC-423) "
            "describes a 43-chapter Ethiopic Didascalia with additions relative to the Syriac Didascalia and reports Platt's translation as partial; "
            "this genealogy is a scholarly interpretation. Harden's 43 OCR heading labels have been visually checked against that scan, but its chapter sequence has not been reconciled with Platt's witness or established as the Church-list work's boundaries. "
            "Platt 1834 and Harden 1920 are distinct bibliographic editions, with raw OCR from both stored locally for research. "
            "Harden's printed introduction reports edition-specific 43-chapter and manuscript-variation details; its OCR heading sequence has two numeral conflicts. "
            "Neither text has undergone complete transcription, translation, "
            "or boundary review. The title match does not prove identical work scope, recension, completeness, or exact Church-list "
            "identity. Treat both as edition leads, not verified readers."
        ),
        "source_id": CHURCH_SOURCE,
        "catalogue_seed_url": "https://www.ethiopianorthodox.org/english/canonical/books.html?lang=en",
        "evidence_source_ids": [CHURCH_SOURCE, SCHOLARSHIP_SOURCE, TAU_MENU_SOURCE, TAU_RIGHTS_SOURCE, TAU_INFO_SOURCE, MDZ_SOURCE, IA_OCR_SOURCE, QNL_CATALOGUE_SOURCE, QNL_RIGHTS_SOURCE, HARDEN_IA_SOURCE, HARDEN_GOOGLE_SOURCE, GEBRU_THESIS_SOURCE, HARDEN_BIO_SOURCE],
    })

    canon = archive["canon_registry"]
    book = next(item for item in canon["books"] if item["canon_id"] == CANON_ID)
    book["source_ids"] = _sort_sources(set(book.get("source_ids", [])) | {
        CHURCH_SOURCE, SCHOLARSHIP_SOURCE, TAU_MENU_SOURCE, TAU_RIGHTS_SOURCE, TAU_INFO_SOURCE, MDZ_SOURCE, IA_OCR_SOURCE, QNL_CATALOGUE_SOURCE, QNL_RIGHTS_SOURCE, HARDEN_IA_SOURCE, HARDEN_GOOGLE_SOURCE, GEBRU_THESIS_SOURCE, HARDEN_BIO_SOURCE,
    })
    book["reader_status"] = (
        "No verified reader bundled; raw OCR from Platt 1834 and Harden 1920 is stored for research, but text accuracy, boundaries, and exact Church-list identity remain unverified"
    )
    book["mapping_note"] = (
        "The Church list names Didascalia and Asale discusses it among broader-list additions. Platt 1834 and Harden 1920 "
        "are title-level candidate editions; their boundaries and relationship to the listed work have not been established. Gebru (2012, p. 29) "
        "describes a 43-chapter Ethiopic work with material beyond the Syriac Didascalia and reports Platt's English as partial (first 23 chapters); "
        "the report's textual-history interpretation and chapter numbering have not been checked against the witnesses. No verified reader text is bundled."
    )

    registry_path = ROOT / "translation-registry.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    source_ids = [CHURCH_SOURCE, SCHOLARSHIP_SOURCE, TAU_MENU_SOURCE, TAU_RIGHTS_SOURCE, TAU_INFO_SOURCE, MDZ_SOURCE, IA_OCR_SOURCE, QNL_CATALOGUE_SOURCE, QNL_RIGHTS_SOURCE, GEBRU_THESIS_SOURCE]
    edition_lead = {
        "edition_id": EDITION_ID,
        "candidate_canon_id": CANON_ID,
        "mapping_state": "uncertain",
        "title": "The Ethiopic Didascalia — Platt 1834, TAU image edition",
        "witness_type": "digital_edition",
        "language_tag": "gez",
        "language_name": "Geʽez (Classical Ethiopic)",
        "script_code": "Ethi",
        "edition_statement": (
            "Thomas Pell Platt, editor and translator, The Ethiopic Didascalia, or the Ethiopic Version of the Apostolical "
            "Constitutions, Received in the Church of Abyssinia, with an English Translation (London, 1834). TAU describes "
            "its copy as an internet image version following Platt's edition; MDZ catalogs a bilingual English/Geʽez copy."
        ),
        "scope_description": (
            "The TAU menu exposes an introduction, 22 numbered sections (I–XXII), and notes as image-page selections. "
            "Only four image-page wrappers were sampled. Gebru (2012, printed p. 29) reports that Platt's English translation "
            "contains only the first 23 chapters of the 43-chapter Ethiopic work; this secondary report and TAU's 22 menu labels "
            "remain unreconciled. Neither describes a verified full extent or chapter crosswalk to the Church-list Didascalia. "
            "Raw IA OCR is stored separately for research, not as reader text."
        ),
        "source_ids": source_ids,
        "text_bundled": False,
        "rights_status": (
            "TAU grants noncommercial use, copying, and distribution of its digitized Ethiopic texts only with the stated "
            "Ran HaCohen copyright and permission notices; MDZ labels its scan ‘No Copyright - Non-Commercial Use Only’. "
            "This is conditional noncommercial permission, not an open or commercial license. QNL labels its catalogue object “No Known Copyright” but its disclaimer says third-party rights may apply and leaves reuse determinations to users. Image reuse and territory "
            "specific status remain to be reviewed; no verified text or images are bundled for this edition lead. A separate IA raw OCR capture is research-only."
        ),
        "rights_classification": "permission_limited",
        "review_status": (
            "Bibliographic and menu metadata reviewed 2026-10-25. The HTML form lists sections I–XXII; four wrapper pages "
            "were sampled and each contained one scan image. The English translation, full page sequence, chapter boundaries, "
            "text accuracy, complete extent, exact canon mapping, and image reuse terms have not been audited."
        ),
    }
    _put_edition_lead(registry, edition_lead)
    harden_lead = {
        "edition_id": "harden-ethiopic-didascalia-1920",
        "candidate_canon_id": CANON_ID,
        "mapping_state": "uncertain",
        "title": "The Ethiopic Didascalia — Harden 1920, raw OCR research edition",
        "witness_type": "digital_edition",
        "language_tag": "en",
        "language_name": "English",
        "script_code": "Latn",
        "edition_statement": (
            "J. M. Harden, The Ethiopic Didascalia (London: Society for Promoting Christian Knowledge; New York: Macmillan, 1920). "
            "Internet Archive describes its copy as a Cornell University Library scan; Google Books catalogs Harden as editor/translator."
        ),
        "scope_description": (
            "The source OCR is stored locally as unproofread TXT and page-structured XML. Harden's Introduction reports 43 chapters in four "
            "of five named manuscripts and says Platt's manuscript combines IV/V; this is a statement about the 1920 edition's reported witnesses. "
            "The OCR contains 43 main-text heading occurrences; all 43 headings were visually checked against the corresponding scan pages. "
            "The audit corrects OCR numeral errors on PDF pages 87 (X, OCR xX) and 165 (XXXI, OCR XXXII). Full text accuracy and scan completeness have not been reviewed. "
            "The relation to the Church-list Didascalia remains unverified. "
            "This is a source-access record, not a verified reader or canon crosswalk."
        ),
        "source_ids": [HARDEN_IA_SOURCE, HARDEN_GOOGLE_SOURCE, CHURCH_SOURCE, SCHOLARSHIP_SOURCE, GEBRU_THESIS_SOURCE, HARDEN_BIO_SOURCE],
        "text_bundled": False,
        "rights_status": (
            "The scanned volume's front matter states that there are no known copyright restrictions in the United States. The Arquivo Histórico da Igreja Lusitana "
            "lists a John Mason Harden as 1871–1931 (SRC-429), but this preliminary biographical record does not establish identity with this translator. "
            "These are source-reported leads, not an explicit open license or a global legal determination."
        ),
        "rights_classification": "public_domain_claimed",
        "review_status": (
            "The 1920 edition metadata, raw OCR checksums, the preliminary biographical lead SRC-429, and Harden Introduction's pp. xvii–xviii statement of 43 chapters in four of five witnesses "
            "were inspected. Platt's manuscript exception joining IV/V is recorded as Harden's report. The local OCR yields 43 main-text heading "
            "occurrences. All 43 headings were visually checked against the corresponding scan pages; PDF pages 87 and 165 correct Tesseract numeral "
            "readings (X vs. xX; XXXI vs. XXXII). Complete text accuracy, scan completeness, and exact Church-list identity remain unreviewed. "
            "No full-text accuracy, translation, completeness, or exact Church-list identity review was performed."
        ),
    }
    _put_edition_lead(registry, harden_lead)
    _put_translation_lead(registry, {
        "translation_id": "didascalia-en-platt-1834",
        "canon_id": CANON_ID,
        "title": "The Ethiopic Didascalia — English translation accompanying Platt’s 1834 edition",
        "mapping_state": "uncertain",
        "scope_description": (
            "Partial English translation accompanying the 1834 Ethiopic edition. Gebru (2012, printed p. 29) reports that Platt's "
            "translation contains only the first 23 chapters of the 43-chapter Ethiopic Didascalia. TAU's menu labels I–XXII; "
            "the difference and the menu's relationship to printed chapters require examination. No English text is extracted or bundled, "
            "and the exact relation to the Church-list entry has not been established."
        ),
        "language_tag": "en",
        "translator": "Thomas Pell Platt (bibliographically credited as editor and translator)",
        "edition": "The Ethiopic Didascalia (London, 1834), English translation accompanying the Ethiopic edition",
        "translation_path": ["gez", "en"],
        "source_ids": [TAU_INFO_SOURCE, MDZ_SOURCE, TAU_RIGHTS_SOURCE, QNL_CATALOGUE_SOURCE, QNL_RIGHTS_SOURCE, GEBRU_THESIS_SOURCE],
        "text_bundled": False,
        "rights_status": (
            "MDZ labels the digitized volume ‘No Copyright - Non-Commercial Use Only’; TAU's permission for its digitized "
            "Ethiopic text requires noncommercial use and its stated notices. This is not an unrestricted or commercial license."
        ),
        "rights_classification": "permission_limited",
        "review_status": (
            "The edition title identifies an English translation accompanying the Ethiopic version, and the catalogue "
            "credits Platt as translator; the recorded Geʽez-to-English path is bibliographic attribution only. No "
            "translation text, wording accuracy, completeness, or correspondence to the Church-list entry was reviewed."
        ),
        "notes": (
            "The Geʽez-to-English direction is reported from the edition title and catalogued languages, not verified by "
            "comparing text. The underlying Geʽez/English pages were not extracted; no reviewed translation text or wording equivalence, "
            "verse alignment, or accuracy is asserted."
        ),
    })
    unbundled_lead_count = sum(
        1
        for key in ("translation_leads", "edition_leads", "corpus_leads")
        for item in registry.get(key, [])
        if item.get("text_bundled") is False
    )
    coverage = registry.get("coverage_statement", "")
    updated_coverage, replacements = re.subn(
        r"The registry also contains \d+ unbundled translation, source-edition, or corpus leads\.",
        f"The registry also contains {unbundled_lead_count} unbundled translation, source-edition, or corpus leads.",
        coverage,
    )
    if replacements != 1:
        raise ValueError("Expected exactly one unbundled-lead count in the translation coverage statement")
    registry["coverage_statement"] = updated_coverage

    archive["translation_registry"] = registry
    canon_path = ROOT / "canon-registry.json"
    write_text_atomically(canon_path, json.dumps(canon, ensure_ascii=False, indent=2) + "\n")
    write_text_atomically(registry_path, json.dumps(registry, ensure_ascii=False, indent=2) + "\n")
    write_text_atomically(archive_path, json.dumps(archive, ensure_ascii=False, indent=2) + "\n")

    report = (
        "# Ethiopic Didascalia — source discovery review\n\n"
        "The [EOTC English canon page](https://www.ethiopianorthodox.org/english/canonical/books.html?lang=en) includes the Church-list title Didascalia. "
        "In its explanatory section, the same Church page describes the Ethiopic Didascalia as containing the first seven books of the Apostolic Constitutions and says its subject matter differs from Latin, Arabic, and Syriac versions. This is the Church page's own description; it does not identify the Platt or Harden witnesses as the exact current Church-list edition. "
        "Asale's discussion is attributed comparative scholarship, not a Church ruling. "
        "[TAU's Didascalia notes](" + TAU_INFO_URL + ") identify the 1834 Platt edition and describe TAU's copy as an image version; "
        "the [TAU menu](https://www.tau.ac.il/~hacohen/NTBiblia.html) exposes an introduction, sections I–XXII, and notes. "
        "Four menu targets were sampled, each as a single-image wrapper. The [MDZ catalogue](" + MDZ_URL + ") identifies Platt as editor/translator, lists Geʽez and English, and marks the digitized object NoC-NC. The [Qatar National Library catalogue](" + QNL_URL + ") independently records the 1834 title, Platt attribution, English translation in the title, and print extent (2 unnumbered pages, xvi, 131 pages, 21 unnumbered pages); its Rights field says ‘No Known Copyright’. The [QNL disclaimer](" + QNL_DISCLAIMER_URL + ") warns that materials may remain subject to third-party rights and requires users to determine reuse conditions. This metadata does not clear global reuse. Its [official IIIF manifest](https://api.digitale-sammlungen.de/iiif/presentation/v2/bsb10218768/manifest) enumerates 178 scan canvases labelled (0001)–(0178), matching the catalogued scan count. A local copy of the manifest metadata and its SHA-256 are stored [here](../readers/source/didascalia-platt1834/capture-manifest.json). The independent [Internet Archive item](" + IA_URL + ") also provides an OCR derivative; the raw TXT and XML are stored [here](../readers/source/didascalia-platt1834/internet-archive-djvu.txt) and [here](../readers/source/didascalia-platt1834/internet-archive-djvu.xml), with checksums and limitations in the [capture manifest](../readers/source/didascalia-platt1834/internet-archive-capture-manifest.json).\n\n"
        "\n\nA separate edition, J. M. Harden's The Ethiopic Didascalia (1920), is catalogued by [Google Books](" + HARDEN_GOOGLE_URL + ") as an English work of 204 pages and is held in a [Cornell scan at Internet Archive](" + HARDEN_IA_URL + "). Its raw Tesseract TXT and page-structured XML are stored locally [here](../readers/source/didascalia-harden1920/djvu.txt), [here](../readers/source/didascalia-harden1920/djvu.xml), and [here](../readers/source/didascalia-harden1920/capture-manifest.json). The provider checksums match; the scan front matter states that no known copyright restrictions apply in the United States. This is not an explicit open license or a global rights determination. Harden's Introduction (pp. xvii–xviii) reports 43 chapters in four of five manuscripts and says Platt's manuscript joins IV/V under one title. The local OCR contains 43 main-text chapter-heading occurrences. All 43 headings were visually checked against the corresponding scan pages; the [structured audit](didascalia-harden1920-chapter-heading-audit.json) records the confirmed I–XLIII sequence and corrects OCR numeral errors on PDF pages 87 (X, OCR xX) and 165 (XXXI, OCR XXXII). The [chapter-indexed OCR research view](didascalia-harden1920-ocr-reader.html) exposes grouped OCR lines for inspection; its body text has not been proofread. Scan completeness has not been reviewed, and the audit does not establish the Church-list work's chapter structure or identity. These are edition-specific observations, not a verified reader.\n\n"
        "A separate scholarly context source, [Mebratu Kiros Gebru's 2012 doctoral thesis](" + GEBRU_THESIS_URL + "), describes the Ethiopic Didascalia as 43 chapters: chapters 1–32 correspond with variation to the 27 Syriac Didascalia chapters, while 33–43 include material from Apostolic Constitutions VI–VII. It discusses competing accounts of the Ethiopic text's ancestry and suggests an Arabic basis; that genealogy is an attributed scholarly interpretation. Gebru reports that Platt's English translation contains only the first 23 chapters, while Harden's is complete. This clarifies that Platt cannot serve as a whole-work English reader, but the claim has not been checked against the scans and the TAU menu's I–XXII labels remain unexplained. No text is added. Source SRC-423.\n\n"
        "The [Arquivo Histórico da Igreja Lusitana authority record](" + HARDEN_BIO_URL + ") lists John Mason Harden's dates as 1871–1931 and marks its own description preliminary and minimal. This is a biographical lead for the 1920 translator, not a proven identity or a copyright determination; the archive's text and images are marked as restricted for reuse. No image or extended archival text is bundled. Source SRC-429.\n\n"
        "The menu count is not proof of the Church-list work's scope, completeness, canonical classification, or textual accuracy. "
        "Platt is credited as translator, and the recorded Geʽez-to-English path is based on the title and catalogue metadata, "
        "not text comparison. TAU's notice is conditional on "
        "noncommercial reuse with the required notices; image-specific and jurisdiction-specific reuse still needs review. "
        "The scan manifest confirms only the digital object's listed canvases, not completeness of the printed volume or Church-list work. "
        "The Internet Archive OCR remains unreviewed: TXT has no Ethiopic Unicode or page breaks, XML has 186 page objects while the item page reports 190 pages. It is not a Geʽez transcription or reader. The US-only public-domain claim reflects the provider's 1834/no-visible-notice metadata, not an explicit open license or a global legal determination. "
        "No reader or canon-linked coverage is added. Sources SRC-029, SRC-073, SRC-086, SRC-100, SRC-345, SRC-346, SRC-358, SRC-359, SRC-360, SRC-376, SRC-377, SRC-423, and SRC-429.\n"
    )
    write_text_atomically(ROOT / "research" / "didascalia-source-review.md", report)
    print("Recorded Platt 1834 and Harden 1920 Didascalia source editions; raw OCR is exposed for research, with no reader or canon crosswalk asserted.")


if __name__ == "__main__":
    build()
