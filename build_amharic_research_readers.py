"""Build permission-limited Amharic NT readers from the pinned eBible HTML capture."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import zipfile

from build_gamo_research_readers import chapter_links, extract_chapter, find, normalized, parse_html
from build_gamo_title_normalization import BOOK_NAMES
from book_code_crosswalks import PUBLISHER_BOOK_CODE_CANDIDATES


ROOT = Path(__file__).resolve().parent
SOURCE_DIR = ROOT / "readers" / "source" / "amharic"
SOURCE_ZIP = SOURCE_DIR / "amh-html-pages.zip"
CAPTURE_MANIFEST = SOURCE_DIR / "capture-manifest.json"
OUTPUT_DIR = ROOT / "readers"
LANGUAGE_TAG = "am"
SCRIPT_CODE = "Ethi"
SOURCE_IDS = ["SRC-196", "SRC-197", "SRC-198", "SRC-341", "SRC-342"]
EDITION_ID = "AMH2003 / amh"
TRANSLATION_ID = "amh2003eb"

STANDARD_NT_CODES = {
    "MAT", "MRK", "LUK", "JHN", "ACT", "ROM", "1CO", "2CO", "GAL", "EPH", "PHP", "COL",
    "1TH", "2TH", "1TI", "2TI", "TIT", "PHM", "HEB", "JAS", "1PE", "2PE", "1JN", "2JN",
    "3JN", "JUD", "REV",
}

NT_CATALOGUE_CANDIDATES = {code: PUBLISHER_BOOK_CODE_CANDIDATES[code] for code in STANDARD_NT_CODES}

COPYRIGHT_NOTICE = (
    "Copyright © 1962, 2003 United Bible Societies. Language: አማርኛ (Amharic). Amharic NT. "
    "Revised Amharic Bible in XML (2003). Printed version by United Bible Societies (© 1962). "
    "E-text in transliterated ASCII format by Lapsley/Brooks Foundation (1994). Unicode UTF-8 "
    "transformation and XML-tagging by Dirk Röckmann (2003; www.nt-text.net). With kind permission "
    "of the Bible Society of Ethiopia. Every non-commercial work using this data in any form must "
    "fully include this copyright statement. Every commercial use of parts or the complete data in "
    "any form needs written permission of the Bible Society of Ethiopia. Copyright page dated 2014-09-09."
)


def _load_capture() -> tuple[dict[str, bytes], dict]:
    manifest = json.loads(CAPTURE_MANIFEST.read_text(encoding="utf-8"))
    if manifest.get("upstream_url") != "https://ebible.org/Scriptures/amh_html.zip":
        raise ValueError("Amharic capture manifest does not identify the official eBible source package.")
    if manifest.get("filtered_capture_file") != SOURCE_ZIP.name:
        raise ValueError("Amharic capture manifest points to a different filtered package.")
    raw_zip = SOURCE_ZIP.read_bytes()
    if hashlib.sha256(raw_zip).hexdigest() != manifest.get("filtered_capture_sha256"):
        raise ValueError("Amharic HTML-only source package checksum mismatch.")
    members = {item["path"]: item for item in manifest.get("members", [])}
    with zipfile.ZipFile(SOURCE_ZIP) as source:
        names = sorted(source.namelist())
        if names != sorted(members):
            raise ValueError("Amharic HTML package members do not match the capture manifest.")
        pages = {}
        for name in names:
            item = members[name]
            body = source.read(name)
            if len(body) != item.get("bytes") or hashlib.sha256(body).hexdigest() != item.get("sha256"):
                raise ValueError(f"Amharic captured page failed size/SHA validation: {name}")
            if not name.lower().endswith((".htm", ".html")):
                raise ValueError(f"Non-HTML asset found in media-free Amharic capture: {name}")
            pages[name] = body
    if len(pages) != 290 or not {"index.htm", "copyright.htm", "copr.htm"}.issubset(pages):
        raise ValueError(f"Expected 290 HTML pages including publisher and copyright indexes, found {len(pages)}.")
    return pages, manifest


def _read_menu(index_bytes: bytes) -> list[dict]:
    document = parse_html(index_bytes)
    containers = find(document, lambda node: node.tag == "div" and "bookList" in node.classes())
    if len(containers) != 1:
        raise ValueError("Expected one .bookList in the Amharic publisher index.")
    entries = []
    for anchor in find(containers[0], lambda node: node.tag == "a"):
        href = (anchor.attrs.get("href") or "").split("?")[0]
        match = re.fullmatch(r"([A-Z0-9]{3})01\.htm", href)
        title = normalized(anchor.text())
        if match and title:
            entries.append({"code": match.group(1), "source_title_label": title, "position": len(entries) + 1})
    observed_codes = [item["code"] for item in entries]
    if len(entries) != 27 or len(set(observed_codes)) != 27 or set(observed_codes) != STANDARD_NT_CODES:
        raise ValueError(f"Expected the 27 standard New Testament menu codes; observed {observed_codes!r}.")
    return entries


def build() -> tuple[list[dict], list[dict], list[dict]]:
    """Return reader records, scoped corpus records, and evidence sources."""
    pages, manifest = _load_capture()
    entries = _read_menu(pages["index.htm"])
    canon_registry = json.loads((ROOT / "canon-registry.json").read_text(encoding="utf-8"))
    canon_titles = {book["canon_id"]: book["display_name"] for book in canon_registry["books"]}
    readers: list[dict] = []
    corpora: list[dict] = []
    source_index_hashes = {
        name: hashlib.sha256(pages[name]).hexdigest()
        for name in ["index.htm", "copyright.htm", "copr.htm"]
    }
    total_chapters = 0

    for item in entries:
        code = item["code"]
        if code not in BOOK_NAMES:
            raise ValueError(f"No standard English navigation name registered for Amharic book code {code}.")
        if code not in NT_CATALOGUE_CANDIDATES:
            raise ValueError(f"No provisional 81-entry catalogue candidate registered for Amharic book code {code}.")
        index_name = f"{code}.htm"
        if index_name not in pages:
            raise ValueError(f"Amharic book index is missing: {index_name}")
        links = chapter_links(parse_html(pages[index_name]), code)
        chapters = []
        page_hashes = [{"page": index_name, "sha256": hashlib.sha256(pages[index_name]).hexdigest()}]
        unit_count = 0
        for number, filename, source_chapter_label in links:
            if filename not in pages:
                raise ValueError(f"Amharic chapter menu points to missing page: {filename}")
            page_title, headings, units, notes = extract_chapter(pages[filename], code, source_chapter_label)
            if not units or any(not unit.get("text", "").strip() for unit in units):
                raise ValueError(f"Empty Amharic text unit in {filename}.")
            page_hashes.append({"page": filename, "sha256": hashlib.sha256(pages[filename]).hexdigest()})
            chapters.append({
                "chapter": number,
                "source_chapter_label": source_chapter_label,
                "source_page_title": page_title,
                "heading": headings,
                "units": units,
                "notes": notes,
            })
            unit_count += len(units)

        if len(chapters) != links[-1][0]:
            raise ValueError(f"Amharic chapter sequence is not complete from 1 through {links[-1][0]} for {code}.")
        total_chapters += len(chapters)
        english_name = BOOK_NAMES[code]
        source_label = item["source_title_label"]
        candidate_canon_id = NT_CATALOGUE_CANDIDATES[code]
        canon_title = canon_titles[candidate_canon_id]
        reader_id = f"amh2003-{code.lower()}-research"
        corpus_id = reader_id
        code_title_note = (
            f"Reviewed work/title match for {candidate_canon_id} ({canon_title}): the EOTC's cited "
            f"81-entry list names {canon_title}; the captured publisher menu and page identify this member "
            f"with standard code {code}; the official USFM/USX table maps that code to {english_name}. "
            "The Amharic title remains verbatim and is not translated by this normalization. This is a "
            "title crosswalk only, not evidence that this edition belongs to or follows the EOTC canon. "
            "Evidence: SRC-029, SRC-196, SRC-197, SRC-198, and SRC-396."
        )
        reader = {
            "reader_id": reader_id,
            "research_corpus_id": corpus_id,
            "publisher_book_code": code,
            "source_menu_position": item["position"],
            "source_title_label": source_label,
            "reader_scope": "research_witness_reviewed_title_match",
            "title": f"{english_name} — Amharic text ({source_label})",
            "display_name": f"{english_name} · Amharic (AMH2003)",
            "normalized_title_en": english_name,
            "title_normalization": {
                "method": "publisher_standard_book_code_lookup",
                "publisher_book_code": code,
                "normalized_english_name": english_name,
                "source_title_label": source_label,
                "is_translation_of_source_label": False,
                "canon_mapping": "reviewed_work_title_match",
                "source_ids": ["SRC-029", "SRC-196", "SRC-197", "SRC-198", "SRC-396"],
                "note": code_title_note,
            },
            "text_origin": "published_translation",
            "language": "Amharic (አማርኛ)",
            "language_tag": LANGUAGE_TAG,
            "language_assignment_status": "publisher_identified_amharic",
            "script_code": SCRIPT_CODE,
            "translation_id": TRANSLATION_ID,
            "translator": "Translation team not named in the cited copyright page; source notes identify Lapsley/Brooks Foundation e-text (1994) and Dirk Röckmann's UTF-8 conversion/XML tagging (2003).",
            "translation_basis_status": "unknown",
            "translation_basis_note": "The eBible publisher metadata does not document a source-text path. Haile Selassie's 1961 statement describes the 1947–1952 committee's aim as revising the existing Amharic Bible with reference to Hebrew and Greek. A. F. Matthew, a committee member, reports that the 1955 New Testament revision used Nestle's 1904 Greek text, following an Ethiopic reading where the Nestle apparatus listed the same alternative. These are historical statements about the revision process, not proof that this 2003 digital witness reproduces the 1962 print text without change. No collation establishes this reader's book-level lineage, so its path remains unknown.",
            "edition": "United Bible Societies, Revised Amharic Bible in XML (2003), based on the printed version (1962); Lapsley/Brooks Foundation e-text (1994); Unicode UTF-8 transformation/XML tagging by Dirk Röckmann (2003); eBible.org source files dated 2025-12-12.",
            "edition_scope": f"This is the Amharic New Testament publisher-menu entry {item['position']} under label {source_label!r} and standard book code {code}. The 81-entry catalogue link is provisional and title-level; relation to any particular church canon list or printed exemplar is not established.",
            "rights_classification": "permission_limited",
            "copyright_notice": COPYRIGHT_NOTICE,
            "commercial_use": "The source page permits use in non-commercial works only when the complete copyright statement is included with every such work. Commercial use of any part or all of the data requires written permission from the Bible Society of Ethiopia. This is permission-limited reuse, not an open license or a general public-domain claim.",
            "license_id": None,
            "license_url": "https://ebible.org/amh/copyright.htm",
            "chapter_count": len(chapters),
            "unit_count": unit_count,
            "unit_label": "publisher-displayed Amharic verse marker",
            "verse_marker_count": unit_count,
            "section_label": "Chapter",
            "chapter_structure_note": "Chapter sequence follows the publisher's linked book index and filename order. The original Ethiopic chapter label is retained alongside the numeric navigation order; verse markers are retained verbatim and are not renumbered. Counts describe captured page structure only.",
            "transcription_note": "Text was parsed from the retained eBible.org HTML-only page capture. Ethiopic letters and source verse labels are preserved; HTML whitespace is normalized. Page navigation, copyright footer, and any separately parsed apparatus are excluded from verse bodies. This is a structural extraction, not a new translation or independent proofreading.",
            "editorial_signs_note": "Publisher verse-marker strings and any parsed source notes are retained. No editorial sign is reinterpreted or silently removed from a verse body.",
            "verification_status": f"Structural extraction from the pinned eBible.org AMH2003 / amh capture: this menu entry links to {len(chapters)} consecutive chapter pages; {unit_count} nonempty verse spans retain their displayed Ethiopic labels; source page hashes are recorded. The standard book-code match to the EOTC list title is reviewed separately; this structural check does not validate translation accuracy, completeness against a printed edition, source language, or exact Church-edition identity.",
            "source_ids": SOURCE_IDS,
            "source_pages": f"readers/source/amharic/amh-html-pages.zip; publisher pages index.htm, {index_name}, and {len(chapters)} chapter pages; copyright.htm and copr.htm retained.",
            "source_snapshot_url": "https://ebible.org/Scriptures/amh_html.zip",
            "source_snapshot_sha256": manifest["upstream_package_sha256"],
            "source_extract_sha256": manifest["filtered_capture_sha256"],
            "source_index_hashes": source_index_hashes,
            "source_page_hashes": page_hashes,
            "chapters": chapters,
        }
        readers.append(reader)
        corpora.append({
            "corpus_id": corpus_id,
            "title": f"{english_name} ({EDITION_ID}) — Amharic research reader",
            "reader_id": reader_id,
            "unit_count": unit_count,
            "reader_status": "bundled_research_reader",
            "canon_mapping_state": "reviewed_match",
            "candidate_canon_id": candidate_canon_id,
            "canon_mapping_note": (
                f"Reviewed work/title match for {candidate_canon_id} ({canon_title}): the Ethiopian Orthodox Church's "
                f"cited 81-entry list names {canon_title}; the retained eBible AMH2003 / amh menu and linked publisher "
                f"pages identify this member with standard code {code}; the official USFM/USX table maps {code} to "
                f"{english_name}. The captured Amharic label {source_label!r} is preserved verbatim and is not treated "
                "as an English translation. Evidence: SRC-029, SRC-196, SRC-197, SRC-198, and SRC-396. This is a "
                "work/title crosswalk only. It does not establish EOTC, Eritrean, or other tradition affiliation; exact "
                "edition identity; textual accuracy; printed completeness; or the translation's source/relay language. "
                "The Amharic text remains a separate, permission-limited research reader, not canon-linked coverage."
            ),
            "language_description": "The eBible.org copyright and book pages identify this work as Amharic (አማርኛ); the source pages use Ethiopic script.",
            "script_description": "Ethiopic script (Ethi), observed in the captured pages and identified by the source.",
            "unit_summary": f"{len(chapters)} linked chapter pages and {unit_count} nonempty publisher verse spans in this book entry; source-structure counts are not a completeness or accuracy review.",
            "rights_classification": "permission_limited",
            "rights_status": "The provider permits non-commercial use only when the complete copyright statement accompanies every work using the data. Commercial use requires written permission from the Bible Society of Ethiopia. No standardized open license is claimed.",
            "license_id": None,
            "license_url": "https://ebible.org/amh/copyright.htm",
            "review_status": "Machine-checked structural extraction from retained HTML pages only; no independent wording review, translation-basis audit, print collation, textual-completeness claim, or exact Church-edition identification. The separate book-code/title crosswalk is reviewed against cited list and code-table evidence.",
            "source_ids": SOURCE_IDS,
            "text_origin": "published_translation",
            "language_tag": LANGUAGE_TAG,
            "script_code": SCRIPT_CODE,
            "translation_id": TRANSLATION_ID,
            "translator": reader["translator"],
            "translation_basis_status": "unknown",
            "translation_basis_note": reader["translation_basis_note"],
            "edition_statement": reader["edition"],
        })

    if total_chapters != 260:
        raise ValueError(f"Expected the captured 27-book NT menus to link 260 chapter pages; observed {total_chapters}.")

    sources = [
        {
            "source_id": "SRC-197",
            "source_name": "eBible.org — Amharic New Testament edition and copyright statement (AMH2003 / amh)",
            "url": "https://ebible.org/amh/copyright.htm",
            "inspection_and_limitations": "The source identifies the text as the New Testament in Amharic, copyright © 1962, 2003 United Bible Societies; Revised Amharic Bible in XML (2003); printed version © 1962; e-text in transliterated ASCII by Lapsley/Brooks Foundation (1994); Unicode UTF-8 transformation and XML tagging by Dirk Röckmann (2003); and publication with kind permission of the Bible Society of Ethiopia. It expressly permits inclusion in non-commercial works only with the complete copyright statement and requires written permission for commercial use. The source does not establish the translation's source-language path, completeness against a print witness, accuracy, or an EOTC canon crosswalk.",
            "archive_status": "Edition, contribution history, language, script, and non-commercial reuse condition recorded; no commercial/open-license claim",
        },
        {
            "source_id": "SRC-198",
            "source_name": "eBible.org — Amharic NT HTML package, locally retained HTML-only capture",
            "url": "readers/source/amharic/amh-html-pages.zip",
            "inspection_and_limitations": f"The upstream package {manifest['upstream_url']} was downloaded 2026-10-25 (1,292,269 bytes; SHA-256 {manifest['upstream_package_sha256']}). This archive retains a deterministic 290-member HTML-only ZIP (SHA-256 {manifest['filtered_capture_sha256']}) plus per-page byte counts and SHA-256 values in readers/source/amharic/capture-manifest.json. Fonts, stylesheets, images, and other non-HTML assets were excluded. The 27 publisher book indexes link to 260 sequential chapter pages; extraction counts are structure observations, not independent content review or proof of printed-edition completeness.",
            "archive_status": "Captured local HTML-only source snapshot with per-page hashes; non-HTML assets excluded",
        },
        {
            "source_id": "SRC-341",
            "source_name": "Haile Selassie I — statement on the revised Amharic Bible (23 July 1961; English transcription)",
            "url": "https://www.greengoldgardens.com/CE/UCI/CIH/Leaders/01-Haile-Selassie-I/Selected_Speeches/Haile_Selassie_I-Selected_Speeches-Chapter_XV-19610723.html",
            "inspection_and_limitations": "Inspected 2026-10-25. This page transcribes Haile Selassie I's statement dated 23 July 1961 about the revised Amharic Bible. He says the Bible Committee established in 1947 worked on a revision of the existing translation with reference to the original Hebrew and Greek, and presented its work in 1952. This is evidence of the stated purpose and process as described by the Emperor, not independent proof of source-text use in every book. The English transcription is hosted by a non-institutional site and was not collated here against the printed 1961 preface. It does not establish the exact lineage of the 2003 e-text or the text used for any individual book.",
            "archive_status": "Primary historical statement in an unverified English transcription; records declared revision aim, not book-level translation path",
        },
        {
            "source_id": "SRC-342",
            "source_name": "A. F. Matthew — The Revision of the Amharic New Testament (committee member's report, 1956)",
            "url": "https://translation.bible/wp-content/uploads/2024/05/matthew-hazlitt-1956-the-revision-of-the-amharic-new-testament.pdf",
            "inspection_and_limitations": "Inspected 2026-10-25. Published in The Bible Translator 7, no. 2 (1956), pp. 72–76. A. F. Matthew identifies himself as the British and Foreign Bible Society representative on the joint revision committee and reports that its New Testament revision used Nestle's 1904 Greek text, generally following it except where the apparatus's alternative reading matched the Ethiopic version, in which case that alternative was followed. The report describes the 1955 New Testament revision and committee process; it does not demonstrate that the eBible.org 2003 electronic text is textually identical to that 1955 edition or the 1962 print edition. No book-by-book collation of this reader was performed.",
            "archive_status": "Committee-member's historical report on 1955 New Testament textual basis; lineage to the bundled 1962/2003 witness remains unverified",
        },
    ]
    return readers, corpora, sources

