"""Bundle the open-labeled 1890 Bilin Mark scan as a facsimile, not a transcription."""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET


PDF_SHA256 = "6c8cbeb9109df6a2ef8b0b334c2a421a87eb48e4da5b105d3bebc61021b81619"
OCR_SHA256 = "90ef69f6dc1b33a851aaa95e66c23bf0dabbc96f1b8d60531943674da863d375"
METADATA_SHA256 = "6bf948b82a64a0fb3b51f5d796cb5eadb03654ec63edbdfcd0a21eb3e170076e"
SCANDATA_SHA256 = "29f3a6f477eeb666fee0e172c8ec3a66e47a9990971a1146435ed3acf67be477"
ROOT = Path(__file__).resolve().parent
CAPTURE_DIR = ROOT / "readers" / "source" / "bilin-mark-1890"


def validate_capture() -> dict:
    """Verify captured source bytes and the scan's physical page count, without asserting text accuracy."""
    files = {
        "Bilin-1890-Mark.pdf": (2_846_416, PDF_SHA256),
        "Bilin-1890-Mark_djvu.txt": (64_080, OCR_SHA256),
        "internet-archive-metadata.json": (6_728, METADATA_SHA256),
        "Bilin-1890-Mark_scandata.xml": (28_292, SCANDATA_SHA256),
    }
    captured = {}
    for filename, (expected_size, expected_sha256) in files.items():
        path = CAPTURE_DIR / filename
        if not path.is_file():
            raise ValueError(f"Bilin Mark source capture is missing: {filename}")
        payload = path.read_bytes()
        digest = hashlib.sha256(payload).hexdigest()
        if len(payload) != expected_size or digest != expected_sha256:
            raise ValueError(f"Bilin Mark source capture changed: {filename}")
        source_files = {
            "Bilin-1890-Mark.pdf": "Bilin-%281890%29-Mark.pdf",
            "Bilin-1890-Mark_djvu.txt": "Bilin-%281890%29-Mark_djvu.txt",
            "Bilin-1890-Mark_scandata.xml": "Bilin-%281890%29-Mark_scandata.xml",
        }
        captured[filename] = {
            "size_bytes": len(payload),
            "sha256": digest,
            "source_url": (
                "https://archive.org/metadata/BYNEWT_DBS_HS"
                if filename == "internet-archive-metadata.json"
                else "https://archive.org/download/BYNEWT_DBS_HS/" + source_files[filename]
            ),
        }
    scan_data = ET.parse(CAPTURE_DIR / "Bilin-1890-Mark_scandata.xml").getroot()
    page_data = scan_data.find("pageData")
    page_count = len(page_data) if page_data is not None else 0
    if page_count != 80:
        raise ValueError(f"Internet Archive scan-data page count changed: expected 80, found {page_count}")
    metadata = json.loads((CAPTURE_DIR / "internet-archive-metadata.json").read_text(encoding="utf-8"))
    item = metadata.get("metadata", {})
    if item.get("identifier") != "BYNEWT_DBS_HS" or item.get("language") != "byn":
        raise ValueError("Bilin Mark captured item metadata identity/language mismatch.")
    if item.get("ocr_invalid_language") != "byn" or item.get("ocr_detected_lang") != "kk":
        raise ValueError("Expected OCR language-detection warning is absent from captured metadata.")
    manifest = {
        "source_id": "SRC-305",
        "capture_date": "2026-10-25",
        "source_item_id": "BYNEWT_DBS_HS",
        "rights_evidence_source_ids": ["SRC-304", "SRC-339"],
        "http_status": 200,
        "pdf_content_type": "application/pdf",
        "physical_page_count": page_count,
        "page_count_basis": "80 page records in captured Internet Archive scandata.xml; pdfinfo independently reported 80 PDF pages at capture time",
        "script_observation": {
            "code": "Ethi",
            "basis": "Visual inspection of rendered cover and three interior pages",
            "conflict": "DBS metadata conflict: this witness is labeled Latin (Latn)",
        },
        "ocr_assessment": {
            "file": "Bilin-1890-Mark_djvu.txt",
            "method_as_reported": item.get("ocr"),
            "configured_languages": item.get("ocr_parameters"),
            "detected_language": item.get("ocr_detected_lang"),
            "invalid_source_language": item.get("ocr_invalid_language"),
            "use": "Diagnostic only; not a transcription or reader layer",
        },
        "files": captured,
        "scope_note": "Captured scan and metadata do not establish textual accuracy, complete edition boundaries, translation basis, or canon affiliation.",
    }
    (CAPTURE_DIR / "capture-manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return manifest

SOURCES = [
    {
        "source_id": "SRC-339",
        "source_name": "Internet Archive — BYNEWT_DBS_HS item metadata and OCR derivatives",
        "url": "https://archive.org/metadata/BYNEWT_DBS_HS",
        "inspection_and_limitations": (
            "Retrieved 2026-10-25. The captured 6,728-byte JSON metadata identifies item BYNEWT_DBS_HS, title "
            "'Bilin (1890) Mark', language code byn, an 80-page 600-ppi PDF (2,846,416 bytes), and a 64,080-byte "
            "Tesseract OCR derivative. The item metadata says the Digital Bible Society is unaware of copyright "
            "restrictions; the OCR parameters omit byn, mark byn invalid, and report Kazakh (kk) with Cyrillic as "
            "the detected language/script. That OCR is retained only as a diagnostic and is not a reading text. "
            "Captured metadata SHA-256: 6bf948b82a64a0fb3b51f5d796cb5eadb03654ec63edbdfcd0a21eb3e170076e. "
            "The scan's first cover and three interior page renders were visually inspected; no full collation, "
            "transcription, completeness review, or translation-basis review was performed."
        ),
        "archive_status": "Captured item metadata and OCR diagnostic; the OCR is rejected as unsuitable for reading",
    }
]


def apply(archive: dict) -> None:
    """Idempotently record the scan, script conflict, and bounded Bilen survey update."""
    validate_capture()
    sources = {item["source_id"]: item for item in archive.get("sources", [])}
    sources.update({item["source_id"]: deepcopy(item) for item in SOURCES})
    sources["SRC-304"] = {
        "source_id": "SRC-304",
        "source_name": "Digital Bible Society / Find a Bible — BYNEWT Bilen New Testament record",
        "url": "https://arc.dbs.org/data/scripture/BYNEWT/",
        "inspection_and_limitations": (
            "Inspected 2026-10-25. Record title says 'Bilen New Testament,' but its scope metadata says 'New "
            "Testament portions' and its description identifies only the Gospel of Mark translated by Stefanos "
            "under Leo Reinisch and published by the British and Foreign Bible Society at Vienna. It labels "
            "the language Bilin (byn), script Latin, and copyright Public Domain / OPEN. The linked 1890 scan "
            "is now retained as a facsimile; visual review of its cover and three interior pages shows Ethiopic "
            "script, so the record's Latin script label conflicts with the scanned witness. The provider's rights "
            "classification is preserved as a claim, not an independent legal determination. The 2018 Blin New "
            "Testament report describes a separate, modern project."
        ),
        "archive_status": "Provider record inspected; linked 1890 Mark scan bundled as a facsimile with a recorded script-metadata conflict",
    }
    sources["SRC-305"] = {
        "source_id": "SRC-305",
        "source_name": "Internet Archive — Bilin (1890) Mark scanned PDF linked by DBS",
        "url": "https://archive.org/download/BYNEWT_DBS_HS/Bilin-%281890%29-Mark.pdf",
        "local_copy_url": "research/bilin-mark-1890.html",
        "inspection_and_limitations": (
            "Retrieved 2026-10-25 from the file linked by the Digital Bible Society BYNEWT record (HTTP 200, "
            "application/pdf, 2,846,416 bytes, SHA-256 6c8cbeb9109df6a2ef8b0b334c2a421a87eb48e4da5b105d3bebc61021b81619). "
            "The PDF contains 80 scanned pages at 600 ppi. The cover and three interior pages were rendered and "
            "visually inspected; the printed text uses Ethiopic script, in conflict with DBS's Latin script field. "
            "The scan is bundled unchanged as a facsimile; no OCR text is presented as scripture. DBS/Find a Bible "
            "labels the item Public Domain / OPEN, while Internet Archive metadata says its contributor is unaware "
            "of copyright restrictions. This provider-stated rights basis is not a worldwide legal determination. "
            "No page-by-page completeness, textual accuracy, translation-basis, or canon-affiliation audit was performed."
        ),
        "archive_status": "80-page facsimile bundled offline under provider-stated public-domain status; text and canon mapping remain unverified",
        "rights_classification": "public_domain_claimed",
        "rights_basis": "Digital Bible Society / Find a Bible labels this item Public Domain / OPEN; Internet Archive metadata says the contributor is unaware of copyright restrictions. Provider claims are preserved without a worldwide legal conclusion.",
        "rights_status": "DBS/Find a Bible labels the linked scan Public Domain / OPEN; Internet Archive records its contributor as unaware of copyright restrictions. These are provider claims, not an independent worldwide rights determination or separate clearance of digitization rights. The PDF is bundled unchanged as a facsimile; no OCR text is presented as scripture.",
    }
    archive["sources"] = sorted(sources.values(), key=lambda item: item["source_id"])

    registry = archive.setdefault("translation_registry", {})
    profile = next((item for item in registry.get("languages", []) if item.get("language_tag") == "byn"), None)
    if profile is None:
        raise ValueError("Bilin (byn) language profile is required before recording the scan.")
    linked_source_ids = {"SRC-303", "SRC-304", "SRC-305", "SRC-306", "SRC-307", "SRC-339"}
    profile["source_ids"] = sorted(
        set(profile.get("source_ids", [])) | linked_source_ids,
        key=lambda value: int(value.split("-")[1]),
    )
    profile["script_codes"] = ["Ethi", "Latn"]
    profile["script_code"] = "Zzzz"
    profile["script_profile_note"] = (
        "Sources document historical Ethiopic use and later/current Latin-based orthography. The bundled 1890 "
        "Mark scan visibly uses Ethiopic script, although the Digital Bible Society record for that item says "
        "Latin; the conflict is preserved and the two scripts are not generalized to all Bilin texts. The script "
        "of the separate 2018 New Testament witness has not been checked."
    )
    survey = profile.get("availability_survey")
    if not isinstance(survey, dict):
        raise ValueError("Bilin availability survey is required before recording the scan.")
    survey["source_ids"] = sorted(
        set(survey.get("source_ids", [])) | linked_source_ids,
        key=lambda value: int(value.split("-")[1]),
    )
    survey["scope"] = (
        "Inspected the Scripture Earth Blin (byn) resource listing, the Digital Bible Society BYNEWT record and "
        "its linked 1890 Mark scan, and two publication reports concerning the 2018 Blin New Testament launch. "
        "The bounded result count is two digital resource listings, not two translations or complete editions. The 1890 "
        "Mark item is bundled as an 80-page Ethiopic-script facsimile; the provider's Latin script label conflicts "
        "with the scan. Its Tesseract OCR is retained only as an unusable diagnostic, not as reader text. The "
        "reported 2018 New Testament is a separate modern edition and remains unbundled. This survey does not "
        "establish the complete present-day Blin corpus, the scope or rights of the modern edition, an EOTC or "
        "Eritrean Orthodox canon crosswalk, or the accuracy/completeness of the 1890 scan."
    )
    survey["notes"] = (
        "The 1890 scan was retrieved from the exact PDF linked by DBS and retained with the original IA metadata, "
        "OCR derivative, and scan data. DBS/Find a Bible labels it Public Domain / OPEN; IA metadata says the "
        "contributor is unaware of restrictions. This is recorded as a provider-stated rights claim. The scan is "
        "available as a local facsimile; no text transcription was created. Its rendered Ethiopic script conflicts "
        "with the DBS record's Latin script field. The OCR settings omit the byn language, identify it as invalid, "
        "and misclassify the text as Kazakh/Cyrillic, so the OCR is not suitable as scripture text. The modern "
        "2018 Blin New Testament reports do not identify a public digital text or reuse license. See SRC-303–SRC-307 "
        "and SRC-339."
    )
