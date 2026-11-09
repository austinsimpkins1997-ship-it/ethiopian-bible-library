"""Build Alaba-K’abeena New Testament research readers from retained eBible.org USFM."""

from __future__ import annotations

import hashlib
import html
import json
import re
import zipfile
from pathlib import Path

import build_maale_research_readers as maale
from archive_manifest import write_text_atomically
from book_code_crosswalks import PUBLISHER_BOOK_CODE_CANDIDATES

ROOT = Path(__file__).resolve().parent
SOURCE_DIR = ROOT / "readers" / "source" / "alaba-kabeena"
SOURCE = SOURCE_DIR / "alw_usfm.zip"
DETAILS = SOURCE_DIR / "alw-details.html"
COPYRIGHT_PAGE = SOURCE_DIR / "alw-copyright.html"
ARC_2015_PAGE = SOURCE_DIR / "arc-2015.html"
PACKAGE_URL = "https://www.ebible.org/Scriptures/alw_usfm.zip"
DETAIL_URL = "https://ebible.org/bible/details.php?all=1&id=alw"
ARC_2015_URL = "https://arc.dbs.org/data/scripture/ALWWFTW/index.html"
RIGHTS_URL = "https://ebible.org/alw/copyright.htm"
LICENSE_URL = "https://creativecommons.org/licenses/by-sa/4.0/"
KEY_FINGERPRINT_URL = maale.KEY_FINGERPRINT_URL
KEY_FINGERPRINT = maale.KEY_FINGERPRINT
SOURCE_IDS = ["SRC-414", "SRC-415"]
ARC_2015_SOURCE_ID = "SRC-436"
ARC_2015_SHA256 = "625ecc48059129d8dfaff61d172c7ed98e650b65326a5304b409515822c6b94f"
EXPECTED_PACKAGE_SHA256 = "57ba620cf2a288d02cdfc5fa61caa92d682423d383c19c9626ffea007437542a"
EXPECTED_CODES = [
    "MAT", "MRK", "LUK", "JHN", "ACT", "ROM", "1CO", "2CO", "GAL", "EPH", "PHP", "COL",
    "1TH", "2TH", "1TI", "2TI", "TIT", "PHM", "HEB", "JAS", "1PE", "2PE", "1JN", "2JN",
    "3JN", "JUD", "REV",
]
REVIEWED_AT = "2026-10-26"
COPYRIGHT = (
    "Copyright © 2025 The Word for the World International. Source: eBible.org Alaba-K’abeena NT "
    "(ALWWTW / alw), language tag alw. The edition page names The Word for the World International as contributor, "
    "and states CC BY-SA 4.0 for translation text. This archive converted the retained USFM to reader JSON, "
    "preserves source labels and supported structure, and identifies the conversion as a change; no publisher endorsement is implied. "
    "Images have separate terms and are not included."
)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_source_package() -> tuple[bytes, dict[str, bytes], dict[str, str], dict]:
    package = SOURCE.read_bytes()
    if sha256(package) != EXPECTED_PACKAGE_SHA256:
        raise ValueError("Retained Alaba-K’abeena USFM package differs from the pinned provider bytes.")
    with zipfile.ZipFile(SOURCE) as archive:
        bad = archive.testzip()
        if bad:
            raise ValueError(f"Alaba-K’abeena ZIP CRC validation failed at {bad}.")
        members = {name: archive.read(name) for name in archive.namelist()}
    if not {"keys.asc", "signature.txt.asc"}.issubset(members):
        raise ValueError("Alaba-K’abeena package lacks its included signing key or signed hash list.")
    signature = maale.verify_checksum_signature(members["keys.asc"], members["signature.txt.asc"])
    declared = {
        match.group(2): match.group(1).lower()
        for match in re.finditer(
            r"^([0-9a-f]{64})\s+(\S+)\s*$",
            members["signature.txt.asc"].decode("utf-8", "replace"), re.M,
        )
    }
    expected_names = set(members) - {"keys.asc", "signature.txt.asc"}
    if set(declared) != expected_names:
        raise ValueError("Signed Alaba-K’abeena hash list does not cover exactly the ordinary ZIP members.")
    mismatched = [name for name, digest in declared.items() if sha256(members[name]) != digest]
    if mismatched:
        raise ValueError(f"Alaba-K’abeena package members disagree with signed hashes: {sorted(mismatched)}.")
    return package, members, declared, signature


def build() -> tuple[list[dict], list[dict], list[dict], dict]:
    for path in (DETAILS, COPYRIGHT_PAGE):
        if not path.is_file():
            raise FileNotFoundError(f"Retain the captured Alaba-K’abeena page: {path.name}.")
    details = DETAILS.read_text(encoding="utf-8", errors="replace")
    copyright_html = COPYRIGHT_PAGE.read_text(encoding="utf-8", errors="replace")
    required = (
        "Alaba-K’abeena NT", "ALWWTW", "copyright © 2025", "Creative Commons Attribution Share-Alike license 4.0",
        "alw_usfm.zip", "The Word for the World International",
    )
    if any(phrase not in details for phrase in required):
        raise ValueError("Retained Alaba-K’abeena edition page lacks its pinned title, contributor, rights, or package evidence.")
    if "Creative Commons Attribution Share-Alike license 4.0" not in copyright_html:
        raise ValueError("Retained Alaba-K’abeena copyright page does not state the expected text license.")
    if not ARC_2015_PAGE.is_file():
        raise FileNotFoundError("Retain the Digital Bible Society ARC 2015 Alaba-K’abeena metadata capture.")
    arc_2015_bytes = ARC_2015_PAGE.read_bytes()
    if sha256(arc_2015_bytes) != ARC_2015_SHA256:
        raise ValueError("The retained Digital Bible Society ARC metadata page differs from the pinned 2015 capture.")
    arc_2015_text = arc_2015_bytes.decode("utf-8", errors="replace")
    if not all(value in arc_2015_text for value in ("The Halaba New Testament", "ALWWFTW", ">2015<")):
        raise ValueError("The retained ARC page does not identify the expected 2015 Halaba New Testament record.")

    package, members, hashes, signature = read_source_package()
    canon_registry = json.loads((ROOT / "canon-registry.json").read_text(encoding="utf-8"))
    canon_titles = {book["canon_id"]: book["display_name"] for book in canon_registry["books"]}
    source_files = {name: data for name, data in members.items() if name.lower().endswith(".usfm")}
    readers, corpora, title_labels, inventory = [], [], [], []
    for name, raw in source_files.items():
        if not re.fullmatch(r"\d{2}-[A-Z0-9]{3}alw\.usfm", name):
            raise ValueError(f"Unexpected Alaba-K’abeena USFM member name {name!r}.")
        parsed = maale.parse_book(raw, name)
        if not name.endswith(f"-{parsed['code']}alw.usfm"):
            raise ValueError(f"USFM filename and book identity disagree in {name}.")
        if parsed["code"] in {row["book_code"] for row in inventory}:
            raise ValueError(f"Duplicate Alaba-K’abeena book code {parsed['code']}.")
        title = maale.BOOK_NAMES[parsed["code"]]
        candidate_canon_id = PUBLISHER_BOOK_CODE_CANDIDATES.get(parsed["code"])
        if candidate_canon_id not in canon_titles or not candidate_canon_id.startswith("eotc-nt-"):
            raise ValueError(f"No direct EOTC New Testament title crosswalk exists for USFM code {parsed['code']}.")
        canon_title = canon_titles[candidate_canon_id]
        source_title = next((item["text"] for item in parsed["book_metadata"] if item["marker"] == "toc2"), parsed["source_title"])
        title_labels.append({
            "position": len(title_labels) + 1, "book_code": parsed["code"],
            "source_title_label": source_title, "candidate_canon_id": candidate_canon_id,
        })
        reader_id = f"alaba-kabeena-{parsed['code'].lower()}-research"
        corpus_id = f"alw-2025-{parsed['code'].lower()}"
        label_count = parsed["unit_count"]
        note_count = sum(len(chapter.get("notes", [])) for chapter in parsed["chapters"])
        continuation_count = sum(
            len(verse.get("continuations", []))
            for chapter in parsed["chapters"] for verse in chapter["verses"]
        )
        scope = (
            f"One of 27 conventional New Testament USFM book modules in the provider's ALWWTW / alw edition. "
            f"A reviewed work/title crosswalk links USFM {parsed['code']} to the EOTC list title {canon_title} "
            f"({candidate_canon_id}) using the official Church list and USFM code table (SRC-029 and SRC-396). "
            "This reader remains a separate research translation; the crosswalk does not establish EOTC or Eritrean edition identity, "
            "tradition affiliation, translation accuracy, or completeness."
        )
        verification = (
            f"The exact source member {name} has SHA-256 {hashes[name]}, matching the signed file list in the retained ZIP. "
            f"GnuPG verifies that list against the co-distributed key ({signature['signer_fingerprint']}); the fingerprint also appears on the key maintainer's "
            "published page, which is not independent proof of identity, custody, or signing authority. The signature uses legacy DSA-1024/SHA-1. "
            "Reader structure is regenerated from the exact retained USFM member and retains its source chapter and verse labels, recognized headings, "
            "introduction matter, notes, and supported structural markers. These checks do not establish translation accuracy, print completeness, "
            "source-language basis, local community review, or Church-canon identity."
        )
        reader = {
            "reader_id": reader_id, "research_corpus_id": corpus_id, "canon_id": None,
            "title": f"{title} — Alaba-K’abeena New Testament (ALWWTW / alw, 2025)",
            "display_name": f"{title} · Alaba-K’abeena · eBible.org",
            "text_origin": "published_translation", "translation_id": "alw-alwwtw-2025",
            "language": "Alaba-K’abeena", "language_tag": "alw",
            "language_assignment_status": "publisher_declared_in_edition_page_and_USFM_package",
            "script_code": "Ethi", "translator": "Not named in the inspected edition page or retained USFM headers",
            "contributor": "The Word for the World International",
            "translation_basis_status": "unknown",
            "translation_basis_note": "The inspected edition page does not identify a source language or relay-language path; none is inferred.",
            "edition": "Alaba-K’abeena: ሃዕሮ ወኣድ መጻፈ (New Testament), ALWWTW / alw; copyright © 2025.",
            "edition_scope": scope, "rights_classification": "open_license",
            "license_id": "CC-BY-SA-4.0", "license_url": LICENSE_URL,
            "copyright_notice": COPYRIGHT,
            "commercial_use": "The source-stated CC BY-SA 4.0 terms permit commercial sharing and adaptations with attribution, indication of changes, and ShareAlike. Images and other media have separate terms and are not bundled.",
            "unit_label": "USFM verse labels observed", "unit_count": label_count,
            "verse_marker_count": label_count, "chapter_count": parsed["chapter_count"], "section_label": "Chapter",
            "chapter_structure_note": (
                f"This member has {parsed['chapter_count']} consecutive chapter divisions, {label_count} distinct source verse labels, "
                f"{note_count} notes, {len(parsed['front_matter'])} front-matter elements, and USFM marker counts {parsed['marker_counts']}. "
                "Counts describe extraction from this exact source member only."
            ),
            "chapter_structure_status": "source_package_parsed_with_limits",
            "source_numbered_unit_count": label_count, "source_unnumbered_unit_count": continuation_count,
            "source_pages": f"readers/source/alaba-kabeena/alw_usfm.zip::{name}",
            "source_package_sha256": sha256(package), "source_snapshot_sha256": hashes[name],
            "source_ids": SOURCE_IDS, "rights_status": COPYRIGHT, "verification_status": verification,
            "transcription_note": "Display-reader extraction from publisher USFM. The exact USFM member remains in the retained source ZIP; no independent wording proofread or print collation is claimed.",
            "editorial_signs_note": "Publisher USFM remains bundled so its original markup and reader extraction can be inspected. This reader does not replace the source encoding.",
            "front_matter": parsed["front_matter"], "source_book_metadata": parsed["book_metadata"],
            "chapters": parsed["chapters"],
        }
        write_text_atomically(ROOT / "readers" / f"{reader_id}.json", json.dumps(reader, ensure_ascii=False, indent=2) + "\n", newline="\n")
        readers.append(reader)
        corpora.append({
            "corpus_id": corpus_id, "title": reader["title"], "reader_id": reader_id,
            "unit_count": label_count, "reader_status": "bundled_research_reader",
            "canon_mapping_state": "reviewed_match", "candidate_canon_id": candidate_canon_id,
            "canon_mapping_note": (
                f"Reviewed work/title match for {candidate_canon_id} ({canon_title}): the Ethiopian Orthodox Church's cited "
                f"81-entry list names {canon_title}; the exact retained Alaba-K’abeena USFM member identifies itself with "
                f"standard code {parsed['code']}; the official USFM/USX table maps that code to {title}. Evidence: SRC-029, "
                "SRC-396, SRC-414, and SRC-415. This is a work/title crosswalk only. It does not establish EOTC, Eritrean, "
                "or other tradition affiliation; exact edition identity; textual accuracy; printed completeness; or translation "
                "source/relay language. This research reader is not canon-linked coverage or a verified Ethiopic Church edition."
            ),
            "language_description": "Alaba-K’abeena, IANA BCP 47 language tag alw.",
            "script_description": "Ethiopic script (Ethi), observed in the retained USFM text; this is edition-level script evidence.",
            "unit_summary": f"{label_count} distinct source verse labels in {parsed['chapter_count']} consecutive USFM chapter divisions; this member only.",
            "rights_classification": "open_license", "rights_status": COPYRIGHT,
            "license_id": "CC-BY-SA-4.0", "license_url": LICENSE_URL,
            "review_status": verification, "source_ids": SOURCE_IDS,
            "text_origin": "published_translation", "language_tag": "alw", "script_code": "Ethi",
            "translation_id": "alw-alwwtw-2025",
            "translator": "Not named in the inspected edition page or retained USFM headers",
            "translation_basis_status": "unknown",
            "translation_basis_note": "The inspected edition page does not identify source or relay language.",
            "edition_statement": reader["edition"],
        })
        inventory.append({
            "position": len(inventory) + 1, "book_code": parsed["code"], "member_name": name,
            "source_title": parsed["source_title"], "source_title_label": source_title,
            "byte_length": len(raw), "sha256": hashes[name], "chapter_count": parsed["chapter_count"],
            "verse_label_count": label_count, "note_count": note_count,
            "front_matter_item_count": len(parsed["front_matter"]),
            "unnumbered_continuation_count": continuation_count, "marker_counts": parsed["marker_counts"],
        })
    if [row["book_code"] for row in inventory] != EXPECTED_CODES:
        raise ValueError("Alaba-K’abeena package no longer has the pinned 27-module USFM book inventory.")

    manifest = {
        "manifest_version": 1,
        "title": "eBible.org Alaba-K’abeena NT (ALWWTW / alw) source package audit",
        "source_ids": SOURCE_IDS, "language_tag": "alw", "script_code": "Ethi",
        "edition_page_url": DETAIL_URL, "rights_page_url": RIGHTS_URL, "package_url": PACKAGE_URL,
        "captured_at": REVIEWED_AT,
        "source_edition_page": {
            "local_path": DETAILS.relative_to(ROOT).as_posix(), "byte_length": DETAILS.stat().st_size,
            "sha256": sha256(DETAILS.read_bytes()),
        },
        "source_copyright_page": {
            "local_path": COPYRIGHT_PAGE.relative_to(ROOT).as_posix(), "byte_length": COPYRIGHT_PAGE.stat().st_size,
            "sha256": sha256(COPYRIGHT_PAGE.read_bytes()),
        },
        "archive_byte_length": len(package), "archive_sha256": sha256(package),
        "member_count": len(members), "zip_crc_check": "passed",
        "signed_member_count": len(hashes), "signature": signature,
        "usfm_book_count": len(inventory), "usfm_members": inventory,
        "verification": "ZIP CRC passed; GnuPG verified the clear-signed member SHA-256 list against its co-distributed key; every listed member hash matches. Reader source member IDs, chapter divisions, and verse labels are generated from this exact package.",
        "limits": "The signing key is included in the same ZIP as the signature. Its fingerprint matches the key maintainer's published page, which is corroboration rather than independent identity/custody/authority proof. DSA-1024/SHA-1 is legacy cryptography. The 27 conventional USFM module identifiers do not establish equivalence to an EOTC/Eritrean canon, print completeness, translation accuracy, language-community review, or source-language basis.",
    }
    manifest_path = ROOT / "research" / "alaba-kabeena-usfm-source-manifest.json"
    write_text_atomically(manifest_path, json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", newline="\n")

    menu = {
        "title": "eBible.org Alaba-K’abeena New Testament",
        "edition_id": "ALWWTW / alw", "language_tag": "alw", "script_code": "Ethi",
        "source_ids": SOURCE_IDS, "canon_mapping_state": "reviewed_match",
        "canon_crosswalk_source_ids": ["SRC-029", "SRC-396"],
        "menu_basis": "USFM package member order; English labels are navigation aids, and publisher source labels remain visible.",
        "scope_note": (
            "Each of the 27 standard USFM member codes has a reviewed work/title match to the corresponding one of the "
            "EOTC list's 27 conventional New Testament titles (sources SRC-029 and SRC-396). These remain Alaba-K’abeena "
            "research translations, not identified EOTC/Eritrean editions; the crosswalk does not establish textual accuracy or completeness."
        ),
        "entries": title_labels,
    }
    write_text_atomically(ROOT / "research" / "alaba-kabeena-menu.json", json.dumps(menu, ensure_ascii=False, indent=2) + "\n", newline="\n")
    items = "\n".join(
        f'<li lang="alw" translate="no"><span>{html.escape(row["source_title_label"])}</span> '
        f'<small>Title match: {html.escape(canon_titles[row["candidate_canon_id"]])} · {html.escape(row["book_code"])}</small> '
        f'<a href="../index.html?reader=alaba-kabeena-{row["book_code"].lower()}-research#reader">Open research reader · {html.escape(maale.BOOK_NAMES[row["book_code"]])}</a></li>'
        for row in title_labels
    )
    html_menu = (
        '<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
        '<title>Alaba-K’abeena New Testament</title><link rel="stylesheet" href="../styles.css">'
        '<main class="research-menu"><p><a href="../index.html">Ethiopian Bible Library</a></p>'
        '<h1>Alaba-K’abeena New Testament</h1>'
        '<p>Publisher: eBible.org, edition ALWWTW / alw, copyright © 2025 The Word for the World International. '
        'The provider states CC BY-SA 4.0 for translation text; image terms are separate. Each standard member code has a reviewed title match to one of the EOTC list’s 27 conventional New Testament titles. These remain research readers, not identified EOTC/Eritrean editions or canon-linked coverage. This title match does not establish text accuracy or completeness.</p>'
        f'<p><a href="{DETAIL_URL}">Publisher edition and license record</a> · '
        f'<a href="{PACKAGE_URL}">Original USFM package</a> · '
        '<a href="alaba-kabeena-usfm-source-manifest.json">Local structure and checksum audit</a></p>'
        f'<p>Modules: {len(title_labels)}. Labels and book order follow the retained publisher package.</p>'
        f'<ol lang="alw" translate="no">{items}</ol>'
        '<p>Package integrity and structural extraction are checked; translation accuracy, source-language basis, community review, print completeness, and canon identity are not established.</p></main></html>\n'
    )
    write_text_atomically(ROOT / "research" / "alaba-kabeena-menu.html", html_menu, newline="\n")
    notice = (
        "Alaba-K’abeena New Testament (ALWWTW / alw) — source and rights notice\n\n"
        "Copyright © 2025 The Word for the World International. The provider names The Word for the World International as contributor; no individual translator is named in the inspected edition page or retained USFM headers.\n"
        f"Edition and rights page: {DETAIL_URL}\nRights notice: {RIGHTS_URL}\nOriginal USFM: {PACKAGE_URL}\nLicense: {LICENSE_URL}\n\n"
        "The provider states CC BY-SA 4.0 for translation text; adaptations must retain attribution, identify changes, and use ShareAlike. Images have separate terms and are not bundled.\n"
        "This archive converted the retained USFM package into JSON research readers and records that change; it does not imply publisher endorsement. The original 31-member ZIP, captured edition pages, and signed member hashes remain available. ZIP CRC and signed hashes passed; the signature uses legacy DSA-1024/SHA-1 and a key co-distributed in the ZIP. A matching key-maintainer fingerprint is corroboration only, not independent proof of identity, custody, or signing authority.\n"
        "The source does not identify a source language or relay path. A separate reviewed work/title crosswalk maps each standard USFM code to the corresponding EOTC list title; this does not identify the translation as an EOTC/Eritrean edition or establish wording accuracy, print completeness, or local community review.\n"
    )
    write_text_atomically(SOURCE_DIR / "SOURCE-NOTICE.txt", notice, newline="\n")
    sources = [
        {
            "source_id": SOURCE_IDS[0],
            "source_name": "eBible.org — Alaba-K’abeena NT (ALWWTW / alw) edition and rights records",
            "url": DETAIL_URL, "local_copy_url": DETAILS.relative_to(ROOT).as_posix(),
            "local_rights_copy_url": COPYRIGHT_PAGE.relative_to(ROOT).as_posix(),
            "inspection_and_limitations": (
                "Inspected 2026-10-26. The retained edition page identifies Alaba-K’abeena (alw), title ሃዕሮ ወኣድ መጻፈ, "
                "edition ALWWTW / alw, copyright © 2025, The Word for the World International as contributor, and its linked USFM package. "
                "The edition and copyright pages state CC BY-SA 4.0 for text, with separate image terms. No individual translator, source/relay language, "
                "translation accuracy, community review, print completeness, or Ethiopian/Eritrean Orthodox canon identity is established."
            ),
            "archive_status": "Edition identity, provider-stated text license, and source-page captures retained; research-only with reviewed work/title crosswalk, not an EOTC/Eritrean edition.",
            "rights_classification": "unknown",
            "rights_status": "This record is the provider's edition and license-information webpage. Its retained notice states that the Alaba-K’abeena scripture text is licensed CC BY-SA 4.0; images have separate terms. This establishes the provider-stated text license, not reuse rights in the webpage itself. Rights for the separately bundled USFM package and converted readers are recorded in their own records.",
            "rights_basis": "The retained edition/copyright pages identify CC BY-SA 4.0 for scripture text but do not establish a license for reproducing the information webpage. The unknown classification is scoped to the webpage resource, not to the separately identified text layer.",
        },
        {
            "source_id": SOURCE_IDS[1],
            "source_name": "eBible.org — Alaba-K’abeena (alw) signed USFM package",
            "url": PACKAGE_URL, "local_copy_url": SOURCE.relative_to(ROOT).as_posix(),
            "local_metadata_url": manifest_path.relative_to(ROOT).as_posix(),
            "inspection_and_limitations": (
                f"Exact provider ZIP retained ({manifest['archive_byte_length']} bytes; SHA-256 {manifest['archive_sha256']}). "
                f"Its {manifest['member_count']}-member ZIP passes CRC; GnuPG verified its signed hash list against the co-distributed key, "
                f"and all {manifest['signed_member_count']} member hashes match. Fingerprint {signature['signer_fingerprint']} matches the key maintainer's page, "
                "not independent identity, custody, or authority evidence; the signature uses legacy DSA-1024/SHA-1. The package contains 27 USFM modules, "
                f"{sum(row['chapter_count'] for row in inventory)} chapter divisions, and {sum(row['verse_label_count'] for row in inventory)} verse labels. "
                "Per-member chapter and verse labels are regenerated from exact package members. These structural checks do not prove text accuracy or completeness."
            ),
            "archive_status": "Original package stored offline; CRC, signed member inventory, hashes, and parser-extracted source labels audited; research-only with reviewed work/title crosswalk.",
            "rights_classification": "mixed",
            "rights_status": "The 27 USFM scripture-text members are identified by the retained provider notice as CC BY-SA 4.0; comply with attribution, change-indication, and ShareAlike conditions. The ZIP also contains a copyright HTML page, stylesheet, public key, and signature files whose reuse terms are not established here. This mixed classification applies to the aggregate package; it does not withdraw or broaden the stated text license. Images are not bundled.",
            "rights_basis": "The retained provider notice and edition record state CC BY-SA 4.0 for text. The 31-member ZIP inventory shows ancillary .htm, .css, and .asc files alongside USFM; no separate permission basis was established for every ancillary member. The text-layer license is recorded separately on each reader.",
        },
        {
            "source_id": ARC_2015_SOURCE_ID,
            "source_name": "Digital Bible Society ARC — The Halaba New Testament (ALWWFTW, 2015) metadata",
            "url": ARC_2015_URL,
            "local_copy_url": ARC_2015_PAGE.relative_to(ROOT).as_posix(),
            "inspection_and_limitations": (
                f"Inspected and retained 2026-10-27 ({len(arc_2015_bytes)} bytes; SHA-256 {ARC_2015_SHA256}). "
                "The ARC metadata page labels ALWWFTW as a 2015 Alaba-K’abeena (alw) New Testament, identifies Ethiopic (Geʽez) script, "
                "The Word for the World Ethiopia as agency, and displays license status RESERVED. This is a catalog record, not the underlying text or a licensing instrument. "
                "It does not state the source/relay language or name individual translators. The relationship between this 2015 ALWWFTW record and eBible.org’s 2025 ALWWTW / alw edition is not established."
            ),
            "archive_status": "Captured metadata-only historical edition lead; no text bundled, no canon crosswalk, and no translation path established.",
            "rights_classification": "unknown",
            "rights_status": (
                "ARC labels the 2015 record’s license field RESERVED. The underlying text and its applicable reuse terms were not inspected; "
                "this metadata does not grant permission. No text or media from this record are bundled."
            ),
        },
    ]
    print(
        f"Built {len(readers)} Alaba-K’abeena research readers; "
        f"{sum(reader['chapter_count'] for reader in readers)} chapter divisions; "
        f"{sum(reader['unit_count'] for reader in readers)} observed verse labels."
    )
    return readers, corpora, sources, manifest


if __name__ == "__main__":
    build()
