"""Build Yemsa New Testament research readers from the retained eBible.org USFM package.

Readers preserve the publisher's language, script, book order, labels, and USFM
structure. English book names are navigation aids only. No EOTC or Eritrean
Orthodox canon crosswalk is inferred.
"""

from __future__ import annotations

import hashlib
import json
import re
import zipfile
from pathlib import Path

import build_maale_research_readers as maale
from archive_manifest import write_text_atomically

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "readers" / "source" / "yemsa" / "jnje_usfm.zip"
DETAILS = ROOT / "readers" / "source" / "yemsa" / "jnje-details.html"
MANIFEST = ROOT / "research" / "yemsa-usfm-source-manifest.json"
NOTICE = ROOT / "readers" / "source" / "yemsa" / "SOURCE-NOTICE.txt"
MENU_JSON = ROOT / "research" / "yemsa-menu.json"
MENU_HTML = ROOT / "research" / "yemsa-menu.html"
SOURCE_IDS = ["SRC-407", "SRC-408", "SRC-409"]
DETAIL_URL = "https://ebible.org/scriptures/details.php?all=1&id=jnje"
PACKAGE_URL = "https://ebible.org/Scriptures/jnje_usfm.zip"
LICENSE_URL = "https://creativecommons.org/licenses/by-sa/4.0/"
KEY_FINGERPRINT_URL = "https://mljohnson.org/gpg.htm"
KEY_FINGERPRINT = "54D714D76956DA6673DC1EEA5F62009D93505F26"
EXPECTED_PACKAGE_SHA256 = "d21d6e0d4109923945ba5907ce84f177252d22357ed99867d30ae9d35c6f1c83"
EXPECTED_CODES = [
    "MAT", "MRK", "LUK", "JHN", "ACT", "ROM", "1CO", "2CO", "GAL", "EPH", "PHP", "COL",
    "1TH", "2TH", "1TI", "2TI", "TIT", "PHM", "HEB", "JAS", "1PE", "2PE", "1JN", "2JN",
    "3JN", "JUD", "REV",
]
REVIEWED_AT = "2026-10-26"
COPYRIGHT = (
    "Copyright © 2025 The Word for the World International. Source: eBible.org, Yemsa NT Ethiopic (JNJETW / jnje), "
    "Yemsa language (jnj), Ethiopic script. The publisher lists The Word for the World International as contributor; "
    "no individual translator is named in the inspected edition record or retained USFM headers. The publisher states CC BY-SA 4.0 for the translation text. "
    "This archive converted publisher USFM to reader JSON with recognized labels and structures represented in the reader; "
    "the original USFM package remains bundled. These format changes do not imply publisher endorsement."
)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def parse_members(package: bytes) -> tuple[dict[str, bytes], dict[str, str], dict]:
    with zipfile.ZipFile(SOURCE) as archive:
        bad = archive.testzip()
        if bad:
            raise ValueError(f"Yemsa USFM source ZIP failed CRC validation at {bad}.")
        all_members = {name: archive.read(name) for name in archive.namelist()}

    if sha256(package) != EXPECTED_PACKAGE_SHA256:
        raise ValueError("The retained Yemsa USFM ZIP differs from the pinned upstream package bytes.")
    if len(all_members) != 31:
        raise ValueError(f"Expected the 31-member Yemsa package, found {len(all_members)}.")
    usfm_members = {name: data for name, data in all_members.items() if name.lower().endswith(".usfm")}
    signed_data = all_members.get("signature.txt.asc")
    key_data = all_members.get("keys.asc")
    if not signed_data or not key_data:
        raise ValueError("Yemsa package is missing its included key or clear-signed checksum list.")

    # Verify the checksum-list signature against the package's included key and
    # compare that key to its published fingerprint page. This establishes
    # tamper evidence, not independent identity or signing authority.
    if maale.KEY_FINGERPRINT != KEY_FINGERPRINT:
        raise ValueError("The signer fingerprint pin differs from the shared checksum verifier.")
    signature = maale.verify_checksum_signature(key_data, signed_data)
    if signature["signer_fingerprint"] != KEY_FINGERPRINT:
        raise ValueError("Yemsa checksum list was signed by an unexpected key.")

    signed_text = signed_data.decode("utf-8", "replace")
    declared = {
        match.group(2): match.group(1).lower()
        for match in re.finditer(r"^([0-9a-f]{64})\s+(\S+)\s*$", signed_text, re.M)
    }
    listed_names = set(declared)
    package_names = set(all_members) - {"keys.asc", "signature.txt.asc"}
    if listed_names != package_names:
        raise ValueError(
            f"Signed Yemsa file inventory differs from ZIP members; missing={sorted(package_names-listed_names)}, "
            f"extra={sorted(listed_names-package_names)}."
        )
    actual_hashes = {name: sha256(data) for name, data in all_members.items() if name in listed_names}
    mismatched = [name for name in listed_names if declared[name] != actual_hashes[name]]
    if mismatched:
        raise ValueError(f"Yemsa package members disagree with the signed SHA-256 list: {sorted(mismatched)}.")
    codes = []
    for name, data in usfm_members.items():
        parsed = maale.parse_book(data, name)
        code = parsed["code"]
        if not re.fullmatch(r"\d{2}-" + re.escape(code) + r"jnje\.usfm", name):
            raise ValueError(f"USFM identity {code} disagrees with Yemsa member name {name}.")
        if code in codes:
            raise ValueError(f"Duplicate Yemsa book code {code}.")
        codes.append(code)
    if len(usfm_members) != 27 or set(codes) != set(EXPECTED_CODES):
        raise ValueError(f"Expected the source's 27 conventional New Testament modules; found {len(codes)} / {sorted(codes)}.")
    return usfm_members, actual_hashes, signature


def build() -> tuple[list[dict], list[dict], list[dict], dict]:
    if not SOURCE.is_file() or not DETAILS.is_file():
        raise FileNotFoundError("Retain the Yemsa package and the captured edition page before building its readers.")
    package = SOURCE.read_bytes()
    members, member_hashes, signature = parse_members(package)
    details_html = DETAILS.read_text(encoding="utf-8", errors="replace")
    required_page_evidence = (
        "Yemsa NT Ethiopic", "The New Testament in the Yemsa language of Ethiopia, Ethiopic script",
        "copyright © 2025", "Creative Commons Attribution Share-Alike license 4.0",
        "jnje_usfm.zip",
    )
    if any(phrase not in details_html for phrase in required_page_evidence):
        raise ValueError("The retained eBible.org edition page no longer contains the pinned Yemsa title, license, and package evidence.")

    readers = []
    corpora = []
    inventory = []
    source_title_labels = []
    ordered_codes = EXPECTED_CODES
    for position, code in enumerate(ordered_codes, start=1):
        member_name = next(name for name in members if re.search(rf"-?{re.escape(code)}jnje\.usfm$", name))
        raw = members[member_name]
        parsed = maale.parse_book(raw, member_name)
        if parsed["code"] != code:
            raise ValueError(f"Unexpected identity in Yemsa member {member_name}.")
        english_title = maale.BOOK_NAMES[code]
        toc2 = next((item["text"] for item in parsed["book_metadata"] if item["marker"] == "toc2"), None)
        vernacular_title = toc2 or parsed["source_title"]
        if not vernacular_title:
            raise ValueError(f"Yemsa source title label is missing for {code}.")
        source_title_labels.append({"position": position, "book_code": code, "source_label": vernacular_title})

        reader_id = f"yemsa-{code.lower()}-research"
        corpus_id = f"jnje-2025-{code.lower()}"
        unit_count = parsed["unit_count"]
        note_count = sum(len(chapter.get("notes", [])) for chapter in parsed["chapters"])
        unnumbered_count = sum(
            len(verse.get("continuations", []))
            for chapter in parsed["chapters"] for verse in chapter["verses"]
        )
        scope = (
            "One of 27 USFM book members in the source-publisher's Yemsa New Testament (Yemsa NT Ethiopic, JNJETW / jnje). "
            "These are conventional New Testament module identifiers; they do not establish equivalence to any EOTC or Eritrean Orthodox canon list. "
            "No canon crosswalk is assigned. Counts describe this source member only."
        )
        structural_note = (
            f"This source member has {parsed['chapter_count']} consecutive chapter markers, {unit_count} distinct verse labels, "
            f"{note_count} source notes, {len(parsed['front_matter'])} recorded front-matter elements, and USFM markers "
            f"{parsed['marker_counts']}. Publisher labels and formatting distinctions are retained in reader structure; "
            "counts establish package-to-reader extraction only, not printed completeness or translation accuracy."
        )
        verification = (
            f"The exact member {member_name} has SHA-256 {member_hashes[member_name]}, matching the clear-signed SHA-256 list in the retained ZIP. "
            f"GnuPG verifies that list against the package-included key ({signature['signer_fingerprint']}); the fingerprint matches the "
            f"key maintainer's published page ({KEY_FINGERPRINT_URL}). This is tamper evidence only: the key is co-distributed, "
            "and its identity, custody, and authority are not independently established. The parser retains source verse labels, "
            "notes, headings, front matter, continuations, and recognized USFM structure. It does not certify accuracy, completeness, "
            "community review, or church-canon identity."
        )
        reader = {
            "reader_id": reader_id,
            "research_corpus_id": corpus_id,
            "canon_id": None,
            "title": f"{english_title} — Yemsa New Testament (JNJETW / jnje, 2025)",
            "display_name": f"{english_title} · Yemsa · eBible.org",
            "text_origin": "published_translation",
            "translation_id": "jnje-jnjetw-2025",
            "language": "Yemsa",
            "language_tag": "jnj",
            "language_assignment_status": "publisher_declared_in_source_package",
            "script_code": "Ethi",
            "translator": "Not named in the publisher's edition record or retained USFM headers",
            "contributor": "The Word for the World International",
            "translation_basis_status": "unknown",
            "translation_basis_note": "The publisher's edition record does not state the source language or a relay-language path; none is inferred.",
            "edition": "The New Testament in the Yemsa language of Ethiopia, Ethiopic script; copyright © 2025; source files dated 2025-05-06.",
            "edition_scope": scope,
            "rights_classification": "open_license",
            "license_id": "CC-BY-SA-4.0",
            "license_url": LICENSE_URL,
            "copyright_notice": COPYRIGHT,
            "commercial_use": "The source-stated CC BY-SA 4.0 terms permit commercial sharing and adaptation with attribution, indication of changes, and ShareAlike for adaptations. No image assets are bundled.",
            "unit_label": "USFM verse labels observed",
            "unit_count": unit_count,
            "verse_marker_count": unit_count,
            "chapter_count": parsed["chapter_count"],
            "section_label": "Chapter",
            "chapter_structure_note": structural_note,
            "chapter_structure_status": "source_package_parsed_with_limits",
            "source_numbered_unit_count": unit_count,
            "source_unnumbered_unit_count": unnumbered_count,
            "source_pages": f"readers/source/yemsa/jnje_usfm.zip::{member_name}",
            "source_package_sha256": sha256(package),
            "source_snapshot_sha256": member_hashes[member_name],
            "source_ids": SOURCE_IDS,
            "rights_status": COPYRIGHT,
            "verification_status": verification,
            "transcription_note": "Machine-readable display extraction from the publisher's USFM; the exact original member is retained in the source ZIP. No wording was independently proofread or collated.",
            "editorial_signs_note": "Source USFM chapter and verse labels, headings, paragraph/poetry markers, notes, cross-references, and front matter remain separately represented where recognized by the parser. The original USFM remains bundled for auditing markup and parser limits.",
            "front_matter": parsed["front_matter"],
            "source_book_metadata": parsed["book_metadata"],
            "chapters": parsed["chapters"],
        }
        write_text_atomically(ROOT / "readers" / f"{reader_id}.json", json.dumps(reader, ensure_ascii=False, indent=2) + "\n", newline="\n")
        readers.append(reader)
        corpora.append({
            "corpus_id": corpus_id,
            "title": reader["title"],
            "reader_id": reader_id,
            "unit_count": unit_count,
            "reader_status": "bundled_research_reader",
            "canon_mapping_state": "not_mapped",
            "candidate_canon_id": None,
            "canon_mapping_note": "No Ethiopian Orthodox Tewahedo or Eritrean Orthodox canon crosswalk is assigned. The source package contains 27 conventional New Testament modules; this does not establish equivalence to either Church's canon list.",
            "language_description": "Yemsa, publisher-declared BCP 47 language tag jnj.",
            "script_description": "Ethiopic script (Ethi), declared by the source edition page.",
            "unit_summary": f"{unit_count} distinct source verse labels in {parsed['chapter_count']} consecutive USFM chapter divisions; source-member count only.",
            "rights_classification": "open_license",
            "rights_status": COPYRIGHT,
            "license_id": "CC-BY-SA-4.0",
            "license_url": LICENSE_URL,
            "review_status": verification,
            "source_ids": SOURCE_IDS,
            "text_origin": "published_translation",
            "language_tag": "jnj",
            "script_code": "Ethi",
            "translation_id": "jnje-jnjetw-2025",
            "translator": "Not named in the publisher's edition record or retained USFM headers",
            "translation_basis_status": "unknown",
            "translation_basis_note": "The publisher's edition page does not identify a source language or relay path.",
            "edition_statement": reader["edition"],
        })
        inventory.append({
            "position": position,
            "book_code": code,
            "member_name": member_name,
            "source_title": parsed["source_title"],
            "vernacular_title_label": vernacular_title,
            "byte_length": len(raw),
            "sha256": member_hashes[member_name],
            "chapter_count": parsed["chapter_count"],
            "verse_label_count": unit_count,
            "note_count": note_count,
            "front_matter_item_count": len(parsed["front_matter"]),
            "unnumbered_continuation_count": unnumbered_count,
            "marker_counts": parsed["marker_counts"],
        })

    source_manifest = {
        "manifest_version": 1,
        "title": "eBible.org Yemsa NT Ethiopic (JNJETW / jnje) source package audit",
        "source_id": "SRC-408",
        "source_url": PACKAGE_URL,
        "edition_page_url": DETAIL_URL,
        "captured_at": REVIEWED_AT,
        "source_edition_page": {
            "local_path": "readers/source/yemsa/jnje-details.html",
            "sha256": sha256(DETAILS.read_bytes()),
            "byte_length": DETAILS.stat().st_size,
        },
        "archive_sha256": sha256(package),
        "archive_byte_length": len(package),
        "zip_crc_check": "passed",
        "member_count": 31,
        "signed_member_count": 29,
        "signature": signature,
        "usfm_book_count": len(inventory),
        "usfm_members": inventory,
        "verification": "ZIP CRCs passed; GnuPG verified the clear-signed member SHA-256 list against the included key; its fingerprint matches the key maintainer's published fingerprint page; all 29 signed file members match their declared hashes; the 27 USFM book codes match the package's NT inventory.",
        "limits": "The signing key is distributed inside the same ZIP as the signed list. The external fingerprint-page comparison is a cross-reference to the key maintainer's page, not independent identity or authority proof. The signature uses legacy DSA-1024/SHA-1. The publisher calls the work the New Testament; the conventional 27-member book set is not an EOTC/Eritrean Orthodox canon crosswalk, proof of print completeness, community review, or translation accuracy.",
    }
    write_text_atomically(MANIFEST, json.dumps(source_manifest, ensure_ascii=False, indent=2) + "\n", newline="\n")
    menu = {
        "title": "eBible.org Yemsa New Testament, Ethiopic script",
        "edition_id": "JNJETW / jnje",
        "language_tag": "jnj",
        "script_code": "Ethi",
        "source_id": "SRC-407",
        "source_package_id": "SRC-408",
        "menu_basis": "27 USFM book members retained from the publisher's downloaded source package; order follows the package's numeric file prefixes.",
        "canon_mapping_state": "not_mapped",
        "scope_note": "English navigation names are interface labels derived from standard USFM book codes. Vernacular source labels are preserved. No Church-canon mapping is asserted.",
        "entries": source_title_labels,
    }
    write_text_atomically(MENU_JSON, json.dumps(menu, ensure_ascii=False, indent=2) + "\n", newline="\n")
    list_items = "\n".join(
        f'<li lang="jnj" translate="no"><span>{entry["source_label"]}</span> '
        f'<a href="../index.html?reader=yemsa-{entry["book_code"].lower()}-research#reader">Open research reader · {maale.BOOK_NAMES[entry["book_code"]]}</a></li>'
        for entry in source_title_labels
    )
    html = (
        '<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
        '<title>Yemsa New Testament — source menu</title><link rel="stylesheet" href="../styles.css">'
        '<main class="research-menu"><p><a href="../index.html">Ethiopian Bible Library</a></p>'
        '<h1>Yemsa New Testament · Ethiopic script</h1>'
        '<p>Publisher: eBible.org, edition JNJETW / jnje, © 2025 The Word for the World International. '
        'The publisher states CC BY-SA 4.0 for the text. Each entry opens a local research reader; '
        'these conventional book modules are not mapped to the EOTC or Eritrean Orthodox canon.</p>'
        f'<p><a href="{DETAIL_URL}">Publisher edition and license record</a> · '
        f'<a href="{PACKAGE_URL}">Original USFM package</a> · '
        '<a href="yemsa-usfm-source-manifest.json">Local structure and checksum audit</a></p>'
        f'<ol lang="jnj" translate="no">{list_items}</ol>'
        '<p>Counts describe source files and the extracted display only. They do not establish print completeness, '
        'translation accuracy, translation basis, or church-canon identity.</p></main></html>\n'
    )
    write_text_atomically(MENU_HTML, html, newline="\n")
    notice = (
        "Yemsa New Testament (JNJETW / jnje), Ethiopic script — source notice\n\n"
        "Copyright © 2025 The Word for the World International.\n"
        "The edition record lists The Word for the World International as contributor; no individual translator is named in the retained record or USFM headers.\n"
        f"Edition and rights page: {DETAIL_URL}\n"
        f"Original USFM package: {PACKAGE_URL}\n"
        "The publisher states Creative Commons Attribution-ShareAlike 4.0 International for the translation text.\n"
        f"License text: {LICENSE_URL}\n\n"
        "Changes in this archive: source USFM was parsed into reader JSON. Chapter and verse labels, notes, headings, front matter, and recognized structure are represented in the reader; the original markup remains in the bundled USFM package. The publisher has not endorsed these changes.\n"
        "The original 31-member source ZIP, captured edition page, and signed checksum evidence are retained locally. The signed file hashes were checked; GnuPG verified the list against the co-distributed key. The key fingerprint matches the key maintainer's published page, but that does not independently prove identity, custody, or authority. DSA-1024/SHA-1 is legacy cryptography.\n"
        "The provider identifies this resource as a Yemsa New Testament. No source language or relay path is inferred. No EOTC or Eritrean Orthodox canon mapping, printed completeness, local community review, or translation accuracy is claimed.\n"
    )
    write_text_atomically(NOTICE, notice, newline="\n")
    sources = [
        {
            "source_id": "SRC-407",
            "source_name": "eBible.org — Yemsa NT Ethiopic (JNJETW / jnje) edition and rights record",
            "url": DETAIL_URL,
            "local_copy_url": "readers/source/yemsa/jnje-details.html",
            "inspection_and_limitations": (
                "Inspected 2026-10-26; the live and retained edition page identifies ‘Yemsa NT Ethiopic,’ title ጋዶ ቴያ, language Yemsa (jnj), "
                "The New Testament in the Yemsa language of Ethiopia, Ethiopic script, copyright © 2025 The Word for the World International, "
                "and the eBible.org USFM download. It states CC BY-SA 4.0 text terms requiring attribution, change indication, and ShareAlike. "
                "It says pictures have separate terms. This metadata does not establish source/relay language, accuracy, print completeness, "
                "community review, or EOTC/Eritrean Orthodox canon identity."
            ),
            "archive_status": "Official edition title, language, script, and text license retained locally; no canon crosswalk or accuracy certification.",
            "rights_classification": "unknown",
            "rights_status": "This record is the provider's edition and license-information webpage. Its retained notice states that the Yemsa scripture text is licensed CC BY-SA 4.0; pictures have separate terms. This establishes the provider-stated text license, not reuse rights in the webpage itself. Rights for the separately bundled USFM package and converted readers are recorded in their own records.",
            "rights_basis": "The captured edition notice identifies CC BY-SA 4.0 for scripture text but does not establish a license for reproducing the information webpage. The unknown classification is scoped to the webpage resource, not to the separately identified text layer.",
        },
        {
            "source_id": "SRC-408",
            "source_name": "eBible.org — Yemsa (jnje) publisher USFM package",
            "url": PACKAGE_URL,
            "local_copy_url": "readers/source/yemsa/jnje_usfm.zip",
            "local_metadata_url": "research/yemsa-usfm-source-manifest.json",
            "inspection_and_limitations": (
                f"Exact downloaded ZIP retained at readers/source/yemsa/jnje_usfm.zip ({len(package)} bytes; SHA-256 {sha256(package)}). "
                "The 31-member archive passes ZIP CRC validation. Its clear-signed checksum list covers 29 file members; GnuPG verified the signature "
                f"against the ZIP-included key ({signature['signer_fingerprint']}) and all signed member hashes match. The fingerprint also matches "
                f"the key maintainer's published page ({KEY_FINGERPRINT_URL}); this does not independently establish identity, key custody, or authority. "
                "The signature uses legacy DSA-1024/SHA-1. Twenty-seven USFM members carry the conventional NT identifiers, sequential chapter structures, "
                "and publisher verse labels; extraction checks establish package-to-reader correspondence only, not text accuracy or print completeness."
            ),
            "archive_status": "Original signed USFM source package stored offline; CRC, signed member inventory, checksums, chapter/label extraction audited; church-canon relation remains unmapped.",
            "rights_classification": "mixed",
            "rights_status": "The 27 USFM scripture-text members are identified by the retained provider notice as CC BY-SA 4.0; follow its attribution, change-indication, and ShareAlike terms. The ZIP also contains a copyright HTML page, stylesheet, public key, and signature files whose reuse terms are not established here. This mixed classification applies to the aggregate package; it does not withdraw or broaden the stated text license. Pictures are not included in the converted readers and have separate terms.",
            "rights_basis": "The retained provider notice states CC BY-SA 4.0 for translation text. The 31-member ZIP inventory shows .htm, .css, and .asc files alongside the USFM members; no separate permission basis was established for every ancillary file. The text-layer license is recorded separately on each reader.",
        },
        {
            "source_id": "SRC-409",
            "source_name": "Michael Paul Johnson — World English Bible editors key fingerprint page",
            "url": KEY_FINGERPRINT_URL,
            "inspection_and_limitations": (
                f"Inspected 2026-10-26. The page lists the World English Bible editors public-key fingerprint {KEY_FINGERPRINT}, matching the signer "
                "reported by GnuPG for the clear-signed checksum list in the Yemsa USFM ZIP. This is a fingerprint comparison to the key maintainer's "
                "published page, not an independent identity proof, certificate, or confirmation of authority over this particular translation."
            ),
            "archive_status": "Key fingerprint cross-reference only; signer identity, custody, and authority are not independently certified.",
        },
    ]
    print(
        f"Built {len(readers)} Yemsa research readers; {sum(x['chapter_count'] for x in readers)} chapter divisions; "
        f"{sum(x['unit_count'] for x in readers)} observed verse labels; source zip SHA-256 {sha256(package)}."
    )
    return readers, corpora, sources, source_manifest


if __name__ == "__main__":
    build()
