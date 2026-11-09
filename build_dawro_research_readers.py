"""Build source-backed research readers from eBible.org's Dawro Latin Bible.

The publisher's 66 USFM modules are stored separately and kept outside all
church-canon mappings. Source labels and structure are parsed conservatively;
the original signed package is retained for comparison.
"""

from __future__ import annotations

from html.parser import HTMLParser
import hashlib
import json
import re
import zipfile
from pathlib import Path

import build_maale_research_readers as maale
from archive_manifest import write_text_atomically

ROOT = Path(__file__).resolve().parent
SOURCE_DIR = ROOT / "readers" / "source" / "dawro"
SOURCE = SOURCE_DIR / "dwrl_usfm.zip"
DETAILS = SOURCE_DIR / "dwrl-details.html"
INDEX = SOURCE_DIR / "ebible-download-index.html"
DEVELOPER_DETAILS = SOURCE_DIR / "dwrl-developer-details.html"
MANIFEST = ROOT / "research" / "dawro-latin-usfm-source-manifest.json"
MENU_JSON = ROOT / "research" / "dawro-latin-menu.json"
MENU_HTML = ROOT / "research" / "dawro-latin-menu.html"
NOTICE = SOURCE_DIR / "SOURCE-NOTICE.txt"

DETAIL_URL = "https://ebible.org/details.php?id=dwrl"
INDEX_URL = "https://ebible.org/download.php"
PACKAGE_URL = "https://ebible.org/Scriptures/dwrl_usfm.zip"
LICENSE_URL = "https://creativecommons.org/licenses/by-sa/4.0/"
KEY_FINGERPRINT_URL = maale.KEY_FINGERPRINT_URL
KEY_FINGERPRINT = maale.KEY_FINGERPRINT
SOURCE_IDS = ["SRC-403", "SRC-404", "SRC-405", "SRC-406"]
REVIEWED_AT = "2026-10-26"
EXPECTED_PACKAGE_SHA256 = "babec0c76176e5eaa10f5f7f0b31296bd889802871ee8ab8350866d76f5d080f"
EXPECTED_MEMBER_COUNT = 70
EXPECTED_USFM_COUNT = 66


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def discover_codes(members: dict[str, bytes]) -> list[str]:
    """Read the book order from the publisher's package, retaining it exactly."""
    codes = []
    seen = set()
    for name, raw in members.items():
        if not name.lower().endswith(".usfm"):
            continue
        parsed = maale.parse_book(raw, name)
        if not re.fullmatch(r"\d{2}-[A-Z0-9]{3}dwrl\.usfm", name):
            raise ValueError(f"Unexpected Dawro USFM member filename {name!r}.")
        if parsed["code"] in seen or not name.endswith(f"-{parsed['code']}dwrl.usfm"):
            raise ValueError(f"Duplicate or mismatched Dawro book code in {name!r}.")
        seen.add(parsed["code"])
        codes.append(parsed["code"])
    if len(codes) != EXPECTED_USFM_COUNT or set(codes) != set(maale.BOOK_NAMES):
        raise ValueError(
            "The retained publisher package is not the pinned 66-module inventory; "
            f"observed {len(codes)} members and codes {codes!r}."
        )
    return codes


def read_and_verify_package(package: bytes) -> tuple[dict[str, bytes], dict[str, str], dict, list[str]]:
    if sha256(package) != EXPECTED_PACKAGE_SHA256:
        raise ValueError("The retained Dawro USFM ZIP differs from the pinned source-package bytes.")
    with zipfile.ZipFile(SOURCE) as archive:
        bad_member = archive.testzip()
        if bad_member:
            raise ValueError(f"Dawro ZIP CRC validation failed at {bad_member}.")
        names = archive.namelist()
        if len(names) != EXPECTED_MEMBER_COUNT or len(names) != len(set(names)):
            raise ValueError(f"Expected {EXPECTED_MEMBER_COUNT} unique package members; found {len(names)}.")
        all_members = {name: archive.read(name) for name in names}
    if not {"keys.asc", "signature.txt.asc", "copr.htm", "liberationsans.css"} <= set(all_members):
        raise ValueError("The Dawro package lacks expected license, signature, key, or stylesheet members.")

    signature = maale.verify_checksum_signature(all_members["keys.asc"], all_members["signature.txt.asc"])
    if signature["signer_fingerprint"] != KEY_FINGERPRINT:
        raise ValueError("The Dawro checksum-list signer differs from the pinned publisher-key fingerprint.")
    signed_text = all_members["signature.txt.asc"].decode("utf-8", "replace")
    declared = {
        match.group(2): match.group(1).lower()
        for match in re.finditer(r"^([0-9a-f]{64})\s+(\S+)\s*$", signed_text, re.M)
    }
    unsigned = {"keys.asc", "signature.txt.asc"}
    if set(declared) != set(all_members) - unsigned:
        raise ValueError("The signed Dawro member inventory differs from the ZIP contents.")
    member_hashes = {name: sha256(data) for name, data in all_members.items() if name in declared}
    mismatches = [name for name, digest in member_hashes.items() if declared[name] != digest]
    if mismatches:
        raise ValueError(f"Dawro member hashes disagree with the signed list: {sorted(mismatches)}.")

    usfm_members = {name: data for name, data in all_members.items() if name.lower().endswith(".usfm")}
    codes = discover_codes(usfm_members)
    return usfm_members, member_hashes, signature, codes


def validate_captures() -> tuple[str, str, str]:
    for path in (DETAILS, INDEX, DEVELOPER_DETAILS):
        if not path.is_file():
            raise FileNotFoundError(f"Retained eBible source capture is missing: {path.relative_to(ROOT)}")
    details = DETAILS.read_text(encoding="utf-8", errors="replace")
    required = (
        "The Holy Bible in the Dawuro language of Ethiopia, Latin script",
        "DWRLTW or dwrl", "Language: ", "copyright © 2024",
        "Contributor: The Word for the World International",
        "Creative Commons Attribution Share-Alike license 4.0",
        "dwrl_usfm.zip", "2025-05-01",
    )
    if any(phrase.lower() not in details.lower() for phrase in required):
        raise ValueError("The retained Dawro edition page does not show the pinned title, language, license, and package evidence.")
    index_text = INDEX.read_text(encoding="utf-8", errors="replace")
    indexed_ids = set(re.findall(r"details\.php\?id=(dwrENT|dwrNT|dwrl)\b", index_text, re.I))
    indexed_ids = {item.lower() for item in indexed_ids}
    if indexed_ids != {"dwrent", "dwrnt", "dwrl"}:
        raise ValueError(f"The retained eBible index shows unexpected Dawro edition identifiers: {sorted(indexed_ids)}.")
    developer_text = DEVELOPER_DETAILS.read_text(encoding="utf-8", errors="replace")
    if "dwrl_usfm.zip" not in developer_text:
        raise ValueError("The retained Dawro developer details page does not link the pinned USFM package.")
    return details, index_text, developer_text


def expected_source_labels(raw: bytes, member_name: str) -> list[tuple[int, str]]:
    """Extract only explicit source chapter/verse labels for order comparison."""
    text = raw.decode("utf-8-sig")
    current_chapter = None
    labels = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        chapter = re.match(r"^\\c\s+(\d+)\s*$", line)
        if chapter:
            current_chapter = int(chapter.group(1))
            continue
        verse = re.match(r"^\\v\s+(\S+)", line)
        if verse:
            if current_chapter is None:
                raise ValueError(f"Verse marker before a chapter in {member_name}:{line_number}.")
            labels.append((current_chapter, verse.group(1)))
    return labels


def build() -> tuple[list[dict], list[dict], list[dict], dict]:
    if not SOURCE.is_file():
        raise FileNotFoundError("Retain the publisher's original Dawro USFM ZIP before building readers.")
    package = SOURCE.read_bytes()
    details_html, index_html, developer_html = validate_captures()
    members, member_hashes, signature, codes = read_and_verify_package(package)
    readers = []
    corpora = []
    inventory = []
    menu_entries = []
    total_chapters = 0
    total_labels = 0

    for position, code in enumerate(codes, start=1):
        member_name = next(name for name in members if name.endswith(f"-{code}dwrl.usfm"))
        raw = members[member_name]
        parsed = maale.parse_book(raw, member_name)
        observed_labels = parsed["unit_labels"]
        source_labels = expected_source_labels(raw, member_name)
        if observed_labels != source_labels:
            raise ValueError(f"Extracted Dawro labels or their order differ from source {member_name}.")
        source_chapters = [
            int(match.group(1)) for match in re.finditer(r"^\\c\s+(\d+)\s*$", raw.decode("utf-8-sig"), re.M)
        ]
        if source_chapters != list(range(1, parsed["chapter_count"] + 1)):
            raise ValueError(f"Nonconsecutive or mismatched source chapter labels in {member_name}.")

        english_title = maale.BOOK_NAMES[code]
        source_title_label = next(
            (item["text"] for item in parsed["book_metadata"] if item["marker"] == "toc2"),
            parsed["source_title"],
        )
        if not source_title_label:
            raise ValueError(f"No publisher-provided title label is preserved for {member_name}.")
        reader_id = f"dawro-latin-{code.lower()}-research"
        corpus_id = f"dawro-dwrl-2024-{code.lower()}"
        note_count = sum(len(chapter.get("notes", [])) for chapter in parsed["chapters"])
        continuation_count = sum(
            len(verse.get("continuations", []))
            for chapter in parsed["chapters"] for verse in chapter["verses"]
        )
        metadata = {
            "reader_id": reader_id,
            "research_corpus_id": corpus_id,
            "canon_id": None,
            "title": f"{english_title} — Dawro Bible (DWRLTW / dwrl, Latin script)",
            "display_name": f"{english_title} · Dawro · eBible.org (Latin)",
            "text_origin": "published_translation",
            "translation_id": "dawro-dwrl-2024",
            "language": "Dawro",
            "language_tag": "dwr",
            "language_assignment_status": "publisher_declared_in_source_page",
            "script_code": "Latn",
            "translator": "Not identified on the publisher's edition page.",
            "contributor": "The Word for the World International",
            "translation_basis_status": "unknown",
            "translation_basis_note": "The publisher's edition page does not identify a source language or relay-language path; neither is inferred.",
            "edition": "The Holy Bible in the Dawuro language of Ethiopia, Latin script; copyright © 2024; the retained edition page is dated 2025-05-01.",
            "edition_scope": (
                f"One of 66 USFM book members in the publisher's DWRLTW / dwrl package. The publisher labels the work a Holy Bible; "
                "the digital module inventory is not a comparison against a print edition and does not establish completeness, translation accuracy, "
                "or equivalence to any Ethiopian Orthodox Tewahedo or Eritrean Orthodox canon list. No canon crosswalk is assigned."
            ),
            "rights_classification": "open_license",
            "license_id": "CC-BY-SA-4.0",
            "license_url": LICENSE_URL,
            "copyright_notice": (
                "Copyright © 2024 The Word for the World International. Source edition: eBible.org, DWRLTW / dwrl, "
                "The Holy Bible in the Dawuro language of Ethiopia, Latin script (Dawro, dwr). The publisher identifies "
                "The Word for the World International as contributor and states CC BY-SA 4.0 for the translation text. "
                "Change made: publisher USFM was parsed into reader JSON; source text and markers were preserved where handled, "
                "and original USFM remains bundled for audit. Any source figures/assets not bundled are excluded; the publisher "
                "states that picture terms differ. The publisher has not endorsed this archive or its changes."
            ),
            "commercial_use": (
                "The source-stated CC BY-SA 4.0 permits commercial sharing and adaptation with attribution, a link to the license, "
                "indication of changes, and ShareAlike for adaptations. Images and other media have separate terms and are not bundled."
            ),
            "unit_label": "USFM verse labels observed",
            "unit_count": parsed["unit_count"],
            "verse_marker_count": parsed["unit_count"],
            "chapter_count": parsed["chapter_count"],
            "section_label": "Chapter",
            "chapter_structure_note": (
                f"This source member has {parsed['chapter_count']} consecutive numeric chapter markers, {parsed['unit_count']} observed verse labels, "
                f"{note_count} extracted notes, {len(parsed['front_matter'])} front-matter elements, {continuation_count} unnumbered continuation segments, "
                f"and USFM markers {parsed['marker_counts']}. Chapter/verse labels are retained in source order. Counts describe this digital member, "
                "not printed completeness, translation accuracy, or a canon match."
            ),
            "chapter_structure_status": "source_package_parsed_with_limits",
            "source_numbered_unit_count": parsed["unit_count"],
            "source_unnumbered_unit_count": continuation_count,
            "book_order_in_source": position,
            "source_pages": f"readers/source/dawro/dwrl_usfm.zip::{member_name}",
            "source_package_sha256": sha256(package),
            "source_snapshot_sha256": member_hashes[member_name],
            "source_ids": SOURCE_IDS,
            "rights_status": "CC BY-SA 4.0 for the translation text as stated on the specific 2024 DWRLTW / dwrl edition page; image/media terms are separate.",
            "verification_status": (
                f"The exact source member {member_name} has SHA-256 {member_hashes[member_name]}, matching the ZIP's clear-signed checksum list. "
                f"The list's signature verifies against the package-included key ({signature['signer_fingerprint']}); a maintainer page lists the same fingerprint, "
                "which is corroboration only and does not independently establish identity, custody, or signing authority. The signature uses legacy DSA-1024/SHA-1. "
                "Automated extraction checked every explicit chapter and verse label against this member, retaining the label sequence and represented USFM structure. "
                "This establishes local extraction and package integrity, not wording accuracy, community review, translation basis, print completeness, or canon identity."
            ),
            "transcription_note": (
                "Machine-readable display extraction from the publisher's USFM. Chapter/verse label sequences were compared directly with source lines; "
                "the original signed package is retained beside the reader. No independent linguistic proofread or collation was performed."
            ),
            "editorial_signs_note": (
                "Publisher title labels, verse labels, chapter divisions, headings, notes, front matter, paragraph/poetry markers, continuations, "
                "and recognized USFM structure are represented in the extracted reader. The complete original USFM remains available in the bundled ZIP; "
                "the reader parser fails on unreviewed structural markers. Source and reader label sequence equality is checked per member."
            ),
            "front_matter": parsed["front_matter"],
            "source_book_metadata": parsed["book_metadata"],
            "chapters": parsed["chapters"],
        }
        reader_path = ROOT / "readers" / f"{reader_id}.json"
        write_text_atomically(reader_path, json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", newline="\n")
        readers.append(metadata)
        total_chapters += parsed["chapter_count"]
        total_labels += parsed["unit_count"]
        review = metadata["verification_status"]
        corpora.append({
            "corpus_id": corpus_id,
            "title": metadata["title"],
            "reader_id": reader_id,
            "unit_count": parsed["unit_count"],
            "reader_status": "bundled_research_reader",
            "canon_mapping_state": "not_mapped",
            "candidate_canon_id": None,
            "canon_mapping_note": "No EOTC or Eritrean Orthodox canon crosswalk is assigned; this source's 66-module inventory is not a Church-list mapping.",
            "language_description": "Dawro, publisher-declared BCP 47 language tag dwr.",
            "script_description": "Latin script (Latn), declared by the specific DWRLTW / dwrl edition page.",
            "unit_summary": f"{parsed['unit_count']} explicit source verse labels across {parsed['chapter_count']} consecutive chapter divisions in this member.",
            "rights_classification": "open_license",
            "rights_status": metadata["copyright_notice"],
            "license_id": "CC-BY-SA-4.0",
            "license_url": LICENSE_URL,
            "review_status": review,
            "source_ids": SOURCE_IDS,
            "text_origin": "published_translation",
            "language_tag": "dwr",
            "script_code": "Latn",
            "translation_id": "dawro-dwrl-2024",
            "translator": metadata["translator"],
            "translation_basis_status": "unknown",
            "translation_basis_note": metadata["translation_basis_note"],
            "edition_statement": metadata["edition"],
        })
        inventory.append({
            "position": position,
            "book_code": code,
            "member_name": member_name,
            "source_title": parsed["source_title"],
            "vernacular_title_label": source_title_label,
            "byte_length": len(raw),
            "sha256": member_hashes[member_name],
            "chapter_count": parsed["chapter_count"],
            "verse_label_count": parsed["unit_count"],
            "note_count": note_count,
            "front_matter_item_count": len(parsed["front_matter"]),
            "unnumbered_continuation_count": continuation_count,
            "marker_counts": parsed["marker_counts"],
        })
        menu_entries.append({
            "position": position,
            "book_code": code,
            "english_navigation_label": english_title,
            "source_title_label": source_title_label,
            "reader_id": reader_id,
            "chapter_count": parsed["chapter_count"],
            "source_verse_label_count": parsed["unit_count"],
            "canon_mapping_state": "not_mapped",
        })

    manifest = {
        "manifest_version": 1,
        "title": "eBible.org DWRLTW / dwrl Dawro Latin-script USFM package audit",
        "source_id": "SRC-405",
        "source_url": PACKAGE_URL,
        "edition_page_url": DETAIL_URL,
        "catalogue_index_url": INDEX_URL,
        "captured_at": REVIEWED_AT,
        "archive_sha256": sha256(package),
        "archive_byte_length": len(package),
        "zip_member_count": EXPECTED_MEMBER_COUNT,
        "zip_crc_check": "passed",
        "signed_member_count": len(member_hashes),
        "signature": signature,
        "usfm_book_count": len(inventory),
        "source_order_codes": codes,
        "usfm_members": inventory,
        "totals": {"chapter_markers": total_chapters, "observed_verse_labels": total_labels},
        "retained_capture_hashes": {
            "edition_page": {"path": DETAILS.relative_to(ROOT).as_posix(), "sha256": sha256(DETAILS.read_bytes()), "byte_length": DETAILS.stat().st_size},
            "developer_details_page": {"path": DEVELOPER_DETAILS.relative_to(ROOT).as_posix(), "sha256": sha256(DEVELOPER_DETAILS.read_bytes()), "byte_length": DEVELOPER_DETAILS.stat().st_size},
            "eBible_download_index": {"path": INDEX.relative_to(ROOT).as_posix(), "sha256": sha256(INDEX.read_bytes()), "byte_length": INDEX.stat().st_size},
        },
        "verification": (
            "Exact ZIP SHA-256 is pinned; ZIP CRC passed; GnuPG verified the clear-signed SHA-256 list against the included key; "
            "all signed member hashes match; the signer fingerprint matches the maintainer page as a cross-reference only; "
            "the 66 USFM identifiers match the conventional 66-module set; every reader's chapter/verse labels match source order."
        ),
        "limits": (
            "Legacy DSA-1024/SHA-1 signature and co-distributed key do not independently prove signer identity, custody, or authority. "
            "The publisher's title calls the work a Holy Bible; this is not a print completeness audit: 66 digital USFM modules do not prove "
            "complete printed contents, translation accuracy, "
            "community review, source/relay language, or equivalence to an EOTC or Eritrean Orthodox canon. English navigation titles are not translations "
            "of the Dawro book titles. Figure assets are not distributed under the text license and are not included."
        ),
    }
    write_text_atomically(MANIFEST, json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", newline="\n")

    menu = {
        "title": "Dawro DWRLTW / dwrl Bible, Latin script",
        "language_tag": "dwr",
        "script_code": "Latn",
        "edition_page_url": DETAIL_URL,
        "package_url": PACKAGE_URL,
        "source_ids": SOURCE_IDS,
        "package_sha256": sha256(package),
        "entry_count": len(menu_entries),
        "canon_mapping_state": "not_mapped",
        "scope_note": "This menu follows the exact publisher ZIP member order. English titles are navigation aids only. The publisher's 66 USFM members are not mapped to an EOTC or Eritrean Orthodox canon list.",
        "entries": menu_entries,
    }
    write_text_atomically(MENU_JSON, json.dumps(menu, ensure_ascii=False, indent=2) + "\n", newline="\n")
    links = "\n".join(
        f'<a class="book" href="../index.html?reader={entry["reader_id"]}#reader">'
        f'<span>{entry["position"]}</span><span><strong>{entry["english_navigation_label"]}</strong>'
        f'<small>{entry["source_title_label"]} · {entry["chapter_count"]} chapters · {entry["source_verse_label_count"]} labels</small></span></a>'
        for entry in menu_entries
    )
    html = f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Dawro Latin-script Bible readers — Ethiopian Bible Library</title>
<style>body{{margin:0;background:#f8f5ee;color:#183a35;font:16px/1.5 system-ui,sans-serif}}main{{max-width:1100px;margin:auto;padding:clamp(1rem,4vw,3rem)}}h1{{font:2rem Georgia,serif}}.note{{padding:1rem;background:#fff;border-left:4px solid #bd9452}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,19rem),1fr));gap:.65rem;margin-top:1.5rem}}.book{{display:flex;gap:1rem;align-items:flex-start;padding:1rem;background:white;border:1px solid #ded8c9;color:inherit;text-decoration:none}}.book:hover,.book:focus{{border-color:#a57431;background:#fffdf7}}.book>span:first-child{{color:#96713d;min-width:1.5rem}}small{{display:block;color:#667571;margin-top:.15rem}}a:focus-visible{{outline:3px solid #286c91;outline-offset:2px}}</style></head>
<body><main><p><a href="../index.html#reader">← Archive reader</a></p><h1>Dawro Bible · Latin script</h1>
<p><em>Geeshsha Mas'aafaa</em> · DWRLTW / dwrl · CC BY-SA 4.0</p>
<p class="note">This offline menu follows the source package order. English titles are navigation aids, not translations of Dawro titles. These 66 digital modules are research readers with no canon crosswalk; extraction checks do not establish wording accuracy, print completeness, or translation basis. See the <a href="../readers/source/dawro/SOURCE-NOTICE.txt">source and rights notice</a> and <a href="dawro-latin-usfm-source-manifest.json">package audit</a>.</p>
<div class="grid">{links}</div></main></body></html>'''
    write_text_atomically(MENU_HTML, html, newline="\n")

    notice = (
        "Dawro Bible (DWRLTW / dwrl), Latin script — source notice\n\n"
        "Copyright © 2024 The Word for the World International. The edition page identifies The Word for the World International as contributor; it does not name an individual translator.\n"
        f"Edition and rights page: {DETAIL_URL}\nOriginal USFM package: {PACKAGE_URL}\n"
        "The publisher states CC BY-SA 4.0 for the translation text.\n"
        f"License: {LICENSE_URL}\n\n"
        "Change made: publisher USFM was parsed into reader JSON. Chapter and verse labels were compared in source order; front matter, headings, notes, recognized structure, and continuations are represented. Original USFM remains in the package. The parser fails closed on unreviewed structural markers. The publisher has not endorsed the archive or these format changes.\n"
        "The eBible.org page says included pictures have separate restrictions; no image files are bundled.\n"
        f"The retained 70-member ZIP passes CRC checks. Its clear-signed SHA-256 list verifies against the public key included in the ZIP; all 68 declared member hashes match. The signer fingerprint ({KEY_FINGERPRINT}) matches the maintainer's page ({KEY_FINGERPRINT_URL}), a cross-reference rather than independent identity, custody, or authority proof. The signature uses legacy DSA-1024/SHA-1.\n"
        "No source/relay language, translation accuracy, independent review, print-edition completeness, or EOTC/Eritrean Orthodox canon equivalence is established. The 66-module inventory is limited to this digital source package. English book names are navigation aids, not translated Dawro titles.\n"
    )
    write_text_atomically(NOTICE, notice, newline="\n")

    sources = [
        {
            "source_id": "SRC-403",
            "source_name": "eBible.org — Dawro resource labels in retained Bible download index",
            "url": INDEX_URL,
            "local_copy_url": INDEX.relative_to(ROOT).as_posix(),
            "local_sha256": sha256(INDEX.read_bytes()),
            "inspection_and_limitations": (
                f"Captured 2026-10-26 at {INDEX.relative_to(ROOT).as_posix()} ({INDEX.stat().st_size} bytes; SHA-256 {sha256(INDEX.read_bytes())}). "
                "The Ethiopia section contains three distinct Dawro resource identifiers: dwrENT (Ethiopic script Bible), dwrNT (Latin-script New Testament), "
                "and dwrl (Latin-script Holy Bible). This is a count of labels on one provider index, not a count of distinct translation projects, "
                "a language-wide census, a rights mapping for the other records, or a completeness/accuracy determination."
            ),
            "archive_status": "Three Dawro labels verified in the captured provider index; not conflated with edition identity or canon coverage.",
        },
        {
            "source_id": "SRC-404",
            "source_name": "eBible.org — DWRLTW / dwrl Dawro Latin-script edition and rights page",
            "url": DETAIL_URL,
            "local_copy_url": DETAILS.relative_to(ROOT).as_posix(),
            "local_sha256": sha256(DETAILS.read_bytes()),
            "inspection_and_limitations": (
                "The retained and live eBible.org page identifies Geeshsha Mas'aafaa, The Holy Bible in the Dawuro language of Ethiopia, Latin script, "
                "language tag dwr, edition code DWRLTW / dwrl, copyright © 2024 The Word for the World International, contributor The Word for the World International, "
                "and a page date of 2025-05-01. The page states CC BY-SA 4.0 for the translation text and distinguishes picture terms. "
                "It does not name individual translators, identify a source or relay language, or establish accuracy, community review, printed completeness, or church-canon identity."
            ),
            "archive_status": "Edition-specific language, script, contributor, and CC BY-SA 4.0 notice captured; no textual or canon certification.",
            "rights_classification": "unknown",
            "rights_status": "This record is the provider's edition and license-information webpage. Its retained notice states CC BY-SA 4.0 for the Dawro translation text and distinguishes picture terms. This establishes the provider-stated text license, not reuse rights in the webpage itself. Rights for the separately bundled USFM package and converted readers are recorded in their own records.",
            "rights_basis": "The captured edition page identifies CC BY-SA 4.0 for translation text but does not establish a license for reproducing the information webpage. The unknown classification is scoped to the webpage resource, not to the separately identified text layer.",
        },
        {
            "source_id": "SRC-405",
            "source_name": "eBible.org — retained DWRLTW / dwrl Dawro publisher USFM package",
            "url": PACKAGE_URL,
            "local_copy_url": SOURCE.relative_to(ROOT).as_posix(),
            "local_metadata_url": MANIFEST.relative_to(ROOT).as_posix(),
            "inspection_and_limitations": (
                f"Retrieved 2026-10-26; retained ZIP is {len(package)} bytes with SHA-256 {sha256(package)}. All {EXPECTED_MEMBER_COUNT} ZIP members pass CRC validation. "
                f"The clear-signed list covers {len(member_hashes)} files; GnuPG verifies it against the included key fingerprint {signature['signer_fingerprint']}, "
                f"and all declared file hashes match. The fingerprint also appears on the key maintainer's page (SRC-406), but that does not independently prove identity, custody, or authority. "
                f"The package contains {len(inventory)} USFM modules. Every module parsed; chapter and verse label sequences match the original member lines. "
                "The module count is not a print completeness audit, language specialist review, accuracy check, or canon crosswalk."
            ),
            "archive_status": "Original USFM package retained; archive and member hashes, CRCs, signature, source labels, and chapter sequences audited with limits stated.",
            "rights_classification": "mixed",
            "rights_status": "The 66 USFM scripture-text members are identified by the retained provider notice as CC BY-SA 4.0; follow its attribution, change-indication, and ShareAlike terms. The ZIP also contains a copyright HTML page, stylesheet, public key, and signature files whose reuse terms are not established here. This mixed classification applies to the aggregate package; it does not withdraw or broaden the stated text license. Images are not bundled.",
            "rights_basis": "The retained provider notice states CC BY-SA 4.0 for translation text. The 70-member ZIP inventory shows .htm, .css, and .asc files alongside USFM; no separate permission basis was established for every ancillary file. The text-layer license is recorded separately on each reader.",
        },
        {
            "source_id": "SRC-406",
            "source_name": "Michael Paul Johnson — published fingerprint reference for eBible.org signed file lists",
            "url": KEY_FINGERPRINT_URL,
            "inspection_and_limitations": (
                f"The page lists public-key fingerprint {KEY_FINGERPRINT}, which matches the signer reported by GnuPG for the checksum list in the retained Dawro ZIP. "
                "This maintainer-page comparison is corroboration only; the key is co-distributed in the ZIP and this does not independently establish key identity, custody, signing authority, or the translation publisher's identity."
            ),
            "archive_status": "Fingerprint cross-reference only; not independent identity or authority verification.",
        },
    ]
    print(
        f"Built {len(readers)} Dawro Latin-script research readers; {total_chapters} chapter markers; "
        f"{total_labels} source verse labels; 70 ZIP members; package SHA-256 {sha256(package)}."
    )
    return readers, corpora, sources, manifest


if __name__ == "__main__":
    build()
